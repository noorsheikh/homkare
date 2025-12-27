"""Module for reranking text chunks using Amazon Bedrock."""

import concurrent.futures
import json
import random
import time

from botocore.exceptions import ClientError
from clients.factory import get_bedrock_client

from .config import Config

bedrock_client = get_bedrock_client()


def _get_single_chunk_score(
	query: str,
	chunk: dict,
) -> list[dict]:
	"""Score the relevance of a single chunk against the query.

	Use a prompt-based evaluation via the configured Bedrock model to
	assign a numeric relevance score (0-10) to the chunk metadata.

	Args:
		query: The user's search query.
		chunk: A dictionary containing the text and metadata.

	Returns:
		The updated chunk dictionary including the 'rerank_score'.

	"""
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
		response = bedrock_client.invoke_model(
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
	max_retries: int = 6,
) -> list[dict]:
	"""Rerank a list of chunks based on query relevance using parallel threads.

	Execute multiple LLM scoring calls concurrently via ThreadPoolExecutor
	and filter the results to return only highly relevant segments.

	Args:
		query: The search query to compare against.
		chunks: A list of chunk dictionaries to be scored.
		max_retries: Max attempts per chunk to handle ThrottlingException.

	Returns:
		A list of chunks with a rerank_score of 5.0 or higher.

	"""

	def _safe_get_score(chunk):
		"""Wrap individual chunk scoring with retries."""
		for attempt in range(max_retries):
			try:
				# Assuming this function uses your shared bedrock client
				return _get_single_chunk_score(query, chunk)
			except ClientError as e:
				error_code = e.response.get('Error', {}).get('Code')
				if error_code == 'ThrottlingException' and attempt < max_retries - 1:
					# Exponential backoff: 1s, 2s, 4s... with random jitter
					sleep_time = (2**attempt) + random.uniform(0, 1)
					print(f'Throttled. Retrying chunk in {sleep_time:.2f}s...')
					time.sleep(sleep_time)
					continue
				raise e  # Re-raise if max retries reached or different error
		return chunk

	# Using ThreatPoolExecutor to run LLM calls in parallel.
	with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
		scored_chunks = list(executor.map(_safe_get_score, chunks))

	# Pick only the chunks with score greater than or equal to 5.0.
	scored_chunks = [
		chunk for chunk in scored_chunks if chunk['metadata']['rerank_score'] >= 5.0
	]
	return scored_chunks
