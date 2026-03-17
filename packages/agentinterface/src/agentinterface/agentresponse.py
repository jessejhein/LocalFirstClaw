#!/usr/bin/env python3
"""Response model for completed agent execution."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AgentResponse:
    """Completed response from one agent run."""

    agent_id: str
    channel_id: str
    correlation_id: str
    output_text: str
    model_name: str
    finish_reason: str | None = None
