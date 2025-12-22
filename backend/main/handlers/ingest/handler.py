import json
import boto3
import uuid
import time
import hashlib

from rag_engine import get_chunks, get_embedding, Config

s3vector = boto3.client("s3vectors")

def lambda_handler(event, context):
  claims = event["requestContext"]["authorizer"]["claims"]
  user_id = claims["sub"]

  body = json.loads(event["body"])
  chunks = get_chunks(body["text"])
  new_vectors = []

  print(f"Processing {len(chunks)} chunks...")

  for chunk in chunks:
    # Skip short and noisy chunks.
    if len(chunk.text) < 10:
      continue

    chunk_hash = hashlib.md5(chunk.text.encode('utf-8')).hexdigest()
    chunk_embedding = get_embedding(chunk.text)

    # Check if a chunk already exist with same embedding and tags.
    existing_check = s3vector.query_vectors(
      vectorBucketName=Config.VECTOR_BUCKET,
      indexName=Config.VECTOR_INDEX,
      topK=1,
      queryVector={"float32": chunk_embedding},
      filter={
        "$and": [
          {"user_id": user_id},
          {"text_hash": chunk_hash}
        ],
      },
      returnMetadata=True,
      returnDistance=True,
    )

    # Skip if a highly similar vector (distance ~0) with same metadata is found
    if existing_check.get("vectors"):
        best_match = existing_check["vectors"][0]
        # If the hash matches exactly AND distance is near zero, it's a duplicate
        if best_match.get("distance", 1.0) < 0.001:
            print(f"Skipping duplicate chunk (Hash: {chunk_hash})")
            continue


    new_vectors.append({
      "key": str(uuid.uuid4()),
        "data": {"float32": chunk_embedding},
        "metadata": {
          "user_id": user_id,
          "text": chunk.text,
          "text_hash": chunk_hash,
        },
    })
    time.sleep(0.1)  # 100ms delay = max 600 requests per minute.

  print(f"Chunks processing completed!")

  # Batch insert only new vectors.
  if new_vectors:
    s3vector.put_vectors(
      vectorBucketName=Config.VECTOR_BUCKET,
      indexName=Config.VECTOR_INDEX,
      vectors=new_vectors,
    )
    print(f"Successfully inserted {len(new_vectors)} new vectors.")
  else:
    print("No new vectors to insert.")

  return {
      "statusCode": 200,
      "body": json.dumps({
          "message": "Ingestion process completed",
          "chunks_processed": len(chunks),
          "new_vectors_added": len(new_vectors)
      })
  }
