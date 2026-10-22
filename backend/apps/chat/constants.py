"""Constants of the chat app (AGENTS.md: no constant values elsewhere in the app)."""

from pathlib import Path

from django.db import models

from apps.common.constants import Lang

FEEDBACK_COMMENT_MAX_CHARS = 1000

HOUR_TTL_S = 3600

DAY_TTL_S = 90_000

FILE_NAME = "answer.schema.json"

CHAT_PATH = "/api/v1/chat"

PROBLEM = {"$ref": "#/components/schemas/Problem"}

CHAT_REQUEST = {"$ref": "#/components/schemas/ChatRequest"}

# RFC 9457 body (contract §1): retry_after only on rate_limited / quota_exceeded,
# scope only on quota_exceeded.
PROBLEM_SCHEMA = {
    "type": "object",
    "required": ["type", "title", "status", "code", "errors"],
    "properties": {
        "type": {"type": "string"},
        "title": {"type": "string"},
        "status": {"type": "integer"},
        "detail": {"type": "string"},
        "code": {"type": "string"},
        "errors": {
            "type": ["object", "null"],
            "additionalProperties": {"type": "array", "items": {"type": "string"}},
        },
        "retry_after": {"type": "integer"},
        "scope": {"type": "string", "enum": ["user", "global"]},
    },
}

NULLABLE_ASSISTANT_FIELDS = ("answer", "office")

PROMPTS_DIR = Path(__file__).parent / "prompts"

USER_MARKER = "=== USER ==="

NONE = "(none)"

LANGUAGE_NAMES = {
    Lang.UZ_LATN: "Uzbek (Latin script)",
    Lang.UZ_CYRL: "Uzbek (Cyrillic script)",
    Lang.RU: "Russian",
    Lang.EN: "English",
}

TITLE_MAX_CHARS = 80

STEPS_MAX = 7

FOLLOW_UPS_MAX = 3

REFUSED_TYPES = frozenset({"not_found", "off_topic"})

GEMINI_UNSUPPORTED_KEYS = frozenset({"additionalProperties"})

PREVIEW_CHARS = 120

TITLE_FROM_QUESTION_CHARS = 60

PING = ": ping\n\n"

MAX_SUGGESTIONS = 6

SUGGESTIONS: dict[str, list[tuple[str, str]]] = {
    Lang.UZ_LATN: [
        ("Pasportimni qanday almashtiraman?", "passport"),
        ("Tugʻilganlik haqidagi guvohnomani qanday olaman?", "civil_registry"),
        ("Nikohni qayerda roʻyxatdan oʻtkazish mumkin?", "civil_registry"),
        ("Yashash joyi boʻyicha roʻyxatdan qanday oʻtaman?", "registration"),
        ("Haydovchilik guvohnomasini qanday almashtiraman?", "transport"),
        ("Mehnat shartnomasi qanday tuziladi?", "labor"),
    ],
    Lang.UZ_CYRL: [
        ("Паспортимни қандай алмаштираман?", "passport"),
        ("Туғилганлик ҳақидаги гувоҳномани қандай оламан?", "civil_registry"),
        ("Никоҳни қаерда рўйхатдан ўтказиш мумкин?", "civil_registry"),
        ("Яшаш жойи бўйича рўйхатдан қандай ўтаман?", "registration"),
        ("Ҳайдовчилик гувоҳномасини қандай алмаштираман?", "transport"),
        ("Меҳнат шартномаси қандай тузилади?", "labor"),
    ],
    Lang.RU: [
        ("Как заменить паспорт?", "passport"),
        ("Как получить свидетельство о рождении?", "civil_registry"),
        ("Где зарегистрировать брак?", "civil_registry"),
        ("Как встать на учёт по месту жительства?", "registration"),
        ("Как заменить водительское удостоверение?", "transport"),
        ("Как оформляется трудовой договор?", "labor"),
    ],
    Lang.EN: [
        ("How do I replace my passport?", "passport"),
        ("How do I get a birth certificate?", "civil_registry"),
        ("Where can I register a marriage?", "civil_registry"),
        ("How do I register my place of residence?", "registration"),
        ("How do I replace my driving licence?", "transport"),
        ("How is an employment contract concluded?", "labor"),
    ],
}

SSE_HEADERS = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}


class MessageRole(models.TextChoices):
    """Who wrote the message."""

    USER = "user", "User"
    ASSISTANT = "assistant", "Assistant"


class MessageStatus(models.TextChoices):
    """Assistant message lifecycle."""

    STREAMING = "streaming", "Streaming"
    COMPLETE = "complete", "Complete"
    FAILED = "failed", "Failed"


class MessageErrorCode(models.TextChoices):
    """Why an assistant message failed (``Message.error_code``, contract §3)."""

    STOPPED = "stopped", "Stopped"
    LLM_UNAVAILABLE = "llm_unavailable", "LLM unavailable"
    LLM_TIMEOUT = "llm_timeout", "LLM timeout"
    INVALID_ANSWER = "invalid_answer", "Invalid answer"
    QUOTA_EXCEEDED = "quota_exceeded", "Quota exceeded"
    INTERNAL_ERROR = "internal_error", "Internal error"


# One-value choice sets: the ``role`` discriminator of each message variant.
USER_ROLE = [MessageRole.USER]
ASSISTANT_ROLE = [MessageRole.ASSISTANT]


class FeedbackRating(models.IntegerChoices):
    """Thumbs up or down."""

    UP = 1, "Up"
    DOWN = -1, "Down"


STREAM_LOCK_PREFIX = "stream:"
LOCK_TOKEN_BITS = 62  # an int: Django's RedisCache stores ints raw, so Lua can compare them
RELEASE_LOCK_LUA = (
    'if redis.call("get", KEYS[1]) == ARGV[1] then return redis.call("del", KEYS[1]) end return 0'
)
