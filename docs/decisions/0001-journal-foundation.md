# ADR 0001: Journal Is The First Implemented Package

## Status

Accepted

## Context

LocalFirstClaw is intended to be an always-on system with multiple packages and several future runtime paths: gateway requests, scheduled jobs, reflex execution, and tool usage. All of those flows need a shared truth source for auditability, debugging, and recall.

The repo started as package scaffolding with no executable behavior.

## Decision

Implement the `journal` package first as a daily-rotated JSONL store with structured events and recent-query support.

Key parts of the decision:

- keep the multi-package workspace
- build a sync core first
- expose async-compatible wrappers
- use UTC timestamps
- require `agent_id` on events
- require `correlation_id` on written events, generating one when omitted
- support deterministic human-style time expressions for query bounds
- keep v1 storage simple and file-based

## Consequences

Positive:

- every later package can emit durable structured events immediately
- debugging and review can be built on a real substrate instead of placeholders
- the event model becomes an early integration contract across packages

Tradeoffs:

- the first milestone is infrastructure rather than a visible runtime app
- cross-process coordination is deferred
- retention and indexing are postponed until real usage data exists

## Follow-On Work

- make `gateway` and `hypothalamus` emit journal events by default
- add review and recall helpers in `tools`
- revisit retention, compression, and cross-process safety once real workloads exist
