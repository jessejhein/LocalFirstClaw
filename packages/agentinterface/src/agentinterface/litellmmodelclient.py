#!/usr/bin/env python3
"""LiteLLM-backed model execution client."""

from __future__ import annotations

import os
from typing import Mapping

from litellm import completion

from agentinterface.agentmessage import AgentMessage
from agentinterface.litellmmodelalias import LiteLLMModelAlias
from agentinterface.modelresult import ModelResult


class LiteLLMModelClient:
    """Execute chat completions through LiteLLM using optional local model aliases."""

    def __init__(
        self,
        *,
        aliases: dict[str, LiteLLMModelAlias] | None = None,
        environment: Mapping[str, str] | None = None,
    ) -> None:
        """
        Create a LiteLLM-backed model client.

        Args:
            aliases: Optional alias map used to resolve local model names.
            environment: Optional environment override used for API key lookup.
        """
        self.aliases = aliases or {}
        self.environment = dict(os.environ if environment is None else environment)

    def complete(self, *, model: str, messages: list[AgentMessage]) -> ModelResult:
        """
        Execute one LiteLLM chat completion and normalize the response shape.

        Args:
            model: Provider-qualified model name or configured alias.
            messages: Ordered chat history to send to LiteLLM.

        Returns:
            Structured model result with text, model name, and finish reason.

        Raises:
            KeyError: If an alias references a missing API key environment variable.
            ValueError: If LiteLLM returns no choices.
        """
        alias = self.aliases.get(model)
        completion_kwargs: dict[str, object] = {
            "model": alias.provider_model if alias else model,
            "messages": [self._serialize_message(message=message) for message in messages],
        }
        if alias and alias.api_base is not None:
            completion_kwargs["api_base"] = alias.api_base
        if alias and alias.api_key_env is not None:
            completion_kwargs["api_key"] = self.environment[alias.api_key_env]

        response = completion(**completion_kwargs)
        if not response.choices:
            raise ValueError("LiteLLM response did not contain any choices")

        first_choice = response.choices[0]
        return ModelResult(
            output_text=self._coerce_content_text(content=first_choice.message.content),
            model_name=response.model,
            finish_reason=first_choice.finish_reason,
        )

    @staticmethod
    def _serialize_message(*, message: AgentMessage) -> dict[str, str]:
        """
        Convert one AgentMessage into the LiteLLM message dictionary shape.

        Args:
            message: Structured agent message.

        Returns:
            JSON-serializable chat message dictionary.
        """
        return {"role": message.role, "content": message.content}

    @staticmethod
    def _coerce_content_text(*, content: object) -> str:
        """
        Normalize LiteLLM choice content into a plain string.

        Args:
            content: Content field returned by the first response choice.

        Returns:
            Best-effort plain-text representation of the model output.
        """
        if isinstance(content, str):
            return content

        return str(content)
