#!/usr/bin/env python3
"""Structured routing result for gateway operations."""

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class GatewayResult:
    """Result of routing one inbound gateway message."""

    kind: str
    message: str
    endpoint_id: str
    primary_channel_id: str
    active_channel_id: str
    target_channel_id: str | None = None
    target_agent_id: str | None = None
    command_name: str | None = None
    output_text: str | None = None
    correlation_id: str | None = None

    def to_dict(self) -> dict[str, str | None]:
        """Convert the result to a JSON-friendly dictionary."""
        return asdict(self)
