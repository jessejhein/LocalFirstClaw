#!/usr/bin/env python3
"""HTTP client for the Telegram Bot API."""

from __future__ import annotations

from dataclasses import dataclass

import httpx


@dataclass
class HttpTelegramApiClient:
    """Simple synchronous Telegram Bot API client."""

    bot_token: str
    base_url: str = "https://api.telegram.org"

    def get_updates(self, *, offset: int | None, timeout_seconds: int) -> list[dict[str, object]]:
        """
        Fetch Telegram updates using long polling.

        Args:
            offset: Optional Telegram update offset.
            timeout_seconds: Long-poll timeout value.

        Returns:
            List of Telegram update dictionaries.
        """
        payload: dict[str, int] = {"timeout": timeout_seconds}
        if offset is not None:
            payload["offset"] = offset

        response = httpx.post(
            f"{self.base_url}/bot{self.bot_token}/getUpdates",
            json=payload,
            timeout=timeout_seconds + 10,
        )
        response.raise_for_status()
        document = response.json()
        return list(document.get("result", []))

    def send_message(self, *, payload: dict[str, object]) -> dict[str, object]:
        """
        Send one outbound Telegram message.

        Args:
            payload: Telegram `sendMessage` payload.

        Returns:
            Telegram API response document.
        """
        response = httpx.post(
            f"{self.base_url}/bot{self.bot_token}/sendMessage",
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        return dict(response.json())
