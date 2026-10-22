"""Section-aware chunker (FIXED for v1, plan §8). Implemented in phase B3."""

from dataclasses import dataclass

CHUNK_MAX_CHARS = 1800
CHUNK_OVERLAP_CHARS = 300
CHUNK_MIN_CHARS = 150
HEADING_SEPARATOR = " › "


@dataclass(frozen=True)
class ChunkDraft:
    """A chunk ready to embed and store."""

    order: int
    heading_path: str
    text: str
    text_normalized: str

    @property
    def char_count(self) -> int:
        """Length of ``text`` in characters."""
        return len(self.text)


def chunk_document(text: str, *, title: str, lang: str) -> list[ChunkDraft]:
    """Split parsed document text into overlapping, heading-aware chunks.

    Args:
        text: Parsed text with ``#``-level heading marker lines.
        title: Document title, the root of every ``heading_path``.
        lang: Document ``Lang``, used for ``text_normalized``.

    Raises:
        NotImplementedError: Until phase B3 lands.
    """
    raise NotImplementedError
