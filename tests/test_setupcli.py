#!/usr/bin/env python3
"""Tests for setup validation and provider connectivity commands."""

from __future__ import annotations

import json
from pathlib import Path

from localfirstclaw import AppPaths
from localfirstclaw.cli import main
from localfirstclaw.providercheck import check_chutes_connectivity
from localfirstclaw.setupvalidation import validate_setup


class FakeHttpResponse:
    """Minimal context-manager response used to fake urllib calls."""

    def __init__(self, payload: dict[str, object]) -> None:
        """Store the JSON payload returned by the fake response."""
        self.payload = payload

    def __enter__(self) -> "FakeHttpResponse":
        """Return the fake response context."""
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        """Suppress no exceptions while leaving the context manager."""
        del exc_type, exc, traceback
        return None

    def read(self) -> bytes:
        """Return the encoded JSON response body."""
        return json.dumps(self.payload).encode("utf-8")


def write_role_based_config(config_root: Path) -> None:
    """Create a representative role-based LocalFirstClaw config tree."""
    config_root.mkdir(parents=True, exist_ok=True)
    (config_root / "agents.yaml").write_text(
        """
agents:
  - agent_id: coordinator
    model: premium
    system_prompt: You are the main coordinator.
  - agent_id: coder-relay
    model: relay
    system_prompt: You relay coding updates.
  - agent_id: heartbeat
    model: cheap
    system_prompt: You handle brief heartbeat tasks.
""".strip() + "\n",
        encoding="utf-8",
    )
    (config_root / "channels.yaml").write_text(
        """
channels:
  - channel_id: main
    default_agent_id: coordinator
  - channel_id: lfc
    default_agent_id: coder-relay
  - channel_id: ops
    default_agent_id: heartbeat
""".strip() + "\n",
        encoding="utf-8",
    )
    (config_root / "endpoints.yaml").write_text(
        """
endpoints:
  - endpoint_id: telegram-main
    transport: telegram
    binding: chat:main
    primary_channel_id: main
    allow_channel_switching: true
""".strip() + "\n",
        encoding="utf-8",
    )
    (config_root / "models.yaml").write_text(
        """
aliases:
  premium:
    provider_model: openai/moonshotai/Kimi-K2.5-TEE
    api_base: https://llm.chutes.ai/v1
    api_key_env: CHUTES_API_KEY
  relay:
    provider_model: openai/Qwen/Qwen3-30B-A3B
    api_base: https://llm.chutes.ai/v1
    api_key_env: CHUTES_API_KEY
  cheap:
    provider_model: openai/openai/gpt-oss-20b
    api_base: https://llm.chutes.ai/v1
    api_key_env: CHUTES_API_KEY
""".strip() + "\n",
        encoding="utf-8",
    )


def write_env_file(config_root: Path, content: str) -> None:
    """Write a LocalFirstClaw .env file under the config root."""
    (config_root / ".env").write_text(content.strip() + "\n", encoding="utf-8")


def test_validate_setup_succeeds_with_role_based_config(tmp_path: Path) -> None:
    """Setup validation should pass when config and required env vars exist."""
    app_paths = AppPaths.from_environment(
        home_directory=tmp_path,
        environment={
            "XDG_CONFIG_HOME": str(tmp_path / "cfg"),
            "XDG_DATA_HOME": str(tmp_path / "data"),
            "CHUTES_API_KEY": "test-key",
        },
    )
    app_paths.ensure_directories()
    write_role_based_config(config_root=app_paths.config_root)

    result = validate_setup(app_paths=app_paths, environment={"CHUTES_API_KEY": "test-key"})

    assert result.ok is True
    assert result.missing_config_files == []
    assert result.missing_env_vars == []
    assert result.agent_ids == ["coder-relay", "coordinator", "heartbeat"]
    assert result.channel_ids == ["lfc", "main", "ops"]


def test_validate_setup_reports_missing_required_env_vars(tmp_path: Path) -> None:
    """Setup validation should fail clearly when required API key env vars are missing."""
    app_paths = AppPaths.from_environment(
        home_directory=tmp_path,
        environment={
            "XDG_CONFIG_HOME": str(tmp_path / "cfg"),
            "XDG_DATA_HOME": str(tmp_path / "data"),
        },
    )
    app_paths.ensure_directories()
    write_role_based_config(config_root=app_paths.config_root)

    result = validate_setup(app_paths=app_paths, environment={})

    assert result.ok is False
    assert result.missing_env_vars == ["CHUTES_API_KEY"]


