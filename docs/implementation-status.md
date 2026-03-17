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
- test coverage for the gateway public behavior

Not implemented yet:

- agent interface behavior beyond package scaffolding
- scheduler runtime
- file-based assistant workspace
- retention/compression policy
- cross-process journal locking
- provider fallback routing
- real transport adapters
- persistent gateway config loading
- agent execution behind routed gateway messages

## Immediate Next Step

Build the next package or runtime feature on top of the journal and gateway rather than bypassing them.

Recommended order:

1. Connect gateway routing to the first real agent execution path.
2. Move endpoint/channel definitions into persistent config.
3. Add higher-level recall/review helpers in `tools` once real query patterns exist.

## Constraints To Preserve

- Keep package boundaries explicit.
- Keep the journal append-only.
- Keep time parsing deterministic inside the journal package.
- Preserve required `agent_id` and `correlation_id` on written events.
- Treat journal write failures as explicit errors, not silent drops.
- Keep gateway command parsing separate from agent prompting.
- Preserve endpoint primary channel versus active channel semantics.
- Keep transport endpoints distinct from internal channels.
