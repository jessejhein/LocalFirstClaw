#!/usr/bin/env python3
"""Setup validation helpers for external config and provider readiness."""

from __future__ import annotations

import urllib.request
from dataclasses import dataclass, field
from typing import Callable, Mapping

from localfirstclaw.apppaths import AppPaths
from localfirstclaw.configloader import load_localfirstclaw_config
from localfirstclaw.envloader import load_runtime_environment
from localfirstclaw.providercheck import ProviderCheckResult, check_chutes_connectivity


@dataclass(frozen=True)
class SetupValidationResult:
    """Structured result from validating a LocalFirstClaw setup."""

    ok: bool
    config_root: str
    data_root: str
    missing_config_files: list[str] = field(default_factory=list)
    missing_data_directories: list[str] = field(default_factory=list)
    missing_env_vars: list[str] = field(default_factory=list)
    agent_ids: list[str] = field(default_factory=list)
    channel_ids: list[str] = field(default_factory=list)
    endpoint_ids: list[str] = field(default_factory=list)
    provider_checks: list[ProviderCheckResult] = field(default_factory=list)
    load_error: str | None = None


def validate_setup(
    *,
    app_paths: AppPaths,
    environment: Mapping[str, str] | None = None,
    check_providers: bool = False,
    urlopen: Callable[..., object] = urllib.request.urlopen,
) -> SetupValidationResult:
    """
    Validate the external config tree, required environment, and optional provider reachability.

    Args:
        app_paths: Resolved application paths to validate.
        environment: Optional environment override used for required secret checks.
        check_providers: Whether to perform metadata-only provider reachability checks.
        urlopen: Injectable urllib opener used by provider-check tests.

    Returns:
        Structured validation result suitable for CLI display or automation.
    """
    env = load_runtime_environment(app_paths=app_paths, base_environment=environment)
    missing_config_files = _find_missing_config_files(app_paths=app_paths)
    missing_data_directories = _find_missing_data_directories(app_paths=app_paths)

    if missing_config_files:
        return SetupValidationResult(
            ok=False,
            config_root=str(app_paths.config_root),
            data_root=str(app_paths.data_root),
            missing_config_files=missing_config_files,
            missing_data_directories=missing_data_directories,
        )

    try:
        config = load_localfirstclaw_config(config_root=app_paths.config_root)
    except Exception as error:
        return SetupValidationResult(
            ok=False,
            config_root=str(app_paths.config_root),
            data_root=str(app_paths.data_root),
            missing_config_files=missing_config_files,
            missing_data_directories=missing_data_directories,
            load_error=str(error),
        )

    missing_env_vars = sorted(
        {
            alias.api_key_env
            for alias in config.model_aliases.values()
            if alias.api_key_env is not None and not env.get(alias.api_key_env)
        }
    )

    provider_checks: list[ProviderCheckResult] = []
    if check_providers and not missing_env_vars:
        for alias in config.model_aliases.values():
            if alias.api_key_env is None:
                continue
            provider_checks.append(
                check_chutes_connectivity(
                    api_key=env[alias.api_key_env],
                    api_base=alias.api_base or "https://llm.chutes.ai/v1",
                    urlopen=urlopen,
                )
            )

    ok = (
        not missing_config_files
        and not missing_data_directories
        and not missing_env_vars
        and all(check.ok for check in provider_checks)
    )

    return SetupValidationResult(
        ok=ok,
        config_root=str(app_paths.config_root),
        data_root=str(app_paths.data_root),
        missing_config_files=missing_config_files,
        missing_data_directories=missing_data_directories,
        missing_env_vars=missing_env_vars,
        agent_ids=sorted(config.agents.keys()),
        channel_ids=sorted(config.channels.keys()),
        endpoint_ids=sorted(config.endpoints.keys()),
        provider_checks=provider_checks,
    )


def _find_missing_config_files(*, app_paths: AppPaths) -> list[str]:
    """Return required config file names that are missing from the config root."""
    required_files = [
        "agents.yaml",
        "channels.yaml",
        "endpoints.yaml",
        "models.yaml",
    ]
    return [name for name in required_files if not (app_paths.config_root / name).is_file()]


def _find_missing_data_directories(*, app_paths: AppPaths) -> list[str]:
    """Return required data directory names that are missing from the data root."""
    required_directories = [
        app_paths.journal_root,
        app_paths.logs_root,
        app_paths.plugins_root,
        app_paths.runtime_root,
    ]
    return [str(path) for path in required_directories if not path.is_dir()]
