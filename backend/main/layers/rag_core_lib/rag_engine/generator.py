import json
import boto3
from .config import Config

bedrock = boto3.client("bedrock-runtime")

def generate_answer(query: str, context_chunks: list) -> str:
    """
    Synthesizes a final answer using Titan Text Express based on context.
    """
    context_text = "\n\n".join([
        f"Source {i+1}: {c['metadata']['chunk_text']}"
        for i, c in enumerate(context_chunks)
    ])

    prompt = f"""You are an assistant for homeowners and HOA members.

    Use ONLY the provided context to answer.
    If the answer is not in the context, say:
    "I don’t have enough information to answer that."

    Context:
    {context_text}

    Question: {query}

    Answer:"""

    # Format the request payload using the model's native structure.
    request = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 512,
        "temperature": 0.5,
        "messages": [
            {
                "role": "user",
                "content": [{"type": "text", "text": prompt}],
            }
        ],
    })

    response = bedrock.invoke_model(
        modelId=Config.GENERATION_MODEL,
        body=request,
        contentType="application/json",
        accept="application/json"
    )

    response_body = json.loads(response.get("body").read())
    return response_body["content"][0]["text"].strip()
