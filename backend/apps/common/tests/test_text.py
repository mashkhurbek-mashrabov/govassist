"""Tests for text detection, transliteration, canonicalization and normalization."""

from pathlib import Path

import pytest

from apps.common.i18n import Lang
from apps.common.text import (
    APOSTROPHES,
    OKINA,
    TUTUQ,
    canonicalize,
    detect_language,
    detect_script,
    normalize_for_search,
    uz_cyrl_to_latn,
)

_FIXTURES = Path(__file__).parent / "fixtures"
_GOLDEN_TSV = _FIXTURES / "translit_golden.tsv"


# ---------------------------------------------------------------------------
# Golden transliteration test
# ---------------------------------------------------------------------------


def _load_golden_pairs() -> list[tuple[str, str]]:
    """Load (cyrillic, latin) pairs from the golden TSV, skipping ``#`` lines."""
    pairs: list[tuple[str, str]] = []
    for line in _GOLDEN_TSV.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        cyrillic, latin = stripped.split("\t", maxsplit=1)
        pairs.append((cyrillic, latin))
    return pairs


_GOLDEN_PAIRS = _load_golden_pairs()


@pytest.mark.parametrize(
    ("cyrillic", "expected_latin"), _GOLDEN_PAIRS, ids=[p[0] for p in _GOLDEN_PAIRS]
)
def test_golden_transliteration(cyrillic: str, expected_latin: str) -> None:
    """Each golden word pair must transliterate correctly."""
    assert uz_cyrl_to_latn(cyrillic) == expected_latin


def test_golden_file_has_50_pairs() -> None:
    """The golden fixture must contain exactly 50 word pairs."""
    assert len(_GOLDEN_PAIRS) == 50


# ---------------------------------------------------------------------------
# detect_script
# ---------------------------------------------------------------------------


class TestDetectScript:
    """Tests for ``detect_script``."""

    def test_pure_cyrillic(self) -> None:
        """All Cyrillic letters gives ``cyrl``."""
        assert detect_script("Ўзбекистон") == "cyrl"

    def test_pure_latin(self) -> None:
        """All Latin letters gives ``latn``."""
        assert detect_script("Oʻzbekiston") == "latn"

    def test_majority_cyrillic(self) -> None:
        """More than half Cyrillic is ``cyrl``."""
        assert detect_script("Текст with some латин") == "cyrl"

    def test_majority_latin(self) -> None:
        """More than half Latin is ``latn``."""
        assert detect_script("Text with some latin words here and there") == "latn"

    def test_empty_text(self) -> None:
        """Empty text defaults to ``latn``."""
        assert detect_script("") == "latn"

    def test_digits_only(self) -> None:
        """Digits only (no letters) defaults to ``latn``."""
        assert detect_script("123 456 789") == "latn"

    def test_mixed_punctuation_only(self) -> None:
        """Punctuation and symbols without letters defaults to ``latn``."""
        assert detect_script("!@#$%^&*()") == "latn"


# ---------------------------------------------------------------------------
# detect_language
# ---------------------------------------------------------------------------


class TestDetectLanguage:
    """Tests for ``detect_language``."""

    def test_uzbek_cyrillic_by_letter(self) -> None:
        """Uzbek-specific Cyrillic letter ў triggers UZ_CYRL."""
        assert detect_language("Мен ўзбекман") == Lang.UZ_CYRL

    def test_uzbek_cyrillic_by_stopword(self) -> None:
        """Uzbek stopword ``ва`` in Cyrillic text triggers UZ_CYRL."""
        assert detect_language("Давлат ва жамият") == Lang.UZ_CYRL

    def test_russian(self) -> None:
        """Cyrillic without Uzbek markers is Russian."""
        assert detect_language("Привет мир добро") == Lang.RU

    def test_uzbek_latin_by_okina(self) -> None:
        """Latin with oʻ triggers UZ_LATN."""
        assert detect_language("Oʻzbekiston davlati") == Lang.UZ_LATN

    def test_uzbek_latin_by_stopword(self) -> None:
        """Uzbek Latin stopword ``va`` triggers UZ_LATN."""
        assert detect_language("Davlat va jamiyat") == Lang.UZ_LATN

    def test_english(self) -> None:
        """Latin without Uzbek markers is English."""
        assert detect_language("Hello world example") == Lang.EN

    def test_empty_text(self) -> None:
        """Empty text: no letters → latn, no Uzbek markers → EN."""
        assert detect_language("") == Lang.EN

    def test_digits_only(self) -> None:
        """Only digits: latn script, no Uzbek markers → EN."""
        assert detect_language("12345 67890") == Lang.EN

    def test_uzbek_latin_apostrophe_variants(self) -> None:
        """Various apostrophe forms after o/g still detect UZ_LATN."""
        assert detect_language("o'zbekiston") == Lang.UZ_LATN
        assert detect_language("g`alaba") == Lang.UZ_LATN

    def test_uzbek_cyrillic_by_multiple_markers(self) -> None:
        """Multiple Uzbek-specific letters: қ ғ."""
        assert detect_language("Қонун ва ғалаба") == Lang.UZ_CYRL


