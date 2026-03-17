#!/usr/bin/env python3
"""Tests for the gateway routing core and FastAPI surface."""

from datetime import UTC, datetime
from pathlib import Path

from agentinterface import AgentConfig, AgentInterface, AgentMessage, AgentResponse
from gateway import (
    ChannelConfig,
    GatewayAppDependencies,
    GatewayRouter,
    InterfaceEndpointConfig,
    MessageInput,
    create_app,
)
from journal import Journal, JournalLevel, JournalQuery


class FakeAgentExecutor:
    """Simple fake executor used to test gateway-to-agent integration."""

    def __init__(self) -> None:
        """Initialize call capture and canned response state."""
        self.calls: list[object] = []

    def run(self, *, request) -> AgentResponse:
        """Capture the request and return a fixed agent response."""
        self.calls.append(request)
        return AgentResponse(
            agent_id=request.agent_id,
            channel_id=request.channel_id,
            correlation_id=request.correlation_id or "generated",
            output_text="Coder response",
            model_name="fake-model",
            finish_reason="stop",
        )


def build_router(tmp_path: Path, agent_executor: object | None = None) -> tuple[GatewayRouter, Journal]:
    """Create a gateway router with a small in-memory configuration."""
    journal = Journal(root_directory=tmp_path / "journal")
    router = GatewayRouter(
        channels={
            "main": ChannelConfig(channel_id="main", default_agent_id="main"),
            "game": ChannelConfig(channel_id="game", default_agent_id="coder"),
            "gateway": ChannelConfig(channel_id="gateway", default_agent_id="gateway"),
        },
        endpoints={
            "telegram-main": InterfaceEndpointConfig(
                endpoint_id="telegram-main",
                transport="telegram",
                binding="chat:main",
                primary_channel_id="main",
                allow_channel_switching=True,
            ),
            "telegram-game": InterfaceEndpointConfig(
                endpoint_id="telegram-game",
                transport="telegram",
                binding="thread:game",
                primary_channel_id="game",
                allow_channel_switching=False,
            ),
        },
        journal=journal,
        agent_executor=agent_executor,
    )
    return router, journal


def test_endpoint_defaults_to_primary_channel(tmp_path: Path) -> None:
    """Endpoints begin on their configured primary channel."""
    router, _ = build_router(tmp_path=tmp_path)

    status = router.get_endpoint_status(endpoint_id="telegram-main")

    assert status.primary_channel_id == "main"
    assert status.active_channel_id == "main"
    assert status.default_agent_id == "main"


def test_bare_channel_switch_changes_endpoint_active_channel(tmp_path: Path) -> None:
    """A bare @channel message updates active routing for eligible endpoints."""
    router, _ = build_router(tmp_path=tmp_path)

    response = router.handle_message(
        endpoint_id="telegram-main",
        text="@game",
        user_id="user-1",
        timestamp=datetime(2026, 3, 17, 12, 0, tzinfo=UTC),
    )

    assert response.kind == "channel_switched"
    assert response.active_channel_id == "game"
    assert router.get_endpoint_status(endpoint_id="telegram-main").active_channel_id == "game"


def test_plain_messages_route_to_active_channel(tmp_path: Path) -> None:
    """After switching, plain text routes to the new active channel."""
    router, _ = build_router(tmp_path=tmp_path)
    router.handle_message(
        endpoint_id="telegram-main",
        text="@game",
        user_id="user-1",
        timestamp=datetime(2026, 3, 17, 12, 0, tzinfo=UTC),
    )

    response = router.handle_message(
        endpoint_id="telegram-main",
        text="How is the build going?",
        user_id="user-1",
        timestamp=datetime(2026, 3, 17, 12, 1, tzinfo=UTC),
    )

    assert response.kind == "message_routed"
    assert response.target_channel_id == "game"
    assert response.target_agent_id == "coder"
    assert router.get_endpoint_status(endpoint_id="telegram-main").active_channel_id == "game"


def test_plain_messages_invoke_agent_executor_when_available(tmp_path: Path) -> None:
    """Plain routed messages call the agent executor and return the reply."""
    fake_executor = FakeAgentExecutor()
    router, journal = build_router(tmp_path=tmp_path, agent_executor=fake_executor)
    timestamp = datetime(2026, 3, 17, 12, 1, tzinfo=UTC)

    response = router.handle_message(
        endpoint_id="telegram-main",
        text="How is the build going?",
        user_id="user-1",
        timestamp=timestamp,
    )

    assert response.kind == "agent_responded"
    assert response.target_channel_id == "main"
    assert response.target_agent_id == "main"
    assert response.output_text == "Coder response"
    assert len(fake_executor.calls) == 1
    sent_request = fake_executor.calls[0]
    assert sent_request.agent_id == "main"
    assert sent_request.channel_id == "main"
    assert sent_request.endpoint_id == "telegram-main"
    assert sent_request.messages == [AgentMessage(role="user", content="How is the build going?")]

    events = journal.query_recent(
        query=JournalQuery(
            since=timestamp,
            until=timestamp,
            levels=[JournalLevel.INFO],
            tags=["gateway"],
        )
    )
    assert "gateway.agent_responded" in {event.event_type for event in events}


