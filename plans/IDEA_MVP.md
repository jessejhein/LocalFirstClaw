**MVP Architecture Summary Document** **Personal Always-On Assistant System** **Version: MVP-1 (March 2026)** **Core Philosophy**: “Dumb as much as possible” — spinal cord + 
hypothalamus handle 95 % of work autonomously; LLM (via LiteLLM) is only the rare brain. Logs = ground truth. Everything git-trackable, YAML-configurable, cheap 
(Chutes-first), and human-editable.
### 1. High-Level Explication (Technical Overview)
The system is a lightweight, Python-native personal agent platform that re-creates the “always-on” magic of OpenClaw while eliminating its LLM-first brittleness and cost. - 
**Spinal Cord** (Python FastAPI gateway + LiteLLM) is the thin control plane: routes messages, normalizes providers (Chutes, Codex via ChatGPT subscription, OpenCode Go), 
handles callbacks/retries/fallbacks, enforces least-privilege, and writes every event to a universal append-only JSONL journal. - **Hypothalamus** (APScheduler + 
hypothalamus.yaml) is the old-school autonomic nervous system: cron-like schedules, autonomous scripts, reflex decisions (Option A = cheap LLM or Option B = pure rules), and 
two escalation paths (LOG ERROR = cheap reflex; LOG URGENT = hot-stove immediate push to main agent). - **Agent Team** lives in a simple file-tree workspace 
(`~/my-assistant/`). One global `agents.md` (constitution read by every agent), global `user.md`, per-agent folders with `soul.md` (personality), `memory.md` (curated 
summary), and `local_rules.md`. `agents_config.yaml` declares the team and default (main). - **Journal** (`journal/*.jsonl`) is the single source of truth — every heartbeat, 
reflex, reminder, LLM call, and user action is tagged and logged. - **Memory** is derived, not stored separately: nightly hypothalamus job summarizes journal tail → appends 
to each agent’s `memory.md`. A core spinal-cord tool (`recall_recent_actions`) gives instant, filterable recall (“last three things I did”) without bloating context. - **LLM 
usage** is minimized: Chutes cheap models for reflex/heartbeat, Codex only for real reasoning. LiteLLM callbacks + fallbacks keep costs predictable and failures silent unless 
truly urgent. - **Extensibility** is Unix-like: add new agents by dropping a folder + updating config; add schedules by asking the main agent (it edits YAML safely and 
reloads). The result is a reliable, low-cost, auditable system that feels like a living team of specialists rather than one expensive brain.
### 2. High-Level Summary
- **Name**: Spinal Assistant (working title) - **Language**: Python 3.12+ (LiteLLM native) - **Core Stack**: LiteLLM (provider gateway) + FastAPI (spinal cord) + APScheduler 
(hypothalamus) + YAML + JSONL journal - **Providers**: Chutes (default cheap), Codex (ChatGPT sub for heavy lifting), OpenCode Go (optional) - **Key Innovation**: 
Logs-as-memory + configurable autonomic layers (autonomous / reflex / reminder) with tags for perfect auditability - **Cost Goal**: < $5–10/month at moderate use (90 %+ 
Chutes) - **UI**: TUI (Textual/Rich) + optional WebUI (FastAPI + HTMX) - **Deployment**: Single Docker container or docker-compose (gateway + hypothalamus background) - **MVP 
Scope**: Fully functional always-on team with 3 agents (main, researcher, coder), 5–6 sample schedules, recall tool, and journal review commands.
### 3. Breakdown of Modules and Components
| Module | Responsibility | Key Files / Tech | Runs As | --------|----------------|------------------|---------| **Spinal Cord (Gateway)** | Message routing, LiteLLM calls, 
| callbacks, error normalization, journal writes, tool dispatch, least-privilege enforcement | `gateway.py` (FastAPI), `litellm_wrapper.py`, `journal_writer.py`, `tools.py` | 
| Main process (async) | **Hypothalamus** | Autonomous scheduling, job execution, reflex logic (A+B), post-process chaining, YAML reload | `hypothalamus.py` 
| (BackgroundScheduler), `hypothalamus.yaml`, `reflex_rules.yaml` | Background thread/process | **Agent Team Layer** | Personality, rules, memory curation, context loading | 
| `agents_config.yaml`, per-agent `soul.md` / `memory.md`, global `agents.md` + `user.md` | Loaded on-demand by gateway | **Journal System** | Append-only truth + tag-based 
| filtering | `journal/*.jsonl` (rotated daily/weekly), `recall_recent_actions` tool | Shared | **Tools & Skills** | Reusable actions (recall, schedule-add, git-commit, etc.) 
| | `skills/` folder (Python + shell scripts) | Called from spinal cord or hypothalamus |
| **Config & Observability** | Human-editable everything | All YAML + Markdown files; structlog + JSONL | Git-tracked workspace |
### 4. Tools Needed for Various Actions (MVP Core Set)
All tools live in the spinal cord and are callable by any agent (via standard function-calling format). They are deliberately dumb-first. - **recall_recent_actions(query, 
lookback_hours=24, max_items=10, tags=None, agents=None, level=None)**
  Core tool you requested. Filters journal by tags/time/agent/level and returns clean Markdown. Zero LLM unless query is fuzzy. - **add_schedule(name, cron_or_interval, 
jobs_list, post_process_list, tags)**
  Main agent uses this when you say “set up nightly report”. Safely appends to hypothalamus.yaml and reloads scheduler. - **review_tagged_actions(tags_list, since_days=7)** 
  “Review all autonomous actions” or “Review all main agent actions”. Returns summarized table from journal.
- **update_memory(agent_name)** Forces hypothalamus to summarize recent journal slice into the agent’s memory.md. - **run_reflex_rule_test(rule_name, data)** Debug tool for 
  Option B rules.
- **git_commit_workspace(message)** Hypothalamus or main agent can auto-commit safe changes (user preferences, new schedules). - **switch_active_agent(agent_name)** For 
  “@researcher: look up ballgame”.
- **quiet_journal_only(message, tags)** Used by reflex path for silent logging. - **escalate_urgent(message, target_agent="main")** Hot-stove path — pushes high-priority to 
  queue.
Future tools (post-MVP) can be dropped into `skills/` and declared in agents.md.
### Additional Documents I Recommend Producing Next (to make this immediately buildable)
We now have the complete high-level spec. To turn this into runnable code I suggest we create three more focused documents (I can generate any/all immediately): 1. **Full 
Starter Workspace Template** — exact folder tree + filled-in sample files (`agents.md`, `user.md`, `hypothalamus.yaml` with 6 schedules, `reflex_rules.yaml`, example soul.md 
for main agent, etc.). 2. **Python Skeleton Repo Structure** — complete file layout with working code stubs (`gateway.py`, `hypothalamus.py`, journal writer, recall tool, 
LiteLLM config for your Chutes/Codex/OpenCode stack, docker-compose.yml). 3. **Deployment & First-Run Guide** — how to clone, set API keys, run, test a heartbeat, add your 
first schedule via chat, and review tags. Just tell me the order (e.g., “give me #1 first” or “all three now”) and I’ll produce them one by one or in parallel.
We have a rock-solid MVP blueprint — ready to code. This matches every original note you gave me. What’s next?
