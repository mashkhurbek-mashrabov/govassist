"""Project tasks (invoke). Containers run via docker compose; quality checks run in .venv."""

import shutil
import sys
from pathlib import Path

from invoke.context import Context
from invoke.tasks import task

ROOT = Path(__file__).resolve().parent
BACKEND = ROOT / "backend"
SCHEMA_DIR = ROOT / "docs" / "schema"
PYTHON = sys.executable
PYTHON_IMAGE = "python:3.14-slim-trixie"
PIP_TOOLS_VERSION = "7.6.2"
REQUIREMENT_SETS = ("base", "crawler", "dev")


def _ensure_env() -> None:
    """Create ``.env`` from ``.env.example`` on a clean checkout (values stay unread)."""
    env_file = ROOT / ".env"
    if not env_file.exists():
        shutil.copyfile(ROOT / ".env.example", env_file)
        print("Created .env from .env.example; set GEMINI_API_KEY there.")


def _compose(c: Context, args: str, *, pty: bool = False) -> None:
    """Run ``docker compose`` from the repo root.

    Args:
        c: Invoke context.
        args: Arguments after ``docker compose``.
        pty: Attach a terminal (interactive commands).
    """
    _ensure_env()
    with c.cd(str(ROOT)):
        c.run(f"docker compose {args}", pty=pty)


def _manage(c: Context, args: str, *, pty: bool = False) -> None:
    """Run ``manage.py`` inside a one-off backend container (entrypoint ``manage`` role).

    Args:
        c: Invoke context.
        args: Arguments after ``manage.py``.
        pty: Attach a terminal.
    """
    _compose(c, f"run --rm backend manage {args}", pty=pty)


def _backend(c: Context, command: str) -> None:
    """Run a local command inside ``backend/`` with the venv's Python.

    Args:
        c: Invoke context.
        command: Arguments after ``python -m``.
    """
    with c.cd(str(BACKEND)):
        c.run(f"{PYTHON} -m {command}")


# --- Containers -------------------------------------------------------------------


@task
def up(c: Context) -> None:
    """Build and start db, redis, backend and worker in the background."""
    _compose(c, "up -d --build")


@task
def down(c: Context) -> None:
    """Stop the stack (data volumes are kept)."""
    _compose(c, "down")


@task
def build(c: Context) -> None:
    """Build the backend (runtime) and worker (crawler) images."""
    _compose(c, "build")


@task
def logs(c: Context, service: str = "") -> None:
    """Follow logs of all services or one service."""
    _compose(c, f"logs -f --tail 200 {service}", pty=True)


@task
def ps(c: Context) -> None:
    """List running services."""
    _compose(c, "ps")


@task
def sh(c: Context, service: str = "backend") -> None:
    """Open a shell in a running service."""
    _compose(c, f"exec {service} sh", pty=True)


@task
def manage(c: Context, cmd: str) -> None:
    """Run any manage.py command, e.g. ``invoke manage --cmd "shell"``."""
    _manage(c, cmd, pty=True)


# --- Database ---------------------------------------------------------------------


@task
def migrate(c: Context) -> None:
    """Apply migrations (entrypoint ``migrate`` role)."""
    _compose(c, "run --rm backend migrate")


@task
def makemigrations(c: Context, app: str = "") -> None:
    """Create migrations locally (host venv, bind-mounted code)."""
    _backend(c, f"django makemigrations {app} --settings=config.settings.test")


@task
def createsuperuser(c: Context) -> None:
    """Create an admin user interactively."""
    _manage(c, "createsuperuser", pty=True)


@task
def backup(c: Context, path: str = "backup.sql.gz") -> None:
    """Dump the database to a gzip file on the host."""
    _ensure_env()
    with c.cd(str(ROOT)):
        c.run(
            "docker compose exec -T db sh -c "
            "'pg_dump -U \"$POSTGRES_USER\" \"$POSTGRES_DB\"' | gzip > " + path
        )


# --- Data -------------------------------------------------------------------------


@task
def seed(c: Context) -> None:
    """Load SOATO geo data, office types and the sample crawl sources."""
    _manage(c, "seed")


@task
def crawl(c: Context, source: str) -> None:
    """Crawl one source now (id or exact name), in the worker image."""
    _compose(c, f'run --rm worker manage crawl --source "{source}"')


@task
def index(c: Context, document: str = "") -> None:
    """Index one document, or every approved document that has no chunks yet."""
    target = f"--document {document}" if document else "--all-pending"
    _compose(c, f"run --rm worker manage index {target}")


# --- Contract ---------------------------------------------------------------------


@task
def schema(c: Context) -> None:
    """Regenerate docs/schema/openapi.json and docs/schema/answer.schema.json."""
    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    _backend(
        c,
        "django spectacular --settings=config.settings.test --format openapi-json "
        f"--validate --fail-on-warn --file {SCHEMA_DIR / 'openapi.json'}",
    )
    _backend(c, f"django export_answer_schema --settings=config.settings.test {SCHEMA_DIR}")


# --- Quality ----------------------------------------------------------------------


@task
def lint(c: Context) -> None:
    """Ruff lint + format check."""
    _backend(c, "ruff check .")
    _backend(c, "ruff format --check .")


@task
def format(c: Context) -> None:  # noqa: A001 (invoke task name)
    """Format and auto-fix with ruff."""
    _backend(c, "ruff format .")
    _backend(c, "ruff check --fix .")


@task
def typecheck(c: Context) -> None:
    """mypy --strict."""
    _backend(c, "mypy .")


@task
def test(c: Context, k: str = "") -> None:
    """Run pytest with coverage (needs the db container: ``invoke up``)."""
    _backend(c, f"pytest {f'-k {k}' if k else ''}")


@task(lint, typecheck, test)
def check(c: Context) -> None:
    """Lint, typecheck and test: the definition of done."""


# --- Dependencies -----------------------------------------------------------------


@task(name="compile-deps")
def compile_deps(c: Context) -> None:
    """Recompile hashed requirements/{base,crawler,dev}.txt from the .in files (Linux)."""
    commands = " && ".join(
        f"pip-compile -q --generate-hashes --allow-unsafe --strip-extras "
        f"--no-emit-index-url requirements/{name}.in -o requirements/{name}.txt"
        for name in REQUIREMENT_SETS
    )
    c.run(
        f'docker run --rm -e CUSTOM_COMPILE_COMMAND="invoke compile-deps" '
        f"-v {BACKEND}:/src -w /src {PYTHON_IMAGE} "
        f'sh -c "pip install -q pip-tools=={PIP_TOOLS_VERSION} && {commands}"'
    )
