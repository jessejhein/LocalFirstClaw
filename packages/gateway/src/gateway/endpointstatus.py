#!/usr/bin/env python3
"""Current status view for a gateway endpoint."""

from dataclasses import dataclass


@dataclass(frozen=True)
class EndpointStatus:
    """Derived status view for one endpoint."""

    endpoint_id: str
    transport: str
    binding: str
    primary_channel_id: str
    active_channel_id: str
    default_agent_id: str
    allow_channel_switching: bool
