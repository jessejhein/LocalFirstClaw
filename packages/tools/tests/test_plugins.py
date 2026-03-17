#!/usr/bin/env python3
"""Tests for plugin registry and Telegram transport plugin behavior."""

from __future__ import annotations

from tools import PluginRegistry, TelegramTransportPlugin


def test_registry_returns_telegram_plugin_description() -> None:
    """The registry should expose the telegram plugin manifest on demand."""
    registry = PluginRegistry(plugins=[TelegramTransportPlugin()])

    manifest = registry.describe_plugin(plugin_id="telegram")

    assert manifest.plugin_id == "telegram"
    assert manifest.display_name == "Telegram Transport"
    assert "transport" in manifest.capabilities
    assert "self_describe" in manifest.capabilities
    assert "maintenance_skill" in manifest.capabilities
    assert any(field.field_name == "bot_token_env" for field in manifest.config_fields)


def test_registry_returns_plugin_maintenance_skill_text() -> None:
    """A plugin should expose operator/agent maintenance guidance on demand."""
    registry = PluginRegistry(plugins=[TelegramTransportPlugin()])

    skill_text = registry.get_plugin_skill(plugin_id="telegram")

    assert "Telegram Transport Plugin" in skill_text
    assert "TELEGRAM_BOT_TOKEN" in skill_text
    assert "How To Configure" in skill_text
    assert "How To Maintain" in skill_text


def test_telegram_plugin_parses_plain_chat_update() -> None:
    """Telegram chat updates should normalize into a gateway-friendly inbound message."""
    plugin = TelegramTransportPlugin()

    inbound_message = plugin.parse_update(
        update={
            "update_id": 101,
            "message": {
                "message_id": 55,
                "date": 1773312000,
                "text": "hello from telegram",
                "chat": {"id": 987654, "type": "private"},
                "from": {"id": 12345},
            },
        }
    )

    assert inbound_message is not None
    assert inbound_message.endpoint_binding == "chat:987654"
    assert inbound_message.text == "hello from telegram"
    assert inbound_message.user_id == "12345"


def test_telegram_plugin_parses_thread_update() -> None:
    """Telegram thread messages should preserve both chat and thread ids in the binding."""
    plugin = TelegramTransportPlugin()

    inbound_message = plugin.parse_update(
        update={
            "update_id": 202,
            "message": {
                "message_id": 56,
                "message_thread_id": 77,
                "date": 1773312001,
                "text": "@lfc status",
                "chat": {"id": -100200300, "type": "supergroup"},
                "from": {"id": 54321},
            },
        }
    )

    assert inbound_message is not None
    assert inbound_message.endpoint_binding == "thread:-100200300:77"
    assert inbound_message.text == "@lfc status"
    assert inbound_message.user_id == "54321"


def test_telegram_plugin_builds_send_payload_for_chat_binding() -> None:
    """Outbound chat sends should target the configured chat id only."""
    plugin = TelegramTransportPlugin()

    payload = plugin.build_send_payload(binding="chat:987654", text="hello back")

    assert payload == {"chat_id": 987654, "text": "hello back"}


def test_telegram_plugin_builds_send_payload_for_thread_binding() -> None:
    """Outbound thread sends should include the Telegram message thread id."""
    plugin = TelegramTransportPlugin()

    payload = plugin.build_send_payload(binding="thread:-100200300:77", text="thread reply")

    assert payload == {
        "chat_id": -100200300,
        "message_thread_id": 77,
        "text": "thread reply",
    }
