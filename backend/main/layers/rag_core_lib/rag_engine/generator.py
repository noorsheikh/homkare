"""Module for generating RAG-based answers using Amazon Bedrock."""

import json

from clients.factory import get_bedrock_client

from .config import Config

bedrock_client = get_bedrock_client()


def generate_answer(query: str, context_chunks: list) -> str:
	"""Synthesize a final answer based on provided source context.

	Assemble context chunks into a numbered list, construct a focused
	instructional prompt for the LLM, and return the generated
	text response.

	Args:
		query: The user's original question.
		context_chunks: A list of retrieved and reranked text segments.

	Returns:
		A string containing the synthesized answer or a fallback
		message if information is missing.

	"""
	context_text = '\n\n'.join(
		[
			f'Source {i + 1}: {c["metadata"]["chunk_text"]}'
			for i, c in enumerate(context_chunks)
		]
	)

	prompt = f"""You are an assistant for homeowners and HOA members.

    Use ONLY the provided context to answer.
    Do NOT mention "Based on the provided context", just start with your answer.
    If the answer is not in the context, say:
    "I don’t have enough information to answer that."

    Context:
    {context_text}

    Question: {query}

    Answer:"""

	# Format the request payload using the model's native structure.
	request = json.dumps(
		{
			'anthropic_version': 'bedrock-2023-05-31',
			'max_tokens': 512,
			'temperature': 0.5,
			'messages': [
				{
					'role': 'user',
					'content': [{'type': 'text', 'text': prompt}],
				}
			],
		}
	)

	response = bedrock_client.invoke_model(
		modelId=Config.GENERATION_MODEL,
		body=request,
		contentType='application/json',
		accept='application/json',
	)

	response_body = json.loads(response.get('body').read())
	return response_body['content'][0]['text'].strip()
