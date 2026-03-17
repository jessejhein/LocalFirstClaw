# AgentInterface Package

The `agentinterface` package is the first execution layer that can turn routed gateway work into an agent run. It owns the typed request/response contract, agent registry lookup, pluggable model client integration, and journaled run lifecycle events.

## Purpose

- accept a structured execution request for a named agent
- look up the configured agent definition
- prepare the final message list sent to the model backend
- call a pluggable model client
- journal run start, completion, and failure

## Public API

Exported types:

- `AgentConfig`
- `AgentInterface`
- `AgentMessage`
- `AgentRequest`
- `AgentResponse`
- `AgentRunError`
- `ModelClient`
- `ModelResult`

## Agent Model

`AgentConfig` currently defines:

- `agent_id`
- `model`
- `system_prompt`

This is intentionally small. It is enough to let the gateway or later config loaders resolve a channel-attached agent into a runnable definition.

## Request And Response Model

### `AgentRequest`

Current request fields:

- `agent_id`
- `channel_id`
- `user_id`
- `endpoint_id`
- `correlation_id`
- `timestamp`
- `messages`
- `metadata`

### `AgentResponse`

Current response fields:

- `agent_id`
- `channel_id`
- `correlation_id`
- `output_text`
- `model_name`
- `finish_reason`

## Message Model

`AgentMessage` supports the roles:

- `system`
- `user`
- `assistant`
- `tool`

The current implementation prepends the configured agent `system_prompt` as the first message before invoking the model client.

## Execution Contract

Main entrypoints:

```python
run(request: AgentRequest) -> AgentResponse
run_async(request: AgentRequest) -> AgentResponse
```

Current behavior:

- unknown agent ids raise `AgentRunError`
- missing request correlation ids are generated automatically
- the configured system prompt is prepended before model execution
- backend failures raise `AgentRunError`
- successful execution returns a typed `AgentResponse`

## Model Client Abstraction

`ModelClient` is a protocol with one current required method:

```python
complete(*, model: str, messages: list[AgentMessage]) -> ModelResult
```

This keeps provider/runtime selection out of the `AgentInterface` core. The package knows how to execute an agent run, but not which concrete backend policy should be used long term.

## Journal Integration

Agent execution lifecycle is journaled through the `journal` package.

Current event types:

- `agentinterface.run_started`
- `agentinterface.run_completed`
- `agentinterface.run_failed`

Current tags:

- `agentinterface`
- `llm`

Lifecycle events currently use the request timestamp and a shared correlation id so one run can be reconstructed from the journal.

## What This Slice Does Not Do Yet

- actual LiteLLM adapter implementation
- fallback routing across models/providers
- token accounting or cost tracking
- tool calling
- memory loading
- prompt templating beyond a single system prompt
- persistent agent config loading

## Intended Next Work

- move agent definitions into persistent config
- add a real LiteLLM-backed `ModelClient`
- journal richer usage metadata once a live backend is wired in
