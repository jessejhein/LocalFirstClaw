#!/usr/bin/env python3
"""Configuration field metadata for self-describing plugins."""

from dataclasses import dataclass


@dataclass(frozen=True)
class PluginConfigField:
    """Describe one configuration field required or supported by a plugin."""

    field_name: str
    description: str
    required: bool = True
    default_value: str | None = None
