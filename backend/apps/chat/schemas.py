"""The Answer schema (contract §5): sent to Gemini as ``response_schema`` and validated here.

Field order is part of the contract (the summary must stream first), so every object also
carries an explicit ``propertyOrdering``.
"""

from typing import Any, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, RootModel, field_validator, model_validator

type LangCode = Literal["uz-Latn", "uz-Cyrl", "ru", "en"]
type AnswerType = Literal["service", "legal", "not_found", "off_topic"]

TITLE_MAX_CHARS = 80
STEPS_MAX = 7
FOLLOW_UPS_MAX = 3
REFUSED_TYPES = frozenset({"not_found", "off_topic"})


def _keep_property_order(schema: dict[str, Any]) -> None:
    """Pin the JSON property order for Gemini (``propertyOrdering``).

    Args:
        schema: The model's JSON schema, edited in place.
    """
    schema["propertyOrdering"] = list(schema.get("properties", {}))


class OrderedModel(BaseModel):
    """Strict base: unknown keys are errors and property order is pinned."""

    model_config = ConfigDict(extra="forbid", json_schema_extra=_keep_property_order)


class Item(OrderedModel):
    """One statement with the context sources that support it."""

    text: str
    source_ids: list[str]


class LawPoint(OrderedModel):
    """An exact legal clause, its plain-language explanation and sources."""

    quote: str
    explanation: str
    source_ids: list[str]


class Answer(OrderedModel):
    """The structured answer card. Every field is always present."""

    answer_type: AnswerType
    language: LangCode
    title: str = Field(max_length=TITLE_MAX_CHARS)
    summary: str
    steps: list[Item] = Field(max_length=STEPS_MAX)
    documents: list[Item]
    fee: Item | None
    processing_time: Item | None
    law_points: list[LawPoint]
    follow_up_questions: list[str] = Field(max_length=FOLLOW_UPS_MAX)

    @field_validator("title", mode="before")
    @classmethod
    def _trim_title(cls, value: Any) -> Any:
        """Cut an over-long model title instead of failing the whole answer.

        Args:
            value: The raw title.
        """
        return value[:TITLE_MAX_CHARS].rstrip() if isinstance(value, str) else value

    @field_validator("steps", "follow_up_questions", mode="before")
    @classmethod
    def _trim_lists(cls, value: Any, info: Any) -> Any:
        """Keep at most the allowed number of steps / follow-up questions.

        Args:
            value: The raw list.
            info: Pydantic validation info (field name).
        """
        limit = STEPS_MAX if info.field_name == "steps" else FOLLOW_UPS_MAX
        return value[:limit] if isinstance(value, list) else value

    @model_validator(mode="after")
    def _refusals_are_bare(self) -> Self:
        """``not_found``/``off_topic`` keep only title, summary and follow-ups.

        Returns:
            The answer with every other field emptied.
        """
        if self.answer_type in REFUSED_TYPES:
            self.steps, self.documents, self.law_points = [], [], []
            self.fee = self.processing_time = None
        return self

    @property
    def refused(self) -> bool:
        """True for ``not_found`` and ``off_topic`` answers."""
        return self.answer_type in REFUSED_TYPES


class ChatRequest(BaseModel):
    """Body of ``POST /api/v1/chat``."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    conversation_id: UUID | None = None
    text: str = Field(min_length=1)


class Source(BaseModel):
    """A cited source (contract §5)."""

    id: str
    kind: Literal["law", "service_page", "other"]
    title: str
    publisher: str
    url: str
    section: str | None
    published_at: str | None
    fetched_at: str


class SourceList(RootModel[list[Source]]):
    """``sources`` of an assistant message (for the OpenAPI schema)."""
