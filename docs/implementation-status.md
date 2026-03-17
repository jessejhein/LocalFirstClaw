# Implementation Status

## Current State

Implemented:

- `journal` package core append/query behavior
- daily-rotated JSONL storage
- structured event and query models
- deterministic time parsing for query bounds
- thread-safe in-process writes
- async-compatible wrappers
- test coverage for the journal public API
- `gateway` routing core for channels and interface endpoints
- gateway command parsing using `!CMD`
- endpoint active-channel switching using bare `@channel`
- minimal FastAPI shell for message ingress and endpoint state
- gateway journaling for inbound messages, command execution, command rejection, channel switches, and routed messages
- gateway integration that invokes agent execution for plain routed messages
- test coverage for the gateway public behavior
- `agentinterface` typed execution contract for named agents
- pluggable model client protocol and structured model result
- journaled agent run start, completion, and failure events
- test coverage for the agentinterface public behavior
- LiteLLM-backed model execution with alias support
- `tui` local line-oriented terminal session over the gateway
- test coverage for the tui public behavior
- XDG-style external config/data path resolution
- YAML-backed loading for agents, channels, endpoints, and model aliases
- bootstrap helpers that build the journal, agent interface, and gateway from persistent config

Not implemented yet:

- scheduler runtime
- file-based assistant workspace
- retention/compression policy
- cross-process journal locking
- provider fallback routing
- real transport adapters
- richer terminal UI behavior
- first-run config generation
- config hot reload

## Immediate Next Step

Build the next package or runtime feature on top of the journal and gateway rather than bypassing them.

Recommended order:

1. Add first-run config scaffolding and example installers.
2. Extend the TUI or add Telegram as the next transport.
3. Add a scheduler/runtime layer that can inspect journal and routing state.

## Constraints To Preserve

- Keep package boundaries explicit.
- Keep the journal append-only.
- Keep time parsing deterministic inside the journal package.
- Preserve required `agent_id` and `correlation_id` on written events.
- Treat journal write failures as explicit errors, not silent drops.
- Keep gateway command parsing separate from agent prompting.
- Preserve endpoint primary channel versus active channel semantics.
- Keep transport endpoints distinct from internal channels.
- Keep agent execution behind the typed request/response boundary.
- Keep TUI input flowing through gateway rather than adding a side path.
- Keep live config under `~/.config/LocalFirstClaw`.
- Keep generated data under `~/.local/share/LocalFirstClaw`.
