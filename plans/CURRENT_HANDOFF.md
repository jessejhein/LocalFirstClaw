# Current Handoff

This document is the current implementation handoff for LocalFirstClaw. It is intended to let another human or agent resume work without reconstructing context from chat history.

## Executive Summary

LocalFirstClaw is still early-stage, but four real subsystems and the first external-config bootstrap layer are now implemented:

- `journal`
- the first `gateway` slice
- the first `agentinterface` slice
- the first `tui` slice

The repo started as a multi-package Python workspace with plans and scaffolding only. The completed execution slices established:

- a working project-level `uv` environment
- working workspace package resolution
- a tested `journal` package
- a tested in-memory `gateway` routing core with a minimal FastAPI shell
- a tested `agentinterface` package with typed execution and journaling
- a tested local `tui` package for end-to-end terminal interaction
- XDG-style external config/data path resolution
- YAML-backed config loading for agents, channels, endpoints, and model aliases
- bootstrap helpers that build runtime objects from external config
- a tested LiteLLM-backed model client with alias support
- a tested root CLI for setup validation and zero-token provider checks
- a tested plugin contract with on-demand self-description and maintenance guidance
- an initial Telegram transport plugin that documents config/use and normalizes Telegram bindings
- a tested Telegram transport runner that polls updates and sends replies through the gateway
- CLI onboarding helpers for Telegram discovery and binding
- initial documentation and a design record trail

The next recommended slice is to add first-run config scaffolding and then connect the next real transport or runtime layer.

## Current Repository State

Current branch:

- `master`

Recent commits, newest first:

- `3b47b40` `Connect gateway routing to agent execution and tui`
- `a097144` `Add gateway-agent and tui failing tests`
- `1a9d6e8` `Document agent interface execution contract`
- `6da32d1` `Implement journaled agent interface execution`
- `4ba351a` `Add failing tests for agent interface execution`
- `ad3359f` `Expand package docstrings for journal and gateway`
- `1dcaa57` `Document gateway routing and updated project status`
- `a8c2ed3` `Implement gateway channel routing core`

Worktree status at handoff time:

- clean after the last committed slice

## Workspace Layout

Top-level areas:

- `packages/agentinterface`
- `packages/gateway`
- `packages/hypothalamus`
- `packages/journal`
- `packages/tools`
- `packages/tui`
- `docs`
- `plans`

Implementation reality:

- `journal` contains real code and tests
- `gateway` contains real code and tests
- `agentinterface` contains real code and tests
- `tui` contains real code and tests
- `hypothalamus` and `tools` are still scaffolds

Important top-level files:

- [AGENTS.md](/home/openclaw/Projects/LocalFirstClaw/AGENTS.md)
- [README.md](/home/openclaw/Projects/LocalFirstClaw/README.md)
- [pyproject.toml](/home/openclaw/Projects/LocalFirstClaw/pyproject.toml)
- [uv.lock](/home/openclaw/Projects/LocalFirstClaw/uv.lock)

## Environment And Tooling

Project environment:

- a project-local `.venv` exists
- the repo is managed with `uv`
- the workspace uses `tool.uv.workspace`
- local workspace package sources are declared in `tool.uv.sources`

Important environment details:

- `UV_CACHE_DIR=.uv-cache`
- `UV_PYTHON_INSTALL_DIR=.uv-python`
- root package stub exists at [src/localfirstclaw/__init__.py](/home/openclaw/Projects/LocalFirstClaw/src/localfirstclaw/__init__.py) so the root project can install cleanly
- live config should be stored under `~/.config/LocalFirstClaw`
- generated data should be stored under `~/.local/share/LocalFirstClaw`

Lint and format decisions:

- use `ruff + black`
- line length target is `120`

## Governing Decisions Already Made

These decisions are settled unless there is a strong reason to reopen them:

- keep the multi-package workspace
- preserve clean package boundaries rather than collapsing packages early
- implement `journal` first
- defer the file-based assistant `workspace/` until core packages are stable
- keep live config and workspace outside the source repo
- keep generated data outside the source repo
- start with plain LiteLLM later, not router complexity on day one
- log provider/runtime failures as structured journal events
- keep the journal append-only
- use daily-rotated JSONL instead of a single monolithic file
- use structured core fields with a freeform payload
- require `agent_id`
- require `correlation_id` on written events, generating one if omitted
- use UTC ISO 8601 timestamps
- support deterministic human-style time expressions, not LLM-based parsing
- keep retention/compression out of v1
- treat journal write failures as explicit errors, not silent best effort
- treat transport rooms, threads, and chats as interface endpoints, not internal channels
- use `!CMD` for gateway commands
- reserve bare `@channel` for endpoint active-channel switching
- keep endpoint primary channel separate from runtime active channel
- keep agent execution behind the typed `AgentRequest`/`AgentResponse` boundary
- keep TUI input flowing through gateway rather than adding a side path

