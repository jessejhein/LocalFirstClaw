#!/usr/bin/env python3
"""Channel configuration model."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ChannelConfig:
    """Persistent configuration for an internal gateway channel."""

    channel_id: str
    default_agent_id: str
