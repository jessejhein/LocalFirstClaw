#!/usr/bin/env python3
"""YAML-backed config loading for LocalFirstClaw runtime objects."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from agentinterface import AgentConfig, LiteLLMModelAlias
from gateway import ChannelConfig, InterfaceEndpointConfig

from localfirstclaw.localfirstclawconfig import LocalFirstClawConfig


def load_localfirstclaw_config(*, config_root: Path | str) -> LocalFirstClawConfig:
    """
    Load persistent config from the configured LocalFirstClaw config root.

    Args:
        config_root: Directory containing the YAML config files.

    Returns:
        Parsed LocalFirstClaw configuration.

    Raises:
        FileNotFoundError: If a required config file is missing.
        ValueError: If a required document key is missing.
        yaml.YAMLError: If a YAML file cannot be parsed.
    """
    root = Path(config_root)
    agents_document = _load_yaml_document(path=root / "agents.yaml", top_level_key="agents")
    channels_document = _load_yaml_document(path=root / "channels.yaml", top_level_key="channels")
    endpoints_document = _load_yaml_document(path=root / "endpoints.yaml", top_level_key="endpoints")
    models_document = _load_yaml_document(path=root / "models.yaml", top_level_key="aliases")

    agents = {agent["agent_id"]: AgentConfig.model_validate(agent) for agent in agents_document["agents"]}
    channels = {channel["channel_id"]: ChannelConfig(**channel) for channel in channels_document["channels"]}
    endpoints = {
        endpoint["endpoint_id"]: InterfaceEndpointConfig(**endpoint) for endpoint in endpoints_document["endpoints"]
    }
    model_aliases = {
        alias: LiteLLMModelAlias(alias=alias, **settings) for alias, settings in models_document["aliases"].items()
    }
    _validate_distinct_agent_and_channel_names(agents=agents, channels=channels)

    return LocalFirstClawConfig(
        agents=agents,
        channels=channels,
        endpoints=endpoints,
        model_aliases=model_aliases,
    )


def _load_yaml_document(*, path: Path, top_level_key: str) -> dict[str, Any]:
    """
    Read one YAML document and validate that it contains the required top-level key.

    Args:
        path: YAML file path to read.
        top_level_key: Required top-level key within the document.

    Returns:
        Parsed YAML document.

    Raises:
        FileNotFoundError: If the YAML file is missing.
        ValueError: If the required key is missing.
        yaml.YAMLError: If parsing fails.
    """
    if not path.is_file():
        raise FileNotFoundError(f"missing config file: {path}")

    with path.open("r", encoding="utf-8") as file_handle:
        document = yaml.safe_load(file_handle) or {}

    if top_level_key not in document:
        raise ValueError(f"config file {path} must define top-level key '{top_level_key}'")

    return document


def _validate_distinct_agent_and_channel_names(
    *,
    agents: dict[str, AgentConfig],
    channels: dict[str, ChannelConfig],
) -> None:
    """
    Reject overlapping identifiers across the agent and channel namespaces.

    Args:
        agents: Parsed agent configs keyed by agent id.
        channels: Parsed channel configs keyed by channel id.

    Raises:
        ValueError: If any identifier appears as both an agent id and a channel id.
    """
    overlapping_names = sorted(set(agents).intersection(channels))
    if overlapping_names:
        raise ValueError(
            "agent ids and channel ids must not overlap; conflicting names: " + ", ".join(overlapping_names)
        )
