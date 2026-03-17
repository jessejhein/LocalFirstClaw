# Telegram Transport

This document explains how to connect LocalFirstClaw to Telegram from the user perspective and how an agent can guide that setup on demand.

## What Exists Now

Current Telegram support includes:

- a self-describing Telegram plugin
- a Telegram polling runner
- normalization of Telegram chats and Telegram threads into gateway endpoint bindings
- outbound replies back to Telegram through the Bot API

Current runner command:

```bash
localfirstclaw run-telegram --once
```

For continuous operation:

```bash
localfirstclaw run-telegram
```

Setup and discovery commands:

```bash
localfirstclaw telegram-discover
localfirstclaw telegram-bind --endpoint-id telegram-main --binding chat:123456789 --channel main --allow-channel-switching
localfirstclaw telegram-onboard --endpoint-id telegram-main --channel main --allow-channel-switching
```

## BotFather Setup

1. Open Telegram.
2. Start a chat with `@BotFather`.
3. Run `/newbot`.
4. Follow BotFather's prompts for:
   - bot display name
   - bot username
5. Copy the bot token BotFather returns.
6. Store the token in `~/.config/LocalFirstClaw/.env`:

```bash
cat >> ~/.config/LocalFirstClaw/.env <<'EOF'
TELEGRAM_BOT_TOKEN=your-real-bot-token
EOF
```

Shell exports are also allowed, but the config-root `.env` file is the preferred setup path.

If you regenerate the token later with BotFather, update the `.env` file or shell environment before restarting the Telegram runner.

## First Connection Flow

1. Message your bot from the Telegram chat you want LocalFirstClaw to use.
2. Run:

```bash
localfirstclaw telegram-discover
```

3. Determine the chat binding:
   - private chat: `chat:<chat_id>`
   - forum topic or thread: `thread:<chat_id>:<message_thread_id>`
4. Bind that chat or thread to a channel:

```bash
localfirstclaw telegram-bind --endpoint-id telegram-main --binding chat:123456789 --channel main --allow-channel-switching
```

5. Start the runner with `localfirstclaw run-telegram --once` or `localfirstclaw run-telegram`.

If you want one command that shows discoveries and then writes the binding you selected, use:

```bash
localfirstclaw telegram-onboard --endpoint-id telegram-main --channel main --allow-channel-switching
```

If exactly one chat or thread was discovered, `telegram-onboard` binds it automatically. If multiple candidates were discovered, rerun it with an explicit `--binding` value.

## Endpoint Config Example

Private chat bound to the `main` channel:

```yaml
endpoints:
  - endpoint_id: telegram-main
    transport: telegram
    binding: chat:123456789
    primary_channel_id: main
    allow_channel_switching: true
```

Telegram thread bound to a coding channel:

```yaml
endpoints:
  - endpoint_id: telegram-lfc
    transport: telegram
    binding: thread:-100200300400:77
    primary_channel_id: lfc
    allow_channel_switching: false
```

## Discoverability For Agents

Agents should not keep Telegram setup instructions permanently in context.

Instead, they can query:

```bash
localfirstclaw describe-plugin telegram
localfirstclaw plugin-skill telegram
```

That returns the Telegram plugin manifest and the maintenance/setup guide on demand.

## Current Limitations

- no send retry/backoff strategy yet
- no process supervisor wrapper yet
