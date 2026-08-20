import asyncio
import json

from app.intelligence.risk import investigate_risk
from app.intelligence.account import analyze_account


async def main():

    print("\n=== RISK INVESTIGATION ===")

    risk = await investigate_risk(
        "northline-grid"
    )

    print("\n=== ACCOUNT ANALYSIS ===")

    account = await analyze_account(
        account_id="northline-grid",
        risk=risk,
    )

    print(
        json.dumps(
            account,
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
