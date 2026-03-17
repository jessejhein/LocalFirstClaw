# Gateway Package

The `gateway` package is the first consumer built on top of the `journal` package. It provides the initial routing core for interface endpoints, channels, gateway commands, and a minimal FastAPI shell.

## Core Concepts

- `Channel`: internal routing destination with one default agent
- `InterfaceEndpoint`: one concrete transport location
- `EndpointRuntimeState`: active channel state for one endpoint
- `GatewayRouter`: in-memory routing and command execution core

Transport terms like Telegram chat, Telegram thread, Discord room, forum thread, TUI session, and Web UI session all map to `InterfaceEndpoint`.

## Current Rules

- every endpoint has exactly one primary channel
- every endpoint has exactly one active channel at a time
- active channel defaults to primary channel
- channel switching is configured per endpoint and defaults off
- agents attach to channels, not endpoints
- every channel has exactly one default agent in v1

## Routing Syntax

- `!CMD ...` means gateway command
- bare `@channel` switches the active channel for the endpoint when allowed
- plain text routes to the endpoint active channel
- `!send @channel ...` sends one message to another channel without changing active state
- `!reset-channel` restores the endpoint active channel to the endpoint primary channel

The gateway does not use `/` commands. That space is intentionally left open for future agent or transport-level conventions.

## Public API

Exported types:

- `ChannelConfig`
- `InterfaceEndpointConfig`
- `GatewayRouter`
- `GatewayAppDependencies`
- `MessageInput`
- `create_app()`

## `GatewayRouter`

Constructor:

```python
GatewayRouter(
    *,
    channels: dict[str, ChannelConfig],
    endpoints: dict[str, InterfaceEndpointConfig],
    journal: Journal,
)
```

Current methods:

```python
get_endpoint_status(endpoint_id: str) -> EndpointStatus
handle_message(
    *,
    endpoint_id: str,
    text: str,
    user_id: str,
    timestamp: datetime,
) -> GatewayResult
```

## FastAPI Surface

The current FastAPI shell is intentionally small. It wraps the routing core rather than owning routing behavior.

Routes:

- `POST /messages`
- `GET /endpoints/{endpoint_id}`

### `POST /messages`

Request body:

```json
{
  "endpoint_id": "telegram-main",
  "user_id": "user-1",
  "text": "@game",
  "timestamp": "2026-03-17T12:07:00+00:00"
}
```

Behavior:

- gateway parses commands first
- then bare `@channel` switching
- otherwise routes text to the current active channel
- when an agent executor is configured, plain routed messages invoke the target agent and return an agent reply result

### `GET /endpoints/{endpoint_id}`

Returns endpoint routing state:

- endpoint id
- transport
- binding
- primary channel id
- active channel id
- default agent id for the active channel
- whether channel switching is allowed

## Journal Integration

Gateway actions are journaled as structured events.

Current event types:

- `gateway.message_received`
- `gateway.channel_switched`
- `gateway.command_executed`
- `gateway.command_rejected`
- `gateway.message_routed`
- `gateway.agent_responded`

Common tags:

- `gateway`
- `routing`
- `command`
- `inbound`

## Current Command Set

- `!help`
- `!status`
- `!who`
- `!channels`
- `!send @channel message...`
- `!reset-channel`
- `!recent`
- `!ping`

Current note:

- some commands are placeholders that return gateway-owned responses now and can grow later without requiring an agent

## What This Slice Does Not Do Yet

- real remote transport adapters
- multi-endpoint fanout delivery
- channel membership history beyond current runtime state and journal events
- script-driven reset helpers
- resilient error handling around live agent execution

Persistent endpoint and channel config loading now exists at the application bootstrap layer rather than inside the `gateway` package itself.

## Intended Next Work

- connect real remote interface adapters
- add failure handling around agent execution
- expose richer gateway inspection and control commands
