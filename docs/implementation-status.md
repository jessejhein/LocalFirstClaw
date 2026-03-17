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

Not implemented yet:

- gateway runtime
- agent interface behavior beyond package scaffolding
- scheduler runtime
- file-based assistant workspace
- retention/compression policy
- cross-process journal locking
- provider fallback routing

## Immediate Next Step

Build the next package on top of the journal rather than bypassing it.

Recommended order:

1. Define the first consumer interface in `agentinterface` or `gateway`.
2. Require that meaningful runtime actions emit journal events.
3. Add higher-level recall/review helpers in `tools` once real query patterns exist.

## Constraints To Preserve

- Keep package boundaries explicit.
- Keep the journal append-only.
- Keep time parsing deterministic inside the journal package.
- Preserve required `agent_id` and `correlation_id` on written events.
- Treat journal write failures as explicit errors, not silent drops.
