#!/usr/bin/env python3
"""Self-describing Telegram transport plugin."""

from __future__ import annotations

from tools.pluginconfigfield import PluginConfigField
from tools.pluginmanifest import PluginManifest
from tools.telegraminboundmessage import TelegramInboundMessage


class TelegramTransportPlugin:
    """Describe and normalize the Telegram transport for LocalFirstClaw."""

    plugin_id = "telegram"

    def describe(self) -> PluginManifest:
        """
        Return the Telegram plugin manifest.

        Returns:
            Self-description for operator and agent discovery.
        """
        return PluginManifest(
            plugin_id=self.plugin_id,
            display_name="Telegram Transport",
            summary="Telegram chat and thread transport for gateway endpoints.",
            capabilities=["transport", "self_describe", "maintenance_skill"],
            config_fields=[
                PluginConfigField(
                    field_name="bot_token_env",
                    description="Environment variable name containing the Telegram bot token.",
                    required=True,
                    default_value="TELEGRAM_BOT_TOKEN",
                ),
                PluginConfigField(
                    field_name="poll_timeout_seconds",
                    description="Long-poll timeout used when reading Telegram updates.",
                    required=False,
                    default_value="30",
                ),
            ],
        )

    def get_maintenance_skill(self) -> str:
        """
        Return the on-demand maintenance instructions for the Telegram plugin.

        Returns:
            Markdown guidance that another agent can request when it needs Telegram-specific help.
        """
        return """# Telegram Transport Plugin

## Summary

This plugin connects LocalFirstClaw to Telegram chats and Telegram message threads.

## How To Configure

- Create a bot with Telegram `@BotFather`.
- Run `/newbot` in BotFather and choose a bot name and username.
- Copy the bot token that BotFather returns.
- Set `TELEGRAM_BOT_TOKEN` in the environment.
- Create Telegram endpoint bindings that use one of:
  - `chat:<chat_id>`
  - `thread:<chat_id>:<message_thread_id>`
- Use `allow_channel_switching: true` only on endpoints where `@channel` switching should be allowed.

## How To Use

- Send one message to the bot from the Telegram chat you want to bind.
- Discover the Telegram chat or thread id from the incoming updates or transport logs.
- Add the matching binding to the LocalFirstClaw endpoint config.
- Telegram private chats normally map to `chat:<chat_id>`.
- Telegram forum topics or message threads map to `thread:<chat_id>:<message_thread_id>`.
- The plugin normalizes inbound Telegram text into gateway-friendly messages.
- The plugin can also build outbound send payloads for the Telegram Bot API.

## How To Maintain

- Confirm `TELEGRAM_BOT_TOKEN` is present before starting the transport.
- If you need to recreate the bot, repeat the BotFather steps and update the token source.
- Verify the endpoint binding matches the intended Telegram chat or thread.
- If transport behavior is unclear, query the plugin manifest and this maintenance skill.
- Do that instead of keeping Telegram setup details permanently in agent context.
"""

    def parse_update(self, *, update: dict[str, object]) -> TelegramInboundMessage | None:
        """
        Normalize a Telegram update dictionary into an inbound message if possible.

        Args:
            update: Raw Telegram update payload.

        Returns:
            Normalized inbound message, or `None` for unsupported update types.
        """
        message = update.get("message")
        if not isinstance(message, dict):
            return None

        text = message.get("text")
        chat = message.get("chat")
        sender = message.get("from")
        if not isinstance(text, str) or not isinstance(chat, dict) or not isinstance(sender, dict):
            return None

        chat_id = int(chat["id"])
        thread_id = message.get("message_thread_id")
        if thread_id is None:
            endpoint_binding = f"chat:{chat_id}"
        else:
            endpoint_binding = f"thread:{chat_id}:{int(thread_id)}"

        return TelegramInboundMessage(
            endpoint_binding=endpoint_binding,
            text=text,
            user_id=str(sender["id"]),
        )

    def build_send_payload(self, *, binding: str, text: str) -> dict[str, int | str]:
        """
        Build the Telegram Bot API payload for an outbound message.

        Args:
            binding: Endpoint binding string using `chat:` or `thread:` syntax.
            text: Outbound message text.

        Returns:
            Telegram API payload dictionary.

        Raises:
            ValueError: If the binding format is not supported.
        """
        if binding.startswith("chat:"):
            _, chat_id = binding.split(":", 1)
            return {"chat_id": int(chat_id), "text": text}

        if binding.startswith("thread:"):
            _, chat_id, thread_id = binding.split(":", 2)
            return {
                "chat_id": int(chat_id),
                "message_thread_id": int(thread_id),
                "text": text,
            }

        raise ValueError(f"unsupported telegram binding: {binding}")
