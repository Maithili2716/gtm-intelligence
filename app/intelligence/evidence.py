from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import json
import re

from app.sor.flytbase import FlytBaseSOR


@dataclass
class Evidence:
    account_id: str
    source: str
    source_type: str
    content: str
    source_date: str | None
    retrieved_at: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class EvidenceBundle:
    account: dict
    usage: dict
    evidence: list[Evidence]
    retrieval_metadata: dict

    def to_dict(self) -> dict:
        return {
            "account": self.account,
            "usage": self.usage,
            "evidence": [
                item.to_dict()
                for item in self.evidence
            ],
            "retrieval_metadata": self.retrieval_metadata,
        }


class EvidenceEngine:

    def __init__(self):
        self.sor = FlytBaseSOR()

    @staticmethod
    def _parse_result(result):
        """
        Convert MCP TextContent results into Python objects.
        """

        values = []

        for item in result.content:

            if not hasattr(item, "text"):
                continue

            text = item.text

            try:
                values.append(json.loads(text))
            except json.JSONDecodeError:
                values.append(text)

        if len(values) == 1:
            return values[0]

        return values

    async def build_account_bundle(
        self,
        account_id: str,
    ) -> EvidenceBundle:

        retrieved_at = datetime.now(
            timezone.utc
        ).isoformat()

        # =========================
        # ACCOUNT
        # =========================

        account_result = await self.sor.get_account(
            account_id
        )

        account = self._parse_result(
            account_result
        )

        # =========================
        # USAGE
        # =========================

        usage_result = await self.sor.get_usage(
            account_id
        )

        usage = self._parse_result(
            usage_result
        )

        # =========================
        # DOCUMENT INDEX
        # =========================

        documents_result = await self.sor.list_documents(
            account_id
        )

        documents = self._parse_result(
            documents_result
        )

        # =========================
        # EVIDENCE
        # =========================

        evidence = []

        # -------------------------
        # Customer documents
        # -------------------------

        for document in documents:

            filename = document["file"]

            result = await self.sor.get_document(
                account_id,
                filename,
            )

            parsed = self._parse_result(
                result
            )

            content = parsed.get(
                "content",
                "",
            )

            date_match = re.search(
                r"\*\*Date:\*\*\s*(\d{4}-\d{2}-\d{2})",
                content,
            )

            source_date = (
                date_match.group(1)
                if date_match
                else None
            )

            evidence.append(
                Evidence(
                    account_id=account_id,
                    source=filename,
                    source_type="customer_document",
                    content=content,
                    source_date=source_date,
                    retrieved_at=retrieved_at,
                )
            )

        # -------------------------
        # Live usage
        # -------------------------

        usage_content = json.dumps(
            usage,
            indent=2,
        )

        monthly = usage.get(
            "monthly",
            [],
        )

        source_date = None

        if monthly:
            source_date = monthly[-1].get(
                "month"
            )

        evidence.append(
            Evidence(
                account_id=account_id,
                source="live_usage",
                source_type="usage_system",
                content=usage_content,
                source_date=source_date,
                retrieved_at=retrieved_at,
            )
        )

        return EvidenceBundle(
            account=account,
            usage=usage,
            evidence=evidence,
            retrieval_metadata={
                "account_id": account_id,
                "retrieved_at": retrieved_at,
                "document_count": len(documents),
                "evidence_count": len(evidence),
                "source": "mcp_sor",
            },
        )
