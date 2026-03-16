### Document 1: Full Starter Workspace Template
**Folder structure & file contents** (Everything is plain text / Markdown / YAML so a junior coder can immediately understand and edit.) ``` my-assistant/ # git init here ├── 
.gitignore # standard python + logs ├── README.md # quick start notes (see below) ├── agents.md # GLOBAL RULES — every agent must obey ├── user.md # GLOBAL — about you ├── 
agents_config.yaml # declares the team ├── hypothalamus.yaml # autonomic nervous system config ├── reflex_rules.yaml # Option B — pure rules reflex (no LLM) ├── journal/ # 
will be created at runtime │ └── .gitkeep # so git tracks the folder ├── skills/ # shared executable pieces │ ├── check_api_status.sh # example shell skill │ └── 
system_health.py # example python skill └── main/ # default agent — the one you talk to
    ├── soul.md ├── memory.md # starts empty, gets appended └── local_rules.md # optional overrides (usually empty) ```
#### File contents (copy-paste ready)
**README.md** ```markdown
# Spinal Assistant MVP
Always-on personal assistant — spinal cord + hypothalamus + agent team.
## Quick Start (for coding agent)
1. `pip install fastapi uvicorn litellm apscheduler pyyaml structlog python-dotenv` 2. Create `.env` with your API keys: ``` CHUTES_API_KEY=sk-... OPENAI_API_KEY=sk-...  # 
   for Codex via ChatGPT-linked key
   # optional: others
   ``` 3. Run: `uvicorn gateway:app --reload` 4. Talk to it via curl / WebSocket / whatever frontend you build first. Philosophy: Dumb body first. LLM only when reasoning 
needed. Logs = truth. Workspace is git-tracked. Edit YAML/MD files to change behavior. ``` **agents.md** (global constitution — read by EVERY agent at load & every 5–10 min) 
```markdown
# Global Agent Constitution
## Hard Rules — Never Violate
1. Least privilege: Never send email, post on social, delete files, spend money, or access private data without explicit user command containing the word "EXECUTE" or "SEND". 
2. No infinite loops or runaway costs: max 3 LLM calls per user message unless user says "continue deeply". 3. Silent by default: only speak when spoken to or when LOG URGENT 
is triggered. 4. Journal everything: every action, decision, error goes to journal/ with tags. 5. Escalate when unsure: prefer LOG ERROR (cheap reflex) over guessing. 6. 
Respect user.md preferences above all other instructions.
## Allowed Autonomous Actions
- Read/write own memory.md and journal - Run hypothalamus-defined scripts - Switch to specialist agents when tagged (@researcher, @coder) - Summarize journal slices into 
memory.md (nightly)
## Forbidden Without User Override
- Accessing external APIs outside LiteLLM fallbacks - Modifying system files outside workspace - Impersonating user ``` **user.md** (global — about you; edit freely) 
```markdown
# User Profile
Name: [Your Name] Preferred name for assistant: Hey / Assistant / whatever you like Communication style: concise, technical, no emojis unless I use them Notification 
preference: silent journal for routine, only ping me on URGENT Important facts: - I care deeply about keeping API costs under $10/month - I value auditability — always prefer 
logs over hidden state - Ballgames (especially [your team]) are a recurring interest - I dislike verbose responses; summarize unless asked for detail Last known preferences 
(auto-updated by system): - Silent quota warnings preferred ``` **agents_config.yaml** ```yaml default_agent: main agents:
  main: directory: main enabled: true primary_model: chutes/glm-5 # cheap default fallback_model: openai/gpt-4o-mini # Codex-like when needed description: "The friendly 
    always-on interface you talk to"
  researcher: directory: researcher # create folder later enabled: false # enable when ready primary_model: chutes/kimi-k2.5 description: "Deep research & lookup specialist" 
  coder:
    directory: coder enabled: false primary_model: openai/gpt-5.1-codex # heavy reasoning description: "Code writing & debugging specialist" ``` **hypothalamus.yaml** (6 
realistic example schedules) ```yaml global:
  journal_path: journal/main.jsonl default_cheap_model: chutes/glm-5-mini reflex_rules_file: reflex_rules.yaml heartbeat_agent: prompt_template: | You are reflex summarizer. 
    Fast. No creativity. Input: {data} Output ONLY one line: LOG ERROR: {one sentence summary} or LOG URGENT: {one sentence summary} Default to ERROR if borderline.
schedules: - name: nightly_system_report tags: [autonomous, health, nightly] trigger: cron cron: "0 2 * * *" jobs: - type: python module: skills.system_health function: 
        collect_metrics
    post_process: - type: script_low module: skills.system_health function: collect_metrics - type: reflex reflex_mode: rules # Option B first - type: post_script command: 
        echo "Nightly done" >> journal/nightly.log
      - type: reminder if: URGENT target_agent: main message_prefix: "Nightly health alert: " - name: quota_check_30min tags: [autonomous, cost, monitoring] trigger: interval 
    seconds: 1800 post_process:
      - type: reflex reflex_mode: llm - type: reminder if: URGENT target_agent: main message_prefix: "API quota critical: " - name: daily_memory_summarize tags: [autonomous, 
    memory, daily] trigger: cron cron: "0 4 * * *" post_process:
      - type: script_low function: summarize_journal_tail args: {hours: 24, target_agent: main} - type: post_script command: git add memory.md && git commit -m "auto: nightly 
        memory update" || true
  - name: morning_ballgame_reminder tags: [reminder, sports] trigger: cron cron: "0 8 * * *" post_process: - type: reminder target_agent: researcher message: "Check today's 
        ballgame results and standings"
  - name: low_disk_alert tags: [autonomous, health] trigger: interval seconds: 3600 post_process: - type: reflex reflex_mode: rules - name: user_defined_example tags: 
    [user-added, example] trigger: cron cron: "*/15 * * * *" post_process:
      - type: script_low command: date - type: reminder if: always target_agent: main ``` **reflex_rules.yaml** (Option B — pure rules, no tokens) ```yaml rules: - pattern: 
  "quota.*<.*10"
    action: LOG URGENT extra: switch_to_kimi - pattern: "disk.*>.*90" action: LOG URGENT extra: run_cleanup_script - pattern: ".*" action: LOG ERROR # default catch-all ``` 
**main/soul.md** (example personality for main agent) ```markdown
# Soul of Main Agent
You are a calm, technical, concise companion. Think like a senior sysadmin who prefers logs and facts over speculation. Tone: dry, precise, slightly dry humor only when user 
starts it. Goal: keep costs low, system reliable, user informed without noise. Never apologize excessively. Never add fluff. When unsure → journal + LOG ERROR rather than 
guess. ``` **main/memory.md** (starts empty — hypothalamus appends) ```markdown
# Main Agent Memory
(initially empty — will be populated by nightly summarizer) ``` **skills/check_api_status.sh** (example shell skill) ```bash
#!/usr/bin/env bash
echo "Checking Chutes & OpenAI status..."
# In real impl → curl health endpoints or LiteLLM status
echo "OK - $(date)" ``` **skills/system_health.py** (example python skill) ```python def collect_metrics(include_quotas=True, **kwargs): import psutil data = { "cpu_percent": 
        psutil.cpu_percent(), "disk_percent": psutil.disk_usage('/').percent, "timestamp": str(datetime.datetime.now())
    }
    if include_quotas: data["quotas_note"] = "placeholder - implement LiteLLM budget check" return data ```
