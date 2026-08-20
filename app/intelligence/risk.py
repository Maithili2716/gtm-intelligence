import json

from app.intelligence.evidence import EvidenceEngine
from app.intelligence.llm import generate_json


RISK_SYSTEM_PROMPT = """
You are a Customer Success Risk Investigator.

Your job is to analyze an account's evidence and distinguish:

FACTS
INFERENCES
SIGNALS
RISKS

You are NOT responsible for recommending actions.

========================================
FACTS
========================================

A fact is information directly supported by the supplied evidence.

Every fact MUST cite its exact evidence source.

Do not interpret facts.

========================================
INFERENCES
========================================

An inference is an interpretation derived from one or more facts.

Every inference MUST identify its supporting facts and evidence.

Never present an inference as a fact.

========================================
SIGNALS
========================================

A signal is a meaningful directional observation.

Every signal MUST have a domain.

Allowed domains:

operational
- usage
- reliability
- incidents
- implementation
- product performance

commercial
- renewal
- budget
- contract
- business relationship
- commercial exposure

procurement
- vendor approval
- purchasing policy
- hardware sourcing

security
- security review
- compliance
- data residency
- regulatory requirements

adoption
- product adoption
- usage depth
- expansion of usage

relationship
- stakeholder engagement
- sentiment
- executive sponsorship

other
- anything that does not fit the above

A signal is NOT automatically a risk.

For example:

Increasing usage
= positive adoption/operational signal

It does NOT automatically mean expansion opportunity.

========================================
RISKS
========================================

A risk is a material threat to:

- renewal
- retention
- adoption
- implementation
- procurement
- security
- compliance
- customer relationship

Do NOT create a risk merely because:

- a metric is flat
- a metric is low
- a metric changed
- something is unusual
- something is negative

There must be a plausible business consequence supported
by evidence.

Every risk MUST reference one or more facts or inferences
through the "basis" field.

Every risk MUST cite exact evidence sources.

========================================
IMPORTANT
========================================

Do not trust CRM health blindly.

Look for meaningful differences between:

- CRM health
- sentiment
- usage
- reliability
- security
- procurement
- renewal signals
- customer requests

But do not manufacture contradictions.

Never invent facts.

Never invent evidence.

Never recommend actions.

Return ONLY valid JSON.

Required output:

{
  "summary": "...",

  "facts": [
    {
      "id": "fact_1",
      "statement": "...",
      "evidence": ["exact_source"]
    }
  ],

  "inferences": [
    {
      "id": "inference_1",
      "statement": "...",
      "basis": ["fact_1"],
      "evidence": ["exact_source"],
      "confidence": 0.0
    }
  ],

  "signals": [
    {
      "title": "...",
      "domain": "operational|commercial|procurement|security|adoption|relationship|other",
      "direction": "positive|negative|neutral",
      "strength": 0.0,
      "status": "emerging|active|resolved|contextual",
      "reason": "...",
      "basis": ["fact_1"],
      "evidence": ["exact_source"]
    }
  ],

  "risks": [
    {
      "title": "...",
      "category": "...",
      "statement": "...",
      "impact": "low|medium|high",
      "likelihood": "low|medium|high",
      "basis": ["fact_1", "inference_1"],
      "evidence": ["exact_source"]
    }
  ],

  "confidence": 0.0
}
"""


