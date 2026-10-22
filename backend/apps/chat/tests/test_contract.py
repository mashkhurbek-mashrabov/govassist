"""Contract tests: the committed docs/schema files match the code (run `invoke schema`)."""

import json
from pathlib import Path

from django.core.management import call_command

from apps.chat.management.commands.export_answer_schema import answer_schema_json

SCHEMA_DIR = Path(__file__).resolve().parents[4] / "docs" / "schema"


def test_answer_schema_file_is_current() -> None:
    """docs/schema/answer.schema.json equals Answer.model_json_schema()."""
    assert (SCHEMA_DIR / "answer.schema.json").read_text(encoding="utf-8") == answer_schema_json()


def test_openapi_file_is_current_and_valid(tmp_path: Path) -> None:
    """A fresh, validated OpenAPI document equals the committed one and includes /chat."""
    fresh = tmp_path / "openapi.json"
    call_command(
        "spectacular",
        "--format",
        "openapi-json",
        "--validate",
        "--fail-on-warn",
        "--file",
        str(fresh),
    )
    committed = json.loads((SCHEMA_DIR / "openapi.json").read_text(encoding="utf-8"))
    generated = json.loads(fresh.read_text(encoding="utf-8"))
    assert generated == committed
    assert "text/event-stream" in json.dumps(generated["paths"]["/api/v1/chat"])
