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
    Extract a JSON object from an LLM response.

    Nemotron may return reasoning text, markdown fences,
    or whitespace around the JSON object.
    """

    if not text:
        raise RuntimeError("LLM response was empty.")

    text = text.strip()

    # ---------------------------------------------------------
    # 1. Pure JSON
    # ---------------------------------------------------------

    try:
        result = json.loads(text)

        if not isinstance(result, dict):
            raise RuntimeError(
                "LLM returned valid JSON, but it was not a JSON object."
            )

        return result

    except json.JSONDecodeError:
        pass

    # ---------------------------------------------------------
    # 2. Remove markdown fences
    # ---------------------------------------------------------

    cleaned = re.sub(
        r"```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(
        r"\s*```",
        "",
        cleaned,
    ).strip()

    try:
        result = json.loads(cleaned)

        if not isinstance(result, dict):
            raise RuntimeError(
                "LLM returned valid JSON, but it was not a JSON object."
            )

        return result

    except json.JSONDecodeError:
        pass

    # ---------------------------------------------------------
    # 3. Find a balanced JSON object
    # ---------------------------------------------------------

    start = cleaned.find("{")

    if start == -1:
        raise RuntimeError(
            "LLM response contained no JSON object:\n"
            + cleaned
        )

    depth = 0
    in_string = False
    escaped = False

    for i in range(start, len(cleaned)):

        char = cleaned[i]

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

                candidate = cleaned[
                    start:i + 1
                ]

                try:
                    result = json.loads(candidate)

                    if not isinstance(result, dict):
                        raise RuntimeError(
                            "Extracted JSON was not an object."
                        )

                    return result

                except json.JSONDecodeError as exc:

                    raise RuntimeError(
                        "Found JSON-looking content, "
                        "but it was invalid:\n"
                        + candidate
                    ) from exc

    # ---------------------------------------------------------
    # 4. Object never closed
    # ---------------------------------------------------------

    raise RuntimeError(
        "LLM response contained an incomplete JSON object:\n"
        + cleaned
    )


async def _call_llm(
    system_prompt: str,
    user_prompt: str,
) -> str:

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

    return content


async def generate_json(
    system_prompt: str,
    user_prompt: str,
) -> dict:

    # ---------------------------------------------------------
    # FIRST ATTEMPT
    # ---------------------------------------------------------

    content = await _call_llm(
        system_prompt,
        user_prompt,
    )

    try:
        return extract_json(content)

    except RuntimeError as first_error:

        # -----------------------------------------------------
        # SECOND ATTEMPT — JSON REPAIR
        # -----------------------------------------------------

        repair_system_prompt = """
You are a JSON repair layer.

The previous model response was supposed to contain exactly
one valid JSON object.

Return ONLY the corrected JSON object.

Rules:

1. Output valid JSON.
2. Use double quotes for all JSON keys and strings.
3. Do not add markdown fences.
4. Do not add explanations.
5. Do not add comments.
6. Preserve the meaning and information of the original response.
7. Do not invent new facts.
8. Preserve evidence references exactly as provided.
9. Ensure every object and array is correctly closed.
10. Ensure every key has exactly one value.

The output must begin with { and end with }.
"""

        repair_user_prompt = f"""
The original task was:

{user_prompt}

The model produced this invalid response:

{content}

The parser error was:

{first_error}

Repair the response and return ONLY valid JSON.
"""

        repaired_content = await _call_llm(
            repair_system_prompt,
            repair_user_prompt,
        )

        try:
            return extract_json(repaired_content)

        except RuntimeError as second_error:

            raise RuntimeError(
                "LLM failed to produce valid JSON after "
                "initial generation and one repair attempt.\n\n"
                f"INITIAL ERROR:\n{first_error}\n\n"
                f"REPAIR ERROR:\n{second_error}\n\n"
                f"REPAIRED RESPONSE:\n{repaired_content}"
            ) from second_error