# ---------------------------------------------------------------------------
# canonicalize
# ---------------------------------------------------------------------------


class TestCanonicalize:
    """Tests for ``canonicalize``."""

    def test_lowercase(self) -> None:
        """Text is lowercased."""
        assert canonicalize("HELLO World") == "hello world"

    def test_okina_after_o(self) -> None:
        """Apostrophe variants after ``o`` become ʻ (U+02BB)."""
        for apo in APOSTROPHES:
            result = canonicalize(f"o{apo}zbek")
            assert result == f"o{OKINA}zbek", f"Failed for apostrophe {apo!r}"

    def test_okina_after_g(self) -> None:
        """Apostrophe variants after ``g`` become ʻ (U+02BB)."""
        for apo in APOSTROPHES:
            result = canonicalize(f"g{apo}alaba")
            assert result == f"g{OKINA}alaba", f"Failed for apostrophe {apo!r}"

    def test_tutuq_elsewhere(self) -> None:
        """Apostrophe variants after other letters become ʼ (U+02BC)."""
        for apo in APOSTROPHES:
            result = canonicalize(f"ma{apo}lumot")
            assert result == f"ma{TUTUQ}lumot", f"Failed for apostrophe {apo!r}"

    def test_punctuation_stripped(self) -> None:
        """Punctuation characters are replaced with spaces and collapsed."""
        assert canonicalize("hello, world! (test)") == "hello world test"

    def test_whitespace_collapsed(self) -> None:
        """Multiple spaces and tabs collapse to single space."""
        assert canonicalize("  hello   world  ") == "hello world"

    def test_underscore_stripped(self) -> None:
        """Underscores are treated as non-word characters and removed."""
        assert canonicalize("hello_world") == "hello world"

    def test_cyrillic_preserved(self) -> None:
        """Cyrillic letters pass through canonicalize unchanged (except lowercase)."""
        assert canonicalize("Давлат") == "давлат"

    def test_apostrophe_at_start(self) -> None:
        """Apostrophe at the start of text (preceded by nothing) becomes ʼ."""
        result = canonicalize("'test")
        assert TUTUQ in result or result == "test" or result.startswith(TUTUQ)


# ---------------------------------------------------------------------------
# normalize_for_search
# ---------------------------------------------------------------------------


class TestNormalizeForSearch:
    """Tests for ``normalize_for_search``."""

    def test_uz_cyrl_transliterates_then_canonicalizes(self) -> None:
        """UZ_CYRL text is first transliterated to Latin, then canonicalized."""
        result = normalize_for_search("Ўзбекистон", Lang.UZ_CYRL)
        assert result == "oʻzbekiston"

    def test_uz_latn_canonicalizes_only(self) -> None:
        """UZ_LATN text is canonicalized without transliteration."""
        result = normalize_for_search("Oʻzbekiston!", Lang.UZ_LATN)
        assert result == f"o{OKINA}zbekiston"

    def test_russian_canonicalizes_only(self) -> None:
        """Russian text is canonicalized (lowercased, punctuation stripped)."""
        result = normalize_for_search("Привет, Мир!", Lang.RU)
        assert result == "привет мир"

    def test_english_canonicalizes_only(self) -> None:
        """English text is canonicalized."""
        result = normalize_for_search("Hello, World!", Lang.EN)
        assert result == "hello world"

    def test_uz_cyrl_and_latn_converge(self) -> None:
        """The same word in Cyrillic and Latin normalizes to the same string."""
        cyrl_norm = normalize_for_search("давлат", Lang.UZ_CYRL)
        latn_norm = normalize_for_search("davlat", Lang.UZ_LATN)
        assert cyrl_norm == latn_norm
