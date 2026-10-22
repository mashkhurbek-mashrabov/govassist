"""Test settings: no network, no Redis, tasks run inline.

Tests run on the host against the dev database container published on ``DB_HOST_PORT``.
"""

import os
from pathlib import Path

import environ

environ.Env.read_env(Path(__file__).resolve().parents[3] / ".env", overwrite=False)
_db_port = os.environ.get("DB_HOST_PORT", "5432")
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", f"postgres://govassist:govassist@localhost:{_db_port}/govassist"
)
os.environ.setdefault("SECRET_KEY", "test-only-secret-key")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")

from .base import *  # noqa: E402

DEBUG = False
GEMINI_API_KEY = ""
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
TASKS = {"default": {"BACKEND": "django.tasks.backends.immediate.ImmediateBackend"}}
MAILERS = {"default": {"BACKEND": "django.core.mail.backends.locmem.EmailBackend"}}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
STORAGES["staticfiles"] = {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}
REST_FRAMEWORK["DEFAULT_THROTTLE_CLASSES"] = []
LOGGING["root"]["level"] = "WARNING"
