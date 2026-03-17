#!/usr/bin/env python3
"""Configuration model for one LiteLLM model alias."""

from pydantic import BaseModel, ConfigDict, field_validator


class LiteLLMModelAlias(BaseModel):
    """Persistent settings that map a local alias to a LiteLLM completion target."""

    model_config = ConfigDict(extra="forbid")

    alias: str
    provider_model: str
    api_base: str | None = None
    api_key_env: str | None = None

    @field_validator("alias", "provider_model")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        """Reject empty required alias fields."""
        cleaned_value = value.strip()
        if not cleaned_value:
            raise ValueError("LiteLLM alias fields must not be empty")

        return cleaned_value

    @field_validator("api_base", "api_key_env")
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        """Normalize optional text fields and reject empty strings."""
        if value is None:
            return None

        cleaned_value = value.strip()
        if not cleaned_value:
            raise ValueError("LiteLLM optional text fields must not be empty strings")

        return cleaned_value
