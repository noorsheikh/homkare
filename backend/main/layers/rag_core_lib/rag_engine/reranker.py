import json
import boto3
from .config import Config

bedrock = boto3.client("bedrock-runtime")

def rerank_chunks(
    query: str,
    chunks: list[dict],
    max_chunks: int = 6,
) -> list[dict]:
  """Cross-encoder reranker to re-rank the chunks to find the more relevant chunk to a given query."""
  scored_chunks = []

  for chunk in chunks:
    text = chunk["metadata"]["chunk_text"]

    prompt = f"""
    You are scoring how relevant a document chunk is to a question.

    Question:
    {query}

    Chunk:
    {text}

    Score relevance from 0 to 10.
    Return ONLY the number.
    """

    request = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 5,
        "temperature": 0.0,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}],
            }
        ],
    })
    print("reranker model: ", Config.RERANKER_MODEL)

    response = bedrock.invoke_model(
        modelId=Config.RERANKER_MODEL,
        body=request,
        contentType="application/json",
        accept="application/json"
    )

    raw = response["body"].read().decode("utf-8")
    print("raw: ", raw)
    score = float("".join(c for c in raw if c.isdigit() or c == "."))
    print("score: ", score)

    chunk["metadata"]["rerank_score"] = score
    scored_chunks.append(chunk)

  scored_chunks.sort(
    key=lambda x: x["metadata"]["rerank_score"],
    reverse=True,
  )


  return scored_chunks[:max_chunks]
