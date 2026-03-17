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
2. Determine the chat binding:
   - private chat: `chat:<chat_id>`
   - forum topic or thread: `thread:<chat_id>:<message_thread_id>`
3. Add a matching Telegram endpoint entry to `~/.config/LocalFirstClaw/endpoints.yaml`.
4. Start the runner with `localfirstclaw run-telegram --once` or `localfirstclaw run-telegram`.

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

- no automatic endpoint creation from unknown Telegram chats yet
- no automatic chat id discovery helper command yet
- no send retry/backoff strategy yet
- no process supervisor wrapper yet

For the live test, manual endpoint config is still required.
