"""Tests for the section-aware document chunker."""

from itertools import pairwise

import pytest

from apps.common.i18n import Lang
from apps.common.text import normalize_for_search
from apps.corpus.chunking import (
    CHUNK_MAX_CHARS,
    CHUNK_MIN_CHARS,
    CHUNK_OVERLAP_CHARS,
    HEADING_SEPARATOR,
    ChunkDraft,
    chunk_document,
)


def _make_paragraph(length: int, word: str = "davlat") -> str:
    """Build a synthetic paragraph of approximately ``length`` characters.

    Args:
        length: Target character count (approximate).
        word: The word to repeat.

    Returns:
        A paragraph string.
    """
    unit = word + " "
    reps = max(1, length // len(unit))
    return (unit * reps).rstrip()


# ---------------------------------------------------------------------------
# Heading stack
# ---------------------------------------------------------------------------


class TestHeadingStack:
    """Tests for heading-path construction and stack management."""

    def test_single_heading(self) -> None:
        """A single heading produces a heading path with just that heading."""
        text = "## 2-bob\n\nSAMPLE paragraph text that is long enough to form a valid chunk easily."
        chunks = chunk_document(text, lang=Lang.UZ_LATN)
        assert len(chunks) >= 1
        assert chunks[0].heading_path == "2-bob"

    def test_nested_headings(self) -> None:
        """Nested headings produce a joined path with HEADING_SEPARATOR."""
        text = (
            "## 2-bob\n### 14-modda\n\n"
            "SAMPLE paragraph text that must be long enough to pass the minimum "
            "character limit for chunking."
        )
        chunks = chunk_document(text, lang=Lang.UZ_LATN)
        assert chunks[0].heading_path == f"2-bob{HEADING_SEPARATOR}14-modda"

    def test_same_level_pops_previous(self) -> None:
        """A new heading of the same level replaces the previous one."""
        text = (
            "## 2-bob\n\n"
            "SAMPLE paragraph one is here with enough text to form a valid chunk of its own.\n\n"
            "## 3-bob\n\n"
            "SAMPLE paragraph two is also here with enough text to form a separate chunk."
        )
        chunks = chunk_document(text, lang=Lang.UZ_LATN)
        paths = [c.heading_path for c in chunks]
        assert "2-bob" in paths
        assert "3-bob" in paths

    def test_deeper_heading_pops_deeper(self) -> None:
        """A heading pops all headings of the same or deeper level."""
        text = (
            "## 2-bob\n### Section A\n#### Detail X\n\n"
            "SAMPLE paragraph at the deepest level with enough text for chunking.\n\n"
            "### Section B\n\n"
            "SAMPLE paragraph in section B with enough text for a valid chunk too."
        )
        chunks = chunk_document(text, lang=Lang.UZ_LATN)
        last_path = chunks[-1].heading_path
        assert "Detail X" not in last_path
        assert "Section B" in last_path

    def test_no_heading(self) -> None:
        """Text without any heading markers has an empty heading path."""
        text = "SAMPLE paragraph without any heading marker but enough text to form a chunk."
        chunks = chunk_document(text, lang=Lang.UZ_LATN)
        assert len(chunks) >= 1
        assert chunks[0].heading_path == ""


# ---------------------------------------------------------------------------
# Greedy paragraph packing
# ---------------------------------------------------------------------------


class TestParagraphPacking:
    """Tests for greedy paragraph packing within CHUNK_MAX_CHARS."""

    def test_small_paragraphs_packed(self) -> None:
        """Several small paragraphs fit in one chunk joined by a blank line."""
        paras = [_make_paragraph(200) for _ in range(3)]
        text = "\n\n".join(paras)
        chunks = chunk_document(text, lang=Lang.UZ_LATN)
        assert len(chunks) == 1
        assert "\n\n" in chunks[0].text

    def test_packing_respects_max_chars(self) -> None:
        """No chunk exceeds CHUNK_MAX_CHARS."""
        paras = [_make_paragraph(500) for _ in range(10)]
        text = "\n\n".join(paras)
        chunks = chunk_document(text, lang=Lang.UZ_LATN)
        for chunk in chunks:
            assert chunk.char_count <= CHUNK_MAX_CHARS


# ---------------------------------------------------------------------------
# Long paragraph / sentence splitting
# ---------------------------------------------------------------------------


class TestLongParagraphSplitting:
    """Tests for splitting paragraphs that exceed CHUNK_MAX_CHARS."""

    def test_long_paragraph_split_at_sentences(self) -> None:
        """A paragraph longer than the limit is split at sentence boundaries."""
        sentences = ["SAMPLE sentence number " + str(i) + " is here. " for i in range(100)]
        para = "".join(sentences).strip()
        assert len(para) > CHUNK_MAX_CHARS
        text = para
        chunks = chunk_document(text, lang=Lang.UZ_LATN)
        assert len(chunks) > 1
        for chunk in chunks:
            assert chunk.char_count <= CHUNK_MAX_CHARS

    def test_long_sentence_split_at_whitespace(self) -> None:
        """A single sentence longer than the limit is split at whitespace."""
        # A single sentence with no sentence-end punctuation until the very end.
        long_sentence = " ".join(["word" + str(i) for i in range(500)])
        assert len(long_sentence) > CHUNK_MAX_CHARS
        chunks = chunk_document(long_sentence, lang=Lang.UZ_LATN)
        assert len(chunks) >= 1
        for chunk in chunks:
            assert chunk.char_count <= CHUNK_MAX_CHARS


# ---------------------------------------------------------------------------
# Overlap
# ---------------------------------------------------------------------------


class TestOverlap:
    """Tests for overlap between consecutive chunks in a section."""

    def test_overlap_exists(self) -> None:
        """The second chunk's text starts with content from the tail of the first."""
        paras = [_make_paragraph(1000), _make_paragraph(1000)]
        text = "\n\n".join(paras)
        chunks = chunk_document(text, lang=Lang.UZ_LATN)
        assert len(chunks) >= 2
        # The second chunk should contain some text from the first chunk's tail.
        first_tail = chunks[0].text[-CHUNK_OVERLAP_CHARS:]
        # At least some words from the tail appear in the second chunk.
        tail_words = set(first_tail.split()[-3:])
        second_start_words = set(chunks[1].text.split()[:10])
        assert tail_words & second_start_words, "Overlap content expected in the second chunk"

    def test_overlap_chunk_within_max(self) -> None:
        """A chunk including its overlap must not exceed CHUNK_MAX_CHARS."""
        paras = [_make_paragraph(1500), _make_paragraph(1500)]
        text = "\n\n".join(paras)
        chunks = chunk_document(text, lang=Lang.UZ_LATN)
        for chunk in chunks:
            assert chunk.char_count <= CHUNK_MAX_CHARS


# ---------------------------------------------------------------------------
# Minimum-size drop vs only-chunk
# ---------------------------------------------------------------------------


class TestMinSizeDrop:
    """Tests for dropping chunks shorter than CHUNK_MIN_CHARS."""

    def test_short_chunk_dropped(self) -> None:
        """A short chunk in a multi-chunk section is dropped."""
        # A big paragraph plus a tiny one.
        big = _make_paragraph(1600)
        tiny = "SAMPLE tiny."  # < CHUNK_MIN_CHARS
        text = f"## Section\n\n{big}\n\n{tiny}"
        chunks = chunk_document(text, lang=Lang.UZ_LATN)
        for chunk in chunks:
            assert chunk.char_count >= CHUNK_MIN_CHARS

    def test_only_chunk_kept_even_if_short(self) -> None:
        """A short chunk is kept if it is the section's only chunk."""
        text = "## Heading\n\nSAMPLE short body only chunk."
        chunks = chunk_document(text, lang=Lang.UZ_LATN)
        assert len(chunks) == 1
        assert chunks[0].char_count < CHUNK_MIN_CHARS


# ---------------------------------------------------------------------------
# Empty sections
# ---------------------------------------------------------------------------


class TestEmptySection:
    """Tests for sections with empty bodies."""

    def test_empty_body_no_chunk(self) -> None:
        """A heading followed immediately by another heading produces no chunk."""
        text = (
            "## Section A\n"
            "## Section B\n\n"
            "SAMPLE paragraph in section B with enough text for a valid chunk here."
        )
        chunks = chunk_document(text, lang=Lang.UZ_LATN)
        paths = {c.heading_path for c in chunks}
        assert "Section A" not in paths
        assert "Section B" in paths

    def test_heading_only_document(self) -> None:
        """A document with only headings and no body text produces no chunks."""
        text = "## A\n## B\n## C"
        chunks = chunk_document(text, lang=Lang.UZ_LATN)
        assert chunks == []


# ---------------------------------------------------------------------------
# Order numbering
# ---------------------------------------------------------------------------


class TestOrder:
    """Tests for the ``order`` field across the whole document."""

    def test_order_zero_based_sequential(self) -> None:
        """Orders are 0, 1, 2, ... across all sections after dropping."""
        text = (
            "## First\n\n" + _make_paragraph(500) + "\n\n"
            "## Second\n\n" + _make_paragraph(500) + "\n\n"
            "## Third\n\n" + _make_paragraph(500)
        )
        chunks = chunk_document(text, lang=Lang.UZ_LATN)
        orders = [c.order for c in chunks]
        assert orders == list(range(len(chunks)))

    def test_order_accounts_for_drops(self) -> None:
        """Dropped chunks do not appear in the order sequence; it stays dense."""
        # Create a section with two chunks (one big, one tiny → tiny dropped).
        big = _make_paragraph(1600)
        tiny = "SAMPLE tiny."
        text = f"## S1\n\n{big}\n\n{tiny}\n\n## S2\n\n" + _make_paragraph(500)
        chunks = chunk_document(text, lang=Lang.UZ_LATN)
        orders = [c.order for c in chunks]
        assert orders == list(range(len(chunks)))


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------


class TestNormalization:
    """Tests for ``text_normalized`` on each chunk."""

    def test_uz_cyrl_normalized(self) -> None:
        """Uzbek Cyrillic text is transliterated and canonicalized in text_normalized."""
        text = "SAMPLE Ўзбекистон давлати ва жамияти ҳақида маълумот ёзилган ушбу ҳужжатни ўқинг"
        chunks = chunk_document(text, lang=Lang.UZ_CYRL)
        assert len(chunks) >= 1
        expected = normalize_for_search(chunks[0].text, Lang.UZ_CYRL)
        assert chunks[0].text_normalized == expected

    def test_uz_latn_normalized(self) -> None:
        """Uzbek Latin text is canonicalized in text_normalized."""
        text = (
            "SAMPLE Oʻzbekiston davlati va jamiyati haqida maʼlumot yozilgan ushbu hujjatni oʻqing"
        )
        chunks = chunk_document(text, lang=Lang.UZ_LATN)
        assert len(chunks) >= 1
        expected = normalize_for_search(chunks[0].text, Lang.UZ_LATN)
        assert chunks[0].text_normalized == expected


# ---------------------------------------------------------------------------
# ChunkDraft properties
# ---------------------------------------------------------------------------


class TestChunkDraft:
    """Tests for ``ChunkDraft`` dataclass."""

    def test_char_count(self) -> None:
        """``char_count`` equals the length of ``text``."""
        draft = ChunkDraft(order=0, heading_path="", text="hello", text_normalized="hello")
        assert draft.char_count == 5

    def test_frozen(self) -> None:
        """``ChunkDraft`` is immutable (frozen dataclass)."""
        draft = ChunkDraft(order=0, heading_path="", text="hello", text_normalized="hello")
        with pytest.raises(AttributeError):
            draft.order = 1  # type: ignore[misc]


def _sentences(count: int, prefix: str) -> str:
    """``count`` numbered NAMUNA sentences of ~60 chars, as one paragraph."""
    return " ".join(
        f"{prefix} NAMUNA gap {i:03d} davlat xizmati haqida maʼlumot beradi." for i in range(count)
    )


class TestOverlapRegressions:
    """Exact overlap rules (fixed bugs: double overlap on the last chunk, dropped overlap)."""

    def test_overlap_is_a_sentence_aligned_tail_used_once(self) -> None:
        """Each later chunk starts with exactly one ≤300-char, sentence-aligned tail."""
        paragraphs = [_sentences(25, f"P{i}") for i in range(3)]
        chunks = chunk_document("\n\n".join(paragraphs), lang=Lang.UZ_LATN)
        assert len(chunks) == 3
        for previous, chunk in pairwise(chunks):
            overlap, _, rest = chunk.text.partition("\n\n")
            assert previous.text.endswith(overlap)
            assert 0 < len(overlap) <= CHUNK_OVERLAP_CHARS
            assert overlap[0].isupper()
            assert not rest.startswith(overlap)
            assert chunk.char_count <= CHUNK_MAX_CHARS

    def test_overlap_shrinks_to_fit_a_large_piece(self) -> None:
        """A piece near the limit still gets an overlap trimmed to the remaining room."""
        small = _sentences(10, "A")
        large = "B " + "soʻz " * 349 + "oxiri."
        chunks = chunk_document(f"{small}\n\n{large}", lang=Lang.UZ_LATN)
        assert len(chunks) == 2
        assert chunks[1].char_count <= CHUNK_MAX_CHARS
        overlap = chunks[1].text.partition("\n\n")[0]
        assert overlap
        assert small.endswith(overlap)

    def test_overlap_falls_back_to_word_start(self) -> None:
        """Without a sentence boundary in the tail, the overlap starts at a word."""
        first = " ".join(f"soʻz{i}" for i in range(150))
        second = " ".join(f"gap{i}" for i in range(150))
        chunks = chunk_document(f"{first}\n\n{second}", lang=Lang.UZ_LATN)
        overlap = chunks[1].text.partition("\n\n")[0]
        assert overlap.split()[0] in chunks[0].text.split()

    def test_long_word_is_cut(self) -> None:
        """A single token longer than the limit is cut, never exceeding it."""
        chunks = chunk_document("x" * (CHUNK_MAX_CHARS + 50), lang=Lang.UZ_LATN)
        assert chunks[0].char_count == CHUNK_MAX_CHARS
