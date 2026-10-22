"""Section-aware chunker (FIXED for v1, plan §8). Implemented in phase B3."""

import re
from dataclasses import dataclass

from apps.common.text import normalize_for_search

CHUNK_MAX_CHARS = 1800
CHUNK_OVERLAP_CHARS = 300
CHUNK_MIN_CHARS = 150
HEADING_SEPARATOR = " › "

_HEADING_RE = re.compile(r"^(#{1,4})\s+(.+)$")
_SENTENCE_END_RE = re.compile(r"(?<=[.!?;])(?:\s|\n)")


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


def _split_at_sentences(text: str) -> list[str]:
    """Split text at sentence-boundary positions.

    A sentence boundary is a `.` `!` `?` or `;` followed by whitespace or newline.

    Args:
        text: Text to split.

    Returns:
        Non-empty fragments.
    """
    parts = _SENTENCE_END_RE.split(text)
    return [p for p in parts if p]


def _split_at_whitespace(text: str) -> list[str]:
    """Split text at whitespace boundaries into pieces ≤ CHUNK_MAX_CHARS.

    Args:
        text: A single sentence that exceeds the character limit.

    Returns:
        Fragments, each ≤ CHUNK_MAX_CHARS characters.
    """
    words = text.split()
    if not words:
        return []
    pieces: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = current + " " + word
        if len(candidate) <= CHUNK_MAX_CHARS:
            current = candidate
        else:
            pieces.append(current)
            current = word
    pieces.append(current)
    return pieces


def _split_long_paragraph(paragraph: str) -> list[str]:
    """Split a paragraph longer than CHUNK_MAX_CHARS into fittable pieces.

    First tries sentence boundaries, then falls back to whitespace.

    Args:
        paragraph: A single paragraph that exceeds the character limit.

    Returns:
        Fragments, each ≤ CHUNK_MAX_CHARS characters.
    """
    sentences = _split_at_sentences(paragraph)
    pieces: list[str] = []
    for sentence in sentences:
        if len(sentence) <= CHUNK_MAX_CHARS:
            pieces.append(sentence)
        else:
            pieces.extend(_split_at_whitespace(sentence))
    return pieces


def _compute_overlap(previous_text: str) -> str:
    """Extract an overlap prefix from the tail of the previous chunk.

    Takes the last CHUNK_OVERLAP_CHARS characters, then advances to a sentence start
    (after ``.`` ``!`` ``?`` ``;`` + space) when possible, else to a word start.

    Args:
        previous_text: Full text of the preceding chunk.

    Returns:
        The overlap string (may be empty if previous_text is short).
    """
    if len(previous_text) <= CHUNK_OVERLAP_CHARS:
        tail = previous_text
    else:
        tail = previous_text[-CHUNK_OVERLAP_CHARS:]

    # Try to cut at a sentence start within the overlap.
    best_cut = -1
    for match in _SENTENCE_END_RE.finditer(tail):
        best_cut = match.end()

    if best_cut > 0:
        return tail[best_cut:]

    # Fall back to a word start: skip to the first space, then past it.
    space_pos = tail.find(" ")
    if space_pos >= 0 and space_pos + 1 < len(tail):
        return tail[space_pos + 1 :]

    return tail


