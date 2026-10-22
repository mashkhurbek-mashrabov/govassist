"""Settings shared by every environment. Every tunable is read from env here."""

from pathlib import Path
from typing import Any

import environ

from config.unfold import SIDEBAR_NAVIGATION

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR.parent / ".env", overwrite=False)

# --- Core -------------------------------------------------------------------
SECRET_KEY = env.str("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])
FRONTEND_URL = env.str("FRONTEND_URL", default="http://localhost:5173").rstrip("/")
ADMIN_URL = env.str("ADMIN_URL", default="admin/")

INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "rest_framework",
    "drf_spectacular",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.headless",
    "django_tasks_db",
    "apps.common",
    "apps.accounts",
    "apps.geo",
    "apps.offices",
    "apps.collector",
    "apps.corpus",
    "apps.chat",
]

MIDDLEWARE = [
    "apps.common.logging.request_id_middleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "config.urls"
ASGI_APPLICATION = "config.asgi.application"
AUTH_USER_MODEL = "accounts.User"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --- Data stores ----------------------------------------------------------------
DATABASES = {"default": env.db("DATABASE_URL")}
DATABASES["default"]["CONN_MAX_AGE"] = 0
DATABASES["default"]["OPTIONS"] = {
    "options": "-c hnsw.ef_search=100 -c hnsw.iterative_scan=relaxed_order",
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env.str("REDIS_URL"),
    },
}

TASKS = {"default": {"BACKEND": "django_tasks_db.backend.DatabaseBackend"}}

# --- Auth -------------------------------------------------------------------------
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
PASSWORD_MIN_LENGTH = 10
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": PASSWORD_MIN_LENGTH},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*"]
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = True
ACCOUNT_EMAIL_VERIFICATION_BY_CODE_ENABLED = False
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_SIGNUP_FORM_CLASS = "apps.accounts.forms.SignupForm"
HEADLESS_ONLY = True
HEADLESS_CLIENTS = ("browser",)
HEADLESS_SERVE_SPECIFICATION = DEBUG
HEADLESS_FRONTEND_URLS = {
    "account_confirm_email": f"{FRONTEND_URL}/verify-email/{{key}}",
    "account_reset_password_from_key": f"{FRONTEND_URL}/reset-password/{{key}}",
    "account_signup": f"{FRONTEND_URL}/signup",
    "socialaccount_login_error": f"{FRONTEND_URL}/login?error=social",
}
SOCIALACCOUNT_EMAIL_AUTHENTICATION = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION_AUTO_CONNECT = True
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APPS": [
            {
                "client_id": env.str("GOOGLE_OAUTH_CLIENT_ID", default=""),
                "secret": env.str("GOOGLE_OAUTH_CLIENT_SECRET", default=""),
            },
        ],
        "SCOPE": ["profile", "email"],
        "EMAIL_AUTHENTICATION": True,
    },
}
TURNSTILE_SECRET_KEY = env.str("TURNSTILE_SECRET_KEY", default="")
TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
TURNSTILE_TIMEOUT_S = 5

SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"

# --- Email ------------------------------------------------------------------------
_email = env.email_url("EMAIL_URL", default="consolemail://")
_SMTP_OPTIONS = {
    "EMAIL_HOST": "host",
    "EMAIL_PORT": "port",
    "EMAIL_HOST_USER": "username",
    "EMAIL_HOST_PASSWORD": "password",
    "EMAIL_USE_TLS": "use_tls",
    "EMAIL_USE_SSL": "use_ssl",
}
MAILERS: dict[str, dict[str, Any]] = {
    "default": {
        "BACKEND": _email["EMAIL_BACKEND"],
        "OPTIONS": (
            {option: _email[key] for key, option in _SMTP_OPTIONS.items() if key in _email}
            if _email["EMAIL_BACKEND"].endswith("smtp.EmailBackend")
            else {}
        ),
    },
}
DEFAULT_FROM_EMAIL = env.str("DEFAULT_FROM_EMAIL", default="GovAssist <no-reply@example.com>")

# --- API --------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": env.str("THROTTLE_ANON", default="60/min"),
        "user": env.str("THROTTLE_USER", default="120/min"),
    },
    "EXCEPTION_HANDLER": "apps.common.problems.exception_handler",
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
    "NUM_PROXIES": env.int("NUM_PROXIES", default=0),
}

