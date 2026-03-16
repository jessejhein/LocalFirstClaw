Using LiteLLM as an SDK is essentially taking that "Proxy" logic and embedding it directly into your Python process. This is the "no-infrastructure" way to handle fallbacks—no need to manage a separate systemd service or a Docker container for the proxy.
To do this with Pydantic AI, we use the litellm.Router. Think of it as an in-memory load balancer that manages your API keys and retry logic.
The Architecture: In-Process Fallback
In this setup, if your primary model (e.g., Claude) is down or hits a rate limit, the Router automatically catches the error and retries with your secondary model (e.g., GPT-4) or your local backup (Ollama) before Pydantic AI even realizes there was a problem.
Python Implementation: Agent + Router SDK
This script sets up a fallback chain: Claude 3.5 Sonnet (Primary) → GPT-4o (Secondary) → Ollama/Codestral (Local Backup).
import os
import asyncio
from litellm import Router
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.function import FunctionModel

# 1. Define the Fallback Strategy
# The Router handles the "plumbing" of switching models.
model_list = [
    {
        "model_name": "primary-coder",
        "litellm_params": {
            "model": "anthropic/claude-3-5-sonnet-20240620",
            "api_key": os.getenv("ANTHROPIC_API_KEY"),
        },
    },
    {
        "model_name": "fallback-coder",
        "litellm_params": {
            "model": "openai/gpt-4o",
            "api_key": os.getenv("OPENAI_API_KEY"),
        },
    },
    {
        "model_name": "local-backup",
        "litellm_params": {
            "model": "ollama/codestral",
            "api_base": "http://localhost:11434",
        },
    }
]

router = Router(
    model_list=model_list,
    fallbacks=[{"primary-coder": ["fallback-coder", "local-backup"]}],
    context_window_fallbacks=[{"primary-coder": ["local-backup"]}], # Switch if diff is too big!
    num_retries=2
)

# 2. Bridge LiteLLM SDK to Pydantic AI
# We use a FunctionModel to wrap the SDK's completion call.
async def litellm_bridge(messages, info):
    response = await router.acompletion(
        model="primary-coder",
        messages=[{"role": m.role, "content": m.content} for m in messages],
        # LiteLLM handles the mapping of tools automatically
    )
    return response.choices[0].message.content

model = FunctionModel(litellm_bridge)

# 3. Define the Agent and Tools
agent = Agent(
    model,
    system_prompt="You are an expert dev. Use tools to analyze and run code.",
    deps_type=str,
)

@agent.tool
async def read_file(ctx: RunContext[str], filename: str) -> str:
    """Read file content safely."""
    path = os.path.join(ctx.deps, filename)
    with open(path, 'r') as f:
        return f.read()

@agent.tool
async def run_bash(ctx: RunContext[str], command: str) -> str:
    """Run bash commands for testing/debugging."""
    import subprocess
    proc = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=ctx.deps)
    return f"Output: {proc.stdout}\nErrors: {proc.stderr}"

# 4. Execute
async def main():
    # Example: Analyzing a local repo (e.g., on your Fedora Silverblue setup)
    project_path = "/var/home/heinjj/dev/my-app"
    
    result = await agent.run(
        "Look at the imports in app.py. If any are missing, try to install them with pip.",
        deps=project_path
    )
    print(f"Agent result: {result.data}")

if __name__ == "__main__":
    asyncio.run(main())

Why this is the "Experienced Developer" Move
 * Context Window Fallbacks: Notice the context_window_fallbacks in the Router config. If you try to feed a massive GitLab diff into a model with a small context, LiteLLM will automatically re-route that specific request to a model that can handle it.
 * Zero-Downtime Local Development: If you're working offline or on a plane, the Router will fail through to your Ollama instance without you changing a single line of agent logic.
 * Immutable Friendly: Since this is all in the SDK, you don't need to mess with system-level services or rpm-ostree layering. It just lives in your project's venv or Flatpak-based dev environment.
A Quick Note on the "Bridge"
Pydantic AI's FunctionModel is incredibly powerful because it lets you inject any logic between the agent and the LLM. You could even use it to log costs to a local SQLite DB or prune the message history before it ever reaches the API.
Would you like me to refine the litellm_bridge to handle streaming or to include token counting before the call?

