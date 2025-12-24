"""Module for reranking text chunks using Amazon Bedrock."""

import concurrent.futures
import json

import boto3

from .config import Config

bedrock = boto3.client('bedrock-runtime')


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
	"""Rerank a list of chunks based on query relevance using parallel threads.

	Execute multiple LLM scoring calls concurrently via ThreadPoolExecutor
	and filter the results to return only highly relevant segments.

	Args:
		query: The search query to compare against.
		chunks: A list of chunk dictionaries to be scored.

	Returns:
		A list of chunks with a rerank_score of 5.0 or higher.

	"""
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
