"""Validated shapes of evaluation inputs (JSONL questions, judge replies, external CSV rows)."""

from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from apps.common.constants import Lang
from apps.evaluation.constants import Category, PromptStyle, Script


class QuestionRow(BaseModel):
    """One line of a question-set JSONL file."""

    model_config = ConfigDict(extra="forbid")

    qid: str = Field(min_length=1, max_length=50)
    question: str = Field(min_length=1)
    language: Lang
    script: Script
    group_id: str = Field(min_length=1, max_length=50)
    category: Category
    expected_facts: list[str] = Field(default_factory=list)
    expected_doc_ids: list[str] = Field(default_factory=list)
    expected_office_type: str = ""
    district_id: int | None = None
    in_corpus: bool = True


class JudgeVerdict(BaseModel):
    """The judge's strict JSON reply."""

    model_config = ConfigDict(extra="forbid")

    correctness: int = Field(ge=0, le=2)
    grounded: bool
    unsupported_claims: list[str] = Field(default_factory=list)


class ExternalRow(BaseModel):
    """One external chatbot answer (systems C and D), as transcribed by a person."""

    qid: str = Field(min_length=1)
    system: str = Field(min_length=1)
    model_version: str = Field(min_length=1)
    prompt_style: PromptStyle
    date: date
    answer_text: str = Field(min_length=1)
    system_prompt: str = ""
