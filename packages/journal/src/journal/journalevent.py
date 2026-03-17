#!/usr/bin/env python3
"""Event model for append-only journal records."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from journal.journallevel import JournalLevel


class JournalEvent(BaseModel):
    """Structured journal event with required metadata."""

    model_config = ConfigDict(extra="forbid")

    timestamp: datetime
    level: JournalLevel
    event_type: str
    source: str
    agent_id: str
    correlation_id: str | None = None
    tags: list[str] = Field(default_factory=list)
    message: str
    payload: dict[str, Any] = Field(default_factory=dict)

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: datetime) -> datetime:
        """Ensure timestamps are timezone-aware and normalized to UTC."""
        if value.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")

        return value.astimezone(UTC)

    @field_validator("event_type", "source", "agent_id", "message")
    @classmethod
    def validate_required_text(cls, value: str, info) -> str:
        """Reject empty required text fields."""
        cleaned_value = value.strip()

        if not cleaned_value:
            raise ValueError(f"{info.field_name} must not be empty")

        return cleaned_value

    @field_validator("correlation_id")
    @classmethod
    def validate_optional_correlation_id(cls, value: str | None) -> str | None:
        """Normalize empty correlation identifiers to missing."""
        if value is None:
            return None

        cleaned_value = value.strip()

        if not cleaned_value:
            return None

        return cleaned_value

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value: list[str]) -> list[str]:
        """Normalize tag values and reject empty tags."""
        normalized_tags: list[str] = []

        for tag in value:
            cleaned_tag = tag.strip()
            if not cleaned_tag:
                raise ValueError("tags must not contain empty values")
            normalized_tags.append(cleaned_tag)

        return normalized_tags
