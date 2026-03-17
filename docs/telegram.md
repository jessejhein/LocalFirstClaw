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
cd /home/openclaw/Projects/LocalFirstClaw
.venv/bin/localfirstclaw run-telegram --once
```

For continuous operation:

```bash
cd /home/openclaw/Projects/LocalFirstClaw
.venv/bin/localfirstclaw run-telegram
```

Setup and discovery commands:

```bash
cd /home/openclaw/Projects/LocalFirstClaw
.venv/bin/localfirstclaw telegram-discover
.venv/bin/localfirstclaw telegram-bind --endpoint-id telegram-main --binding chat:123456789 --channel main --allow-channel-switching
.venv/bin/localfirstclaw telegram-onboard --endpoint-id telegram-main --channel main --allow-channel-switching
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
cd /home/openclaw/Projects/LocalFirstClaw
.venv/bin/localfirstclaw telegram-discover
```

3. Determine the chat binding:
   - private chat: `chat:<chat_id>`
   - forum topic or thread: `thread:<chat_id>:<message_thread_id>`
4. Bind that chat or thread to a channel:

```bash
cd /home/openclaw/Projects/LocalFirstClaw
.venv/bin/localfirstclaw telegram-bind --endpoint-id telegram-main --binding chat:123456789 --channel main --allow-channel-switching
```

5. Start the runner with `localfirstclaw run-telegram --once` or `localfirstclaw run-telegram`.

If you want one command that shows discoveries and then writes the binding you selected, use:

```bash
cd /home/openclaw/Projects/LocalFirstClaw
.venv/bin/localfirstclaw telegram-onboard --endpoint-id telegram-main --channel main --allow-channel-switching
```

If exactly one chat or thread was discovered, `telegram-onboard` binds it automatically. If multiple candidates were discovered, rerun it with an explicit `--binding` value.

## Agent Guidance

If an agent is helping with Telegram onboarding, it should keep the user moving through the whole flow rather than stopping after the token exists.

Minimum question flow:

1. Do you already have a BotFather token, or do you need the BotFather steps?
2. Have you already sent a Telegram message to the bot from the chat or thread you want to bind?
3. Which LocalFirstClaw channel should this bind to first, usually `main`?
4. Should this endpoint allow `@channel` switching?
5. After binding, should I run one polling pass or start the continuous Telegram runner?

If the user has not yet sent a message to the bot, the agent should ask them to do that before running discovery.

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
cd /home/openclaw/Projects/LocalFirstClaw
.venv/bin/localfirstclaw describe-plugin telegram
.venv/bin/localfirstclaw plugin-skill telegram
```

That returns the Telegram plugin manifest and the maintenance/setup guide on demand.

## Current Limitations

- no send retry/backoff strategy yet
- no process supervisor wrapper yet
