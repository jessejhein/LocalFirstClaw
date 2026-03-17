#!/usr/bin/env python3
"""Tests for the agentinterface package public behavior."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest
from journal import Journal, JournalLevel, JournalQuery

from agentinterface import (
    AgentConfig,
    AgentInterface,
    AgentMessage,
    AgentRequest,
    AgentRunError,
    ModelResult,
)


class FakeModelClient:
    """Simple fake client used to capture model invocations."""

    def __init__(self, result: ModelResult):
        """Store the result returned by each call."""
        self.result = result
        self.calls: list[dict[str, object]] = []

    def complete(self, *, model: str, messages: list[AgentMessage]) -> ModelResult:
        """Capture the call and return the configured result."""
        self.calls.append({"model": model, "messages": messages})
        return self.result


class FailingModelClient:
    """Fake client that raises a provider-style failure."""

    def complete(self, *, model: str, messages: list[AgentMessage]) -> ModelResult:
        """Raise a deterministic failure for testing."""
        del model, messages
        raise RuntimeError("provider unavailable")


def build_agentinterface(tmp_path: Path, model_client: object) -> tuple[AgentInterface, Journal]:
    """Create an agent interface with one configured agent."""
    journal = Journal(root_directory=tmp_path / "journal")
    interface = AgentInterface(
        agents={
            "coder": AgentConfig(
                agent_id="coder",
                model="openai/gpt-4o-mini",
                system_prompt="You are the coding agent.",
            )
        },
        model_client=model_client,
        journal=journal,
    )
    return interface, journal


def test_run_prepends_system_prompt_and_returns_structured_response(tmp_path: Path) -> None:
    """AgentInterface builds the final message list and returns a typed result."""
    fake_client = FakeModelClient(
        result=ModelResult(
            output_text="I fixed the issue.",
            model_name="openai/gpt-4o-mini",
            finish_reason="stop",
        )
    )
    interface, _ = build_agentinterface(tmp_path=tmp_path, model_client=fake_client)

    response = interface.run(
        request=AgentRequest(
            agent_id="coder",
            channel_id="game",
            user_id="user-1",
            messages=[AgentMessage(role="user", content="Please fix the build.")],
            timestamp=datetime(2026, 3, 17, 18, 0, tzinfo=UTC),
        )
    )

    assert response.agent_id == "coder"
    assert response.channel_id == "game"
    assert response.output_text == "I fixed the issue."
    assert response.model_name == "openai/gpt-4o-mini"
    assert response.correlation_id
    assert fake_client.calls[0]["model"] == "openai/gpt-4o-mini"
    sent_messages = fake_client.calls[0]["messages"]
    assert isinstance(sent_messages, list)
    assert sent_messages[0].role == "system"
    assert sent_messages[0].content == "You are the coding agent."
    assert sent_messages[1].role == "user"


def test_run_journals_start_and_completion_events(tmp_path: Path) -> None:
    """Successful runs create matching journal events with the same correlation id."""
    fake_client = FakeModelClient(
        result=ModelResult(
            output_text="Done.",
            model_name="openai/gpt-4o-mini",
            finish_reason="stop",
        )
    )
    interface, journal = build_agentinterface(tmp_path=tmp_path, model_client=fake_client)
    timestamp = datetime(2026, 3, 17, 18, 1, tzinfo=UTC)

    response = interface.run(
        request=AgentRequest(
            agent_id="coder",
            channel_id="game",
            user_id="user-1",
            messages=[AgentMessage(role="user", content="Status?")],
            timestamp=timestamp,
        )
    )

    events = journal.query_recent(
        query=JournalQuery(
            since=timestamp,
            until=timestamp,
            levels=[JournalLevel.INFO],
            tags=["agentinterface"],
        )
    )

    event_types = {event.event_type for event in events}
    correlation_ids = {event.correlation_id for event in events}
    assert "agentinterface.run_started" in event_types
    assert "agentinterface.run_completed" in event_types
    assert correlation_ids == {response.correlation_id}


def test_run_raises_agentrunerror_and_journals_failure(tmp_path: Path) -> None:
    """Model failures are journaled and surfaced as AgentRunError."""
    interface, journal = build_agentinterface(tmp_path=tmp_path, model_client=FailingModelClient())
    timestamp = datetime(2026, 3, 17, 18, 2, tzinfo=UTC)

    with pytest.raises(AgentRunError, match="provider unavailable"):
        interface.run(
            request=AgentRequest(
                agent_id="coder",
                channel_id="game",
                user_id="user-1",
                messages=[AgentMessage(role="user", content="Try again.")],
                timestamp=timestamp,
            )
        )

    events = journal.query_recent(
        query=JournalQuery(
            since=timestamp,
            until=timestamp,
            tags=["agentinterface"],
        )
    )

    assert {event.event_type for event in events} >= {
        "agentinterface.run_started",
        "agentinterface.run_failed",
    }


@pytest.mark.asyncio
async def test_run_async_returns_same_shape_as_sync(tmp_path: Path) -> None:
    """Async wrapper delegates to the same execution path and result type."""
    fake_client = FakeModelClient(
        result=ModelResult(
            output_text="Async is fine.",
            model_name="openai/gpt-4o-mini",
            finish_reason="stop",
        )
    )
    interface, _ = build_agentinterface(tmp_path=tmp_path, model_client=fake_client)

    response = await interface.run_async(
        request=AgentRequest(
            agent_id="coder",
            channel_id="game",
            user_id="user-1",
            messages=[AgentMessage(role="user", content="Respond asynchronously.")],
            timestamp=datetime(2026, 3, 17, 18, 3, tzinfo=UTC),
        )
    )

    assert response.agent_id == "coder"
    assert response.output_text == "Async is fine."
