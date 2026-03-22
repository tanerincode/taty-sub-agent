"""
RAG router: finds the best matching skill for a given task via Synatyx memory.
Falls back to local skill loading if Synatyx is not configured.
"""
from typing import Optional
from src.core.models import Skill
from src.memory.synatyx import SynatyxMemory
from src.skills.loader import load_skills_from_dir


class SkillRouter:
    def __init__(self, memory: SynatyxMemory):
        self.memory = memory

    async def find(self, task: str, top_k: int = 1) -> Optional[Skill]:
        skill = await self.memory.find_skill(task, top_k=top_k)
        if skill:
            return skill
        return self._local_fallback(task)

    def _local_fallback(self, task: str) -> Optional[Skill]:
        skills = load_skills_from_dir()
        if not skills:
            return None
        task_lower = task.lower()
        for skill in skills:
            if any(word in task_lower for word in skill.description.lower().split()):
                return skill
        return skills[0]
