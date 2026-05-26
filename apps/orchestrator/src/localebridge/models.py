"""Pydantic models shared across the orchestrator."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Status = Literal["pending_review", "approved", "rejected", "edited"]


class ExtractedString(BaseModel):
    """Mirror of the extractor's output entry."""

    key: str
    default_value: str
    source_file: str
    line: int
    context: str


class Translation(BaseModel):
    """One translation of one key into one locale."""

    key: str
    locale: str
    source_text: str
    translated_text: str
    status: Status = "pending_review"
    edit_reason: str | None = None
    reject_reason: str | None = None


class ValidationIssue(BaseModel):
    severity: Literal["error", "warning"]
    code: str
    message: str
    locale: str
    key: str


class ValidationReport(BaseModel):
    issues: list[ValidationIssue] = Field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return any(i.severity == "error" for i in self.issues)
