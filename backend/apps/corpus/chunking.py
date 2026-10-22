"""Section-aware chunker (FIXED for v1, plan §8).

Changing any constant or rule here changes retrieval and invalidates the evaluation.
"""

import re
from collections.abc import Iterator
from dataclasses import dataclass

from apps.common.text import normalize_for_search

CHUNK_MAX_CHARS = 1800
CHUNK_OVERLAP_CHARS = 300
CHUNK_MIN_CHARS = 150
HEADING_SEPARATOR = " › "
PARAGRAPH_SEPARATOR = "\n\n"

_HEADING = re.compile(r"^(#{1,4})\s+(.+)$")
_SENTENCE_END = re.compile(r"(?<=[.!?;])\s+")
_BLANK_LINES = re.compile(r"\n\s*\n")


@dataclass(frozen=True)
class ChunkDraft:
    """A chunk ready to embed and store.

    ``heading_path`` joins the open headings (``2-bob › 14-modda``); the document title is
    not part of it (the embedder prepends the title).
    """

    order: int
    heading_path: str
    text: str
    text_normalized: str

    @property
    def char_count(self) -> int:
        """Length of ``text`` in characters."""
        return len(self.text)


@dataclass(frozen=True)
class _Section:
    """The body between two heading markers."""

    heading_path: str
    body: str


def _sections(text: str) -> Iterator[_Section]:
    """Split parsed text at heading markers, tracking the heading stack by level.

    A heading pops every open heading of the same or a deeper level.

    Args:
        text: Parsed text with ``#``-level heading lines.
    """
    stack: dict[int, str] = {}
    body: list[str] = []
    path = ""
    for line in text.splitlines():
        heading = _HEADING.match(line)
        if heading is None:
            body.append(line)
            continue
        yield _Section(path, "\n".join(body))
        body = []
        level = len(heading.group(1))
        stack = {depth: title for depth, title in stack.items() if depth < level}
        stack[level] = heading.group(2).strip()
        path = HEADING_SEPARATOR.join(stack[depth] for depth in sorted(stack))
    yield _Section(path, "\n".join(body))


def _split_words(sentence: str) -> list[str]:
    """Split one over-long sentence at whitespace into pieces of at most the limit.

    Args:
        sentence: A sentence longer than ``CHUNK_MAX_CHARS``.
    """
    pieces: list[str] = []
    current = ""
    for word in sentence.split():
        candidate = f"{current} {word}" if current else word
        if len(candidate) <= CHUNK_MAX_CHARS:
            current = candidate
            continue
        pieces.append(current)
        current = word[:CHUNK_MAX_CHARS]
    return [*pieces, current] if current else pieces


def _pieces(paragraph: str) -> list[str]:
    """Return the paragraph, or its sentences (then words) when it is over the limit.

    Args:
        paragraph: One paragraph.
    """
    if len(paragraph) <= CHUNK_MAX_CHARS:
        return [paragraph]
    pieces: list[str] = []
    for sentence in _SENTENCE_END.split(paragraph):
        pieces.extend([sentence] if len(sentence) <= CHUNK_MAX_CHARS else _split_words(sentence))
    return pieces


def _overlap(previous: str, limit: int) -> str:
    """The tail (≤ ``limit`` chars) of the previous chunk, starting at a sentence start.

    Falls back to a word start when the tail holds no sentence boundary.

    Args:
        previous: The previous chunk's text.
        limit: Maximum overlap length.
    """
    if limit <= 0:
        return ""
    if len(previous) <= limit:
        return previous
    tail = previous[-limit:]
    boundary = _SENTENCE_END.search(tail)
    if boundary is not None:
        return tail[boundary.end() :]
    _, _, after_first_space = tail.partition(" ")
    return after_first_space


def _start_chunk(previous: str | None, piece: str) -> str:
    """Begin a chunk with ``piece``, prefixed by an overlap from ``previous`` that fits.

    Args:
        previous: The section's previous chunk, or None for the first chunk.
        piece: The first new piece of text.
    """
    if previous is None:
        return piece
    room = CHUNK_MAX_CHARS - len(piece) - len(PARAGRAPH_SEPARATOR)
    overlap = _overlap(previous, min(CHUNK_OVERLAP_CHARS, room))
    return f"{overlap}{PARAGRAPH_SEPARATOR}{piece}" if overlap else piece


def _pack(body: str) -> list[str]:
    """Greedily pack a section's paragraphs into overlapping chunks.

    Args:
        body: The section body.

    Returns:
        Chunk texts, each at most ``CHUNK_MAX_CHARS`` long.
    """
    paragraphs = [p.strip() for p in _BLANK_LINES.split(body) if p.strip()]
    chunks: list[str] = []
    current = ""
    for piece in (piece for paragraph in paragraphs for piece in _pieces(paragraph)):
        if not current:
            current = _start_chunk(chunks[-1] if chunks else None, piece)
        elif len(current) + len(PARAGRAPH_SEPARATOR) + len(piece) <= CHUNK_MAX_CHARS:
            current = f"{current}{PARAGRAPH_SEPARATOR}{piece}"
        else:
            chunks.append(current)
            current = _start_chunk(current, piece)
    return [*chunks, current] if current else chunks


def chunk_document(text: str, *, lang: str) -> list[ChunkDraft]:
    """Split parsed document text into overlapping, heading-aware chunks.

    Chunks under ``CHUNK_MIN_CHARS`` are dropped unless they are their section's only chunk.

    Args:
        text: Parsed text with ``#``-level heading marker lines (``## 2-bob``).
        lang: Document ``Lang``, used for ``text_normalized``.

    Returns:
        Chunks numbered 0, 1, 2… across the document.
    """
    drafts: list[ChunkDraft] = []
    for section in _sections(text):
        packed = _pack(section.body)
        kept = packed if len(packed) == 1 else [c for c in packed if len(c) >= CHUNK_MIN_CHARS]
        drafts.extend(
            ChunkDraft(
                order=len(drafts) + index,
                heading_path=section.heading_path,
                text=chunk,
                text_normalized=normalize_for_search(chunk, lang),
            )
            for index, chunk in enumerate(kept)
        )
    return drafts