Decision records and design docs:

- [docs/decisions/0001-journal-foundation.md](/home/openclaw/Projects/LocalFirstClaw/docs/decisions/0001-journal-foundation.md)
- [plans/GATEWAY_CHANNEL_ROUTING.md](/home/openclaw/Projects/LocalFirstClaw/plans/GATEWAY_CHANNEL_ROUTING.md)

## What Was Implemented

Implemented journal package:

- [packages/journal/src/journal/__init__.py](/home/openclaw/Projects/LocalFirstClaw/packages/journal/src/journal/__init__.py)
- [packages/journal/src/journal/journal.py](/home/openclaw/Projects/LocalFirstClaw/packages/journal/src/journal/journal.py)
- [packages/journal/src/journal/journalevent.py](/home/openclaw/Projects/LocalFirstClaw/packages/journal/src/journal/journalevent.py)
- [packages/journal/src/journal/journalquery.py](/home/openclaw/Projects/LocalFirstClaw/packages/journal/src/journal/journalquery.py)
- [packages/journal/src/journal/journallevel.py](/home/openclaw/Projects/LocalFirstClaw/packages/journal/src/journal/journallevel.py)
- [packages/journal/src/journal/journalerrors.py](/home/openclaw/Projects/LocalFirstClaw/packages/journal/src/journal/journalerrors.py)
- [packages/journal/src/journal/journaltimeparser.py](/home/openclaw/Projects/LocalFirstClaw/packages/journal/src/journal/journaltimeparser.py)
- [packages/journal/src/journal/journalwriteresult.py](/home/openclaw/Projects/LocalFirstClaw/packages/journal/src/journal/journalwriteresult.py)

Implemented journal test file:

- [packages/journal/tests/test_journal.py](/home/openclaw/Projects/LocalFirstClaw/packages/journal/tests/test_journal.py)

Implemented gateway package:

- [packages/gateway/src/gateway/__init__.py](/home/openclaw/Projects/LocalFirstClaw/packages/gateway/src/gateway/__init__.py)
- [packages/gateway/src/gateway/gatewayrouter.py](/home/openclaw/Projects/LocalFirstClaw/packages/gateway/src/gateway/gatewayrouter.py)
- [packages/gateway/src/gateway/createapp.py](/home/openclaw/Projects/LocalFirstClaw/packages/gateway/src/gateway/createapp.py)
- [packages/gateway/src/gateway/channelconfig.py](/home/openclaw/Projects/LocalFirstClaw/packages/gateway/src/gateway/channelconfig.py)
- [packages/gateway/src/gateway/interfaceendpointconfig.py](/home/openclaw/Projects/LocalFirstClaw/packages/gateway/src/gateway/interfaceendpointconfig.py)
- [packages/gateway/src/gateway/endpointruntimestate.py](/home/openclaw/Projects/LocalFirstClaw/packages/gateway/src/gateway/endpointruntimestate.py)
- [packages/gateway/src/gateway/endpointstatus.py](/home/openclaw/Projects/LocalFirstClaw/packages/gateway/src/gateway/endpointstatus.py)
- [packages/gateway/src/gateway/gatewayresult.py](/home/openclaw/Projects/LocalFirstClaw/packages/gateway/src/gateway/gatewayresult.py)
- [packages/gateway/src/gateway/messageinput.py](/home/openclaw/Projects/LocalFirstClaw/packages/gateway/src/gateway/messageinput.py)

Implemented gateway test file:

- [packages/gateway/tests/test_gateway.py](/home/openclaw/Projects/LocalFirstClaw/packages/gateway/tests/test_gateway.py)

Implemented agentinterface package:

