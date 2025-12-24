import json
import boto3

from rag_engine import generate_answer, get_embedding, rerank_chunks, Config

s3vector = boto3.client("s3vectors")

def lambda_handler(event, context):
  claims = event["requestContext"]["authorizer"]["claims"]
  user_id = claims["sub"]

  body = json.loads(event["body"])
  query = body["query"]

  response = s3vector.query_vectors(
    vectorBucketName=Config.VECTOR_BUCKET,
    indexName=Config.VECTOR_INDEX,
    topK=20,
    queryVector={
      "float32": get_embedding(query),
    },
    filter={
      "$and": [
        {"user_id": user_id},
        {"visibility": "private"},
      ],
    },
    returnMetadata=True,
    returnDistance=True,
  )

  vectors = response.get("vectors", [])

  if not vectors:
    return {
      "statusCode": 200,
      "body": json.dumps({
        "answer": "I don't have enough information to answer that."
      })
    }

  # Rerank the initially vector chunks to show best matching result.
  top_chunks = rerank_chunks(
    query=query,
    chunks=vectors,
  )

  if not top_chunks:
    return {
      "statusCode": 200,
      "body": json.dumps({
        "answer": "I don't have enough information to answer that."
      })
    }

  final_answer = generate_answer(query, top_chunks)

  return {
    "statusCode": 200,
    "body": json.dumps({
      "answer": final_answer,
    }),
  }
