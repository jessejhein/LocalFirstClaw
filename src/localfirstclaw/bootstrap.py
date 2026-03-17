#!/usr/bin/env python3
"""Bootstrap helpers that turn persistent config into runtime objects."""

from __future__ import annotations

from typing import Mapping

from agentinterface import AgentInterface, LiteLLMModelClient
from gateway import GatewayRouter
from journal import Journal

from localfirstclaw.apppaths import AppPaths
from localfirstclaw.localfirstclawconfig import LocalFirstClawConfig


def build_journal(*, app_paths: AppPaths) -> Journal:
    """
    Create a journal rooted in the configured external data directory.

    Args:
        app_paths: Resolved application path set.

    Returns:
        Journal configured to write under the app data root.
    """
    app_paths.ensure_directories()
    return Journal(root_directory=app_paths.journal_root)


def build_agent_interface(
    *,
    config: LocalFirstClawConfig,
    journal: Journal,
    environment: Mapping[str, str] | None = None,
) -> AgentInterface:
    """
    Create the agent execution facade using persisted agent and model config.

    Args:
        config: Loaded persistent LocalFirstClaw config.
        journal: Journal used for agent lifecycle events.
        environment: Optional environment override used for API key lookup.

    Returns:
        Configured agent interface.
    """
    return AgentInterface(
        agents=config.agents,
        model_client=LiteLLMModelClient(aliases=config.model_aliases, environment=environment),
        journal=journal,
    )


def build_gateway_router(
    *,
    config: LocalFirstClawConfig,
    journal: Journal,
    agent_executor: object | None = None,
) -> GatewayRouter:
    """
    Create the gateway router from persisted channel and endpoint config.

    Args:
        config: Loaded persistent LocalFirstClaw config.
        journal: Journal used for gateway events.
        agent_executor: Optional agent execution backend for routed messages.

    Returns:
        Configured gateway router.
    """
    return GatewayRouter(
        channels=config.channels,
        endpoints=config.endpoints,
        journal=journal,
        agent_executor=agent_executor,
    )
