#!/usr/bin/env python3
"""Helpers for loading environment variables from the external config root."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Mapping

from localfirstclaw.apppaths import AppPaths


def load_runtime_environment(
    *,
    app_paths: AppPaths,
    base_environment: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """
    Build the effective runtime environment using the process env plus config-root `.env`.

    Precedence:

    1. values from the provided or process environment
    2. fallback values from `<config_root>/.env`

    Args:
        app_paths: Resolved application paths.
        base_environment: Optional environment override, typically used by tests.

    Returns:
        Effective environment mapping for LocalFirstClaw runtime commands.
    """
    environment = dict(os.environ if base_environment is None else base_environment)
    dotenv_values = _load_dotenv_file(path=app_paths.config_root / ".env")
    for key, value in dotenv_values.items():
        environment.setdefault(key, value)
    return environment


def _load_dotenv_file(*, path: Path) -> dict[str, str]:
    """
    Parse a simple `.env` file into a dictionary.

    Args:
        path: Path to the `.env` file.

    Returns:
        Parsed key/value pairs. Missing files return an empty dictionary.
    """
    if not path.is_file():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        cleaned_key = key.strip()
        cleaned_value = value.strip().strip('"').strip("'")
        if cleaned_key:
            values[cleaned_key] = cleaned_value

    return values
