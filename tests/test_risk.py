import asyncio
import json

from app.intelligence.risk import investigate_risk


async def main():

    print("\n=== RISK INVESTIGATION ===")

    result = await investigate_risk(
        "northline-grid"
    )

    print(
        json.dumps(
            result,
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
