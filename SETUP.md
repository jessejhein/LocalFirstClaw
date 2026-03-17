# Setup

This document explains how to prepare the current LocalFirstClaw codebase for a first manual bring-up.

It documents the system as it exists now, not the eventual MVP. At the moment, the codebase has a working journal, gateway, agentinterface, TUI package, XDG-style config loading, and LiteLLM-backed model client support. It does not yet have a polished standalone runner, Telegram transport, or always-on supervisor process.

## What Setup Means Today

A successful setup today means:

- the Python environment installs cleanly
- the external config and data directories exist
- the required YAML config files are present
- required API keys are exported in the shell
- LocalFirstClaw can load config and construct its runtime objects without errors

This is enough for another human or agent to validate the environment and continue implementation. It is not yet the same as a production-ready deployment.

## Prerequisites

- Python 3.12 or newer
- `uv`
- a shell environment where you can export provider API keys
- optionally a separate git repo at `~/.config/LocalFirstClaw`

## 1. Install The Project Environment

From the source checkout:

```bash
UV_CACHE_DIR=.uv-cache UV_PYTHON_INSTALL_DIR=.uv-python uv sync --all-packages --extra dev
```

That creates or updates the project `.venv` and installs the workspace packages plus the test and lint tools.

## 2. Create The External Directories

LocalFirstClaw keeps live configuration outside the source repo.

Default locations:

- config root: `~/.config/LocalFirstClaw`
- data root: `~/.local/share/LocalFirstClaw`

Create the directories:

```bash
mkdir -p ~/.config/LocalFirstClaw
mkdir -p ~/.config/LocalFirstClaw/workspace
mkdir -p ~/.config/LocalFirstClaw/skills
mkdir -p ~/.local/share/LocalFirstClaw/journal
mkdir -p ~/.local/share/LocalFirstClaw/logs
mkdir -p ~/.local/share/LocalFirstClaw/plugins
mkdir -p ~/.local/share/LocalFirstClaw/runtime
```

If you want the config tree tracked separately, initialize a git repo there yourself:

```bash
cd ~/.config/LocalFirstClaw
git init
```

## 3. Create The Required YAML Config Files

Copy the starter templates from [examples/config/LocalFirstClaw](/home/openclaw/Projects/LocalFirstClaw/examples/config/LocalFirstClaw):

```bash
cp /home/openclaw/Projects/LocalFirstClaw/examples/config/LocalFirstClaw/agents.yaml ~/.config/LocalFirstClaw/
cp /home/openclaw/Projects/LocalFirstClaw/examples/config/LocalFirstClaw/channels.yaml ~/.config/LocalFirstClaw/
cp /home/openclaw/Projects/LocalFirstClaw/examples/config/LocalFirstClaw/endpoints.yaml ~/.config/LocalFirstClaw/
cp /home/openclaw/Projects/LocalFirstClaw/examples/config/LocalFirstClaw/models.yaml ~/.config/LocalFirstClaw/
```

Required files:

- `agents.yaml`
- `channels.yaml`
- `endpoints.yaml`
- `models.yaml`

Current format reference is in [docs/configuration.md](/home/openclaw/Projects/LocalFirstClaw/docs/configuration.md).

## 4. Fill In Model Settings

Edit `~/.config/LocalFirstClaw/models.yaml`.

The example file intentionally contains a placeholder `api_base` and example provider model:

```yaml
aliases:
  kimi:
    provider_model: openai/kimi-k2
    api_base: https://llm.example.test/v1
    api_key_env: CHUTES_API_KEY
```

You need to replace:

- `provider_model` with the real LiteLLM model target you want to use
- `api_base` with the real provider base URL if required by that provider
- `api_key_env` only if you want a different environment variable name

## 5. Export Provider Credentials

If your alias uses `api_key_env: CHUTES_API_KEY`, export that before trying the model client:

```bash
export CHUTES_API_KEY=your-real-key-here
```

Do not store live API keys in the YAML files.

Naming rule:

- do not give an agent the same identifier as a channel
- for example, use channel `main` with agent `coordinator`, not agent `main`

## 6. Smoke Test The Bootstrap Layer

This verifies that config loading and runtime construction work.

```bash
.venv/bin/python - <<'PY'
from localfirstclaw import (
    AppPaths,
    build_agent_interface,
    build_gateway_router,
    build_journal,
    load_localfirstclaw_config,
)

paths = AppPaths.from_environment()
config = load_localfirstclaw_config(config_root=paths.config_root)
journal = build_journal(app_paths=paths)
agent_interface = build_agent_interface(config=config, journal=journal)
gateway = build_gateway_router(config=config, journal=journal, agent_executor=agent_interface)

status = gateway.get_endpoint_status(endpoint_id="tui-main")
print("Config root:", paths.config_root)
print("Data root:", paths.data_root)
print("Endpoint:", status.endpoint_id)
print("Primary channel:", status.primary_channel_id)
print("Active channel:", status.active_channel_id)
print("Default agent:", status.default_agent_id)
PY
```

If that prints endpoint/channel status without a traceback, the current bootstrap layer is working.

## 7. Optional Test Verification

If you want to confirm the current repo state matches the documented implementation:

```bash
.venv/bin/pytest tests/test_appconfig.py \
  packages/agentinterface/tests/test_litellmmodelclient.py \
  packages/agentinterface/tests/test_agentinterface.py \
  packages/gateway/tests/test_gateway.py \
  packages/journal/tests/test_journal.py \
  packages/tui/tests/test_tui.py -q
```

## What Is Not Ready Yet

These are not setup mistakes. They are current implementation limits:

- no standalone CLI entrypoint yet
- no production runner for the TUI yet
- no Telegram transport yet
- no scheduler runtime yet
- no first-run config generator yet
- no hot reload for config changes yet

## Source Of Truth

For the current setup model, use these docs together:

- [README.md](/home/openclaw/Projects/LocalFirstClaw/README.md)
- [docs/configuration.md](/home/openclaw/Projects/LocalFirstClaw/docs/configuration.md)
- [plans/CURRENT_HANDOFF.md](/home/openclaw/Projects/LocalFirstClaw/plans/CURRENT_HANDOFF.md)
