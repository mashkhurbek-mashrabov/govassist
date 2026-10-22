"""Embedding port: ``GeminiEmbedder`` for real runs, ``FakeEmbedder`` for tests (plan §8)."""

import asyncio
import hashlib
import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from django.conf import settings
from google import genai
from google.genai import types

from apps.common.gemini import call_with_retries, get_client
from apps.common.text import canonicalize

QUERY_TEMPLATE = "task: question answering | query: {query}"
DOCUMENT_TEMPLATE = "title: {title} | text: {text}"


@dataclass(frozen=True)
class DocumentInput:
    """One chunk to embed with its context."""

    title: str
    heading_path: str
    text: str


class Embedder(Protocol):
    """Turns chunks and queries into vectors of ``EMBEDDING_DIM`` floats."""

    model_name: str

    async def embed_documents(self, items: Sequence[DocumentInput]) -> list[list[float]]:
        """Embed chunks; returns one vector per item, in order."""
        ...

    async def embed_query(self, query: str) -> list[float]:
        """Embed a (scrubbed) user question."""
        ...


def format_document(item: DocumentInput) -> str:
    """Build the document-side input: ``title: {title} › {path} | text: {text}``.

    Args:
        item: The chunk to format.
    """
    title = " › ".join(part for part in (item.title, item.heading_path) if part)
    return DOCUMENT_TEMPLATE.format(title=title or "none", text=item.text)


class GeminiEmbedder:
    """``gemini-embedding-2``: one request per text (lists are merged into one vector).

    An instance belongs to one event loop (its client and semaphore bind to it): create a
    new one for each ``async_to_sync`` call or request.
    """

    def __init__(
        self,
        client: genai.Client | None = None,
        *,
        model: str | None = None,
        dimensions: int | None = None,
        concurrency: int | None = None,
        max_tries: int | None = None,
    ) -> None:
        self._client = client or get_client()
        self.model_name = model or settings.GEMINI_EMBEDDING_MODEL
        self._dimensions = dimensions or settings.EMBEDDING_DIM
        self._semaphore = asyncio.Semaphore(concurrency or settings.EMBED_CONCURRENCY)
        self._max_tries = max_tries or settings.EMBED_MAX_TRIES

    async def _embed_one(self, content: str) -> list[float]:
        """Embed one text with retries, bounded by the concurrency semaphore.

        Args:
            content: The fully formatted input.

        Raises:
            ValueError: When Gemini returns no embedding.
        """
        config = types.EmbedContentConfig(output_dimensionality=self._dimensions)
        async with self._semaphore:
            response = await call_with_retries(
                lambda: self._client.aio.models.embed_content(
                    model=self.model_name, contents=content, config=config
                ),
                max_tries=self._max_tries,
            )
        if not response.embeddings or response.embeddings[0].values is None:
            msg = "Gemini returned no embedding."
            raise ValueError(msg)
        return list(response.embeddings[0].values)

    async def embed_documents(self, items: Sequence[DocumentInput]) -> list[list[float]]:
        """Embed chunks concurrently (``EMBED_CONCURRENCY`` at a time).

        Args:
            items: Chunks to embed.

        Returns:
            One vector per item, in order.
        """
        return list(await asyncio.gather(*(self._embed_one(format_document(i)) for i in items)))

    async def embed_query(self, query: str) -> list[float]:
        """Embed a question with the question-answering task prefix.

        Args:
            query: The scrubbed question.
        """
        return await self._embed_one(QUERY_TEMPLATE.format(query=query))


class FakeEmbedder:
    """Deterministic bag-of-words hashing embedder for tests (no network).

    Texts that share words get similar vectors, so retrieval tests stay meaningful.
    """

    model_name = "fake-embedder"

    def __init__(self, dimensions: int | None = None) -> None:
        self._dimensions = dimensions or settings.EMBEDDING_DIM

    def _vector(self, text: str) -> list[float]:
        """Hash each canonical word into a bucket and L2-normalize.

        Args:
            text: Any text.
        """
        vector = [0.0] * self._dimensions
        for word in canonicalize(text).split():
            bucket = int.from_bytes(hashlib.sha256(word.encode()).digest()[:4], "big")
            vector[bucket % self._dimensions] += 1.0
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    async def embed_documents(self, items: Sequence[DocumentInput]) -> list[list[float]]:
        """Embed chunk texts.

        Args:
            items: Chunks to embed.
        """
        return [self._vector(item.text) for item in items]

    async def embed_query(self, query: str) -> list[float]:
        """Embed a query.

        Args:
            query: The question.
        """
        return self._vector(query)
