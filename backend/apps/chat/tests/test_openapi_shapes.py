"""Pin the OpenAPI shapes the SPA's generated types rely on (contract §1 and §3).

``test_contract`` keeps ``docs/schema/openapi.json`` equal to the code, so these tests read
the committed file.
"""

import json
from pathlib import Path
from typing import Any

import pytest

from apps.chat.constants import MessageErrorCode
from apps.collector.constants import SOURCE_SUMMARY_KINDS

OPENAPI = Path(__file__).resolve().parents[4] / "docs" / "schema" / "openapi.json"
QUOTA_FIELDS = {"hour_limit", "hour_used", "day_limit", "day_used"}


@pytest.fixture(scope="module")
def schemas() -> dict[str, Any]:
    """The committed components/schemas map."""
    document: dict[str, Any] = json.loads(OPENAPI.read_text(encoding="utf-8"))
    components: dict[str, Any] = document["components"]["schemas"]
    return components


def _enum(schemas: dict[str, Any], prop: dict[str, Any]) -> list[str]:
    """Resolve a ``$ref`` to an enum component and return its values."""
    name = prop["$ref"].rsplit("/", 1)[-1]
    values: list[str] = schemas[name]["enum"]
    return values


def _refs(prop: dict[str, Any]) -> list[str]:
    """``$ref`` targets and types listed in a ``oneOf``."""
    return [item.get("$ref", item.get("type")) for item in prop["oneOf"]]


def test_message_roles_are_discriminator_enums(schemas: dict[str, Any]) -> None:
    """Each message variant's role is a one-value enum, mapped by the discriminator."""
    user_role = schemas["UserMessage"]["properties"]["role"]
    assistant_role = schemas["AssistantMessage"]["properties"]["role"]
    assert _enum(schemas, user_role) == ["user"]
    assert _enum(schemas, assistant_role) == ["assistant"]
    assert schemas["Message"]["discriminator"]["mapping"] == {
        "user": "#/components/schemas/UserMessage",
        "assistant": "#/components/schemas/AssistantMessage",
    }


def test_assistant_answer_office_and_error_code_are_nullable(schemas: dict[str, Any]) -> None:
    """Answer / office are a ref or null; error_code is the failure enum or null."""
    props = schemas["AssistantMessage"]["properties"]
    assert _refs(props["answer"]) == ["#/components/schemas/Answer", "null"]
    assert _refs(props["office"]) == ["#/components/schemas/OfficeMatch", "null"]
    error_code, null = props["error_code"]["oneOf"]
    assert _enum(schemas, error_code) == list(MessageErrorCode.values)
    assert schemas[null["$ref"].rsplit("/", 1)[-1]] == {"type": "null"}


def test_me_quota_has_four_named_ints(schemas: dict[str, Any]) -> None:
    """Me.quota is the Quota object, not a free-form map."""
    quota_ref = schemas["Me"]["properties"]["quota"]["allOf"][0]["$ref"]
    quota = schemas[quota_ref.rsplit("/", 1)[-1]]
    assert set(quota["properties"]) == QUOTA_FIELDS
    assert set(quota["required"]) == QUOTA_FIELDS
    assert {prop["type"] for prop in quota["properties"].values()} == {"integer"}


def test_problem_optional_fields_and_errors_map(schemas: dict[str, Any]) -> None:
    """Detail / retry_after / scope are optional; errors is {field: [str]} or null."""
    problem = schemas["Problem"]
    assert set(problem["required"]) == {"type", "title", "status", "code", "errors"}
    errors = problem["properties"]["errors"]
    assert errors["type"] == ["object", "null"]
    assert errors["additionalProperties"] == {"type": "array", "items": {"type": "string"}}
    assert problem["properties"]["retry_after"] == {"type": "integer"}


@pytest.mark.parametrize("component", ["Conversation", "ConversationSummary"])
def test_conversation_title_is_required(schemas: dict[str, Any], component: str) -> None:
    """Titles are never empty, so the field is required."""
    assert "title" in schemas[component]["required"]


def test_sources_list_has_its_own_component(schemas: dict[str, Any]) -> None:
    """GET /sources is {items: SourceSummary[]}, distinct from the messages' SourceList."""
    items = schemas["SourceSummaryList"]["properties"]["items"]
    assert items["items"] == {"$ref": "#/components/schemas/SourceSummary"}
    assert schemas["SourceSummaryList"]["required"] == ["items"]
    assert schemas["SourceList"]["items"] == {"$ref": "#/components/schemas/Source"}


def test_source_summary_kind_is_an_enum(schemas: dict[str, Any]) -> None:
    """SourceSummary.kind is law | service_page | office | other, not a free string."""
    kind = schemas["SourceSummary"]["properties"]["kind"]
    assert _enum(schemas, kind["allOf"][0]) == ["law", "service_page", "office", "other"]
    assert _enum(schemas, kind["allOf"][0]) == list(SOURCE_SUMMARY_KINDS)
    assert schemas["KindEnum"]["enum"] == ["law", "service_page", "other"]  # messages' Source.kind
