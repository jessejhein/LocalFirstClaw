#!/usr/bin/env python3
"""Typed persistent configuration models for LocalFirstClaw bootstrapping."""

from __future__ import annotations

from dataclasses import dataclass

from agentinterface import AgentConfig, LiteLLMModelAlias
from gateway import ChannelConfig, InterfaceEndpointConfig


@dataclass(frozen=True)
class LocalFirstClawConfig:
    """Loaded persistent config for agents, channels, endpoints, and model aliases."""

    agents: dict[str, AgentConfig]
    channels: dict[str, ChannelConfig]
    endpoints: dict[str, InterfaceEndpointConfig]
    model_aliases: dict[str, LiteLLMModelAlias]