- [packages/agentinterface/src/agentinterface/__init__.py](/home/openclaw/Projects/LocalFirstClaw/packages/agentinterface/src/agentinterface/__init__.py)
- [packages/agentinterface/src/agentinterface/agentconfig.py](/home/openclaw/Projects/LocalFirstClaw/packages/agentinterface/src/agentinterface/agentconfig.py)
- [packages/agentinterface/src/agentinterface/agentinterface.py](/home/openclaw/Projects/LocalFirstClaw/packages/agentinterface/src/agentinterface/agentinterface.py)
- [packages/agentinterface/src/agentinterface/agentmessage.py](/home/openclaw/Projects/LocalFirstClaw/packages/agentinterface/src/agentinterface/agentmessage.py)
- [packages/agentinterface/src/agentinterface/agentrequest.py](/home/openclaw/Projects/LocalFirstClaw/packages/agentinterface/src/agentinterface/agentrequest.py)
- [packages/agentinterface/src/agentinterface/agentresponse.py](/home/openclaw/Projects/LocalFirstClaw/packages/agentinterface/src/agentinterface/agentresponse.py)
- [packages/agentinterface/src/agentinterface/agentrunerror.py](/home/openclaw/Projects/LocalFirstClaw/packages/agentinterface/src/agentinterface/agentrunerror.py)
- [packages/agentinterface/src/agentinterface/litellmmodelalias.py](/home/openclaw/Projects/LocalFirstClaw/packages/agentinterface/src/agentinterface/litellmmodelalias.py)
- [packages/agentinterface/src/agentinterface/litellmmodelclient.py](/home/openclaw/Projects/LocalFirstClaw/packages/agentinterface/src/agentinterface/litellmmodelclient.py)
- [packages/agentinterface/src/agentinterface/modelclient.py](/home/openclaw/Projects/LocalFirstClaw/packages/agentinterface/src/agentinterface/modelclient.py)
- [packages/agentinterface/src/agentinterface/modelresult.py](/home/openclaw/Projects/LocalFirstClaw/packages/agentinterface/src/agentinterface/modelresult.py)

Implemented agentinterface test file:

- [packages/agentinterface/tests/test_agentinterface.py](/home/openclaw/Projects/LocalFirstClaw/packages/agentinterface/tests/test_agentinterface.py)

Implemented tui package:

- [packages/tui/src/tui/__init__.py](/home/openclaw/Projects/LocalFirstClaw/packages/tui/src/tui/__init__.py)
- [packages/tui/src/tui/tuisession.py](/home/openclaw/Projects/LocalFirstClaw/packages/tui/src/tui/tuisession.py)

Implemented tui test file:

- [packages/tui/tests/test_tui.py](/home/openclaw/Projects/LocalFirstClaw/packages/tui/tests/test_tui.py)

Implemented root bootstrap/config package files:

- [src/localfirstclaw/apppaths.py](/home/openclaw/Projects/LocalFirstClaw/src/localfirstclaw/apppaths.py)
- [src/localfirstclaw/configloader.py](/home/openclaw/Projects/LocalFirstClaw/src/localfirstclaw/configloader.py)
- [src/localfirstclaw/localfirstclawconfig.py](/home/openclaw/Projects/LocalFirstClaw/src/localfirstclaw/localfirstclawconfig.py)
- [src/localfirstclaw/bootstrap.py](/home/openclaw/Projects/LocalFirstClaw/src/localfirstclaw/bootstrap.py)

## Journal Package Contract

Journal public API:

- `Journal(root_directory: Path | str)`
- `append_event(event: JournalEvent) -> JournalWriteResult`
- `append_event_async(event: JournalEvent) -> JournalWriteResult`
- `query_recent(query: JournalQuery) -> list[JournalEvent]`
- `query_recent_async(query: JournalQuery) -> list[JournalEvent]`

Core event fields:

- `timestamp`
- `level`
- `event_type`
- `source`
- `agent_id`
- `correlation_id`
- `tags`
- `message`
- `payload`

Supported levels:

- `debug`
- `info`
- `warning`
- `error`
- `urgent`

Supported query filters:

- `since`
- `until`
- `now`
- `levels`
- `tags`
- `agent_ids`
- `event_types`
- `text`

Supported time expressions:

- ISO 8601 with timezone offset
- `today`
- `yesterday`
- `today at HH:MM`
- `N minutes ago`
- `N hours ago`
- `N days ago`
- `last monday` through `last sunday`

Storage behavior:

- one JSONL file per UTC day
- compact one-event-per-line JSON
- append-only file writes
- missing root directory is created on write
- missing root directory returns no results on query
- non-directory root raises explicit journal errors

Concurrency behavior:

- sync core is the source of truth
- in-process writes are serialized with a re-entrant lock
- reads take the same lock while scanning files
- async methods are compatibility wrappers over the sync core, not separate async file I/O

Known current limit:

- no cross-process locking yet

## External Config And Data Layout