def test_validate_setup_loads_missing_env_vars_from_config_root_dotenv(tmp_path: Path) -> None:
    """Setup validation should load secrets from ~/.config/LocalFirstClaw/.env."""
    app_paths = AppPaths.from_environment(
        home_directory=tmp_path,
        environment={
            "XDG_CONFIG_HOME": str(tmp_path / "cfg"),
            "XDG_DATA_HOME": str(tmp_path / "data"),
        },
    )
    app_paths.ensure_directories()
    write_role_based_config(config_root=app_paths.config_root)
    write_env_file(config_root=app_paths.config_root, content="CHUTES_API_KEY=dotenv-key")

    result = validate_setup(app_paths=app_paths, environment={})

    assert result.ok is True
    assert result.missing_env_vars == []


def test_validate_setup_can_check_providers_without_completion_calls(tmp_path: Path) -> None:
    """Provider checks should use the models endpoint and return model counts."""
    app_paths = AppPaths.from_environment(
        home_directory=tmp_path,
        environment={
            "XDG_CONFIG_HOME": str(tmp_path / "cfg"),
            "XDG_DATA_HOME": str(tmp_path / "data"),
            "CHUTES_API_KEY": "test-key",
        },
    )
    app_paths.ensure_directories()
    write_role_based_config(config_root=app_paths.config_root)

    def fake_urlopen(request, timeout: int) -> FakeHttpResponse:
        """Return a fake Chutes model catalog response."""
        del timeout
        assert request.full_url == "https://llm.chutes.ai/v1/models"
        assert request.headers["Authorization"] == "Bearer test-key"
        return FakeHttpResponse(payload={"data": [{"id": "model-a"}, {"id": "model-b"}]})

    result = validate_setup(
        app_paths=app_paths,
        environment={"CHUTES_API_KEY": "test-key"},
        check_providers=True,
        urlopen=fake_urlopen,
    )

    assert result.ok is True
    assert len(result.provider_checks) == 3
    assert {check.model_count for check in result.provider_checks} == {2}


def test_check_chutes_connectivity_returns_model_count() -> None:
    """The Chutes provider check should parse the model catalog response."""

    def fake_urlopen(request, timeout: int) -> FakeHttpResponse:
        """Return a fake catalog with one model entry."""
        del timeout
        assert request.full_url == "https://llm.chutes.ai/v1/models"
        assert request.headers["Authorization"] == "Bearer test-key"
        return FakeHttpResponse(payload={"data": [{"id": "model-a"}]})

    result = check_chutes_connectivity(
        api_key="test-key",
        api_base="https://llm.chutes.ai/v1",
        urlopen=fake_urlopen,
    )

    assert result.ok is True
    assert result.model_count == 1
    assert result.api_base == "https://llm.chutes.ai/v1"


