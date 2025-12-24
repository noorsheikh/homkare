import re

from chonkie import RecursiveChunker, RecursiveRules

from .config import Config

# Initialize chunker once at the module level for efficiency.
_chunker = RecursiveChunker(
	tokenizer='character',
	chunk_size=Config.CHUNK_SIZE,
	rules=RecursiveRules(),
	min_characters_per_chunk=1,
)


def clean_data(text: str) -> str:
	"""Standardizes raw text by removing TOC leaders, fixing hyphens,
	and normalizing whitespace.
	"""
	text = re.sub(r'(?:\.\s?){3,}\s*\d*', ' ', text)
	text = re.sub(r'(\w+)-\s+(\w+)', r'\1\2', text)
	text = re.sub(r'[^\w\s.,?!]', '', text)
	text = re.sub(r'\s+', ' ', text)
	return text.strip().lower()


def get_chunks(text: str):
	"""Cleans and splits text into semantic chunks."""
	cleaned = clean_data(text)
	return _chunker.chunk(cleaned)
