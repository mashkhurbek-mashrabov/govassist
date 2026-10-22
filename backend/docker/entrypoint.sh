#!/bin/sh
# Starts every backend container. The first argument is the role:
#
#   web            API server (uvicorn). Runs `migrate --noinput` first when
#                  DJANGO_MIGRATE_ON_START=true. DJANGO_RELOAD=true (dev) adds --reload
#                  with one worker; otherwise WEB_CONCURRENCY workers (default 2).
#                  Listens on PORT (default 8000).
#   worker         Background jobs (db_worker); --reload when DJANGO_RELOAD=true.
#   migrate        Apply migrations and exit.
#   manage ARGS    Any manage.py command, e.g. `manage check --deploy`.
#   anything else  Run as given, e.g. `sh` or `python -c ...`.
#
# Every role ends in `exec`, so signals reach the real process. Nothing is written to
# disk, so the script works on a read-only root filesystem.
set -eu

is_true() {
    [ "${1:-false}" = "true" ]
}

role="${1:-web}"
if [ "$#" -gt 0 ]; then
    shift
fi

case "$role" in
    web)
        if is_true "${DJANGO_MIGRATE_ON_START:-false}"; then
            python manage.py migrate --noinput
        fi
        set -- --host 0.0.0.0 --port "${PORT:-8000}" --proxy-headers
        if is_true "${DJANGO_RELOAD:-false}"; then
            exec uvicorn config.asgi:application "$@" --reload
        fi
        exec uvicorn config.asgi:application "$@" --workers "${WEB_CONCURRENCY:-2}"
        ;;
    worker)
        if is_true "${DJANGO_RELOAD:-false}"; then
            exec python manage.py db_worker --reload
        fi
        exec python manage.py db_worker
        ;;
    migrate)
        exec python manage.py migrate --noinput
        ;;
    manage)
        exec python manage.py "$@"
        ;;
    *)
        exec "$role" "$@"
        ;;
esac
