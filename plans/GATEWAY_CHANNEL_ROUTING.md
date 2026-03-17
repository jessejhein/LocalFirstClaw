# Gateway Channel Routing

This plan locks the current gateway design before implementation.

## Core Model

- `Channel`: internal routing destination
- `InterfaceEndpoint`: one concrete transport location
- `EndpointRuntimeState`: in-memory state for an endpoint
- `GatewayRouter`: command parser and routing core

Transport examples:

- Telegram main chat
- Telegram thread
- Discord room
- TUI session
- Web UI session

These are all `InterfaceEndpoint` instances from the gateway point of view.

## Binding Rules

- each interface endpoint has exactly one primary channel
- an endpoint may optionally allow channel switching
- channel switching defaults off unless explicitly enabled
- the first main endpoint should support channel switching by default
- each channel has exactly one default agent in v1
- agents attach to channels, not endpoints

## Routing Semantics

- endpoint active channel starts as the endpoint primary channel
- a bare `@channel` message switches the endpoint active channel
- after switching, subsequent plain messages from that endpoint route to the new active channel
- `!reset-channel` restores the endpoint active channel to its primary channel
- `!send @channel ...` routes a one-off message without changing endpoint state
- channels do not merge
- endpoint rerouting is a transport-side shortcut, not a channel-side merge

## Command Syntax

- gateway commands use `!CMD`
- slash commands are reserved for future agent or interface use, not gateway use
- normal conversation text is routed to the current endpoint active channel

Initial gateway command set:

- `!help`
- `!status`
- `!who`
- `!channels`
- `!send @channel message...`
- `!reset-channel`
- `!recent`
- `!ping`

## Persistence And Reset

- persistent defaults live in config
- runtime overrides live in memory
- meaningful runtime changes are journaled
- scripts may inspect runtime or journal state and issue resets
- inactivity reset policy is external automation, not built-in gateway policy

## First Implementation Slice

- build the routing core first
- expose it through a minimal FastAPI app
- journal inbound messages, command execution, channel switches, resets, and routed outbound intent
- keep the implementation in-memory for endpoint/channel runtime state
- defer real Telegram and Discord adapters

## First Test Surface

- endpoint defaults to its primary channel
- `@game` switches an eligible endpoint to `game`
- `!reset-channel` restores the primary channel
- `!send @channel ...` does not mutate endpoint active state
- `!who` reports primary channel, active channel, and default agent
- disallowed switching is rejected clearly
- command routing takes precedence over agent routing
- gateway actions emit journal events
