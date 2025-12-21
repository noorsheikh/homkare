import json
import boto3
from .config import Config

bedrock = boto3.client("bedrock-runtime")

def generate_answer(query: str, context_chunks: list) -> str:
    """
    Synthesizes a final answer using Titan Text Express based on context.
    """
    context_text = "\n\n".join([
        f"Source {i+1}: {c['metadata']['text']}"
        for i, c in enumerate(context_chunks)
    ])

    prompt = f"""Instruction: Answer the user's question using ONLY the context provided.
    If the answer is not in the context, say "I'm sorry, I don't have that info."

    Context:
    {context_text}

    Question: {query}

    Answer:"""

    body = json.dumps({
        "inputText": prompt,
        "textGenerationConfig": {
            "maxTokenCount": 512,
            "temperature": 0.1,
            "topP": 0.9
        }
    })

    response = bedrock.invoke_model(
        modelId=Config.GENERATION_MODEL,
        body=body,
        contentType="application/json",
        accept="application/json"
    )

    response_body = json.loads(response.get("body").read())
    return response_body['results'][0]['outputText'].strip()