def test_cli_validate_setup_reports_success(capsys, monkeypatch, tmp_path: Path) -> None:
    """The CLI should report successful validation in operator-friendly text."""
    app_paths = AppPaths.from_environment(
        home_directory=tmp_path,
        environment={
            "XDG_CONFIG_HOME": str(tmp_path / "cfg"),
            "XDG_DATA_HOME": str(tmp_path / "data"),
            "CHUTES_API_KEY": "test-key",
        },
    )
    app_paths.ensure_directories()
    write_role_based_config(config_root=app_paths.config_root)

    monkeypatch.setattr("localfirstclaw.cli.AppPaths.from_environment", lambda: app_paths)

    exit_code = main(["validate-setup"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Setup validation passed." in captured.out
    assert "Agents: coder-relay, coordinator, heartbeat" in captured.out


def test_cli_validate_setup_uses_dotenv_without_shell_exports(capsys, monkeypatch, tmp_path: Path) -> None:
    """The CLI should succeed when secrets exist only in the config-root .env file."""
    app_paths = AppPaths.from_environment(
        home_directory=tmp_path,
        environment={
            "XDG_CONFIG_HOME": str(tmp_path / "cfg"),
            "XDG_DATA_HOME": str(tmp_path / "data"),
        },
    )
    app_paths.ensure_directories()
    write_role_based_config(config_root=app_paths.config_root)
    write_env_file(config_root=app_paths.config_root, content="CHUTES_API_KEY=dotenv-key")

    monkeypatch.setattr("localfirstclaw.cli.AppPaths.from_environment", lambda: app_paths)
    monkeypatch.setattr("localfirstclaw.cli.os.environ", {})

    exit_code = main(["validate-setup"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Setup validation passed." in captured.out


def test_cli_check_provider_chutes_reports_success(capsys, monkeypatch) -> None:
    """The CLI should support a zero-token Chutes provider check command."""

    def fake_check(*, api_key: str, api_base: str, urlopen=None):
        """Return a deterministic success result for the CLI."""
        del urlopen
        assert api_key == "test-key"
        assert api_base == "https://llm.chutes.ai/v1"
        return type(
            "FakeResult",
            (),
            {
                "ok": True,
                "provider_name": "chutes",
                "api_base": api_base,
                "model_count": 42,
                "error_message": None,
            },
        )()

    monkeypatch.setattr("localfirstclaw.cli.check_chutes_connectivity", fake_check)

    exit_code = main(
        [
            "check-provider",
            "chutes",
            "--api-key",
            "test-key",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Provider check passed for chutes." in captured.out
    assert "Models available: 42" in captured.out


def test_cli_check_provider_uses_dotenv_when_shell_is_missing_key(capsys, monkeypatch, tmp_path: Path) -> None:
    """The provider check command should load CHUTES_API_KEY from the config-root .env file."""
    app_paths = AppPaths.from_environment(
        home_directory=tmp_path,
        environment={
            "XDG_CONFIG_HOME": str(tmp_path / "cfg"),
            "XDG_DATA_HOME": str(tmp_path / "data"),
        },
    )
    app_paths.ensure_directories()
    write_role_based_config(config_root=app_paths.config_root)
    write_env_file(config_root=app_paths.config_root, content="CHUTES_API_KEY=dotenv-key")

    def fake_check(*, api_key: str, api_base: str, urlopen=None):
        """Return a deterministic success result using the dotenv-loaded key."""
        del urlopen
        assert api_key == "dotenv-key"
        return type(
            "FakeResult",
            (),
            {
                "ok": True,
                "provider_name": "chutes",
                "api_base": api_base,
                "model_count": 47,
                "error_message": None,
            },
        )()

    monkeypatch.setattr("localfirstclaw.cli.AppPaths.from_environment", lambda: app_paths)
    monkeypatch.setattr("localfirstclaw.cli.check_chutes_connectivity", fake_check)
    monkeypatch.setattr("localfirstclaw.cli.os.environ", {})

    exit_code = main(["check-provider", "chutes"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Models available: 47" in captured.out


def test_cli_describe_plugin_reports_manifest(capsys) -> None:
    """The CLI should expose plugin documentation on demand."""
    exit_code = main(["describe-plugin", "telegram"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Plugin: telegram" in captured.out
    assert "Display name: Telegram Transport" in captured.out
    assert "Capabilities: transport, self_describe, maintenance_skill" in captured.out


def test_cli_plugin_skill_reports_maintenance_guidance(capsys) -> None:
    """The CLI should expose plugin maintenance guidance without loading it into every prompt."""
    exit_code = main(["plugin-skill", "telegram"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "Telegram Transport Plugin" in captured.out
    assert "How To Configure" in captured.out


def test_cli_describe_plugin_includes_botfather_guidance_reference(capsys) -> None:
    """The Telegram plugin manifest path should exist for setup agents to discover."""
    exit_code = main(["describe-plugin", "telegram"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "bot_token_env" in captured.out


def test_cli_plugin_skill_mentions_botfather_steps(capsys) -> None:
    """The on-demand Telegram setup guide should mention BotFather and chat binding."""
    exit_code = main(["plugin-skill", "telegram"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "BotFather" in captured.out
    assert "chat:<chat_id>" in captured.out
