import json
import boto3
import uuid
import os

bedrock = boto3.client("bedrock-runtime")
s3control = boto3.client("s3vectors")

VECTOR_INDEX = os.environ["VECTOR_INDEX"]
VECTOR_BUCKET = os.environ["VECTOR_BUCKET"]

def get_embedding(text: str):
  response = bedrock.invoke_model(
    modelId="amazon.titan-embed-text-v2:0",
    body=json.dumps({"inputText": text}),
    contentType="application/json",
  )
  return json.loads(response["body"].read())["embedding"]

def lambda_handler(event, context):
  claims = event["requestContext"]["authorizer"]["claims"]
  user_id = claims["sub"]

  body = json.loads(event["body"])
  query = body["query"]

  embedding = get_embedding(query)

  response = s3control.query_vectors(
    vectorBucketName=VECTOR_BUCKET,
    indexName=VECTOR_INDEX,
    topK=3,
    queryVector={
      "float32": embedding,
    },
    filter={
      "user_id": user_id,
    },
    returnMetadata=True,
    returnDistance=True,
  )

  return {
    "statusCode": 200,
    "body": json.dumps(response),
  }
