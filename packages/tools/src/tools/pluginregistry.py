#!/usr/bin/env python3
"""Registry for self-describing plugins."""

from __future__ import annotations

from tools.pluginmanifest import PluginManifest


class PluginRegistry:
    """Store plugins and expose on-demand descriptions and maintenance skills."""

    def __init__(self, *, plugins: list[object]) -> None:
        """
        Create a registry from plugin instances.

        Args:
            plugins: Plugin instances keyed by their `plugin_id` attributes.
        """
        self.plugins = {plugin.plugin_id: plugin for plugin in plugins}

    def describe_plugin(self, *, plugin_id: str) -> PluginManifest:
        """
        Return the manifest for one plugin.

        Args:
            plugin_id: Registered plugin identifier.

        Returns:
            Self-description for the requested plugin.

        Raises:
            KeyError: If the plugin id is unknown.
        """
        return self.plugins[plugin_id].describe()

    def get_plugin_skill(self, *, plugin_id: str) -> str:
        """
        Return the on-demand maintenance skill text for one plugin.

        Args:
            plugin_id: Registered plugin identifier.

        Returns:
            Maintenance guidance text for the requested plugin.

        Raises:
            KeyError: If the plugin id is unknown.
        """
        return self.plugins[plugin_id].get_maintenance_skill()
