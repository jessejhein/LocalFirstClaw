#!/usr/bin/env python3
"""Small operator CLI for validating LocalFirstClaw setup."""

from __future__ import annotations

import argparse
import os
from collections.abc import Sequence
from pathlib import Path

import yaml
from telegramtransport import HttpTelegramApiClient, TelegramTransportRunner
from tools import PluginRegistry, TelegramTransportPlugin

from localfirstclaw.apppaths import AppPaths
from localfirstclaw.bootstrap import build_agent_interface, build_gateway_router, build_journal
from localfirstclaw.configloader import load_localfirstclaw_config
from localfirstclaw.envloader import load_runtime_environment
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

    if args.command == "run-telegram":
        return _run_telegram(once=args.once, bot_token=args.bot_token, bot_token_env=args.bot_token_env)

    if args.command == "telegram-discover":
        return _run_telegram_discover()

    if args.command == "telegram-bind":
        return _run_telegram_bind(
            endpoint_id=args.endpoint_id,
            binding=args.binding,
            channel_id=args.channel,
            allow_channel_switching=args.allow_channel_switching,
        )

    if args.command == "telegram-onboard":
        return _run_telegram_onboard(
            endpoint_id=args.endpoint_id,
            channel_id=args.channel,
            binding=args.binding,
            allow_channel_switching=args.allow_channel_switching,
        )

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

    run_telegram_parser = subparsers.add_parser(
        "run-telegram",
        help="run the Telegram transport against configured Telegram endpoints",
    )
    run_telegram_parser.add_argument("--once", action="store_true", help="poll and process one batch of updates only")
    run_telegram_parser.add_argument("--bot-token")
    run_telegram_parser.add_argument("--bot-token-env", default="TELEGRAM_BOT_TOKEN")

    telegram_discover_parser = subparsers.add_parser(
        "telegram-discover",
        help="poll Telegram once and list discovered chat/thread bindings",
    )
    telegram_discover_parser.set_defaults(_telegram_command=True)

    telegram_bind_parser = subparsers.add_parser(
        "telegram-bind",
        help="write a Telegram endpoint binding into endpoints.yaml",
    )
    telegram_bind_parser.add_argument("--endpoint-id", required=True)
    telegram_bind_parser.add_argument("--binding", required=True)
    telegram_bind_parser.add_argument("--channel", required=True)
    telegram_bind_parser.add_argument("--allow-channel-switching", action="store_true")

    telegram_onboard_parser = subparsers.add_parser(
        "telegram-onboard",
        help="discover Telegram bindings and write the selected endpoint config",
    )
    telegram_onboard_parser.add_argument("--endpoint-id", required=True)
    telegram_onboard_parser.add_argument("--channel", required=True)
    telegram_onboard_parser.add_argument("--binding")
    telegram_onboard_parser.add_argument("--allow-channel-switching", action="store_true")

    return parser


