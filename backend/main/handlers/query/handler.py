import json
import boto3

from rag_engine import generate_answer, get_embedding, Config

s3vector = boto3.client("s3vectors")

def lambda_handler(event, context):
  claims = event["requestContext"]["authorizer"]["claims"]
  user_id = claims["sub"]

  body = json.loads(event["body"])
  query = body["query"]

  response = s3vector.query_vectors(
    vectorBucketName=Config.VECTOR_BUCKET,
    indexName=Config.VECTOR_INDEX,
    topK=5,
    queryVector={
      "float32": get_embedding(query),
    },
    filter={
      "user_id": user_id,
    },
    returnMetadata=True,
    returnDistance=True,
  )

  results = response.get("vectors", [])
  print(f"vectors: {results}")

  final_answer = generate_answer(query, results)

  return {
    "statusCode": 200,
    "body": json.dumps({
      "answer": final_answer,
    }),
  }
