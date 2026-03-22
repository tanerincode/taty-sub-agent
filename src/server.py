"""
taty-sub-agent MCP server.

Exposes sub-agent invocation as MCP tools so Claude Code (or any MCP client)
can dispatch tasks to skill-matched sub-agents directly.
"""
import sys
from pathlib import Path

# Ensure project root is on sys.path regardless of how the server is launched
_project_root = str(Path(__file__).resolve().parents[1])
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import asyncio
from typing import Optional

from fastmcp import FastMCP, Context
from src.agent.invoker import AgentInvoker
from src.memory.synatyx import SynatyxMemory
from src.core.models import AgentTask, TaskBatch, Skill
from src.core.config import settings

mcp = FastMCP(
    name="taty-sub-agent",
    instructions=(
        "Dispatch tasks to specialized sub-agents via RAG skill matching. "
        "Use invoke_agent for a single task or invoke_parallel for multiple concurrent tasks."
    ),
)


@mcp.custom_route("/health", methods=["GET"])
async def health(request):
    from starlette.responses import JSONResponse
    return JSONResponse({"status": "ok", "service": "taty-sub-agent"})

_invoker: Optional[AgentInvoker] = None

# In-memory token cache — populated via elicitation when keys are missing
_token_cache: dict[str, str] = {}


def get_invoker() -> AgentInvoker:
    global _invoker
    if _invoker is None:
        _invoker = AgentInvoker()
    return _invoker


async def _ensure_api_keys(ctx: Context, provider: str | None) -> None:
    """
    Ensure API keys are available. Strategy (in order):
    1. Already in settings (env var / MCP config)
    2. Already cached from a previous call this session
    3. Elicit from user (supported by Augment + Claude Desktop)
    4. If elicitation not supported, raise with instructions to use configure_keys tool
    """
    # Restore from session cache first
    if "anthropic" in _token_cache and not settings.anthropic_api_key:
        settings.anthropic_api_key = _token_cache["anthropic"]
    if "openai" in _token_cache and not settings.openai_api_key:
        settings.openai_api_key = _token_cache["openai"]

    needs_anthropic = not settings.anthropic_api_key and provider != "openai"
    needs_openai = not settings.openai_api_key and provider == "openai"

    for key, label, needs in [
        ("anthropic", "Anthropic", needs_anthropic),
        ("openai", "OpenAI", needs_openai),
    ]:
        if not needs or key in _token_cache:
            continue
        try:
            result = await ctx.elicit(
                message=f"No {label.upper()}_API_KEY found. Enter your {label} bearer token:",
                schema={
                    "type": "object",
                    "properties": {"token": {"type": "string", "title": f"{label} API Key"}},
                    "required": ["token"],
                },
            )
            if result.action == "submit":
                token = result.data["token"]
                _token_cache[key] = token
                if key == "anthropic":
                    settings.anthropic_api_key = token
                else:
                    settings.openai_api_key = token
        except Exception:
            # Client does not support elicitation (e.g. Claude CLI)
            raise RuntimeError(
                f"No {label} API key configured. "
                f"Call configure_keys(anthropic_api_key='sk-ant-...') first, "
                f"or set {label.upper()}_API_KEY in your MCP server environment."
            )


@mcp.tool()
async def invoke_agent(
    ctx: Context,
    task: str,
    skill_name: Optional[str] = None,
    context: Optional[str] = None,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    store_result: bool = True,
    enable_tools: bool = True,
) -> dict:
    """
    Invoke a single sub-agent for a task.

    RAG-matches the best skill automatically unless skill_name is provided.
    Returns the agent output and which skill was used.

    Args:
        task: The task description for the sub-agent to complete.
        skill_name: Optional skill to use directly (e.g. 'python-developer'). If omitted, RAG routing picks the best match.
        context: Optional extra context injected into the sub-agent's system prompt.
        provider: Model provider — 'anthropic' (default) or 'openai'.
        model: Model override (e.g. 'gpt-4o', 'claude-opus-4-6'). Uses provider default if omitted.
        store_result: Whether to persist the result to Synatyx L2 memory (default: True).
        enable_tools: Give the sub-agent file and shell tools (write_file, read_file, list_directory, run_command). Default: True.
    """
    await _ensure_api_keys(ctx, provider)
    from src.core.models import Provider
    invoker = get_invoker()
    skill = None

    if skill_name:
        from src.skills.loader import load_skills_from_dir
        local = {s.name: s for s in load_skills_from_dir()}
        skill = local.get(skill_name)
        if skill is None:
            matched = await invoker.memory.find_skill(skill_name, top_k=1)
            skill = matched

    agent_task = AgentTask(
        task=task,
        skill=skill,
        context=context,
        provider=Provider(provider) if provider else None,
        model=model,
        store_result=store_result,
        enable_tools=enable_tools,
    )

    result = await invoker.invoke(agent_task)
    return {
        "skill_used": result.skill_name,
        "success": result.success,
        "output": result.output,
        "error": result.error,
    }


