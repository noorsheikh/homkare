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
  text = body["text"]

  embedding = get_embedding(text)

  s3control.put_vectors(
    vectorBucketName=VECTOR_BUCKET,
    indexName=VECTOR_INDEX,
    vectors=[
      {
        "key": str(uuid.uuid4()),
        "data": {
          "float32": embedding,
        },
        "metadata": {
          "user_id": user_id,
          "text": text,
        },
      },
    ],
  )

  return {
    "statusCode": 200,
    "body": json.dumps({"message": "Data Ingested Successfully!"})
  }
