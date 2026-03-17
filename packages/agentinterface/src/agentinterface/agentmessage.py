#!/usr/bin/env python3
"""Message model for agent execution inputs."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator


class AgentMessage(BaseModel):
    """One message in an agent execution transcript."""

    model_config = ConfigDict(extra="forbid")

    role: Literal["system", "user", "assistant", "tool"]
    content: str

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        """Reject empty message content."""
        cleaned_value = value.strip()
        if not cleaned_value:
            raise ValueError("message content must not be empty")

        return cleaned_value
