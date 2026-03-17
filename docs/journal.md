# Journal Package

The `journal` package is the first implemented subsystem in LocalFirstClaw. It provides the append-only truth layer the rest of the system will build on.

## Purpose

- Persist structured operational events as daily JSONL files.
- Provide deterministic filtering over recent events.
- Keep the storage model simple enough for direct inspection and git-friendly development.

## Public API

### `Journal`

Main file-backed journal interface.

Constructor:

```python
Journal(root_directory: Path | str)
```

Methods:

```python
append_event(event: JournalEvent) -> JournalWriteResult
append_event_async(event: JournalEvent) -> JournalWriteResult
query_recent(query: JournalQuery) -> list[JournalEvent]
query_recent_async(query: JournalQuery) -> list[JournalEvent]
```

Notes:

- The sync API is the source of truth.
- The async methods are compatibility wrappers with the same behavior and return types.
- Writes are serialized with an internal lock so concurrent threads do not corrupt the JSONL files.

### `JournalEvent`

Required fields:

- `timestamp`: timezone-aware `datetime`, normalized to UTC
- `level`: `JournalLevel`
- `event_type`: event classifier such as `provider.error`
- `source`: emitting component such as `gateway` or `hypothalamus`
- `agent_id`: emitting agent or logical actor
- `tags`: list of filterable strings
- `message`: short human-readable summary
- `payload`: structured freeform details

Optional field:

- `correlation_id`: request/job trace identifier. If missing, `append_event` generates one before write.

### `JournalQuery`

Supported filters:

- `since`
- `until`
- `now`
- `levels`
- `tags`
- `agent_ids`
- `event_types`
- `text`

`since` and `until` accept either timezone-aware datetimes or supported deterministic time expressions.

### `JournalLevel`

Supported values:

- `debug`
- `info`
- `warning`
- `error`
- `urgent`

### Exceptions

- `JournalError`: base journal exception
- `JournalWriteError`: raised when an event cannot be written
- `JournalQueryError`: raised when a query cannot be resolved or read safely

## Storage Layout

Events are written under the configured root directory as one file per UTC day:

```text
journal-root/
  2026-03-16.jsonl
  2026-03-17.jsonl
```

Each line is one compact JSON object. Files are append-only.

## Supported Time Expressions

The journal currently supports deterministic human-style time inputs for query bounds:

- ISO 8601 datetimes with timezone offsets
- `today`
- `yesterday`
- `today at HH:MM`
- `N minutes ago`
- `N hours ago`
- `N days ago`
- `last monday` through `last sunday`

This is intentionally constrained. The journal package does not use an LLM for time parsing.

## Query Semantics

- Results are sorted by event timestamp ascending.
- Tag filtering requires the query tags to be a subset of the event tags.
- Text search is case-insensitive substring matching over the event message and serialized payload.
- Querying a missing journal directory returns an empty result.
- Querying a non-directory root raises `JournalQueryError`.

## Concurrency Model

- Writes use an internal re-entrant lock.
- Reads also acquire the same lock while scanning files so partially written lines are not observed.
- The package is thread-safe for in-process use.

## Current Limits

- No retention policy beyond daily rotation.
- No compression of older files.
- No indexed search.
- No cross-process locking yet.
- Async wrappers are API-compatible wrappers over the sync core, not independent async I/O implementations.

## Expected Next Consumers

- `gateway` for inbound request and provider events
- `hypothalamus` for scheduled jobs and reflex paths
- `tools` for recall and review commands
