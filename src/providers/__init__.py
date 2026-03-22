from src.core.models import Provider
from src.core.config import settings
from src.providers.anthropic import call_anthropic
from src.providers.openai import call_openai


async def call_model(
    provider: Provider,
    system_prompt: str,
    task: str,
    model: str | None = None,
    max_tokens: int | None = None,
    enable_tools: bool = False,
) -> str:
    max_tokens = max_tokens or settings.max_tokens

    tools_anthropic = None
    tools_openai = None
    if enable_tools:
        from src.agent.tools import ANTHROPIC_TOOLS, OPENAI_TOOLS
        tools_anthropic = ANTHROPIC_TOOLS
        tools_openai = OPENAI_TOOLS

    if provider == Provider.OPENAI:
        return await call_openai(
            system_prompt=system_prompt,
            task=task,
            model=model or settings.openai_default_model,
            max_tokens=max_tokens,
            tools=tools_openai,
        )

    return await call_anthropic(
        system_prompt=system_prompt,
        task=task,
        model=model or settings.default_model,
        max_tokens=max_tokens,
        tools=tools_anthropic,
    )
