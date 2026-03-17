#!/usr/bin/env python3
"""Query model for recent journal reads."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from journal.journallevel import JournalLevel


class JournalQuery(BaseModel):
    """Structured filters for recent journal queries."""

    model_config = ConfigDict(extra="forbid")

    since: datetime | str | None = None
    until: datetime | str | None = None
    now: datetime | None = None
    levels: list[JournalLevel] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    agent_ids: list[str] = Field(default_factory=list)
    event_types: list[str] = Field(default_factory=list)
    text: str | None = None

    @field_validator("now")
    @classmethod
    def validate_now(cls, value: datetime | None) -> datetime | None:
        """Normalize explicit query reference times to UTC."""
        if value is None:
            return None
        if value.tzinfo is None:
            raise ValueError("now must be timezone-aware")

        return value.astimezone(UTC)

    @field_validator("tags", "agent_ids", "event_types")
    @classmethod
    def validate_string_lists(cls, value: list[str]) -> list[str]:
        """Strip surrounding whitespace and reject empty list members."""
        normalized_values: list[str] = []

        for entry in value:
            cleaned_entry = entry.strip()
            if not cleaned_entry:
                raise ValueError("query filters must not contain empty values")
            normalized_values.append(cleaned_entry)

        return normalized_values

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str | None) -> str | None:
        """Normalize optional text search input."""
        if value is None:
            return None

        cleaned_value = value.strip()

        if not cleaned_value:
            return None

        return cleaned_value