class RiskInvestigator:

    def __init__(self):
        self.evidence_engine = EvidenceEngine()

    async def investigate(
        self,
        account_id: str,
    ) -> dict:

        bundle = await self.evidence_engine.build_account_bundle(
            account_id
        )

        data = bundle.to_dict()

        prompt = f"""
Analyze this account using ONLY the supplied evidence.

ACCOUNT:
{json.dumps(data["account"], indent=2)}

USAGE:
{json.dumps(data["usage"], indent=2)}

EVIDENCE:
{json.dumps(data["evidence"], indent=2)}

RETRIEVAL METADATA:
{json.dumps(data["retrieval_metadata"], indent=2)}

Build the reasoning hierarchy:

1. Extract directly supported FACTS.
2. Derive carefully supported INFERENCES.
3. Identify meaningful SIGNALS.
4. Identify only MATERIAL RISKS.

Important:

Classify every signal with the correct domain.

For example:

- reliability -> operational
- increasing usage -> adoption or operational
- procurement review -> procurement
- hardware sourcing policy -> procurement
- data residency review -> security
- renewal uncertainty -> commercial
- stakeholder sentiment -> relationship

Do not classify a procurement or security signal as
an operational signal merely because it affects the account.

58 -> 61 -> 64 flight hours is a FACTUAL trend.

Whether that represents meaningful growth is an INFERENCE.

Whether that creates a MATERIAL BUSINESS RISK requires
additional reasoning and evidence.

Do not recommend actions.

Return only the requested JSON.
"""

        result = await generate_json(
            RISK_SYSTEM_PROMPT,
            prompt,
        )

        return self._validate(
            result,
            data,
            account_id,
        )

    @staticmethod
    def _validate(
        result: dict,
        bundle: dict,
        account_id: str,
    ) -> dict:

        valid_sources = {
            item["source"]
            for item in bundle["evidence"]
        }

        # =====================================
        # FACTS
        # =====================================

        facts = []

        for fact in result.get(
            "facts",
            [],
        ):

            evidence = [
                source
                for source in fact.get(
                    "evidence",
                    [],
                )
                if source in valid_sources
            ]

            if not evidence:
                continue

            facts.append(
                {
                    "id": fact.get(
                        "id",
                        f"fact_{len(facts) + 1}",
                    ),
                    "statement": fact.get(
                        "statement",
                        "",
                    ),
                    "evidence": evidence,
                }
            )

        # =====================================
        # INFERENCES
        # =====================================

        valid_fact_ids = {
            fact["id"]
            for fact in facts
        }

        inferences = []

        for inference in result.get(
            "inferences",
            [],
        ):

            basis = [
                item
                for item in inference.get(
                    "basis",
                    [],
                )
                if item in valid_fact_ids
            ]

            evidence = [
                source
                for source in inference.get(
                    "evidence",
                    [],
                )
                if source in valid_sources
            ]

            if not basis or not evidence:
                continue

            try:
                confidence = float(
                    inference.get(
                        "confidence",
                        0.0,
                    )
                )
            except (TypeError, ValueError):
                confidence = 0.0

            inferences.append(
                {
                    "id": inference.get(
                        "id",
                        f"inference_{len(inferences) + 1}",
                    ),
                    "statement": inference.get(
                        "statement",
                        "",
                    ),
                    "basis": basis,
                    "evidence": evidence,
                    "confidence": max(
                        0.0,
                        min(1.0, confidence),
                    ),
                }
            )

        # =====================================
        # SIGNALS
        # =====================================

        valid_inference_ids = {
            inference["id"]
            for inference in inferences
        }

        valid_basis_ids = (
            valid_fact_ids
            | valid_inference_ids
        )

        allowed_domains = {
            "operational",
            "commercial",
            "procurement",
            "security",
            "adoption",
            "relationship",
            "other",
        }

        signals = []

        for signal in result.get(
            "signals",
            [],
        ):

            basis = [
                item
                for item in signal.get(
                    "basis",
                    [],
                )
                if item in valid_basis_ids
            ]

            evidence = [
                source
                for source in signal.get(
                    "evidence",
                    [],
                )
                if source in valid_sources
            ]

            if not basis or not evidence:
                continue

            domain = signal.get(
                "domain",
                "other",
            )

            if domain not in allowed_domains:
                domain = "other"

            try:
                strength = float(
                    signal.get(
                        "strength",
                        0.0,
                    )
                )
            except (TypeError, ValueError):
                strength = 0.0

            direction = signal.get(
                "direction",
                "neutral",
            )

            if direction not in {
                "positive",
                "negative",
                "neutral",
            }:
                direction = "neutral"

            status = signal.get(
                "status",
                "contextual",
            )

            if status not in {
                "emerging",
                "active",
                "resolved",
                "contextual",
            }:
                status = "contextual"

            signals.append(
                {
                    "account_id": account_id,

                    "title": signal.get(
                        "title",
                        "Unnamed signal",
                    ),

                    "domain": domain,

                    "direction": direction,

                    "strength": max(
                        0.0,
                        min(1.0, strength),
                    ),

                    "status": status,

                    "reason": signal.get(
                        "reason",
                        "",
                    ),

                    "basis": basis,

                    "evidence": evidence,
                }
            )

        # =====================================
        # RISKS
        # =====================================

        risks = []

        for risk in result.get(
            "risks",
            [],
        ):

            basis = [
                item
                for item in risk.get(
                    "basis",
                    [],
                )
                if item in valid_basis_ids
            ]

            evidence = [
                source
                for source in risk.get(
                    "evidence",
                    [],
                )
                if source in valid_sources
            ]

            if not basis or not evidence:
                continue

            risks.append(
                {
                    "title": risk.get(
                        "title",
                        "Unnamed risk",
                    ),

                    "category": risk.get(
                        "category",
                        "unknown",
                    ),

                    "statement": risk.get(
                        "statement",
                        "",
                    ),

                    "impact": risk.get(
                        "impact",
                        "medium",
                    ),

                    "likelihood": risk.get(
                        "likelihood",
                        "medium",
                    ),

                    "basis": basis,

                    "evidence": evidence,
                }
            )

        # =====================================
        # FINAL RESULT
        # =====================================

        try:
            confidence = float(
                result.get(
                    "confidence",
                    0.0,
                )
            )
        except (TypeError, ValueError):
            confidence = 0.0

        return {
            "account_id": account_id,

            "investigation": "risk",

            "summary": result.get(
                "summary",
                "",
            ),

            "facts": facts,

            "inferences": inferences,

            "signals": signals,

            "risks": risks,

            "confidence": max(
                0.0,
                min(1.0, confidence),
            ),
        }


async def investigate_risk(
    account_id: str,
) -> dict:

    return await RiskInvestigator().investigate(
        account_id
    )
