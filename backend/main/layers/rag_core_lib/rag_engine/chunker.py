"""Module for recursive text chunking using Chonkie.

This module provides a standardized interface for cleaning raw text and
splitting it into manageable, semantic chunks using a configured
RecursiveChunker instance.
"""

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
	"""Standardize raw text for processing.

	Remove TOC leaders, fix broken hyphens, strip special characters,
	and normalize whitespace to return a lowercase, trimmed string.

	Args:
		text: The raw input string to be cleaned.

	Returns:
		The standardized and cleaned string.

	"""
	text = re.sub(r'(?:\.\s?){3,}\s*\d*', ' ', text)
	text = re.sub(r'(\w+)-\s+(\w+)', r'\1\2', text)
	text = re.sub(r'[^\w\s.,?!]', '', text)
	text = re.sub(r'\s+', ' ', text)
	return text.strip().lower()


def get_chunks(text: str):
	"""Clean and split text into semantic chunks.

	First standardize the input text using clean_data, then apply
	the module-level RecursiveChunker to generate text segments.

	Args:
		text: The input text to be segmented.

	Returns:
		A list or generator of text chunks.

	"""
	cleaned = clean_data(text)
	return _chunker.chunk(cleaned)
