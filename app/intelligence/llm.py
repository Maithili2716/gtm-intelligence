import json
import os
import re

from dotenv import load_dotenv
from openai import AsyncOpenAI


load_dotenv()


client = AsyncOpenAI(
    api_key=os.environ["NVIDIA_API_KEY"],
    base_url=os.environ["NVIDIA_BASE_URL"],
)

MODEL = os.environ["NVIDIA_MODEL"]


def extract_json(text: str) -> dict:
    """
    Extract the first complete JSON object from an LLM response.

    Nemotron may return reasoning text before the final JSON.
    """

    text = text.strip()

    # First: response is already pure JSON.
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Remove markdown fences if present.
    text = re.sub(
        r"```json\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"```\s*$",
        "",
        text,
    ).strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Find the first JSON object.
    start = text.find("{")

    if start == -1:
        raise RuntimeError(
            "LLM response contained no JSON object:\n"
            + text
        )

    depth = 0
    in_string = False
    escaped = False

    for i in range(start, len(text)):

        char = text[i]

        if escaped:
            escaped = False
            continue

        if char == "\\" and in_string:
            escaped = True
            continue

        if char == '"':
            in_string = not in_string
            continue

        if in_string:
            continue

        if char == "{":
            depth += 1

        elif char == "}":
            depth -= 1

            if depth == 0:

                candidate = text[
                    start:i + 1
                ]

                try:
                    return json.loads(candidate)

                except json.JSONDecodeError as exc:
                    raise RuntimeError(
                        "Found JSON-looking content, "
                        "but it was invalid:\n"
                        + candidate
                    ) from exc

    raise RuntimeError(
        "LLM response contained an incomplete JSON object:\n"
        + text
    )


async def generate_json(
    system_prompt: str,
    user_prompt: str,
) -> dict:

    response = await client.chat.completions.create(
        model=MODEL,

        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],

        temperature=0.0,
        top_p=1.0,
        max_tokens=2048,

        extra_body={
            "chat_template_kwargs": {
                "enable_thinking": False,
            }
        },
    )

    content = response.choices[0].message.content

    if not content:
        raise RuntimeError(
            "LLM returned an empty response."
        )

    return extract_json(content)