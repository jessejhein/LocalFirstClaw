#!/usr/bin/env python3
"""Helpers for resolving LocalFirstClaw config and data directories."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


@dataclass(frozen=True)
class AppPaths:
    """Resolved application paths for config, workspace, and generated data."""

    config_root: Path
    data_root: Path
    workspace_root: Path
    skills_root: Path
    logs_root: Path
    plugins_root: Path
    journal_root: Path
    runtime_root: Path

    @classmethod
    def from_environment(
        cls,
        *,
        home_directory: Path | None = None,
        environment: Mapping[str, str] | None = None,
    ) -> "AppPaths":
        """
        Resolve application paths using XDG-style defaults.

        Args:
            home_directory: Optional home directory override for tests or bootstrapping.
            environment: Optional process environment override.

        Returns:
            Fully resolved LocalFirstClaw path set.
        """
        env = dict(os.environ if environment is None else environment)
        home = home_directory or Path.home()
        config_home = Path(env["XDG_CONFIG_HOME"]) if "XDG_CONFIG_HOME" in env else home / ".config"
        data_home = Path(env["XDG_DATA_HOME"]) if "XDG_DATA_HOME" in env else home / ".local" / "share"
        config_root = config_home / "LocalFirstClaw"
        data_root = data_home / "LocalFirstClaw"
        return cls(
            config_root=config_root,
            data_root=data_root,
            workspace_root=config_root / "workspace",
            skills_root=config_root / "skills",
            logs_root=data_root / "logs",
            plugins_root=data_root / "plugins",
            journal_root=data_root / "journal",
            runtime_root=data_root / "runtime",
        )

    def ensure_directories(self) -> None:
        """
        Create the standard config and data directories if they do not yet exist.

        This is intended for first-run setup and test scaffolding. Existing directories
        are left untouched.
        """
        for directory in (
            self.config_root,
            self.data_root,
            self.workspace_root,
            self.skills_root,
            self.logs_root,
            self.plugins_root,
            self.journal_root,
            self.runtime_root,
        ):
            directory.mkdir(parents=True, exist_ok=True)
