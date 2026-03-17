#!/usr/bin/env python3
"""Tests for application path defaults and persistent config loading."""

from __future__ import annotations

from pathlib import Path

from agentinterface import AgentInterface
from gateway import GatewayRouter
from journal import Journal

from localfirstclaw import (
    AppPaths,
    LocalFirstClawConfig,
    build_agent_interface,
    build_gateway_router,
    build_journal,
    load_localfirstclaw_config,
)


def test_app_paths_follow_xdg_defaults_when_environment_is_unset(tmp_path: Path) -> None:
    """The application should default to XDG-style config and data roots."""
    paths = AppPaths.from_environment(home_directory=tmp_path, environment={})

    assert paths.config_root == tmp_path / ".config" / "LocalFirstClaw"
    assert paths.data_root == tmp_path / ".local" / "share" / "LocalFirstClaw"
    assert paths.workspace_root == paths.config_root / "workspace"
    assert paths.skills_root == paths.config_root / "skills"
    assert paths.plugins_root == paths.data_root / "plugins"
    assert paths.journal_root == paths.data_root / "journal"


def test_app_paths_can_create_expected_directories(tmp_path: Path) -> None:
    """The helper should materialize the required config and data directories."""
    paths = AppPaths.from_environment(home_directory=tmp_path, environment={})

    paths.ensure_directories()

    assert paths.config_root.is_dir()
    assert paths.data_root.is_dir()
    assert paths.workspace_root.is_dir()
    assert paths.skills_root.is_dir()
    assert paths.journal_root.is_dir()
    assert paths.logs_root.is_dir()
    assert paths.plugins_root.is_dir()


def test_load_localfirstclaw_config_reads_agents_channels_endpoints_and_models(tmp_path: Path) -> None:
    """The config loader should parse the YAML files from the external config root."""
    config_root = tmp_path / "config"
    config_root.mkdir()
    (config_root / "agents.yaml").write_text(
        """
agents:
  - agent_id: coordinator
    model: kimi
    system_prompt: You are the main assistant.
  - agent_id: coder
    model: kimi
    system_prompt: You are the coding assistant.
""".strip() + "\n",
        encoding="utf-8",
    )
    (config_root / "channels.yaml").write_text(
        """
channels:
  - channel_id: main
    default_agent_id: coordinator
  - channel_id: game
    default_agent_id: coder
""".strip() + "\n",
        encoding="utf-8",
    )
    (config_root / "endpoints.yaml").write_text(
        """
endpoints:
  - endpoint_id: tui-main
    transport: tui
    binding: session:main
    primary_channel_id: main
    allow_channel_switching: true
""".strip() + "\n",
        encoding="utf-8",
    )
    (config_root / "models.yaml").write_text(
        """
aliases:
  kimi:
    provider_model: openai/kimi-k2
    api_base: https://llm.example.test/v1
    api_key_env: CHUTES_API_KEY
""".strip() + "\n",
        encoding="utf-8",
    )

    config = load_localfirstclaw_config(config_root=config_root)

    assert isinstance(config, LocalFirstClawConfig)
    assert set(config.agents.keys()) == {"coordinator", "coder"}
    assert set(config.channels.keys()) == {"main", "game"}
    assert set(config.endpoints.keys()) == {"tui-main"}
    assert config.model_aliases["kimi"].provider_model == "openai/kimi-k2"
    assert config.model_aliases["kimi"].api_key_env == "CHUTES_API_KEY"


def test_build_helpers_create_runtime_objects_from_loaded_config(tmp_path: Path) -> None:
    """Bootstrap helpers should turn persisted config into runtime components."""
    app_paths = AppPaths.from_environment(
        home_directory=tmp_path,
        environment={
            "XDG_CONFIG_HOME": str(tmp_path / "cfg"),
            "XDG_DATA_HOME": str(tmp_path / "data"),
        },
    )
    app_paths.ensure_directories()

    (app_paths.config_root / "agents.yaml").write_text(
        """
agents:
  - agent_id: coordinator
    model: kimi
    system_prompt: You are the main assistant.
""".strip() + "\n",
        encoding="utf-8",
    )
    (app_paths.config_root / "channels.yaml").write_text(
        """
channels:
  - channel_id: main
    default_agent_id: coordinator
""".strip() + "\n",
        encoding="utf-8",
    )
    (app_paths.config_root / "endpoints.yaml").write_text(
        """
endpoints:
  - endpoint_id: tui-main
    transport: tui
    binding: session:main
    primary_channel_id: main
    allow_channel_switching: true
""".strip() + "\n",
        encoding="utf-8",
    )
    (app_paths.config_root / "models.yaml").write_text(
        """
aliases:
  kimi:
    provider_model: openai/kimi-k2
    api_base: https://llm.example.test/v1
    api_key_env: CHUTES_API_KEY
""".strip() + "\n",
        encoding="utf-8",
    )

    config = load_localfirstclaw_config(config_root=app_paths.config_root)
    journal = build_journal(app_paths=app_paths)
    agent_interface = build_agent_interface(config=config, journal=journal)
    gateway_router = build_gateway_router(config=config, journal=journal, agent_executor=agent_interface)

    assert isinstance(journal, Journal)
    assert isinstance(agent_interface, AgentInterface)
    assert isinstance(gateway_router, GatewayRouter)
    assert gateway_router.get_endpoint_status(endpoint_id="tui-main").active_channel_id == "main"


def test_load_localfirstclaw_config_rejects_agent_and_channel_name_collisions(tmp_path: Path) -> None:
    """Agent ids and channel ids must stay in separate namespaces."""
    config_root = tmp_path / "config"
    config_root.mkdir()
    (config_root / "agents.yaml").write_text(
        """
agents:
  - agent_id: main
    model: kimi
    system_prompt: You are the coordinator.
""".strip() + "\n",
        encoding="utf-8",
    )
    (config_root / "channels.yaml").write_text(
        """
channels:
  - channel_id: main
    default_agent_id: main
""".strip() + "\n",
        encoding="utf-8",
    )
    (config_root / "endpoints.yaml").write_text(
        """
endpoints:
  - endpoint_id: tui-main
    transport: tui
    binding: session:main
    primary_channel_id: main
    allow_channel_switching: true
""".strip() + "\n",
        encoding="utf-8",
    )
    (config_root / "models.yaml").write_text(
        """
aliases:
  kimi:
    provider_model: openai/kimi-k2
    api_base: https://llm.example.test/v1
    api_key_env: CHUTES_API_KEY
""".strip() + "\n",
        encoding="utf-8",
    )

    try:
        load_localfirstclaw_config(config_root=config_root)
    except ValueError as error:
        assert "must not overlap" in str(error)
        assert "main" in str(error)
    else:
        raise AssertionError("expected config loader to reject overlapping agent and channel names")
