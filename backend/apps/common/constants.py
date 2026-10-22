"""Constants of the common app (AGENTS.md: no constant values elsewhere in the app)."""

import re

from django.db import models

HEALTH_CACHE_KEY = "health:ping"

OK = "ok"

FAIL = "fail"

PERCENT = 100

RETRYABLE_STATUS = frozenset({408, 429, 500, 502, 503, 504})

BACKOFF_BASE_S = 0.5

BACKOFF_CAP_S = 20.0

RETRY_INFO_CAP_S = 90.0

RETRY_INFO_TYPE = "type.googleapis.com/google.rpc.RetryInfo"

MS_PER_S = 1000


class Lang(models.TextChoices):
    """The four supported languages/scripts."""

    UZ_LATN = "uz-Latn", "Oʻzbekcha"
    UZ_CYRL = "uz-Cyrl", "Ўзбекча"
    RU = "ru", "Русский"
    EN = "en", "English"


DEFAULT_LANG = Lang.UZ_LATN

ACCEPT_LANGUAGE_PREFIXES: tuple[tuple[str, Lang], ...] = (
    ("uz-cyrl", Lang.UZ_CYRL),
    ("uz", Lang.UZ_LATN),
    ("ru", Lang.RU),
    ("en", Lang.EN),
)

REQUEST_ID_HEADER = "X-Request-ID"

MAX_REQUEST_ID_LENGTH = 64


class ReviewStatus(models.TextChoices):
    """Admin review state of crawled documents and offices."""

    PENDING = "pending", "Pending"
    APPROVED = "approved", "Approved"
    REJECTED = "rejected", "Rejected"


DEFAULT_PAGE_SIZE = 20

MAX_PAGE_SIZE = 50

RULES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"), "[EMAIL]"),
    (re.compile(r"\b\d{14}\b"), "[PINFL]"),
    (re.compile(r"\b[A-Z]{2}\s?\d{7}\b", re.IGNORECASE), "[PASSPORT]"),
    (
        re.compile(r"(?<![\w+])(\+?998[\s-]?)?\(?\d{2}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}(?!\d)"),
        "[PHONE]",
    ),
)
"""Order matters: emails and 14-digit PINFLs go first so the phone rule never eats them."""

PROBLEM_CONTENT_TYPE = "application/problem+json"

CYRILLIC_RATIO_THRESHOLD = 0.5

UZ_CYRILLIC_LETTERS = frozenset("ўқғҳЎҚҒҲ")

UZ_CYRILLIC_STOPWORDS = frozenset({"ва", "учун", "билан"})

UZ_LATIN_STOPWORDS = frozenset({"va", "uchun", "bilan", "qanday"})

OKINA = "ʻ"  # U+02BB, after o/g: oʻ, gʻ

TUTUQ = "ʼ"  # U+02BC, glottal stop

APOSTROPHES = "ʻʼ'`‘’ʹ"

UZ_LATIN_OKINA = re.compile(rf"[og][{APOSTROPHES}]", re.IGNORECASE)

APOSTROPHE_AFTER = re.compile(rf"(.?)[{APOSTROPHES}]")

NOT_WORD = re.compile(rf"[^\w\s{OKINA}{TUTUQ}]|_")

SPACES = re.compile(r"\s+")

CYRILLIC = re.compile(r"[Ѐ-ӿ]")

LETTER = re.compile(r"[^\W\d_]")

WORD = re.compile(r"\w+")

CYRL_VOWELS = frozenset("аеёиоуэюяўАЕЁИОУЭЮЯЎ")

SIGNS = frozenset("ъьЪЬ")

CYRL_TO_LATN: dict[str, str] = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "ё": "yo", "ж": "j", "з": "z",
    "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p",
    "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "x", "ц": "ts", "ч": "ch",
    "ш": "sh", "щ": "sh", "ъ": TUTUQ, "ы": "i", "ь": "", "э": "e", "ю": "yu", "я": "ya",
    "ў": f"o{OKINA}", "қ": "q", "ғ": f"g{OKINA}", "ҳ": "h",
}  # fmt: skip

API_PREFIXES = ("/api/", "/_allauth/")

CSRF_DETAIL = "CSRF check failed. Reload the page and try again."


CLIENT_IP_HEADER = "X-Real-IP"  # set by our nginx from CF-Connecting-IP
