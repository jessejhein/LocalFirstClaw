# Plugin System

LocalFirstClaw now has a standard plugin contract for transports and other optional integrations.

The key design rule is:

- plugin-specific setup and maintenance knowledge should be queried on demand
- agents should not carry every plugin's instructions in their default context

This keeps prompt cost down and avoids loading unused integration details.

## Current Standard

Plugins should provide:

- a manifest
- config field descriptions
- a maintenance skill or setup guide that can be requested on demand

Current capabilities used by the first plugin:

- `transport`
- `self_describe`
- `maintenance_skill`

## Operator And Agent Access

The root CLI exposes the standard query path:

```bash
localfirstclaw describe-plugin telegram
localfirstclaw plugin-skill telegram
```

Expected use:

- default agent context says "for plugin-specific setup or maintenance, query the plugin"
- the agent requests the manifest or maintenance skill only when needed
- the plugin returns its own setup and operational guidance

## Current Telegram Plugin

The first plugin is the Telegram transport plugin.

It currently provides:

- self-description and config field metadata
- maintenance/setup guidance on demand
- inbound update normalization for Telegram chat and thread messages
- outbound payload shaping for Telegram Bot API sends

Current scope does not yet include:

- live polling loop
- send/retry network client
- process runner integration
- dynamic channel attachment logic

Those come next, but the plugin contract and the on-demand documentation path are now established.
