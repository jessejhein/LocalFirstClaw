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

The starter example now includes role-oriented aliases:

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

Recommended role split:

- `premium` for the `coordinator`
- `relay` for `coder-relay`
- `cheap` for `heartbeat`

You can edit those aliases if you want different models, but keep the provider model ids and `api_base` values valid for your provider.

## 5. Export Provider Credentials

LocalFirstClaw now supports a config-root `.env` file.

Recommended location:

- `~/.config/LocalFirstClaw/.env`

Example:

```bash
cat > ~/.config/LocalFirstClaw/.env <<'EOF'
CHUTES_API_KEY=your-real-key-here
TELEGRAM_BOT_TOKEN=your-real-telegram-bot-token
EOF
```

If your alias uses `api_key_env: CHUTES_API_KEY`, that `.env` file is enough for LocalFirstClaw commands.

Shell exports are still allowed and take precedence. For example:

```bash
export CHUTES_API_KEY=your-real-key-here
```

Do not store live API keys in the YAML files.

Naming rule:

- do not give an agent the same identifier as a channel
- for example, use channel `main` with agent `coordinator`, not agent `main`

## 6. Validate Setup Without Spending Tokens

This checks config loading, data directories, and required environment variables.

```bash
localfirstclaw validate-setup
```

If that reports `Setup validation passed.`, the current bootstrap layer is loadable.

## 7. Zero-Token Provider Connectivity Check

This validates that Chutes is reachable and the API key works by hitting the provider metadata endpoint instead of a completion endpoint.

```bash
localfirstclaw check-provider chutes
```

This should be safe to run frequently because it checks the model catalog, not a chat completion.

## 8. Optional Paid Completion Test

Only run this if you explicitly want to prove the configured model can answer a prompt. This may incur provider cost.

```bash
.venv/bin/python - <<'PY'
from datetime import UTC, datetime

from agentinterface import AgentMessage, AgentRequest
from localfirstclaw import AppPaths, build_agent_interface, build_journal, load_localfirstclaw_config

paths = AppPaths.from_environment()
config = load_localfirstclaw_config(config_root=paths.config_root)
journal = build_journal(app_paths=paths)
agent_interface = build_agent_interface(config=config, journal=journal)

response = agent_interface.run(
    request=AgentRequest(
        agent_id='coordinator',
        channel_id='main',
        user_id='setup-test',
        endpoint_id='tui-main',
        timestamp=datetime.now(UTC),
        messages=[AgentMessage(role='user', content='Reply with exactly: LOCALFIRSTCLAW_OK')],
    )
)
print(response.output_text)
PY
```

## 9. Optional Test Verification

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

- no production runner for the TUI yet
- no scheduler runtime yet
- no first-run config generator yet
- no hot reload for config changes yet
- no automatic Telegram chat discovery inside `endpoints.yaml` without using the CLI onboarding commands

## CLI Commands Added For Setup

- `localfirstclaw validate-setup`
  Validates config files, data directories, and required environment variables.
- `localfirstclaw validate-setup --check-providers`
  Also calls provider metadata endpoints. This should not use completion tokens.
- `localfirstclaw check-provider chutes`
  Performs a zero-token Chutes reachability check against the `/models` endpoint.
- `localfirstclaw describe-plugin telegram`
  Prints the Telegram plugin manifest and config field descriptions.
- `localfirstclaw plugin-skill telegram`
  Prints the Telegram plugin's setup and maintenance guidance on demand.
- `localfirstclaw telegram-discover`
  Polls Telegram once and lists candidate `chat:` or `thread:` bindings.
- `localfirstclaw telegram-bind ...`
  Writes a Telegram endpoint entry into `endpoints.yaml`.
- `localfirstclaw telegram-onboard ...`
  Shows discovered bindings and then writes the selected endpoint config. If exactly one binding was discovered, it can bind automatically without an explicit `--binding`.
- `localfirstclaw run-telegram --once`
  Polls Telegram once and routes any matching updates through the gateway.
- `localfirstclaw run-telegram`
  Runs the Telegram polling loop continuously.

These commands load fallback secrets from `~/.config/LocalFirstClaw/.env`, so they do not require you to pre-source the shell every time.

## Source Of Truth

For the current setup model, use these docs together:

- [README.md](/home/openclaw/Projects/LocalFirstClaw/README.md)
- [docs/configuration.md](/home/openclaw/Projects/LocalFirstClaw/docs/configuration.md)
- [plans/CURRENT_HANDOFF.md](/home/openclaw/Projects/LocalFirstClaw/plans/CURRENT_HANDOFF.md)
