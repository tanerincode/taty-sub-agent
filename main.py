"""
taty-sub-agent — entry point.

Example: invoke a sub-agent with RAG skill routing.
For production use, wire SynatyxMemory with real MCP/HTTP callables.
"""
import asyncio
import logging
from src.agent.invoker import AgentInvoker
from src.core.models import AgentTask, TaskBatch

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


async def main():
    invoker = AgentInvoker()

    # Single task (skill auto-routed via RAG or local fallback)
    result = await invoker.invoke(
        AgentTask(task="Write a Python FastAPI endpoint for user registration with JWT auth.")
    )
    print(f"\n[{result.skill_name}] {'OK' if result.success else 'FAIL'}")
    print(result.output if result.success else result.error)

    # Parallel batch
    batch = TaskBatch(
        description="Code review + refactor",
        tasks=[
            AgentTask(task="Review this code for security issues: `eval(user_input)`"),
            AgentTask(task="Write a Node.js HTTP server with rate limiting."),
        ],
    )
    results = await invoker.invoke_parallel(batch)
    for r in results:
        print(f"\n[{r.skill_name}] {'OK' if r.success else 'FAIL'}: {r.task[:60]}")


if __name__ == "__main__":
    asyncio.run(main())
