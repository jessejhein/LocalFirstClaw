#!/usr/bin/env python3
"""Simple local terminal session wrapper over the gateway router."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from gateway import GatewayRouter


@dataclass
class TuiSession:
    """Line-oriented terminal session bound to one gateway endpoint."""

    router: GatewayRouter
    endpoint_id: str
    user_id: str

    def handle_input(self, *, text: str, timestamp: datetime) -> list[str]:
        """
        Route one line of terminal input and return rendered output lines.

        Args:
            text: Raw user input from the terminal.
            timestamp: Time the input entered the session.

        Returns:
            Rendered output lines ready for display in the terminal UI.
        """
        result = self.router.handle_message(
            endpoint_id=self.endpoint_id,
            text=text,
            user_id=self.user_id,
            timestamp=timestamp,
        )

        if result.kind == "channel_switched":
            return [f"Switched active channel to {result.active_channel_id}"]

        if result.kind == "command_result":
            return [f"Gateway: {result.message}"]

        if result.kind == "command_error":
            return [f"Gateway error: {result.message}"]

        if result.kind == "agent_responded":
            return [f"[{result.target_channel_id}] {result.target_agent_id}: {result.output_text}"]

        return [f"[{result.target_channel_id}] routed to {result.target_agent_id}"]
