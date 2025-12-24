import concurrent.futures
import json

import boto3

from .config import Config

bedrock = boto3.client('bedrock-runtime')


def _get_single_chunk_score(
	query: str,
	chunk: dict,
) -> list[dict]:
	"""Helper to get score for one chunk (Parallelizable)."""
	text = chunk['metadata']['chunk_text']
	prompt = f"""
    Score the relevance of this chunk to the question: '{query}'.\nChunk: {text}\n
    Return ONLY a number 0-10.
    """

	# Correct Messages API Payload for Claude 3.5 Haiku.
	body = json.dumps(
		{
			'anthropic_version': 'bedrock-2023-05-31',
			'max_tokens': 10,
			'temperature': 0,
			'messages': [{'role': 'user', 'content': [{'type': 'text', 'text': prompt}]}],
		}
	)

	try:
		response = bedrock.invoke_model(
			modelId=Config.RERANKER_MODEL, body=body, contentType='application/json'
		)

		# Correct Parsing for Messages API
		response_body = json.loads(response['body'].read().decode('utf-8'))
		raw_text = response_body['content'][0]['text'].strip()

		# Extract numeric value safely
		score = float(''.join(c for c in raw_text if c.isdigit() or c == '.'))
		chunk['metadata']['rerank_score'] = score
	except Exception as e:
		print(f'Error scoring chunk: {e}')
		chunk['metadata']['rerank_score'] = 0.0

	return chunk


def rerank_chunks(
	query: str,
	chunks: list[dict],
) -> list[dict]:
	"""Uses Parallel threads to rerank chunks."""
	# Using ThreatPoolExecutor to run LLM calls in parallel.
	with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
		scored_chunks = list(
			executor.map(lambda c: _get_single_chunk_score(query, c), chunks)
		)

	# Pick only the chunks with score greater than or equal to 5.0.
	scored_chunks = [
		chunk for chunk in scored_chunks if chunk['metadata']['rerank_score'] >= 5.0
	]
	return scored_chunks