@mcp.tool()
async def invoke_parallel(
    ctx: Context,
    tasks: list[dict],
    batch_description: str = "",
) -> list[dict]:
    """
    Invoke multiple sub-agents concurrently.

    Each task is independently RAG-routed to the best matching skill and
    processed in parallel. Concurrency is capped by MAX_PARALLEL_AGENTS.

    Args:
        tasks: List of task objects. Each must have a 'task' string, and
               optionally 'skill_name', 'context', and 'store_result'.
               Example: [{"task": "write a REST API"}, {"task": "review this code"}]
        batch_description: Human-readable label for this batch (for logging).
    """
    # Elicit keys using the first task's provider hint (if any)
    first_provider = tasks[0].get("provider") if tasks else None
    await _ensure_api_keys(ctx, first_provider)
    invoker = get_invoker()

    from src.core.models import Provider
    agent_tasks = [
        AgentTask(
            task=t["task"],
            context=t.get("context"),
            provider=Provider(t["provider"]) if t.get("provider") else None,
            model=t.get("model"),
            store_result=t.get("store_result", True),
            enable_tools=t.get("enable_tools", True),
        )
        for t in tasks
    ]

    batch = TaskBatch(tasks=agent_tasks, description=batch_description)
    results = await invoker.invoke_parallel(batch)

    return [
        {
            "task": r.task,
            "skill_used": r.skill_name,
            "success": r.success,
            "output": r.output,
            "error": r.error,
        }
        for r in results
    ]


@mcp.tool()
async def configure_keys(
    anthropic_api_key: Optional[str] = None,
    openai_api_key: Optional[str] = None,
) -> dict:
    """
    Set API keys for this session without using environment variables.

    Use this in clients that don't support elicitation (e.g. Claude CLI):
        configure_keys(anthropic_api_key="sk-ant-...")

    Keys are stored in memory for the duration of the server process.

    Args:
        anthropic_api_key: Anthropic bearer token (sk-ant-...)
        openai_api_key: OpenAI bearer token (sk-proj-...)
    """
    updated = []
    if anthropic_api_key:
        _token_cache["anthropic"] = anthropic_api_key
        settings.anthropic_api_key = anthropic_api_key
        updated.append("anthropic")
    if openai_api_key:
        _token_cache["openai"] = openai_api_key
        settings.openai_api_key = openai_api_key
        updated.append("openai")
    if not updated:
        return {"status": "no_op", "message": "No keys provided."}
    return {"status": "ok", "configured": updated}


@mcp.tool()
async def list_skills(project: Optional[str] = "taty-sub-agent") -> list[dict]:
    """
    List all available agent skills.

    Returns skills from local skills/ directory merged with any stored in Synatyx.

    Args:
        project: Project scope to filter Synatyx skills (default: taty-sub-agent).
    """
    from src.skills.loader import load_skills_from_dir
    local = load_skills_from_dir()
    return [
        {"name": s.name, "description": s.description, "source": "local"}
        for s in local
    ]


import os


def main() -> None:
    _transport = os.getenv("MCP_TRANSPORT", "stdio")
    _host = os.getenv("MCP_HOST", "0.0.0.0")
    _port = int(os.getenv("MCP_PORT", "9002"))
    if _transport == "stdio":
        mcp.run(transport="stdio")
    else:
        mcp.run(transport="streamable-http", host=_host, port=_port)


if __name__ == "__main__":
    main()
