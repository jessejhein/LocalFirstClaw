#!/usr/bin/env python3
"""Interface endpoint configuration model."""

from dataclasses import dataclass


@dataclass(frozen=True)
class InterfaceEndpointConfig:
    """Persistent configuration for one transport endpoint binding."""

    endpoint_id: str
    transport: str
    binding: str
    primary_channel_id: str
    allow_channel_switching: bool = False
