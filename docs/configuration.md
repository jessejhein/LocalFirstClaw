# Configuration And Runtime Layout

LocalFirstClaw keeps live configuration and workspace files outside the source repo. This allows the code checkout to be temporary while the user configuration and workspace remain stable and separately versioned.

## Default Paths

The current default path resolution follows XDG-style rules:

- `XDG_CONFIG_HOME/LocalFirstClaw` or `~/.config/LocalFirstClaw`
- `XDG_DATA_HOME/LocalFirstClaw` or `~/.local/share/LocalFirstClaw`

The root package exposes `AppPaths.from_environment(...)` to resolve these defaults and `ensure_directories()` to create them.

## Config Root

The config root is intended to be human-edited and suitable for git tracking.

Current files and directories:

- `agents.yaml`
- `channels.yaml`
- `endpoints.yaml`
- `models.yaml`
- `.env`
- `skills/`
- `workspace/`

Recommended use:

- keep prompts, plans, distilled memory, and curated notes in `workspace/`
- keep provider and routing definitions in the YAML files
- keep secrets in `.env`, not in YAML
- keep plugin configuration in the config root

## Data Root

The data root is intended for generated or bulky state that should not normally be committed.

Current directories:

- `journal/`
- `logs/`
- `plugins/`
- `runtime/`

Recommended use:

- raw append-only memory lives in `journal/`
- operational logs live in `logs/`
- installed plugin code or artifacts live in `plugins/`
- lock files and runtime state live in `runtime/`

## YAML File Formats

### `agents.yaml`

```yaml
agents:
  - agent_id: coordinator
    model: premium
    system_prompt: You coordinate the system and the user-facing main channel.
  - agent_id: coder-relay
    model: relay
    system_prompt: You relay coding session updates and keep the user informed.
  - agent_id: heartbeat
    model: cheap
    system_prompt: You handle short autonomous heartbeat and maintenance tasks.
```

`model` can be either a direct provider-qualified model name or a configured LiteLLM alias from `models.yaml`.

### `channels.yaml`

```yaml
channels:
  - channel_id: main
    default_agent_id: coordinator
  - channel_id: lfc
    default_agent_id: coder-relay
  - channel_id: ops
    default_agent_id: heartbeat
```

### `endpoints.yaml`

```yaml
endpoints:
  - endpoint_id: tui-main
    transport: tui
    binding: session:main
    primary_channel_id: main
    allow_channel_switching: true
  - endpoint_id: telegram-game
    transport: telegram
    binding: thread:game
    primary_channel_id: game
    allow_channel_switching: false
```

### `models.yaml`

```yaml
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
```

The `api_key_env` value names the environment variable that should contain the real provider key. The key itself does not belong in the YAML file.

## Naming Constraint

Agent ids and channel ids must be globally distinct.

Current rule:

- an agent cannot have the same name as any channel
- a channel cannot have the same name as any agent

For example:

- channel `main` with agent `coordinator` is valid
- channel `main` with agent `main` is rejected

This is a deliberate limitation to prevent ambiguous routing, status output, and operator mistakes.

## Bootstrap Helpers

The root package now provides these helpers:

```python
AppPaths.from_environment(...)
load_localfirstclaw_config(config_root=...)
build_journal(app_paths=...)
build_agent_interface(config=..., journal=...)
build_gateway_router(config=..., journal=..., agent_executor=...)
```

Current behavior:

- config is loaded from YAML under the config root
- runtime secrets can be loaded from `<config_root>/.env`
- journal writes go to the external data root
- the default agent executor uses `LiteLLMModelClient`
- model aliases are resolved before the LiteLLM call

Environment precedence:

1. already-exported shell environment
2. fallback values from `<config_root>/.env`

## Setup Validation Commands

The root package now installs the `localfirstclaw` CLI.

Current commands:

- `localfirstclaw validate-setup`
- `localfirstclaw validate-setup --check-providers`
- `localfirstclaw check-provider chutes`

The default validation command checks local config and required secrets only.

The Chutes provider check and `--check-providers` path use the provider metadata endpoint rather than a chat completion endpoint, so they should not spend completion tokens.

## Current Limitations

- no automatic first-run config generation yet
- no config hot reload yet
- no secrets manager abstraction beyond environment variables
- no plugin discovery from the external plugin directory yet
