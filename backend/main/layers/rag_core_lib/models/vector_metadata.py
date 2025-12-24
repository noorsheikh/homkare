"""Define metadata schemas for vector storage and RAG operations.

This module provides Pydantic models to validate and standardize metadata
associated with different data sources (files, text, chat, and public docs)
stored in vector databases.
"""

from typing import Literal, Optional

import pendulum
from pydantic import BaseModel, Field, model_validator

Visibility = Literal['private', 'tenant', 'public']

Source = Literal['file', 'text', 'chat', 'note']


class BaseVectorMetadata(BaseModel):
	"""Represent the base schema for all vector metadata.

	Provide common fields such as IDs, visibility scope, source type,
	and timestamps required for filtering and auditing.
	"""

	user_id: Optional[str] = Field(
		None,
		description='User who created the content (None for platform-owned)',
	)

	tenant_id: Optional[str] = Field(
		None,
		description='HOA / Community / Organization ID',
	)

	visibility: Visibility = Field(
		...,
		description="""
        Access scope: private (user), tenant (community), public (platform)
        """,
	)

	source: Source = Field(
		...,
		description='Source of the file (e.g., file, text, chat or note)',
	)

	chunk_text: str = Field(
		...,
		description='The actual chunked text that is embedded',
	)

	chunk_hash: str = Field(
		...,
		description='The hash of the chunked text that is embedded',
	)

	created_at: str = Field(
		default_factory=lambda: pendulum.now().to_iso8601_string(),
		description='Vector creation date and time',
	)

	@model_validator(mode='after')
	def validate_visibility_scope(self):
		"""Ensure visibility settings align with provided identifiers.

		Validate that private content has a user_id, tenant content has
		a tenant_id, and public content has neither.

		Raises:
			ValueError: If the visibility scope contradicts the metadata.

		"""
		if self.visibility == 'private' and not self.user_id:
			raise ValueError('private visibility requires user_id')

		if self.visibility == 'tenant' and not self.tenant_id:
			raise ValueError('tenant visibility requires tenant_id')

		if self.visibility == 'public' and (self.user_id or self.tenant_id):
			raise ValueError('public visibility must not have user_id or tenant_id')

		return self

	def to_s3_metadata(self) -> dict[str, str | int | float | bool]:
		"""Convert metadata to an S3-compatible primitive format.

		Dump the model to JSON and ensure all values are primitives
		(str, int, float, bool) accepted by S3 metadata storage.

		Returns:
			A dictionary of primitive key-value pairs.

		"""
		data = self.model_dump(mode='json', exclude_none=True)

		# Force everything to primitives S3 accepts.
		return {
			k: (v if isinstance(v, (str, int, float, bool)) else str(v))
			for k, v in data.items()
		}


class FileVectorMetadata(BaseVectorMetadata):
	"""Metadata schema for content sourced from uploaded files.

	Extends the base metadata with file-specific details such as
	page numbers and file types.
	"""

	source: Source = 'file'

	file_id: str = Field(..., description='Unique file identifier')

	file_name: str = Field(..., description='Original file name')

	file_type: Literal['pdf', 'doc', 'docx', 'txt', 'md', 'undefined'] = Field(
		..., description='The type of the file'
	)

	page_number: Optional[int] = Field(None, description='Page number of the file')

	chunk_index: int = Field(..., description='Chunk index within the file')


class TextVectorMetadata(BaseVectorMetadata):
	"""Metadata schema for direct text inputs and snippets.

	Tracks the logical grouping and sequence of chunks for manual entries.
	"""

	source: Source = 'text'

	context_id: str = Field(
		..., description='Logical grouping of text (note_id, section_id, etc.)'
	)

	chunk_index: int = Field(..., description='Chunk index within the file')


class ChatVectorMetadata(BaseVectorMetadata):
	"""Metadata schema for segments of chat history.

	Maintains context regarding the participant role and message order.
	"""

	source: Source = 'chat'

	chat_id: str = Field(
		..., description='Unique identifier for from the chat history for the chat'
	)

	message_index: str = Field(..., description='Message index from the chat history')

	role: Literal['user', 'assistant'] = Field(
		...,
		description='The role of the message author',
	)


class PublicVectorMetadata(BaseVectorMetadata):
	"""Metadata schema for global, platform-wide public documents.

	Enforces empty IDs and public visibility for general resources.
	"""

	user_id: None = None
	tenant_id: None = None
	visibility: Visibility = 'public'

	category: Literal[
		'help',
		'faq',
		'docs',
		'policy',
		'guidelines',
		'tutorial',
		'diy',
	]
