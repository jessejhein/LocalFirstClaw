#!/usr/bin/env python3
"""Configuration model for one callable agent."""

from pydantic import BaseModel, ConfigDict, field_validator


class AgentConfig(BaseModel):
    """Persistent configuration for one agent entry."""

    model_config = ConfigDict(extra="forbid")

    agent_id: str
    model: str
    system_prompt: str

    @field_validator("agent_id", "model", "system_prompt")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        """Reject empty required text values."""
        cleaned_value = value.strip()
        if not cleaned_value:
            raise ValueError("agent configuration fields must not be empty")

        return cleaned_value