def _run_validate_setup(*, check_providers: bool) -> int:
    """Validate the current LocalFirstClaw setup and print a human-readable summary."""
    app_paths = AppPaths.from_environment()
    result = validate_setup(
        app_paths=app_paths,
        environment=load_runtime_environment(app_paths=app_paths, base_environment=os.environ),
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
    app_paths = AppPaths.from_environment()
    environment = load_runtime_environment(app_paths=app_paths, base_environment=os.environ)
    resolved_api_key = api_key or environment.get(api_key_env)
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


def _run_telegram(*, once: bool, bot_token: str | None, bot_token_env: str) -> int:
    """Run the Telegram transport using the current LocalFirstClaw config."""
    app_paths = AppPaths.from_environment()
    environment = load_runtime_environment(app_paths=app_paths, base_environment=os.environ)
    resolved_bot_token = bot_token or environment.get(bot_token_env)
    if not resolved_bot_token:
        print(f"Missing Telegram bot token. Set {bot_token_env} or pass --bot-token.")
        return 1

    config = load_localfirstclaw_config(config_root=app_paths.config_root)
    journal = build_journal(app_paths=app_paths)
    agent_interface = build_agent_interface(config=config, journal=journal, environment=environment)
    router = build_gateway_router(config=config, journal=journal, agent_executor=agent_interface)
    runner = TelegramTransportRunner(
        router=router,
        api_client=HttpTelegramApiClient(bot_token=resolved_bot_token),
    )

    if once:
        processed_count = runner.process_once()
        print(f"Processed {processed_count} Telegram update(s).")
        return 0

    while True:
        runner.process_once()


def _run_telegram_discover() -> int:
    """Poll Telegram once and print discovered chat/thread bindings."""
    discoveries = _discover_telegram_bindings()
    print("Discovered Telegram bindings:")
    for discovery in discoveries:
        print(f"- {discovery['binding']}: {discovery['label']}")
    return 0


def _run_telegram_bind(
    *,
    endpoint_id: str,
    binding: str,
    channel_id: str,
    allow_channel_switching: bool,
) -> int:
    """Write one Telegram endpoint binding into endpoints.yaml."""
    app_paths = AppPaths.from_environment()
    config = load_localfirstclaw_config(config_root=app_paths.config_root)
    if channel_id not in config.channels:
        print(f"Unknown channel: {channel_id}")
        return 1

    _upsert_endpoint_config(
        endpoints_path=app_paths.config_root / "endpoints.yaml",
        endpoint_id=endpoint_id,
        binding=binding,
        channel_id=channel_id,
        allow_channel_switching=allow_channel_switching,
    )
    print(f"Bound {endpoint_id} to {binding}")
    return 0


def _run_telegram_onboard(
    *,
    endpoint_id: str,
    channel_id: str,
    binding: str | None,
    allow_channel_switching: bool,
) -> int:
    """
    Discover bindings, then bind the selected Telegram endpoint.

    Args:
        endpoint_id: Endpoint identifier to create or replace.
        channel_id: Primary channel id for the endpoint.
        binding: Optional explicit Telegram binding chosen by the operator.
        allow_channel_switching: Whether this endpoint may switch channels with `@channel`.

    Returns:
        Process exit code.
    """
    discoveries = _discover_telegram_bindings()
    print("Discovered Telegram bindings:")
    for discovery in discoveries:
        print(f"- {discovery['binding']}: {discovery['label']}")

    selected_binding = binding
    if selected_binding is None:
        if not discoveries:
            print("No Telegram bindings were discovered. Send a message to the bot, then try again.")
            return 1
        if len(discoveries) == 1:
            selected_binding = discoveries[0]["binding"]
            print("Only one Telegram binding was discovered. Binding it automatically.")
        else:
            print("Multiple Telegram bindings were discovered.")
            print("Run telegram-onboard again with --binding chat:<chat_id> or --binding thread:<chat_id>:<thread_id>.")
            return 1

    return _run_telegram_bind(
        endpoint_id=endpoint_id,
        binding=selected_binding,
        channel_id=channel_id,
        allow_channel_switching=allow_channel_switching,
    )


def _discover_telegram_bindings() -> list[dict[str, str]]:
    """
    Poll Telegram once and return discovered binding candidates.

    Returns:
        A stable list of unique `binding` and `label` pairs extracted from recent Telegram updates.
    """
    environment = _load_telegram_runtime_environment()
    client = _build_telegram_api_client(bot_token=environment["TELEGRAM_BOT_TOKEN"])
    plugin = TelegramTransportPlugin()
    discoveries: list[dict[str, str]] = []
    seen_bindings: set[str] = set()
    for update in client.get_updates(offset=None, timeout_seconds=1):
        inbound_message = plugin.parse_update(update=update)
        if inbound_message is None:
            continue
        if inbound_message.endpoint_binding in seen_bindings:
            continue
        seen_bindings.add(inbound_message.endpoint_binding)
        label = _format_telegram_discovery_label(update=update, binding=inbound_message.endpoint_binding)
        discoveries.append({"binding": inbound_message.endpoint_binding, "label": label})
    return discoveries


def _load_telegram_runtime_environment() -> dict[str, str]:
    """Load the runtime environment needed for Telegram commands."""
    app_paths = AppPaths.from_environment()
    environment = load_runtime_environment(app_paths=app_paths, base_environment=os.environ)
    if not environment.get("TELEGRAM_BOT_TOKEN"):
        raise KeyError("TELEGRAM_BOT_TOKEN")
    return environment


def _build_telegram_api_client(*, bot_token: str) -> HttpTelegramApiClient:
    """Construct the default Telegram API client."""
    return HttpTelegramApiClient(bot_token=bot_token)


def _format_telegram_discovery_label(*, update: dict[str, object], binding: str) -> str:
    """Build a human-readable label for a discovered Telegram binding."""
    message = update.get("message", {})
    if not isinstance(message, dict):
        return binding
    chat = message.get("chat", {})
    if not isinstance(chat, dict):
        return binding
    chat_type = str(chat.get("type", "unknown"))
    title = chat.get("title")
    if title:
        return f'{chat_type} chat "{title}"'
    return f"{chat_type} chat"


def _upsert_endpoint_config(
    *,
    endpoints_path: Path,
    endpoint_id: str,
    binding: str,
    channel_id: str,
    allow_channel_switching: bool,
) -> None:
    """Create or replace one endpoint entry inside endpoints.yaml."""
    document = {}
    if endpoints_path.is_file():
        document = yaml.safe_load(endpoints_path.read_text(encoding="utf-8")) or {}
    endpoints = list(document.get("endpoints", []))

    new_entry = {
        "endpoint_id": endpoint_id,
        "transport": "telegram",
        "binding": binding,
        "primary_channel_id": channel_id,
        "allow_channel_switching": allow_channel_switching,
    }

    updated_endpoints = [entry for entry in endpoints if entry.get("endpoint_id") != endpoint_id]
    updated_endpoints.append(new_entry)
    document["endpoints"] = updated_endpoints
    endpoints_path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
