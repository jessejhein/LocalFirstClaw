# TUI Package

The `tui` package is the first real user-facing interface for LocalFirstClaw. It is intentionally minimal: a line-oriented terminal session wrapper over the gateway router.

## Purpose

- provide a local interface for sending messages into the gateway
- render gateway command output, channel switching, and agent replies
- validate the end-to-end local flow before adding remote transports like Telegram

## Public API

Current export:

- `TuiSession`

## `TuiSession`

Current constructor fields:

- `router`
- `endpoint_id`
- `user_id`

Main method:

```python
handle_input(*, text: str, timestamp: datetime) -> list[str]
```

## Rendering Rules

Current output behavior:

- channel switch: `Switched active channel to game`
- gateway command result: `Gateway: ...`
- gateway command error: `Gateway error: ...`
- agent reply: `[channel] agent: response text`

This is intentionally simple. The package is a terminal interface, not yet a full-screen terminal application framework.

## Gateway Integration

The TUI does not bypass the gateway. Every line of user input is sent through `GatewayRouter.handle_message(...)`.

That means the TUI automatically inherits:

- `!CMD` gateway commands
- bare `@channel` active-channel switching
- agent execution on plain routed messages when the gateway has an executor configured

## What This Slice Does Not Do Yet

- full-screen terminal rendering
- input history
- async background updates
- multiple panes or channel lists
- live journal viewer
- endpoint configuration loading

## Intended Next Work

- turn the line-oriented session into a richer terminal app
- add channel/status display
- show command help inline
- surface recent journal events and system status from the terminal
