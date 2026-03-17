#!/usr/bin/env python3
"""Small operator CLI for validating LocalFirstClaw setup."""

from __future__ import annotations

import argparse
import os
from collections.abc import Sequence

from tools import PluginRegistry, TelegramTransportPlugin

from localfirstclaw.apppaths import AppPaths
from localfirstclaw.providercheck import check_chutes_connectivity
from localfirstclaw.setupvalidation import validate_setup


def main(argv: Sequence[str] | None = None) -> int:
    """
    Run the LocalFirstClaw operator CLI.

    Args:
        argv: Optional command-line arguments excluding the executable name.

    Returns:
        Process exit code.
    """
    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    if args.command == "validate-setup":
        return _run_validate_setup(check_providers=args.check_providers)

    if args.command == "check-provider" and args.provider == "chutes":
        return _run_check_provider_chutes(api_base=args.api_base, api_key=args.api_key, api_key_env=args.api_key_env)

    if args.command == "describe-plugin":
        return _run_describe_plugin(plugin_id=args.plugin_id)

    if args.command == "plugin-skill":
        return _run_plugin_skill(plugin_id=args.plugin_id)

    parser.error("unknown command")
    return 2


def _build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(prog="localfirstclaw")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_setup_parser = subparsers.add_parser(
        "validate-setup",
        help="validate config, data directories, required env vars, and optional provider reachability",
    )
    validate_setup_parser.add_argument(
        "--check-providers",
        action="store_true",
        help="call provider metadata endpoints to confirm connectivity without using completion tokens",
    )

    check_provider_parser = subparsers.add_parser(
        "check-provider",
        help="run a metadata-only connectivity check for one configured provider",
    )
    check_provider_parser.add_argument("provider", choices=["chutes"])
    check_provider_parser.add_argument("--api-base", default="https://llm.chutes.ai/v1")
    check_provider_parser.add_argument("--api-key")
    check_provider_parser.add_argument("--api-key-env", default="CHUTES_API_KEY")

    describe_plugin_parser = subparsers.add_parser(
        "describe-plugin",
        help="print plugin manifest information on demand",
    )
    describe_plugin_parser.add_argument("plugin_id", choices=["telegram"])

    plugin_skill_parser = subparsers.add_parser(
        "plugin-skill",
        help="print plugin maintenance guidance on demand",
    )
    plugin_skill_parser.add_argument("plugin_id", choices=["telegram"])

    return parser


def _run_validate_setup(*, check_providers: bool) -> int:
    """Validate the current LocalFirstClaw setup and print a human-readable summary."""
    result = validate_setup(
        app_paths=AppPaths.from_environment(),
        environment=os.environ,
        check_providers=check_providers,
    )

    if not result.ok:
        print("Setup validation failed.")
        if result.load_error is not None:
            print(f"Config load error: {result.load_error}")
        if result.missing_config_files:
            print("Missing config files: " + ", ".join(result.missing_config_files))
        if result.missing_data_directories:
            print("Missing data directories:")
            for directory in result.missing_data_directories:
                print(f"  - {directory}")
        if result.missing_env_vars:
            print("Missing environment variables: " + ", ".join(result.missing_env_vars))
        for check in result.provider_checks:
            if not check.ok:
                print(f"Provider check failed for {check.provider_name}: {check.error_message}")
        return 1

    print("Setup validation passed.")
    print(f"Config root: {result.config_root}")
    print(f"Data root: {result.data_root}")
    print("Agents: " + ", ".join(result.agent_ids))
    print("Channels: " + ", ".join(result.channel_ids))
    print("Endpoints: " + ", ".join(result.endpoint_ids))
    for check in result.provider_checks:
        print(f"Provider {check.provider_name}: ok, api_base={check.api_base}, " f"models={check.model_count}")
    return 0


def _run_check_provider_chutes(*, api_base: str, api_key: str | None, api_key_env: str) -> int:
    """Run a zero-token Chutes metadata check and print the result."""
    resolved_api_key = api_key or os.environ.get(api_key_env)
    if not resolved_api_key:
        print(f"Missing API key. Set {api_key_env} or pass --api-key.")
        return 1

    result = check_chutes_connectivity(api_key=resolved_api_key, api_base=api_base)
    if not result.ok:
        print(f"Provider check failed for {result.provider_name}: {result.error_message}")
        return 1

    print(f"Provider check passed for {result.provider_name}.")
    print(f"API base: {result.api_base}")
    print(f"Models available: {result.model_count}")
    return 0


def _run_describe_plugin(*, plugin_id: str) -> int:
    """Print the manifest for one registered plugin."""
    registry = _build_plugin_registry()
    manifest = registry.describe_plugin(plugin_id=plugin_id)
    print(f"Plugin: {manifest.plugin_id}")
    print(f"Display name: {manifest.display_name}")
    print(f"Summary: {manifest.summary}")
    print("Capabilities: " + ", ".join(manifest.capabilities))
    print("Config fields:")
    for field in manifest.config_fields:
        default_suffix = "" if field.default_value is None else f" [default={field.default_value}]"
        required_label = "required" if field.required else "optional"
        print(f"  - {field.field_name} ({required_label}){default_suffix}: {field.description}")
    return 0


def _run_plugin_skill(*, plugin_id: str) -> int:
    """Print the maintenance skill text for one registered plugin."""
    registry = _build_plugin_registry()
    print(registry.get_plugin_skill(plugin_id=plugin_id))
    return 0


def _build_plugin_registry() -> PluginRegistry:
    """Construct the current plugin registry."""
    return PluginRegistry(plugins=[TelegramTransportPlugin()])
