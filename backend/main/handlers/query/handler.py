import json
import boto3
import uuid
import os

bedrock = boto3.client("bedrock-runtime")
s3control = boto3.client("s3vectors")

VECTOR_BUCKET_NAME = os.environ["VECTOR_BUCKET_NAME"]
VECTOR_INDEX_NAME = os.environ["VECTOR_INDEX_NAME"]

def get_embedding(text: str):
  response = bedrock.invoke_model(
    modelId="amazon.titan-embed-text-v2:0",
    body=json.dumps({"inputText": text, "dimensions": 1024}),
    contentType="application/json",
  )
  return json.loads(response["body"].read())["embedding"]

def generate_answer(query, context_chunks):
  """
  Synthesizes a final answer using Claude 3 Haiku based ONLY on retrieved context.
  """
  # 1. Prepare the context from your vector search results
  context_text = "\n\n".join([f"Source {i+1}: {c['metadata']['text']}" for i, c in enumerate(context_chunks)])

  # 2. Build the Titan-style prompt
  # Best practice for Titan: Instructions first, then context, then question.
  prompt = f"""
  Human: You are a helpful Homeowner Assistant. Answer the user's question using ONLY the provided context.
  If the answer is not in the context, say "I'm sorry, I don't have that specific information in my records. Please contact Customer Care at 877-550-7926."

  <context>
  {context_text}
  </context>

  Question: {query}

  Assistant:"""

  # 3. Call Amazon Titan Embed Text V1 model.
  body = json.dumps({
      "inputText": prompt,
      "textGenerationConfig": {
          "maxTokenCount": 512,  # Maximum length of the AI's response
          "temperature": 0.5,    # Low temperature = high factual accuracy
          "topP": 0.9,
          "stopSequences": []
      }
  })

  # 4. Invoke the model
  # Ensure your IAM role has bedrock:InvokeModel permission for this ID.
  response = bedrock.invoke_model(
      modelId="amazon.titan-text-express-v1",
      body=body,
      contentType="application/json",
      accept="application/json"
  )

  # 5. Parse the Titan-specific response format
  response_body = json.loads(response.get("body").read())
  print(response_body)

  # Titan returns a list of completions in the 'results' field
  return response_body['results'][0]['outputText'].strip()

def lambda_handler(event, context):
  claims = event["requestContext"]["authorizer"]["claims"]
  user_id = claims["sub"]

  body = json.loads(event["body"])
  query = body["query"]

  embedding = get_embedding(query)

  response = s3control.query_vectors(
    vectorBucketName=VECTOR_BUCKET_NAME,
    indexName=VECTOR_INDEX_NAME,
    topK=5,
    queryVector={
      "float32": embedding,
    },
    filter={
      "user_id": user_id,
    },
    returnMetadata=True,
    returnDistance=True,
  )

  results = response.get("vectors", [])
  print(results)

  final_answer = generate_answer(query, results)

  return {
    "statusCode": 200,
    "body": json.dumps({
      "answer": final_answer,
    }),
  }
