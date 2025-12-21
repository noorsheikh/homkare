import json
import boto3
import uuid
import os
import re

from chonkie import RecursiveChunker, RecursiveRules

bedrock = boto3.client("bedrock-runtime")
s3control = boto3.client("s3vectors")

VECTOR_BUCKET_NAME = os.environ["VECTOR_BUCKET_NAME"]
VECTOR_INDEX_NAME = os.environ["VECTOR_INDEX_NAME"]

chunker = RecursiveChunker(
  tokenizer="character",
  chunk_size=512,
  rules=RecursiveRules(),
  min_characters_per_chunk=1,
)

def get_embedding(text: str):
  response = bedrock.invoke_model(
    modelId="amazon.titan-embed-text-v2:0",
    body=json.dumps({"inputText": text, "dimensions": 1024}),
    contentType="application/json",
  )
  return json.loads(response["body"].read())["embedding"]

def clean_data(text: str) -> str:
    """
    Cleans raw homeowner document text by removing formatting artifacts and
    standardizing whitespace for optimal vector embedding.

    The function targets:
    1. Table of Contents leaders (dots/dashes followed by page numbers).
    2. Non-alphanumeric noise (excluding basic punctuation needed for context).
    3. Line-break hyphens (rejoining fragmented words).
    4. Excessive whitespace and inconsistent casing.

    Args:
        text (str): The raw extracted text from home warranty or orientation docs.

    Returns:
        str: A sanitized, lowercase string ready for semantic chunking.
    """
    # 1. Remove TOC leaders: Matches 3+ dots/spaces followed by optional digits
    # Example: ". . . . . . 23" -> " "
    text = re.sub(r'(?:\.\s?){3,}\s*\d*', ' ', text)

    # 2. Join broken words from line-breaks (Founda- tion -> Foundation)
    text = re.sub(r'(\w+)-\s+(\w+)', r'\1\2', text)

    # 3. Clean special characters but KEEP basic punctuation (. , ? !)
    # This preserves sentence boundaries for better semantic chunking.
    # If you want NO punctuation at all, use: re.sub(r'[^a-zA-Z0-9\s]', '', text)
    text = re.sub(r'[^\w\s.,?!]', '', text)

    # 4. Standardize whitespace: Collapse multiple spaces/newlines into one
    text = re.sub(r'\s+', ' ', text)

    return text.strip().lower()

def lambda_handler(event, context):
  claims = event["requestContext"]["authorizer"]["claims"]
  user_id = claims["sub"]

  body = json.loads(event["body"])
  text = body["text"]
  cleaned_text = clean_data(text)

  chunks = chunker.chunk(cleaned_text)

  vectors = []

  print(f"Processing {len(chunks)} chunks...")

  for chunk in chunks:

    # Skip short and noisy chunks.
    if len(chunk.text) < 10:
      continue

    embedding = get_embedding(chunk.text)

    vectors.append({
      "key": str(uuid.uuid4()),
        "data": {
          "float32": embedding,
        },
        "metadata": {
          "user_id": user_id,
          "text": chunk.text,
        },
    })

  print(f"Chunks processing completed!")

  s3control.put_vectors(
    vectorBucketName=VECTOR_BUCKET_NAME,
    indexName=VECTOR_INDEX_NAME,
    vectors=vectors,
  )

  return {
    "statusCode": 200,
    "body": json.dumps({
      "messsage": "Data ingested successfully",
      "chunks_created": len(chunks),
    })
  }
