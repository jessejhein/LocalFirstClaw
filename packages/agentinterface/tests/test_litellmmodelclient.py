#!/usr/bin/env python3
"""Tests for the LiteLLM-backed model client."""

from __future__ import annotations

from agentinterface import AgentMessage, LiteLLMModelAlias, LiteLLMModelClient


class FakeChoiceMessage:
    """Minimal fake choice message returned by LiteLLM."""

    def __init__(self, content: str) -> None:
        """Store the completion text."""
        self.content = content


class FakeChoice:
    """Minimal fake response choice."""

    def __init__(self, content: str, finish_reason: str) -> None:
        """Store the fake message and finish reason."""
        self.message = FakeChoiceMessage(content=content)
        self.finish_reason = finish_reason


class FakeResponse:
    """Minimal fake LiteLLM response."""

    def __init__(self) -> None:
        """Populate the canned first choice."""
        self.choices = [FakeChoice(content="Configured response", finish_reason="stop")]
        self.model = "openai/kimi-k2"


def test_litellm_model_client_resolves_alias_and_calls_completion(monkeypatch) -> None:
    """The client should translate alias settings into a LiteLLM completion call."""
    captured: dict[str, object] = {}

    def fake_completion(**kwargs):
        """Capture the request and return a fake response."""
        captured.update(kwargs)
        return FakeResponse()

    monkeypatch.setattr("agentinterface.litellmmodelclient.completion", fake_completion)
    client = LiteLLMModelClient(
        aliases={
            "kimi": LiteLLMModelAlias(
                alias="kimi",
                provider_model="openai/kimi-k2",
                api_base="https://llm.example.test/v1",
                api_key_env="CHUTES_API_KEY",
            )
        },
        environment={"CHUTES_API_KEY": "secret-token"},
    )

    result = client.complete(
        model="kimi",
        messages=[AgentMessage(role="user", content="Give me a status update.")],
    )

    assert captured["model"] == "openai/kimi-k2"
    assert captured["api_base"] == "https://llm.example.test/v1"
    assert captured["api_key"] == "secret-token"
    assert captured["messages"] == [{"role": "user", "content": "Give me a status update."}]
    assert result.output_text == "Configured response"
    assert result.model_name == "openai/kimi-k2"
    assert result.finish_reason == "stop"
