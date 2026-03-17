#!/usr/bin/env python3
"""Telegram polling runner that routes messages through the gateway."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from gateway import GatewayRouter
from tools import TelegramTransportPlugin


@dataclass
class TelegramTransportRunner:
    """Poll Telegram updates and send rendered gateway replies back to Telegram."""

    router: GatewayRouter
    api_client: object
    plugin: TelegramTransportPlugin = TelegramTransportPlugin()
    poll_timeout_seconds: int = 30
    last_update_id: int | None = None

    def process_once(self, *, now: datetime | None = None) -> int:
        """
        Poll one batch of Telegram updates and process them through the gateway.

        Args:
            now: Optional timestamp override used for tests.

        Returns:
            Count of updates that mapped to configured endpoints and were processed.
        """
        timestamp = now or datetime.now(UTC)
        updates = self.api_client.get_updates(
            offset=None if self.last_update_id is None else self.last_update_id + 1,
            timeout_seconds=self.poll_timeout_seconds,
        )

        processed_count = 0
        for update in updates:
            update_id = int(update["update_id"])
            self.last_update_id = update_id
            inbound_message = self.plugin.parse_update(update=update)
            if inbound_message is None:
                continue

            endpoint_id = self._find_endpoint_id(binding=inbound_message.endpoint_binding)
            if endpoint_id is None:
                continue

            result = self.router.handle_message(
                endpoint_id=endpoint_id,
                text=inbound_message.text,
                user_id=inbound_message.user_id,
                timestamp=timestamp,
            )
            rendered_lines = self._render_result(result=result)
            for line in rendered_lines:
                payload = self.plugin.build_send_payload(binding=inbound_message.endpoint_binding, text=line)
                self.api_client.send_message(payload=payload)
            processed_count += 1

        return processed_count

    def _find_endpoint_id(self, *, binding: str) -> str | None:
        """
        Return the configured gateway endpoint id for one Telegram binding.

        Args:
            binding: Telegram `chat:` or `thread:` binding string.

        Returns:
            Matching endpoint id, or `None` when the binding is not configured.
        """
        for endpoint_id, config in self.router.endpoints.items():
            if config.transport == "telegram" and config.binding == binding:
                return endpoint_id

        return None

    @staticmethod
    def _render_result(*, result) -> list[str]:
        """
        Convert a gateway result into outbound Telegram text lines.

        Args:
            result: Gateway routing result.

        Returns:
            Rendered outbound lines.
        """
        if result.kind == "channel_switched":
            return [f"Switched active channel to {result.active_channel_id}"]

        if result.kind == "command_result":
            return [f"Gateway: {result.message}"]

        if result.kind == "command_error":
            return [f"Gateway error: {result.message}"]

        if result.kind == "agent_responded":
            return [f"[{result.target_channel_id}] {result.target_agent_id}: {result.output_text}"]

        return [f"[{result.target_channel_id}] routed to {result.target_agent_id}"]
