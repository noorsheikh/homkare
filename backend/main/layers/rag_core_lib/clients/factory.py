"""Client Factory Module for AWS AI/ML Services."""

import boto3
from botocore.config import Config

# Optimized config for AI/RAG workloads
# Increased retries and timeouts for LLM latency
DEFAULT_CONFIG = Config(
	retries={'max_attempts': 3, 'mode': 'standard'},
	connect_timeout=5,
	read_timeout=60,  # Bedrock can take time for large generations
)

# Global cache for clients to enable reuse across "warm" invocations
_CLIENT_CACHE = {}


def get_bedrock_client(region: str = 'us-east-1'):
	"""Return a cached bedrock-runtime client.

	Args:
        region (str): The AWS region for Bedrock. Defaults to us-east-1.

	Returns:
        boto3.client: An initialized bedrock-runtime client.

	"""
	if 'bedrock' not in _CLIENT_CACHE:
		_CLIENT_CACHE['bedrock'] = boto3.client(
			service_name='bedrock-runtime', region_name=region, config=DEFAULT_CONFIG
		)
	return _CLIENT_CACHE['bedrock']


def get_s3_vector_client(region: str = 'us-east-1'):
	"""Return a cached S3 client for Vector searches.

	Note: S3 Vectors uses the standard S3 client with specific parameters.

	Returns:
        boto3.client: An initialized S3 client.

	"""
	if 's3vectors' not in _CLIENT_CACHE:
		_CLIENT_CACHE['s3vectors'] = boto3.client(
			service_name='s3vectors', region_name=region, config=DEFAULT_CONFIG
		)
	return _CLIENT_CACHE['s3vectors']
