"""Module for managing RAG Engine configurations."""

import os


class Config:
	"""Provide centralized configuration for the RAG Engine.

	Load and validate environment variables required for RAG Engine.
	"""

	VECTOR_BUCKET = os.environ.get('VECTOR_BUCKET_NAME')
	VECTOR_INDEX = os.environ.get('VECTOR_INDEX_NAME')

	# Model IDs
	EMBEDDING_MODEL = os.environ.get('EMBEDDING_MODEL', 'amazon.titan-embed-text-v2:0')
	GENERATION_MODEL = os.environ.get(
		'GENERATION_MODEL', 'anthropic.claude-3-5-sonnet-20240620-v1:0'
	)
	RERANKER_MODEL = os.environ.get(
		'RERANKER_MODEL',
		'arn:aws:bedrock:us-east-1:896368780050:inference-profile/us.anthropic.claude-3-5-haiku-20241022-v1:0',
	)

	CHUNK_SIZE = os.environ.get('CHUNK_SIZE', 512)

	@classmethod
	def validate(cls):
		"""Ensure all required environment variables are present.

		Check for the existence of VECTOR_BUCKET and VECTOR_INDEX.

		Raises:
				EnvironmentError: If required bucket or index names are missing.

		"""
		if not cls.VECTOR_BUCKET or not cls.VECTOR_INDEX:
			raise EnvironmentError('Missing VECTOR_BUCKET_NAME OR VECTOR_INDEX_NAME')
