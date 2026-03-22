import json
import logging
import openai
from src.core.config import settings

logger = logging.getLogger(__name__)


async def call_openai(
    system_prompt: str,
    task: str,
    model: str,
    max_tokens: int,
    tools: list[dict] | None = None,
) -> str:
    client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": task},
    ]

    if tools:
        from src.agent.tools import execute_tool

    while True:
        kwargs = dict(model=model, max_tokens=max_tokens, messages=messages)
        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = await client.chat.completions.create(**kwargs)
        message = response.choices[0].message

        if message.tool_calls:
            # Append assistant turn
            messages.append(message)

            # Execute each tool call
            for tc in message.tool_calls:
                args = json.loads(tc.function.arguments)
                logger.info("Tool call: %s(%s)", tc.function.name, args)
                result = execute_tool(tc.function.name, args)
                logger.info("Tool result: %s", result[:200])
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": result,
                })

        else:
            return message.content or ""
