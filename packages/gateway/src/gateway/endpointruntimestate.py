#!/usr/bin/env python3
"""Runtime state for a configured interface endpoint."""

from dataclasses import dataclass


@dataclass
class EndpointRuntimeState:
    """Mutable runtime state for one endpoint."""

    active_channel_id: str
