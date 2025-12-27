"""Module for interacting with Amazon Bedrock to generate vector embeddings."""

import json

from clients.factory import get_bedrock_client

from .config import Config

bedrock_client = get_bedrock_client()


def get_embedding(text: str):
	"""Generate a 1024-dimensional vector embedding for the given text.

	Use the configured Bedrock embedding model to transform the input
	string into a numerical vector representation.

	Args:
		text: The string to be embedded.

	Returns:
		A list of floats representing the 1024-dimensional embedding.

	"""
	body = json.dumps(
		{
			'inputText': text,
			'dimensions': 1024,
		}
	)

	response = bedrock_client.invoke_model(
		modelId=Config.EMBEDDING_MODEL,
		body=body,
		contentType='application/json',
	)
	return json.loads(response['body'].read())['embedding']
