#!/usr/bin/env python3
"""Request model for agent execution."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from agentinterface.agentmessage import AgentMessage


class AgentRequest(BaseModel):
    """Execution request for one agent run."""

    model_config = ConfigDict(extra="forbid")

    agent_id: str
    channel_id: str
    user_id: str | None = None
    endpoint_id: str | None = None
    correlation_id: str | None = None
    timestamp: datetime
    messages: list[AgentMessage]
    metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("agent_id", "channel_id")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        """Reject empty identifier values."""
        cleaned_value = value.strip()
        if not cleaned_value:
            raise ValueError("request identifiers must not be empty")

        return cleaned_value

    @field_validator("user_id", "endpoint_id", "correlation_id")
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        """Normalize blank optional text values to None."""
        if value is None:
            return None

        cleaned_value = value.strip()
        if not cleaned_value:
            return None

        return cleaned_value

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: datetime) -> datetime:
        """Normalize request timestamps to UTC."""
        if value.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")

        return value.astimezone(UTC)

    @field_validator("messages")
    @classmethod
    def validate_messages(cls, value: list[AgentMessage]) -> list[AgentMessage]:
        """Require at least one message to execute."""
        if not value:
            raise ValueError("messages must not be empty")

        return value
