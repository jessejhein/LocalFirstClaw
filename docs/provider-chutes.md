# Chutes Provider Notes

This document records the current Chutes integration findings for LocalFirstClaw.

The goal is to capture the API shape, config pattern, model discovery method, and a practical recommendation for which Chutes model to use for lightweight orchestration tasks.

## What Was Verified

Verified on 2026-03-17:

- the Chutes OpenAI-compatible base URL works at `https://llm.chutes.ai/v1`
- the model catalog is available at `https://llm.chutes.ai/v1/models`
- LocalFirstClaw can successfully call Chutes through LiteLLM when the model id is correct
- `moonshotai/Kimi-K2.5-TEE` responded successfully during a live end-to-end test

## API Shape

Chutes is usable through an OpenAI-compatible interface.

Current pattern:

- base URL: `https://llm.chutes.ai/v1`
- model list endpoint: `https://llm.chutes.ai/v1/models`
- auth: bearer token using `CHUTES_API_KEY`

For LocalFirstClaw's LiteLLM integration, the provider model should be configured with the `openai/` prefix because LiteLLM needs the provider family made explicit.

Example:

```yaml
aliases:
  kimi:
    provider_model: openai/moonshotai/Kimi-K2.5-TEE
    api_base: https://llm.chutes.ai/v1
    api_key_env: CHUTES_API_KEY
```

## How To Get The Current Model List

There are two currently verified ways.

### Direct Provider Query

```bash
.venv/bin/python - <<'PY'
import json
import os
import urllib.request

request = urllib.request.Request(
    'https://llm.chutes.ai/v1/models',
    headers={'Authorization': f"Bearer {os.environ['CHUTES_API_KEY']}"},
)
with urllib.request.urlopen(request, timeout=30) as response:
    data = json.load(response)

for model in data['data']:
    print(model['id'])
PY
```

### Existing OpenClaw Helper Script

There is also a local helper script at:

- `/home/openclaw/openclaw-tools/bin/update-chutes-models`

That script fetches the Chutes catalog and writes it into OpenClaw's provider config.

## Current Notable Models

The following models were present in the live catalog when this document was written.

Lower-cost general interactive options:

- `Qwen/Qwen3-32B` - input `0.08`, output `0.24`, reasoning + tools
- `Qwen/Qwen3-30B-A3B` - input `0.06`, output `0.22`, reasoning + tools
- `openai/gpt-oss-20b` - input `0.03`, output `0.11`, reasoning + tools
- `NousResearch/Hermes-4-14B` - input `0.01`, output `0.05`, reasoning + tools

Stronger but more expensive options:

- `moonshotai/Kimi-K2.5-TEE` - input `0.45`, output `2.2`, reasoning + tools
- `MiniMaxAI/MiniMax-M2.5-TEE` - input `0.3`, output `1.1`, reasoning + tools
- `zai-org/GLM-5-Turbo` - input `0.49`, output `1.96`, reasoning + tools
- `zai-org/GLM-5-TEE` - input `0.95`, output `3.15`, reasoning + tools

Coding-oriented option:

- `Qwen/Qwen3-Coder-Next-TEE` - input `0.12`, output `0.75`, tools, no reasoning flag in the catalog

Vision-capable low-cost option:

- `chutesai/Mistral-Small-3.2-24B-Instruct-2506` - input `0.06`, output `0.18`, text + image

## Recommendation For The AoE Relay Role

Kimi is probably overkill for the narrow role you described.

For an AoE-style orchestrator that:

- relays status to the user
- stays interactive
- performs light routing/orchestration
- does not need deep long-horizon reasoning on every turn

the current best default starting point is:

- `Qwen/Qwen3-30B-A3B`

Reason:

- materially cheaper than Kimi
- still carries the `reasoning` and `tools` flags in the live catalog
- should be strong enough for short interactive summaries, coordination, and relay behavior

If you want a slightly safer quality margin while staying far below Kimi cost, use:

- `Qwen/Qwen3-32B`

If you want the absolute cheapest thing that still looks plausible for lightweight relay work, test:

- `openai/gpt-oss-20b`

I would reserve:

- `moonshotai/Kimi-K2.5-TEE`

for higher-value tasks like synthesis, harder planning, or fallback when the cheaper orchestrator model is clearly not holding up.

This recommendation is an inference from the live Chutes model catalog, reported pricing, advertised capability flags, and the stated task shape. It is not yet backed by side-by-side task benchmarking inside LocalFirstClaw.

## Suggested Config Pattern

For a cheap default plus premium fallback later, use aliases like:

```yaml
aliases:
  relay:
    provider_model: openai/Qwen/Qwen3-30B-A3B
    api_base: https://llm.chutes.ai/v1
    api_key_env: CHUTES_API_KEY

  relay_plus:
    provider_model: openai/Qwen/Qwen3-32B
    api_base: https://llm.chutes.ai/v1
    api_key_env: CHUTES_API_KEY

  premium:
    provider_model: openai/moonshotai/Kimi-K2.5-TEE
    api_base: https://llm.chutes.ai/v1
    api_key_env: CHUTES_API_KEY
```

Then bind agents by role rather than treating one model as universal.

## Current External Setup

The live LocalFirstClaw config currently uses:

```yaml
aliases:
  kimi:
    provider_model: openai/moonshotai/Kimi-K2.5-TEE
    api_base: https://llm.chutes.ai/v1
    api_key_env: CHUTES_API_KEY
```

That was proven to work end to end on 2026-03-17.
