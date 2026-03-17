# LocalFirstClaw

A Python-based personal always-on assistant system that re-creates OpenClaw's capabilities with improved cost efficiency and reliability.

## About

LocalFirstClaw is a lightweight, Python-native personal agent platform that provides an "always-on" intelligent assistant while eliminating LLM-first brittleness and high costs. The system uses a "spinal cord + hypothalamus" architecture where simple autonomous reflexes handle 95% of work, with LLM calls reserved for complex reasoning.

## Architecture

- **Spinal Cord** - Python FastAPI gateway + LiteLLM for message routing, provider normalization, and error handling
- **Hypothalamus** - APScheduler-based autonomous system handling schedules, reflex decisions, and escalation paths
- **Agent Team** - File-based workspace with per-agent personalities, rules, and memory
- **Journal System** - Append-only JSONL truth source for all actions and events
- **Log-First Memory** - Derived memory from journal entries rather than separate storage

## MVP Goals

- Fully functional always-on team with 3 agents (main, researcher, coder)
- 5-6 sample schedules demonstrating autonomous capabilities
- Core tool set including recall, scheduling, and review functionality
- Cost target: < $5-10/month at moderate usage (90%+ on cheap models)
- Git-tracked, human-editable YAML configuration

## Tech Stack

- **Python 3.12+** (LiteLLM native)
- **LiteLLM** - Provider gateway with fallback support
- **FastAPI** - API gateway and spinal cord
- **APScheduler** - Hypothalamus scheduling engine
- **Pydantic** - Data validation and structured outputs
- **YAML + JSONL** - Human-readable configuration and logging

## Project Structure

```
LocalFirstClaw/
├── packages/                    # Multi-package workspace
│   ├── gateway/                 # FastAPI spinal cord
│   ├── agentinterface/          # Pydantic + LiteLLM agent layer
│   ├── journal/                 # JSONL logging system
│   ├── tools/                   # Reusable tool library
│   ├── hypothalamus/            # Scheduling engine
│   └── tui/                     # Local terminal interface
├── docs/                       # Documentation
├── examples/                   # Example external config templates
└── plans/                      # Design documents
```

## External Runtime Layout

LocalFirstClaw keeps live user configuration and runtime data outside the source repository.

- Config and workspace root: `~/.config/LocalFirstClaw`
- Data and logs root: `~/.local/share/LocalFirstClaw`

Current default layout:

```text
~/.config/LocalFirstClaw/
├── agents.yaml
├── channels.yaml
├── endpoints.yaml
├── models.yaml
├── skills/
└── workspace/

~/.local/share/LocalFirstClaw/
├── journal/
├── logs/
├── plugins/
└── runtime/
```

Use the config tree for human-edited, git-trackable files. Use the data tree for generated, bulky, or non-git state like journals, logs, runtime files, and installed plugins.

## Development Philosophy

- **Dumb as possible**: Simple rules and reflexes over complex AI when possible
- **Logs = truth**: Everything is journaled and auditable
- **Git-tracked**: Configuration is human-editable and version-controlled
- **Modular**: Add new agents/skills by dropping files, not code changes
- **Cost-aware**: LiteLLM routing prioritizes cheap providers with smart fallbacks

## Getting Started

1. Create the project environment with `uv sync`.
2. Create the external config repo under `~/.config/LocalFirstClaw`.
3. Create the external data directories under `~/.local/share/LocalFirstClaw`.
4. Add `agents.yaml`, `channels.yaml`, `endpoints.yaml`, and `models.yaml` under the config root.
5. Set any required provider API keys in your shell environment.

See [SETUP.md](/home/openclaw/Projects/LocalFirstClaw/SETUP.md) for the full setup sequence, [configuration.md](/home/openclaw/Projects/LocalFirstClaw/docs/configuration.md) for the current file formats, and [examples/config/LocalFirstClaw](/home/openclaw/Projects/LocalFirstClaw/examples/config/LocalFirstClaw) for starter templates.

## License

See LICENSE file for details.
