import asyncio
import json

from app.intelligence.evidence import EvidenceEngine


async def main():

    engine = EvidenceEngine()

    print("\n=== BUILDING EVIDENCE BUNDLE ===")

    bundle = await engine.build_account_bundle(
        "northline-grid"
    )

    data = bundle.to_dict()

    print("\n=== ACCOUNT ===")
    print(
        json.dumps(
            data["account"],
            indent=2,
        )
    )

    print("\n=== USAGE ===")
    print(
        json.dumps(
            data["usage"],
            indent=2,
        )
    )

    print("\n=== EVIDENCE ===")

    for item in data["evidence"]:

        print(
            f"\nSOURCE: {item['source']}"
        )

        print(
            f"TYPE: {item['source_type']}"
        )

        print(
            f"ACCOUNT: {item['account_id']}"
        )

        print(
            f"RETRIEVED: {item['retrieved_at']}"
        )

        print(
            item["content"]
        )

    print("\n=== RETRIEVAL METADATA ===")

    print(
        json.dumps(
            data["retrieval_metadata"],
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