SPECTACULAR_SETTINGS = {
    "TITLE": "GovAssist API",
    "DESCRIPTION": "App API. Source of truth: docs/contract.md.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "SCHEMA_PATH_PREFIX": "/api/v1",
}

# --- i18n / static --------------------------------------------------------------------
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Tashkent"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# --- Gemini, RAG, chat -------------------------------------------------------------
GEMINI_API_KEY = env.str("GEMINI_API_KEY", default="")
GEMINI_MODEL = env.str("GEMINI_MODEL", default="gemini-3.8-flash")
GEMINI_EMBEDDING_MODEL = env.str("GEMINI_EMBEDDING_MODEL", default="gemini-embedding-2")
EMBEDDING_DIM = env.int("EMBEDDING_DIM", default=768)
EMBED_CONCURRENCY = env.int("EMBED_CONCURRENCY", default=8)
EMBED_MAX_TRIES = env.int("EMBED_MAX_TRIES", default=5)
LLM_TIMEOUT_S = env.int("LLM_TIMEOUT_S", default=40)
LLM_MAX_OUTPUT_TOKENS = env.int("LLM_MAX_OUTPUT_TOKENS", default=1500)
LLM_TEMPERATURE = env.float("LLM_TEMPERATURE", default=0.1)
LLM_MAX_RETRIES = env.int("LLM_MAX_RETRIES", default=2)
RAG_TOP_K_VECTOR = env.int("RAG_TOP_K_VECTOR", default=8)
RAG_TOP_K_KEYWORD = env.int("RAG_TOP_K_KEYWORD", default=8)
RAG_FINAL_K = env.int("RAG_FINAL_K", default=5)
RAG_MAX_PER_DOC = env.int("RAG_MAX_PER_DOC", default=2)
RAG_RRF_K = env.int("RAG_RRF_K", default=60)
PROMPT_VERSION = env.str("PROMPT_VERSION", default="v1")
CORPUS_VERSION = env.str("CORPUS_VERSION", default="2026.10")
QUESTION_MAX_CHARS = env.int("QUESTION_MAX_CHARS", default=1000)
HISTORY_TURNS = env.int("HISTORY_TURNS", default=4)
CHAT_LIMIT_HOUR = env.int("CHAT_LIMIT_HOUR", default=20)
CHAT_LIMIT_DAY = env.int("CHAT_LIMIT_DAY", default=100)
GLOBAL_DAILY_TOKEN_CAP = env.int("GLOBAL_DAILY_TOKEN_CAP", default=2_000_000)
STREAM_LOCK_TTL_S = env.int("STREAM_LOCK_TTL_S", default=120)
SSE_KEEPALIVE_S = env.int("SSE_KEEPALIVE_S", default=15)

# --- Collector ----------------------------------------------------------------------
CRAWLER_USER_AGENT = env.str(
    "CRAWLER_USER_AGENT",
    default="GovAssist-research/1.0 (+https://github.com/mashkhurbek-mashrabov/govassist)",
)
CRAWLER_RATE_PER_HOST = env.float("CRAWLER_RATE_PER_HOST", default=1.0)
CRAWLER_TIMEOUT_S = env.int("CRAWLER_TIMEOUT_S", default=30)
RAW_DATA_DIR = Path(env.str("RAW_DATA_DIR", default=str(BASE_DIR.parent / "data" / "raw")))

# --- Admin (django-unfold) ---------------------------------------------------------
ENVIRONMENT_NAME = env.str("ENVIRONMENT_NAME", default="DEV" if DEBUG else "PROD")
UNFOLD = {
    "SITE_TITLE": "GovAssist Admin",
    "SITE_HEADER": "GovAssist Admin",
    "ENVIRONMENT": "config.unfold.environment_callback",
    "DASHBOARD_CALLBACK": "config.unfold.dashboard_callback",
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": SIDEBAR_NAVIGATION,
    },
}

# --- Logging -------------------------------------------------------------------------
LOG_LEVEL = env.str("LOG_LEVEL", default="INFO")
LOGGING: dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {"request_id": {"()": "apps.common.logging.RequestIdFilter"}},
    "formatters": {
        "json": {
            "()": "pythonjsonlogger.json.JsonFormatter",
            "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "filters": ["request_id"],
        },
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
    "loggers": {"httpx": {"level": "WARNING"}, "google_genai": {"level": "WARNING"}},
}
