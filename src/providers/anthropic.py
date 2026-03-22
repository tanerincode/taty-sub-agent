import logging
import anthropic
from src.core.config import settings

logger = logging.getLogger(__name__)


async def call_anthropic(
    system_prompt: str,
    task: str,
    model: str,
    max_tokens: int,
    tools: list[dict] | None = None,
) -> str:
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    messages = [{"role": "user", "content": task}]

    # Import executor only when tools are enabled
    if tools:
        from src.agent.tools import execute_tool

    while True:
        kwargs = dict(
            model=model,
            max_tokens=max_tokens,
            system=system_prompt,
            messages=messages,
        )
        if tools:
            kwargs["tools"] = tools

        response = await client.messages.create(**kwargs)

        if response.stop_reason == "tool_use":
            # Append assistant turn with all content blocks
            messages.append({"role": "assistant", "content": response.content})

            # Execute each tool call and collect results
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    logger.info("Tool call: %s(%s)", block.name, block.input)
                    result = execute_tool(block.name, block.input)
                    logger.info("Tool result: %s", result[:200])
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result,
                    })

            messages.append({"role": "user", "content": tool_results})

        else:
            # end_turn or any other stop reason — return final text
            text_blocks = [b.text for b in response.content if hasattr(b, "text")]
            return "\n".join(text_blocks)
