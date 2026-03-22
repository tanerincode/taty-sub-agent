"""
taty-sub-agent MCP server.

Exposes sub-agent invocation as MCP tools so Claude Code (or any MCP client)
can dispatch tasks to skill-matched sub-agents directly.
"""
import asyncio
from typing import Optional

from fastmcp import FastMCP
from src.agent.invoker import AgentInvoker
from src.memory.synatyx import SynatyxMemory
from src.core.models import AgentTask, TaskBatch, Skill

mcp = FastMCP(
    name="taty-sub-agent",
    instructions=(
        "Dispatch tasks to specialized sub-agents via RAG skill matching. "
        "Use invoke_agent for a single task or invoke_parallel for multiple concurrent tasks."
    ),
)

_invoker: Optional[AgentInvoker] = None


def get_invoker() -> AgentInvoker:
    global _invoker
    if _invoker is None:
        _invoker = AgentInvoker()
    return _invoker


@mcp.tool()
async def invoke_agent(
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


mcp.run(transport="stdio")
