import json
import boto3
import uuid
import time

from rag_engine import get_chunks, get_embedding, Config

s3vector = boto3.client("s3vectors")

def lambda_handler(event, context):
  claims = event["requestContext"]["authorizer"]["claims"]
  user_id = claims["sub"]

  body = json.loads(event["body"])
  chunks = get_chunks(body["text"])
  vectors = []

  print(f"Processing {len(chunks)} chunks...")

  for chunk in chunks:
    # Skip short and noisy chunks.
    if len(chunk.text) < 10:
      continue

    vectors.append({
      "key": str(uuid.uuid4()),
        "data": {
          "float32": get_embedding(chunk.text),
        },
        "metadata": {
          "user_id": user_id,
          "text": chunk.text,
        },
    })
    time.sleep(0.1)  # 100ms delay = max 600 requests per minute.

  print(f"Chunks processing completed!")

  s3vector.put_vectors(
    vectorBucketName=Config.VECTOR_BUCKET,
    indexName=Config.VECTOR_INDEX,
    vectors=vectors,
  )

  return {
    "statusCode": 200,
    "body": json.dumps({
      "messsage": "Data ingested successfully",
      "chunks_created": len(chunks),
    })
  }
