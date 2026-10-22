"""Constants of the corpus app (AGENTS.md: no constant values elsewhere in the app)."""

import re

from django.db import models

CHUNK_MAX_CHARS = 1800

CHUNK_OVERLAP_CHARS = 300

CHUNK_MIN_CHARS = 150

HEADING_SEPARATOR = " › "

PARAGRAPH_SEPARATOR = "\n\n"

HEADING = re.compile(r"^(#{1,4})\s+(.+)$")

SENTENCE_END = re.compile(r"(?<=[.!?;])\s+")

BLANK_LINES = re.compile(r"\n\s*\n")

QUERY_TEMPLATE = "task: question answering | query: {query}"

DOCUMENT_TEMPLATE = "title: {title} | text: {text}"

SEARCH_CONFIG = "simple"

HNSW_M = 16

HNSW_EF_CONSTRUCTION = 64


class DocumentKind(models.TextChoices):
    """What a document is; maps to ``Source.kind`` in the contract."""

    LAW = "law", "Law"
    SERVICE_PAGE = "service_page", "Service page"
    OTHER = "other", "Other"
