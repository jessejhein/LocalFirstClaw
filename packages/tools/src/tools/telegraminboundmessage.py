#!/usr/bin/env python3
"""Normalized inbound Telegram message model."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TelegramInboundMessage:
    """Gateway-friendly normalization of a Telegram update message."""

    endpoint_binding: str
    text: str
    user_id: str
