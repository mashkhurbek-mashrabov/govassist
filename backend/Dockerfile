# syntax=docker/dockerfile:1.7
# Targets: runtime (API, ≤ 300 MB) and crawler (db_worker + Chromium).

FROM python:3.14-slim-trixie AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH=/opt/venv/bin:$PATH
RUN groupadd --system --gid 10001 app \
 && useradd --system --uid 10001 --gid app --home-dir /app --no-create-home app
WORKDIR /app

FROM base AS builder
# The venv gets no pip (installed with the base image's pip) and no .pyc files:
# both only cost image size; the root filesystem is read-only at runtime anyway.
RUN python -m venv --without-pip /opt/venv
COPY requirements/base.txt requirements/base.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip --python /opt/venv/bin/python install --no-compile --require-hashes --no-deps \
      -r requirements/base.txt
COPY . .
RUN SECRET_KEY=collectstatic-only \
    DATABASE_URL=postgres://unused@localhost/unused \
    REDIS_URL=redis://localhost:6379/0 \
    DJANGO_SETTINGS_MODULE=config.settings.prod \
    python manage.py collectstatic --noinput

FROM base AS runtime
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app /app
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=4)"]
CMD ["uvicorn", "config.asgi:application", "--host", "0.0.0.0", "--port", "8000", "--workers", "2", "--proxy-headers"]

FROM base AS crawler
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
COPY --from=builder /opt/venv /opt/venv
COPY requirements/crawler.txt requirements/crawler.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip --python /opt/venv/bin/python install --no-compile --require-hashes --no-deps \
      -r requirements/crawler.txt \
 && playwright install --with-deps chromium \
 && rm -rf /var/lib/apt/lists/*
COPY --from=builder /app /app
USER app
CMD ["python", "manage.py", "db_worker"]
