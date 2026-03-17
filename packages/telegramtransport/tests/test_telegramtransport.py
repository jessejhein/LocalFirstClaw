#!/usr/bin/env python3
"""Tests for the Telegram transport runner."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from agentinterface import AgentResponse
from gateway import ChannelConfig, GatewayRouter, InterfaceEndpointConfig
from journal import Journal
from telegramtransport import TelegramTransportRunner


class FakeAgentExecutor:
    """Fake gateway agent executor used to produce deterministic replies."""

    def run(self, *, request) -> AgentResponse:
        """Return a fixed response matching the target agent and channel."""
        return AgentResponse(
            agent_id=request.agent_id,
            channel_id=request.channel_id,
            correlation_id=request.correlation_id or "generated",
            output_text="Telegram reply",
            model_name="fake-model",
            finish_reason="stop",
        )


class FakeTelegramApiClient:
    """Fake Telegram API client used to capture polling and send behavior."""

    def __init__(self, updates: list[dict[str, object]]) -> None:
        """Store canned updates and capture send calls."""
        self.updates = updates
        self.sent_messages: list[dict[str, object]] = []
        self.requested_offsets: list[int | None] = []

    def get_updates(self, *, offset: int | None, timeout_seconds: int) -> list[dict[str, object]]:
        """Return the canned updates and capture the offset used."""
        del timeout_seconds
        self.requested_offsets.append(offset)
        updates, self.updates = self.updates, []
        return updates

    def send_message(self, *, payload: dict[str, object]) -> dict[str, object]:
        """Capture one outbound Telegram send payload."""
        self.sent_messages.append(payload)
        return {"ok": True, "result": {"message_id": len(self.sent_messages)}}


def build_router(tmp_path: Path) -> GatewayRouter:
    """Create a gateway router with Telegram endpoints and a fake agent executor."""
    journal = Journal(root_directory=tmp_path / "journal")
    return GatewayRouter(
        channels={
            "main": ChannelConfig(channel_id="main", default_agent_id="coordinator"),
            "lfc": ChannelConfig(channel_id="lfc", default_agent_id="coder-relay"),
        },
        endpoints={
            "telegram-main": InterfaceEndpointConfig(
                endpoint_id="telegram-main",
                transport="telegram",
                binding="chat:987654",
                primary_channel_id="main",
                allow_channel_switching=True,
            ),
            "telegram-lfc": InterfaceEndpointConfig(
                endpoint_id="telegram-lfc",
                transport="telegram",
                binding="thread:-100200300:77",
                primary_channel_id="lfc",
                allow_channel_switching=False,
            ),
        },
        journal=journal,
        agent_executor=FakeAgentExecutor(),
    )


def test_runner_routes_private_chat_message_and_sends_agent_reply(tmp_path: Path) -> None:
    """A Telegram private chat update should route through the gateway and send the rendered reply."""
    client = FakeTelegramApiClient(
        updates=[
            {
                "update_id": 101,
                "message": {
                    "message_id": 55,
                    "date": 1773312000,
                    "text": "hello from telegram",
                    "chat": {"id": 987654, "type": "private"},
                    "from": {"id": 12345},
                },
            }
        ]
    )
    runner = TelegramTransportRunner(router=build_router(tmp_path), api_client=client)

    processed_count = runner.process_once(now=datetime(2026, 3, 17, 18, 0, tzinfo=UTC))

    assert processed_count == 1
    assert client.requested_offsets == [None]
    assert client.sent_messages == [{"chat_id": 987654, "text": "[main] coordinator: Telegram reply"}]
    assert runner.last_update_id == 101


def test_runner_renders_gateway_command_result_back_to_telegram(tmp_path: Path) -> None:
    """Gateway-owned command results should be sent back to the same Telegram binding."""
    client = FakeTelegramApiClient(
        updates=[
            {
                "update_id": 102,
                "message": {
                    "message_id": 56,
                    "date": 1773312001,
                    "text": "!who",
                    "chat": {"id": 987654, "type": "private"},
                    "from": {"id": 12345},
                },
            }
        ]
    )
    runner = TelegramTransportRunner(router=build_router(tmp_path), api_client=client)

    processed_count = runner.process_once(now=datetime(2026, 3, 17, 18, 1, tzinfo=UTC))

    assert processed_count == 1
    assert client.sent_messages == [{"chat_id": 987654, "text": "Gateway: Endpoint routing status returned"}]


def test_runner_sends_to_telegram_thread_binding(tmp_path: Path) -> None:
    """Thread-bound Telegram endpoints should send replies with the message_thread_id."""
    client = FakeTelegramApiClient(
        updates=[
            {
                "update_id": 103,
                "message": {
                    "message_id": 57,
                    "message_thread_id": 77,
                    "date": 1773312002,
                    "text": "thread message",
                    "chat": {"id": -100200300, "type": "supergroup"},
                    "from": {"id": 54321},
                },
            }
        ]
    )
    runner = TelegramTransportRunner(router=build_router(tmp_path), api_client=client)

    processed_count = runner.process_once(now=datetime(2026, 3, 17, 18, 2, tzinfo=UTC))

    assert processed_count == 1
    assert client.sent_messages == [
        {
            "chat_id": -100200300,
            "message_thread_id": 77,
            "text": "[lfc] coder-relay: Telegram reply",
        }
    ]


def test_runner_ignores_unbound_telegram_updates(tmp_path: Path) -> None:
    """Telegram updates without a matching configured binding should be ignored for now."""
    client = FakeTelegramApiClient(
        updates=[
            {
                "update_id": 104,
                "message": {
                    "message_id": 58,
                    "date": 1773312003,
                    "text": "who am i",
                    "chat": {"id": 999999, "type": "private"},
                    "from": {"id": 999},
                },
            }
        ]
    )
    runner = TelegramTransportRunner(router=build_router(tmp_path), api_client=client)

    processed_count = runner.process_once(now=datetime(2026, 3, 17, 18, 3, tzinfo=UTC))

    assert processed_count == 0
    assert client.sent_messages == []
    assert runner.last_update_id == 104
