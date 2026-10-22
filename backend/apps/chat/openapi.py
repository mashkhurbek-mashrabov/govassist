"""Adds the SSE chat endpoint (a plain async Django view) to the OpenAPI document."""

from typing import Any

from apps.chat.schemas import ChatRequest

CHAT_PATH = "/api/v1/chat"
PROBLEM = {"$ref": "#/components/schemas/Problem"}
CHAT_REQUEST = {"$ref": "#/components/schemas/ChatRequest"}


def _problem(description: str) -> dict[str, Any]:
    """A problem+json response entry."""
    content = {"application/problem+json": {"schema": PROBLEM}}
    return {"description": description, "content": content}


def add_chat_stream(result: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    """drf-spectacular postprocessing hook: document ``POST /api/v1/chat``.

    Args:
        result: The generated OpenAPI document.
        **kwargs: Hook context (unused).

    Returns:
        The document with the chat path and the shared Problem schema.
    """
    schemas = result.setdefault("components", {}).setdefault("schemas", {})
    schemas["ChatRequest"] = ChatRequest.model_json_schema()
    schemas["Problem"] = {
        "type": "object",
        "required": ["type", "title", "status", "detail", "code", "errors"],
        "properties": {
            "type": {"type": "string"},
            "title": {"type": "string"},
            "status": {"type": "integer"},
            "detail": {"type": "string"},
            "code": {"type": "string"},
            "errors": {"type": "object", "nullable": True},
            "retry_after": {"type": "integer"},
            "scope": {"type": "string", "enum": ["user", "global"]},
        },
    }
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
