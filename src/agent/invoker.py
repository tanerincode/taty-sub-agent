"""
AgentInvoker: spawns sub-agents using a skill as their system prompt.
Supports Anthropic (Claude) and OpenAI (GPT) providers per task or skill.
"""
import asyncio
import logging
from typing import Optional

from src.core.config import settings
from src.core.models import AgentTask, AgentResult, TaskBatch, Provider
from src.providers import call_model
from src.memory.synatyx import SynatyxMemory
from src.skills.router import SkillRouter

logger = logging.getLogger(__name__)


class AgentInvoker:
    def __init__(self, memory: Optional[SynatyxMemory] = None):
        self.memory = memory or SynatyxMemory()
        self.router = SkillRouter(memory=self.memory)

    async def invoke(self, task: AgentTask) -> AgentResult:
        skill = task.skill

        if skill is None:
            skill = await self.router.find(task.task)

        if skill is None:
            return AgentResult(
                task=task.task,
                skill_name="none",
                output="",
                success=False,
                error="No matching skill found for task.",
            )

        provider = task.provider or skill.provider or Provider.ANTHROPIC
        model = task.model or skill.model

        system_parts = [skill.content]
        if task.context:
            system_parts.append(f"## Additional Context\n{task.context}")

        retrieved = await self.memory.retrieve_context(task.task)
        if retrieved:
            system_parts.append(f"## Relevant Memory\n{retrieved}")

        system_prompt = "\n\n".join(system_parts)

        logger.info(
            "Invoking [%s/%s] skill='%s' task='%s'",
            provider.value,
            model or "default",
            skill.name,
            task.task[:80],
        )

        try:
            output = await call_model(
                provider=provider,
                system_prompt=system_prompt,
                task=task.task,
                model=model,
                enable_tools=task.enable_tools,
            )
            result = AgentResult(
                task=task.task,
                skill_name=skill.name,
                output=output,
                success=True,
            )
        except Exception as e:
            logger.error("Agent invocation failed: %s", e)
            result = AgentResult(
                task=task.task,
                skill_name=skill.name,
                output="",
                success=False,
                error=str(e),
            )

        if task.store_result and result.success:
            await self.memory.store_result(result)

        return result

    async def invoke_parallel(self, batch: TaskBatch) -> list[AgentResult]:
        semaphore = asyncio.Semaphore(settings.max_parallel_agents)
        logger.info("Running batch '%s' (%d tasks)", batch.description, len(batch.tasks))

        async def bounded(task: AgentTask) -> AgentResult:
            async with semaphore:
                return await self.invoke(task)

        return await asyncio.gather(*[bounded(t) for t in batch.tasks])
