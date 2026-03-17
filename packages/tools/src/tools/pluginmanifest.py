#!/usr/bin/env python3
"""Plugin manifest model used for on-demand self-description."""

from dataclasses import dataclass

from tools.pluginconfigfield import PluginConfigField


@dataclass(frozen=True)
class PluginManifest:
    """Describe a plugin's identity, capabilities, and config surface."""

    plugin_id: str
    display_name: str
    summary: str
    capabilities: list[str]
    config_fields: list[PluginConfigField]
