# LocalFirstClaw Docs

This directory is the working documentation set for the codebase.

## Current Documents

- `agentinterface.md` - Agent execution contract and journaling behavior.
- `configuration.md` - External config/data layout and YAML file formats.
- `gateway.md` - Gateway routing model, commands, and API surface.
- `journal.md` - Public API and behavior for the journal package.
- `provider-chutes.md` - Chutes API notes, model discovery, and current model recommendations.
- `tui.md` - Local terminal interface behavior and rendering rules.
- `SETUP.md` at repo root - First-run setup and validation steps for operators and other agents.
- `implementation-status.md` - What exists now and what should come next.
- `decisions/0001-journal-foundation.md` - Why the project starts with the journal package.

## Documentation Rules

- Update docs in the same change set as API or behavior changes.
- Record durable design choices in `docs/decisions/`.
- Keep this directory understandable to both human contributors and LLM agents.