def test_reset_channel_restores_primary_channel(tmp_path: Path) -> None:
    """Gateway reset returns the endpoint to its primary channel."""
    router, _ = build_router(tmp_path=tmp_path)
    router.handle_message(
        endpoint_id="telegram-main",
        text="@game",
        user_id="user-1",
        timestamp=datetime(2026, 3, 17, 12, 0, tzinfo=UTC),
    )

    response = router.handle_message(
        endpoint_id="telegram-main",
        text="!reset-channel",
        user_id="user-1",
        timestamp=datetime(2026, 3, 17, 12, 2, tzinfo=UTC),
    )

    assert response.kind == "command_result"
    assert response.active_channel_id == "main"
    assert router.get_endpoint_status(endpoint_id="telegram-main").active_channel_id == "main"


def test_send_command_routes_one_message_without_changing_state(tmp_path: Path) -> None:
    """A one-off send does not alter endpoint active routing."""
    router, _ = build_router(tmp_path=tmp_path)

    response = router.handle_message(
        endpoint_id="telegram-main",
        text="!send @game quick update",
        user_id="user-1",
        timestamp=datetime(2026, 3, 17, 12, 3, tzinfo=UTC),
    )

    assert response.kind == "message_routed"
    assert response.target_channel_id == "game"
    assert response.target_agent_id == "coder"
    assert router.get_endpoint_status(endpoint_id="telegram-main").active_channel_id == "main"


def test_who_command_reports_endpoint_state(tmp_path: Path) -> None:
    """Gateway can report current endpoint routing state without an agent."""
    router, _ = build_router(tmp_path=tmp_path)
    router.handle_message(
        endpoint_id="telegram-main",
        text="@game",
        user_id="user-1",
        timestamp=datetime(2026, 3, 17, 12, 0, tzinfo=UTC),
    )

    response = router.handle_message(
        endpoint_id="telegram-main",
        text="!who",
        user_id="user-1",
        timestamp=datetime(2026, 3, 17, 12, 4, tzinfo=UTC),
    )

    assert response.kind == "command_result"
    assert response.active_channel_id == "game"
    assert response.primary_channel_id == "main"
    assert response.target_agent_id == "coder"


def test_switching_is_rejected_for_endpoints_that_disallow_it(tmp_path: Path) -> None:
    """Endpoints without switching enabled reject bare @channel rerouting."""
    router, _ = build_router(tmp_path=tmp_path)

    response = router.handle_message(
        endpoint_id="telegram-game",
        text="@main",
        user_id="user-1",
        timestamp=datetime(2026, 3, 17, 12, 5, tzinfo=UTC),
    )

    assert response.kind == "command_error"
    assert "switch" in response.message.lower()
    assert router.get_endpoint_status(endpoint_id="telegram-game").active_channel_id == "game"


def test_gateway_actions_emit_journal_events(tmp_path: Path) -> None:
    """Routing and commands produce structured journal events."""
    router, journal = build_router(tmp_path=tmp_path)
    timestamp = datetime(2026, 3, 17, 12, 6, tzinfo=UTC)

    router.handle_message(
        endpoint_id="telegram-main",
        text="@game",
        user_id="user-1",
        timestamp=timestamp,
    )
    router.handle_message(
        endpoint_id="telegram-main",
        text="!who",
        user_id="user-1",
        timestamp=timestamp,
    )
    router.handle_message(
        endpoint_id="telegram-main",
        text="status report",
        user_id="user-1",
        timestamp=timestamp,
    )

    events = journal.query_recent(
        query=JournalQuery(
            since=timestamp,
            until=timestamp,
            levels=[JournalLevel.INFO],
            tags=["gateway"],
        )
    )

    event_types = {event.event_type for event in events}
    assert "gateway.channel_switched" in event_types
    assert "gateway.command_executed" in event_types
    assert "gateway.message_routed" in event_types


def test_fastapi_surface_routes_messages_and_exposes_state(tmp_path: Path) -> None:
    """The minimal API route handlers delegate to the routing core."""
    router, _ = build_router(tmp_path=tmp_path)
    app = create_app(dependencies=GatewayAppDependencies(router=router))
    post_route = next(route for route in app.routes if getattr(route, "path", None) == "/messages")
    get_route = next(route for route in app.routes if getattr(route, "path", None) == "/endpoints/{endpoint_id}")

    switch_response = post_route.endpoint(
        MessageInput(
            endpoint_id="telegram-main",
            user_id="user-1",
            text="@game",
            timestamp=datetime(2026, 3, 17, 12, 7, tzinfo=UTC),
        )
    )
    state_response = get_route.endpoint("telegram-main")

    assert switch_response["active_channel_id"] == "game"
    assert state_response["active_channel_id"] == "game"
