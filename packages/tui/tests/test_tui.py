#!/usr/bin/env python3
"""Tests for the local terminal interface package."""

from datetime import UTC, datetime
from pathlib import Path

from agentinterface import AgentResponse
from gateway import (
    ChannelConfig,
    GatewayRouter,
    InterfaceEndpointConfig,
)
from journal import Journal
from tui import TuiSession


class FakeAgentExecutor:
    """Simple fake executor that returns canned output."""

    def run(self, *, request) -> AgentResponse:
        """Return a response that echoes the target agent and text."""
        return AgentResponse(
            agent_id=request.agent_id,
            channel_id=request.channel_id,
            correlation_id=request.correlation_id or "generated",
            output_text=f"reply to {request.messages[-1].content}",
            model_name="fake-model",
            finish_reason="stop",
        )


def build_session(tmp_path: Path) -> TuiSession:
    """Create a TUI session bound to a gateway router."""
    journal = Journal(root_directory=tmp_path / "journal")
    router = GatewayRouter(
        channels={
            "main": ChannelConfig(channel_id="main", default_agent_id="main"),
            "game": ChannelConfig(channel_id="game", default_agent_id="coder"),
        },
        endpoints={
            "tui-main": InterfaceEndpointConfig(
                endpoint_id="tui-main",
                transport="tui",
                binding="session:main",
                primary_channel_id="main",
                allow_channel_switching=True,
            )
        },
        journal=journal,
        agent_executor=FakeAgentExecutor(),
    )
    return TuiSession(router=router, endpoint_id="tui-main", user_id="local-user")


def test_tui_formats_agent_reply_for_plain_message(tmp_path: Path) -> None:
    """A plain message is rendered as an agent reply line."""
    session = build_session(tmp_path=tmp_path)

    lines = session.handle_input(
        text="hello there",
        timestamp=datetime(2026, 3, 17, 19, 0, tzinfo=UTC),
    )

    assert lines == ["[main] main: reply to hello there"]


def test_tui_formats_channel_switch_and_follow_up_reply(tmp_path: Path) -> None:
    """The TUI shows channel switching and then renders replies in that channel."""
    session = build_session(tmp_path=tmp_path)

    switch_lines = session.handle_input(
        text="@game",
        timestamp=datetime(2026, 3, 17, 19, 1, tzinfo=UTC),
    )
    reply_lines = session.handle_input(
        text="status update",
        timestamp=datetime(2026, 3, 17, 19, 2, tzinfo=UTC),
    )

    assert switch_lines == ["Switched active channel to game"]
    assert reply_lines == ["[game] coder: reply to status update"]


def test_tui_formats_gateway_command_output(tmp_path: Path) -> None:
    """Gateway-owned command responses are rendered without an agent prefix."""
    session = build_session(tmp_path=tmp_path)

    lines = session.handle_input(
        text="!who",
        timestamp=datetime(2026, 3, 17, 19, 3, tzinfo=UTC),
    )

    assert lines == ["Gateway: Endpoint routing status returned"]
