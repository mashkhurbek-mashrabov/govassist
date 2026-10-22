"""Script/language detection and Uzbek text normalization (FIXED for v1, see plan §6).

Changing any rule here changes retrieval and therefore the evaluation results.
"""

import re
from typing import Literal

from apps.common.i18n import Lang

type Script = Literal["latn", "cyrl"]

CYRILLIC_RATIO_THRESHOLD = 0.5
UZ_CYRILLIC_LETTERS = frozenset("ўқғҳЎҚҒҲ")
UZ_CYRILLIC_STOPWORDS = frozenset({"ва", "учун", "билан"})
UZ_LATIN_STOPWORDS = frozenset({"va", "uchun", "bilan", "qanday"})

OKINA = "ʻ"  # U+02BB, after o/g: oʻ, gʻ
TUTUQ = "ʼ"  # U+02BC, glottal stop
APOSTROPHES = "ʻʼ'`‘’ʹ"
_UZ_LATIN_OKINA = re.compile(rf"[og][{APOSTROPHES}]", re.IGNORECASE)
_APOSTROPHE_AFTER = re.compile(rf"(.?)[{APOSTROPHES}]")
_NOT_WORD = re.compile(rf"[^\w\s{OKINA}{TUTUQ}]|_")
_SPACES = re.compile(r"\s+")
_CYRILLIC = re.compile(r"[Ѐ-ӿ]")
_LETTER = re.compile(r"[^\W\d_]")
_WORD = re.compile(r"\w+")

_CYRL_VOWELS = frozenset("аеёиоуэюяўАЕЁИОУЭЮЯЎ")
_SIGNS = frozenset("ъьЪЬ")
_CYRL_TO_LATN: dict[str, str] = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "ё": "yo", "ж": "j", "з": "z",
    "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p",
    "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "x", "ц": "ts", "ч": "ch",
    "ш": "sh", "щ": "sh", "ъ": TUTUQ, "ы": "i", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    "ў": f"o{OKINA}", "қ": "q", "ғ": f"g{OKINA}", "ҳ": "h",
}  # fmt: skip


def detect_script(text: str) -> Script:
    """Return ``cyrl`` when most letters are Cyrillic, else ``latn``.

    Args:
        text: Any user text.
    """
    letters = _LETTER.findall(text)
    if not letters:
        return "latn"
    cyrillic = sum(1 for letter in letters if _CYRILLIC.match(letter))
    return "cyrl" if cyrillic / len(letters) > CYRILLIC_RATIO_THRESHOLD else "latn"


def _words(text: str) -> set[str]:
    """Lowercased word set of ``text``."""
    return {word.lower() for word in _WORD.findall(text)}


def detect_language(text: str) -> Lang:
    """Guess the language/script of a question.

    Cyrillic is Uzbek when it has ў қ ғ ҳ or Uzbek stop-words, else Russian. Latin is Uzbek
    when it has oʻ/gʻ (any apostrophe) or Uzbek stop-words, else English.

    Args:
        text: The (scrubbed) question.
    """
    words = _words(text)
    if detect_script(text) == "cyrl":
        is_uzbek = bool(UZ_CYRILLIC_LETTERS & set(text)) or bool(UZ_CYRILLIC_STOPWORDS & words)
        return Lang.UZ_CYRL if is_uzbek else Lang.RU
    is_uzbek = bool(_UZ_LATIN_OKINA.search(text)) or bool(UZ_LATIN_STOPWORDS & words)
    return Lang.UZ_LATN if is_uzbek else Lang.EN


def _latin_for(char: str, previous: str) -> str:
    """Transliterate one Cyrillic character given the character before it.

    ``е`` becomes ``ye`` at the start of a word or after a vowel or sign, else ``e``.
    Upper case is kept on the first output letter (Ш → Sh).

    Args:
        char: The character to convert.
        previous: The preceding source character ("" at the start).
    """
    lower = char.lower()
    if lower == "е":
        starts_syllable = not previous.isalpha() or previous in _CYRL_VOWELS | _SIGNS
        latin = "ye" if starts_syllable else "e"
    else:
        latin = _CYRL_TO_LATN.get(lower, char)
    return latin.capitalize() if char != lower and latin else latin


def uz_cyrl_to_latn(text: str) -> str:
    """Transliterate Uzbek Cyrillic to the official Latin alphabet.

    Args:
        text: Uzbek text in Cyrillic (other characters pass through).

    Returns:
        The Latin text.
    """
    return "".join(_latin_for(char, text[i - 1] if i else "") for i, char in enumerate(text))


def _unify_apostrophe(match: re.Match[str]) -> str:
    """Map one apostrophe to ʻ after o/g, else to ʼ (keeping the preceding char)."""
    before = match.group(1)
    return before + (OKINA if before.lower() in {"o", "g"} else TUTUQ)


def canonicalize(text: str) -> str:
    """Lowercase, unify apostrophes, strip punctuation and collapse whitespace.

    Args:
        text: Latin or Cyrillic text.
    """
    lowered = _APOSTROPHE_AFTER.sub(_unify_apostrophe, text.lower())
    return _SPACES.sub(" ", _NOT_WORD.sub(" ", lowered)).strip()


def normalize_for_search(text: str, lang: str) -> str:
    """Normalize text for keyword search.

    Uzbek Cyrillic is transliterated to Latin first, so both scripts meet in one index.

    Args:
        text: Document chunk or query text.
        lang: The text's ``Lang``.
    """
    if lang == Lang.UZ_CYRL:
        text = uz_cyrl_to_latn(text)
    return canonicalize(text)
