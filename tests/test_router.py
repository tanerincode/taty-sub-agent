import pytest
from unittest.mock import AsyncMock
from src.core.models import Skill
from src.memory.synatyx import SynatyxMemory
from src.skills.router import SkillRouter


MOCK_SKILL = Skill(
    name="python-developer",
    description="Senior Python developer for backend services",
    content="You are a senior Python developer.",
)


@pytest.mark.asyncio
async def test_router_uses_synatyx():
    memory = SynatyxMemory()
    memory.find_skill = AsyncMock(return_value=MOCK_SKILL)
    router = SkillRouter(memory=memory)
    skill = await router.find("write a python script")
    assert skill.name == "python-developer"
    memory.find_skill.assert_called_once()


@pytest.mark.asyncio
async def test_router_local_fallback(monkeypatch):
    monkeypatch.setattr("src.skills.router.load_skills_from_dir", lambda: [MOCK_SKILL])
    memory = SynatyxMemory()
    memory.find_skill = AsyncMock(return_value=None)
    router = SkillRouter(memory=memory)
    skill = await router.find("write a python script")
    assert skill is not None
