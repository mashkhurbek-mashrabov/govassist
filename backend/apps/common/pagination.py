from typing import Any
from urllib.parse import parse_qs, urlparse

from rest_framework.pagination import CursorPagination
from rest_framework.response import Response

from apps.common.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE


class ContractCursorPagination(CursorPagination):
    """Cursor pagination returning ``{"results": [...], "next": "<cursor>" | null}``.

    The contract wants the bare cursor token, not DRF's full next-page URL.
    """

    page_size = DEFAULT_PAGE_SIZE
    max_page_size = MAX_PAGE_SIZE
    page_size_query_param = "limit"
    ordering = "-updated_at"

    def next_cursor(self) -> str | None:
        """Extract the cursor token from DRF's next link.

        Returns:
            The opaque cursor, or None on the last page.
        """
        link = self.get_next_link()
        if link is None:
            return None
        return parse_qs(urlparse(link).query)[self.cursor_query_param][0]

    def get_paginated_response(self, data: Any) -> Response:
        """Wrap a page in the contract envelope.

        Args:
            data: Serialized page items.

        Returns:
            The paginated response.
        """
        return Response({"results": data, "next": self.next_cursor()})

    def get_paginated_response_schema(self, schema: dict[str, Any]) -> dict[str, Any]:
        """Describe the contract envelope for OpenAPI.

        Args:
            schema: The item list schema.

        Returns:
            The envelope schema.
        """
        return {
            "type": "object",
            "required": ["results", "next"],
            "properties": {"results": schema, "next": {"type": "string", "nullable": True}},
        }