def _pack_section(
    paragraphs: list[str],
    heading_path: str,
    lang: str,
) -> list[tuple[str, str]]:
    """Pack paragraphs into chunks, respecting max size and overlap rules.

    Args:
        paragraphs: Non-empty paragraph strings for this section.
        heading_path: The heading path for all chunks in this section.
        lang: Language code for normalization.

    Returns:
        List of ``(text, text_normalized)`` pairs, before min-size filtering.
    """
    if not paragraphs:
        return []

    # Flatten paragraphs that are too long.
    flat: list[str] = []
    for para in paragraphs:
        if len(para) <= CHUNK_MAX_CHARS:
            flat.append(para)
        else:
            flat.extend(_split_long_paragraph(para))

    chunks: list[str] = []
    current_parts: list[str] = []
    current_len = 0

    for piece in flat:
        joined_addition = len("\n\n") + len(piece) if current_parts else len(piece)
        if current_parts and current_len + joined_addition > CHUNK_MAX_CHARS:
            # Flush the current chunk.
            chunks.append("\n\n".join(current_parts))
            current_parts = []
            current_len = 0

        if not current_parts and chunks:
            # Add overlap from the previous chunk.
            overlap = _compute_overlap(chunks[-1])
            candidate = overlap + "\n\n" + piece if overlap else piece
            if len(candidate) <= CHUNK_MAX_CHARS:
                current_parts = [candidate]
                current_len = len(candidate)
                continue
            # Overlap + piece exceeds the limit; try without overlap.
            current_parts = [piece]
            current_len = len(piece)
            continue

        current_parts.append(piece)
        current_len = len("\n\n".join(current_parts))

    if current_parts:
        text = "\n\n".join(current_parts)
        if not chunks:
            chunks.append(text)
        else:
            overlap = _compute_overlap(chunks[-1])
            candidate = overlap + "\n\n" + text if overlap else text
            if len(candidate) <= CHUNK_MAX_CHARS:
                chunks.append(candidate)
            else:
                chunks.append(text)

    return [(c, normalize_for_search(c, lang)) for c in chunks]


def chunk_document(text: str, *, lang: str) -> list[ChunkDraft]:
    """Split parsed document text into overlapping, heading-aware chunks.

    Args:
        text: Parsed text with ``#``-level heading marker lines (``## 2-bob``).
        lang: Document ``Lang``, used for ``text_normalized``.

    Returns:
        Ordered list of ``ChunkDraft`` instances.
    """
    lines = text.split("\n")
    heading_stack: dict[int, str] = {}
    sections: list[tuple[str, list[str]]] = []
    current_paragraphs: list[str] = []
    current_heading_path = ""
    current_paragraph_lines: list[str] = []

    def _flush_paragraph() -> None:
        """Flush accumulated paragraph lines into current_paragraphs."""
        if current_paragraph_lines:
            current_paragraphs.append("\n".join(current_paragraph_lines))
            current_paragraph_lines.clear()

    def _flush_section() -> None:
        """Flush the current section (heading path + paragraphs) into sections."""
        _flush_paragraph()
        sections.append((current_heading_path, list(current_paragraphs)))
        current_paragraphs.clear()

    for line in lines:
        heading_match = _HEADING_RE.match(line)
        if heading_match:
            # Flush the previous section.
            _flush_section()

            level = len(heading_match.group(1))
            heading_text = heading_match.group(2).strip()

            # Pop headings of the same or deeper level.
            heading_stack = {lvl: txt for lvl, txt in heading_stack.items() if lvl < level}
            heading_stack[level] = heading_text

            current_heading_path = HEADING_SEPARATOR.join(
                heading_stack[lvl] for lvl in sorted(heading_stack)
            )
            continue

        if line.strip() == "":
            _flush_paragraph()
        else:
            current_paragraph_lines.append(line)

    # Flush the last section.
    _flush_section()

    # Pack each section and collect chunks.
    all_chunks: list[ChunkDraft] = []
    order = 0
    for heading_path, paragraphs in sections:
        # Filter out empty paragraphs.
        paragraphs = [p for p in paragraphs if p.strip()]
        packed = _pack_section(paragraphs, heading_path, lang)

        if not packed:
            continue

        is_single = len(packed) == 1
        for chunk_text, chunk_normalized in packed:
            if len(chunk_text) < CHUNK_MIN_CHARS and not is_single:
                continue
            all_chunks.append(
                ChunkDraft(
                    order=order,
                    heading_path=heading_path,
                    text=chunk_text,
                    text_normalized=chunk_normalized,
                )
            )
            order += 1

    return all_chunks
