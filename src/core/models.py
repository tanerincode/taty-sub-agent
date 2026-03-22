from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class MemoryLayer(str, Enum):
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"


class Provider(str, Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"


class Skill(BaseModel):
    name: str
    description: str
    content: str
    project: Optional[str] = None
    provider: Provider = Provider.ANTHROPIC   # default provider for this skill
    model: Optional[str] = None              # override model (e.g. "gpt-4o")


class AgentTask(BaseModel):
    task: str
    skill: Optional[Skill] = None        # if None, router will find one
    context: Optional[str] = None        # extra context injected into system prompt
    store_result: bool = True            # persist result to Synatyx L2
    provider: Optional[Provider] = None  # override skill's provider
    model: Optional[str] = None          # override model
    enable_tools: bool = True            # give sub-agent file + shell tools


class AgentResult(BaseModel):
    task: str
    skill_name: str
    output: str
    success: bool
    error: Optional[str] = None


class TaskBatch(BaseModel):
    tasks: list[AgentTask]
    description: str = Field(default="", description="Human-readable batch label")
