import asyncio
import json

from app.intelligence.llm import generate_json


async def main():

    result = await generate_json(
        """
Return ONLY JSON.
""",
        """
Return:
{
  "status": "working",
  "message": "LLM connection successful"
}
""",
    )

    print(
        json.dumps(
            result,
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
