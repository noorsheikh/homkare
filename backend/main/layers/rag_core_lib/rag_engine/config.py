import os

class Config:
  """
  Centralized configuration for the RAG Engine.
  Loads and validates environment variables.
  """
  VECTOR_BUCKET = os.environ.get("VECTOR_BUCKET_NAME")
  VECTOR_INDEX = os.environ.get("VECTOR_INDEX_NAME")

  # Model IDs
  EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "amazon.titan-embed-text-v2:0")
  GENERATION_MODEL = os.environ.get("GENERATION_MODEL", "anthropic.claude-3-5-sonnet-20240620-v1:0")

  CHUNK_SIZE = os.environ.get("CHUNK_SIZE", 512)

  @classmethod
  def validate(cls):
    """Ensures all required variables are present."""
    if not cls.VECTOR_BUCKET or not cls.VECTOR_INDEX:
      raise EnvironmentError("Missing VECTOR_BUCKET_NAME OR VECTOR_INDEX_NAME")