Live user state should not be stored in the source checkout.

Current default layout:

- config root: `~/.config/LocalFirstClaw`
- data root: `~/.local/share/LocalFirstClaw`

Config root contents:

- `agents.yaml`
- `channels.yaml`
- `endpoints.yaml`
- `models.yaml`
- `skills/`
- `workspace/`

Data root contents:

- `journal/`
- `logs/`
- `plugins/`
- `runtime/`

Bootstrap flow:

1. resolve paths with `AppPaths.from_environment(...)`
2. create directories with `ensure_directories()`
3. load config with `load_localfirstclaw_config(...)`
4. create journal with `build_journal(...)`
5. create agent interface with `build_agent_interface(...)`
6. create gateway router with `build_gateway_router(...)`

## Gateway Package Contract

Gateway public API:

- `ChannelConfig`
- `InterfaceEndpointConfig`
- `GatewayRouter`
- `GatewayAppDependencies`
- `MessageInput`
- `create_app()`

Current gateway semantics:

- internal routing target is a `Channel`
- one transport location maps to one `InterfaceEndpoint`
- each endpoint has one primary channel
- each endpoint has one active channel at runtime
- active channel defaults to primary channel
- endpoints may allow or reject channel switching
- channels have one default agent in v1
- plain routed messages invoke the configured agent executor when one is present

Current gateway syntax:

- `!CMD` means gateway command
- bare `@channel` switches the endpoint active channel when allowed
- `!send @channel ...` routes one message without changing endpoint state
- `!reset-channel` restores the primary channel

Current FastAPI routes:

- `POST /messages`
- `GET /endpoints/{endpoint_id}`

Current gateway event types:

- `gateway.message_received`
- `gateway.channel_switched`
- `gateway.command_executed`
- `gateway.command_rejected`
- `gateway.message_routed`
- `gateway.agent_responded`

## AgentInterface Package Contract

Agentinterface public API:

- `AgentConfig`
- `AgentInterface`
- `AgentMessage`
- `AgentRequest`
- `AgentResponse`
- `AgentRunError`
- `ModelClient`
- `ModelResult`

Current agentinterface semantics:

- requests target a named agent id
- agent configs supply `model` and `system_prompt`
- request correlation ids are generated if missing
- the system prompt is prepended before model execution
- execution lifecycle is journaled
- backend failures surface as `AgentRunError`

Current agentinterface event types:

- `agentinterface.run_started`
- `agentinterface.run_completed`
- `agentinterface.run_failed`

## TUI Package Contract

TUI public API:

- `TuiSession`

Current tui semantics:

- terminal input is always routed through `GatewayRouter.handle_message(...)`
- gateway command results are rendered as gateway output
- bare `@channel` switches are rendered as local status lines
- agent replies are rendered as `[channel] agent: text`
- the current implementation is line-oriented, not full-screen

## Verification Status

These checks passed at the end of the implementation slices:

- `.venv/bin/pytest packages/journal/tests/test_journal.py -q`
- `.venv/bin/ruff check packages/journal/src packages/journal/tests`
- `.venv/bin/black --check packages/journal/src packages/journal/tests`
- `.venv/bin/pytest packages/gateway/tests/test_gateway.py -q`
- `.venv/bin/ruff check packages/gateway/src packages/gateway/tests`
- `.venv/bin/black --check packages/gateway/src packages/gateway/tests`
- `.venv/bin/pytest packages/agentinterface/tests/test_agentinterface.py -q`
- `.venv/bin/ruff check packages/agentinterface/src packages/agentinterface/tests`
- `.venv/bin/black --check packages/agentinterface/src packages/agentinterface/tests`
- `.venv/bin/pytest packages/tui/tests/test_tui.py -q`
- `.venv/bin/ruff check packages/tui/src packages/tui/tests`
- `.venv/bin/black --check packages/tui/src packages/tui/tests`

The journal tests currently cover:

- append with generated correlation ID
- required `agent_id` validation
- metadata and text filtering
- deterministic time parsing
- thread-safe concurrent writes
- async wrapper behavior
- daily rotation by event date
- explicit write failure behavior

The gateway tests currently cover:

- endpoint primary channel defaults
- bare `@channel` switching
- routing plain text to the active channel
- invoking the agent executor on plain messages
- `!reset-channel`
- `!send @channel ...`
- `!who`
- rejecting channel switching for disallowed endpoints
- journaling gateway actions
- the minimal FastAPI route handlers

The agentinterface tests currently cover:

- prepending the configured system prompt
- returning a typed response
- journaling run start and completion
- journaling failures and raising `AgentRunError`
- async wrapper behavior

The tui tests currently cover:

- formatting plain agent replies
- formatting channel switching
- formatting gateway command output

## Documentation Already Written

Main docs:

- [docs/README.md](/home/openclaw/Projects/LocalFirstClaw/docs/README.md)
- [docs/agentinterface.md](/home/openclaw/Projects/LocalFirstClaw/docs/agentinterface.md)
- [docs/journal.md](/home/openclaw/Projects/LocalFirstClaw/docs/journal.md)
- [docs/gateway.md](/home/openclaw/Projects/LocalFirstClaw/docs/gateway.md)
- [docs/tui.md](/home/openclaw/Projects/LocalFirstClaw/docs/tui.md)
- [docs/implementation-status.md](/home/openclaw/Projects/LocalFirstClaw/docs/implementation-status.md)
- [docs/decisions/0001-journal-foundation.md](/home/openclaw/Projects/LocalFirstClaw/docs/decisions/0001-journal-foundation.md)

Use those as the current source of truth for the implemented packages. This handoff document adds cross-cutting status and next-step guidance.

## What Is Not Implemented Yet

Still scaffold-only or absent:

- `hypothalamus` runtime
- `tools` behavior
- file-based assistant `workspace/`
- retention policy
- log compression
- indexed recall/review tools
- cross-process write safety
- provider fallback routing
- real remote transport adapters
- persistent gateway config loading
- real LiteLLM-backed model execution
- Telegram transport
- richer TUI behavior

## Recommended Next Slice

Recommended priority:

1. move gateway endpoint/channel and agent definitions into persistent config
2. add a real LiteLLM-backed `ModelClient`
3. add Telegram as the next real transport

Preferred next target:

- persistent config if the goal is to lock user-facing routing and agent definitions before wider transport rollout
- LiteLLM model client if the goal is to replace fake execution with real model calls

## Suggested Execution Sequence For The Next Agent

1. read [AGENTS.md](/home/openclaw/Projects/LocalFirstClaw/AGENTS.md), this file, and the docs under `docs/`
2. inspect the current target package before designing changes
3. write failing tests first
4. commit the test-only change
5. implement the minimal code to satisfy the tests
6. run package tests and repo-relevant lint checks
7. commit implementation
8. update `docs/` and this handoff file if public API or architecture changed
9. commit docs separately

## Constraints The Next Agent Should Preserve

- do not bypass the journal for meaningful runtime actions
- do not bypass the gateway command parser for gateway-owned commands
- do not silently swallow journal write failures
- do not replace deterministic time parsing with LLM parsing inside `journal`
- do not break the multi-package workspace setup
- do not introduce speculative package coupling
- do not add retention/compression behavior to the journal unless that is the explicit task
- keep endpoint state runtime-only unless the task explicitly adds persistent config handling
- keep agent execution behind the typed `AgentRequest`/`AgentResponse` boundary
- keep TUI input flowing through gateway rather than adding a side path
- keep commit granularity aligned with the TDD flow in `AGENTS.md`

## If The Next Agent Needs To Recreate The Working Environment

Use the project venv and workspace sync flow:

- `UV_CACHE_DIR=.uv-cache UV_PYTHON_INSTALL_DIR=.uv-python uv sync`

If package dev tooling or all workspace packages are needed:

- `UV_CACHE_DIR=.uv-cache UV_PYTHON_INSTALL_DIR=.uv-python uv sync --all-packages --all-extras`

Then use tools from `.venv/bin/`.

## Short Resume Prompt For Another Agent

LocalFirstClaw is a multi-package Python workspace. `journal`, the first `gateway` slice, the first `agentinterface` slice, and the first `tui` slice are implemented and tested. The journal is a daily-rotated, append-only JSONL store with structured events, deterministic time-filter queries, in-process thread safety, and async-compatible wrappers over the sync core. The gateway models interface endpoints, channels, endpoint active-channel switching with bare `@channel`, gateway-owned `!CMD` commands, and plain-message handoff to an agent executor. The agentinterface package provides a typed execution contract, agent registry lookup, pluggable model client protocol, and journaled run lifecycle. The TUI package provides a line-oriented local interface that routes all input through the gateway. The next task should add persistent config, a real LiteLLM-backed model client, or Telegram transport using TDD and commit-first workflow. Read `AGENTS.md`, `plans/CURRENT_HANDOFF.md`, and the docs under `docs/` before changing anything.
