"""
Synatyx memory integration.
Stores agent results and retrieves context from the Synatyx context engine.
"""
from typing import Optional, Callable, Awaitable
from src.core.models import AgentResult, Skill
from src.core.config import settings


class SynatyxMemory:
    def __init__(
        self,
        user_id: Optional[str] = None,
        project: Optional[str] = None,
    ):
        self.user_id = user_id or settings.synatyx_user_id
        self.project = project or settings.synatyx_project
        self._store_fn: Optional[Callable[..., Awaitable]] = None
        self._retrieve_fn: Optional[Callable[..., Awaitable]] = None
        self._skill_find_fn: Optional[Callable[..., Awaitable]] = None

    def configure(
        self,
        store_fn: Callable,
        retrieve_fn: Callable,
        skill_find_fn: Callable,
    ):
        self._store_fn = store_fn
        self._retrieve_fn = retrieve_fn
        self._skill_find_fn = skill_find_fn

    async def store_result(self, result: AgentResult) -> None:
        if not self._store_fn:
            return
        content = (
            f"Agent '{result.skill_name}' completed task: {result.task}\n"
            f"Success: {result.success}\n"
            f"Output:\n{result.output}"
        )
        await self._store_fn(
            content=content,
            user_id=self.user_id,
            memory_layer="L2",
            session_id=self.project,
            importance=0.6,
        )

    async def find_skill(self, query: str, top_k: int = 1) -> Optional[Skill]:
        if not self._skill_find_fn:
            return None
        results = await self._skill_find_fn(
            query=query,
            user_id=self.user_id,
            project=self.project,
            top_k=top_k,
        )
        if not results:
            return None
        first = results[0]
        return Skill(
            name=first["name"],
            description=first["description"],
            content=first["content"],
            project=first.get("project"),
        )

    async def retrieve_context(self, query: str, top_k: int = 5) -> str:
        if not self._retrieve_fn:
            return ""
        results = await self._retrieve_fn(
            query=query,
            user_id=self.user_id,
            session_id=self.project,
            project=self.project,
            top_k=top_k,
        )
        if not results:
            return ""
        return "\n\n".join(r.get("content", "") for r in results)
