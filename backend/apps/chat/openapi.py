"""Adds the SSE chat endpoint (a plain async Django view) to the OpenAPI document."""

from typing import Any

from apps.chat.constants import (
    CHAT_PATH,
    CHAT_REQUEST,
    NULLABLE_ASSISTANT_FIELDS,
    PROBLEM,
    PROBLEM_SCHEMA,
)
from apps.chat.schemas import ChatRequest


def _problem(description: str) -> dict[str, Any]:
    """A problem+json response entry."""
    content = {"application/problem+json": {"schema": PROBLEM}}
    return {"description": description, "content": content}


def _make_nullable(properties: dict[str, Any], names: tuple[str, ...]) -> None:
    """Allow ``null`` on component-typed fields.

    drf-spectacular renders a pydantic-model field as ``allOf: [$ref]`` and cannot mark it
    nullable, so the ref is rewritten to ``oneOf: [$ref, null]`` (OpenAPI 3.1).

    Args:
        properties: A component's ``properties`` map, changed in place.
        names: The fields to make nullable.
    """
    for name in names:
        field = properties[name]
        field["oneOf"] = [*field.pop("allOf"), {"type": "null"}]


def add_chat_stream(result: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    """drf-spectacular postprocessing hook: document ``POST /api/v1/chat``.

    Args:
        result: The generated OpenAPI document.
        **kwargs: Hook context (unused).

    Returns:
        The document with the chat path, the shared Problem schema and nullable
        ``AssistantMessage.answer`` / ``office``.
    """
    schemas = result.setdefault("components", {}).setdefault("schemas", {})
    schemas["ChatRequest"] = ChatRequest.model_json_schema()
    schemas["Problem"] = PROBLEM_SCHEMA
    _make_nullable(schemas["AssistantMessage"]["properties"], NULLABLE_ASSISTANT_FIELDS)
    result.setdefault("paths", {})[CHAT_PATH] = {
        "post": {
            "operationId": "chat_stream",
            "summary": "Ask a question; the answer streams as Server-Sent Events",
            "description": (
                "Events: meta → status* → office? → delta* → final → done; error ends the "
                "stream. See docs/contract.md §4."
            ),
            "tags": ["chat"],
            "security": [{"cookieAuth": []}],
            "requestBody": {
                "required": True,
                "content": {"application/json": {"schema": CHAT_REQUEST}},
            },
            "responses": {
                "200": {
                    "description": "SSE stream (contract §4).",
                    "content": {"text/event-stream": {"schema": {"type": "string"}}},
                },
                "400": _problem("validation_error"),
                "401": _problem("not_authenticated"),
                "403": _problem("email_not_verified | profile_incomplete | csrf_failed"),
                "404": _problem("not_found (conversation)"),
                "409": _problem("stream_in_progress"),
                "429": _problem("rate_limited | quota_exceeded"),
            },
        }
    }
    return result
