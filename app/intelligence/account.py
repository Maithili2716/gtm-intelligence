import json

from app.intelligence.llm import generate_json


ACCOUNT_ANALYSIS_SYSTEM_PROMPT = """
You are an Account Analysis Engine for a Customer Success
intelligence system.

Your job is to compress structured investigation findings
into a concise CURRENT ACCOUNT SITUATION.

You are NOT an action engine.

Do not recommend actions.
Do not generate customer-facing content.
Do not retrieve additional evidence.
Do not call another investigator.

Your output must answer:

1. How healthy is the account operationally?
2. How healthy is the account commercially?
3. What is the primary issue?
4. Why does it matter?
5. What is the key tension?
6. Where is the operational trajectory heading?
7. Where is the commercial trajectory heading?

OPERATIONAL HEALTH

Judge operational health from signals whose domain is:

- operational
- adoption

Do NOT treat procurement, security, or commercial risks
as operational health problems.

COMMERCIAL HEALTH

Judge commercial health from signals and risks involving:

- commercial
- procurement
- security
- relationship
- renewal

KEY TENSION

Describe the most important tension between valid account facts.

Example:

Strong operational performance versus commercial uncertainty
created by an active procurement review.

Do NOT call this a contradiction unless two facts actually
contradict each other.

TRAJECTORY

Use:

Positive
Stable
Negative
Uncertain
Unknown

IMPORTANT:

- Use ONLY supplied structured investigation findings.
- Do NOT invent facts.
- Do NOT recommend actions.
- Do NOT calculate quantitative metrics.
- Keep every field concise.
- Do not repeat every signal.
- Return ONLY valid JSON.

Required output:

{
  "commercial_health": "Strong|Stable|Uncertain|At Risk|Unknown",

  "primary_issue": "...",

  "why": "...",

  "key_tension": "...",

  "trajectory": {
    "operational": "Positive|Stable|Negative|Uncertain|Unknown",
    "commercial": "Positive|Stable|Negative|Uncertain|Unknown"
  },

  "confidence": 0.0
}
"""


class AccountAnalysisEngine:

    async def analyze(
        self,
        account_id: str,
        risk: dict,
        poc: dict | None = None,
        expansion: dict | None = None,
    ) -> dict:

        investigations = {
            "risk": risk,
            "poc": poc,
            "expansion": expansion,
        }

        prompt = f"""
Generate the current account situation for:

ACCOUNT ID:
{account_id}

STRUCTURED INVESTIGATION FINDINGS:
{json.dumps(investigations, indent=2)}

The investigators have already retrieved and analyzed
the underlying evidence.

Use ONLY the structured findings above.

Do NOT retrieve additional evidence.
Do NOT call another investigator.
Do NOT recommend an action.

Determine the account-level situation.

Pay particular attention to:

- operational signals
- adoption signals
- commercial signals
- procurement signals
- security signals
- relationship signals
- material risks
- positive operational evidence
- renewal/procurement uncertainty
- meaningful tension between operational and commercial health

Return only the requested JSON.
"""

        result = await generate_json(
            ACCOUNT_ANALYSIS_SYSTEM_PROMPT,
            prompt,
        )

        return self._validate(
            result,
            risk,
            account_id,
        )

    @staticmethod
    def _validate(
        result: dict,
        risk: dict,
        account_id: str,
    ) -> dict:

        # =====================================
        # TRAJECTORY
        # =====================================

        allowed_trajectory = {
            "Positive",
            "Stable",
            "Negative",
            "Uncertain",
            "Unknown",
        }

        trajectory = result.get(
            "trajectory",
            {},
        )

        operational_trajectory = trajectory.get(
            "operational",
            "Unknown",
        )

        commercial_trajectory = trajectory.get(
            "commercial",
            "Unknown",
        )

        if operational_trajectory not in allowed_trajectory:
            operational_trajectory = "Unknown"

        if commercial_trajectory not in allowed_trajectory:
            commercial_trajectory = "Unknown"

        # =====================================
        # COMMERCIAL HEALTH
        # =====================================

        allowed_commercial = {
            "Strong",
            "Stable",
            "Uncertain",
            "At Risk",
            "Unknown",
        }

        commercial_health = result.get(
            "commercial_health",
            "Unknown",
        )

        if commercial_health not in allowed_commercial:
            commercial_health = "Unknown"

        # =====================================
        # OPERATIONAL HEALTH
        # =====================================

        operational_health = (
            AccountAnalysisEngine
            ._derive_operational_health(
                risk
            )
        )

        # =====================================
        # PRIORITY
        # =====================================

        priority = (
            AccountAnalysisEngine
            ._derive_priority(
                risk,
                commercial_health,
            )
        )

        # =====================================
        # CONFIDENCE
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

        confidence = max(
            0.0,
            min(1.0, confidence),
        )

        # =====================================
        # FINAL ACCOUNT SITUATION
        # =====================================

        return {
            "account_id": account_id,

            "operational_health":
                operational_health,

            "commercial_health":
                commercial_health,

            "primary_issue":
                result.get(
                    "primary_issue",
                    "No material issue identified.",
                ),

            "why":
                result.get(
                    "why",
                    "",
                ),

            "key_tension":
                result.get(
                    "key_tension",
                    "None material identified.",
                ),

            "trajectory": {
                "operational":
                    operational_trajectory,

                "commercial":
                    commercial_trajectory,
            },

            "priority": priority,

            "confidence": confidence,
        }

    @staticmethod
    def _derive_operational_health(
        risk: dict,
    ) -> str:

        signals = risk.get(
            "signals",
            [],
        )

        # Only operational/adoption signals
        # can determine operational health.

        operational_signals = [
            signal
            for signal in signals
            if signal.get("domain")
            in {
                "operational",
                "adoption",
            }
        ]

        positive = [
            signal
            for signal in operational_signals
            if signal.get("direction")
            == "positive"
        ]

        negative = [
            signal
            for signal in operational_signals
            if signal.get("direction")
            == "negative"
        ]

        strong_negative = [
            signal
            for signal in negative
            if float(
                signal.get(
                    "strength",
                    0,
                )
            ) >= 0.75
        ]

        strong_positive = [
            signal
            for signal in positive
            if float(
                signal.get(
                    "strength",
                    0,
                )
            ) >= 0.75
        ]

        if strong_negative:
            return "At Risk"

        if strong_positive:
            return "Strong"

        if positive:
            return "Stable"

        return "Unknown"

    @staticmethod
    def _derive_priority(
        risk: dict,
        commercial_health: str,
    ) -> str:

        risks = risk.get(
            "risks",
            [],
        )

        # A high-impact material risk deserves
        # immediate attention even if likelihood
        # remains uncertain.

        high_impact = [
            item
            for item in risks
            if item.get("impact")
            == "high"
        ]

        if high_impact:
            return "HIGH"

        # Active/emerging strong negative
        # commercial/procurement/security signals
        # deserve attention.

        material_negative = [
            signal
            for signal in risk.get(
                "signals",
                [],
            )
            if signal.get("direction")
            == "negative"

            and signal.get("status")
            in {
                "active",
                "emerging",
            }

            and signal.get("domain")
            in {
                "commercial",
                "procurement",
                "security",
                "relationship",
            }

            and float(
                signal.get(
                    "strength",
                    0,
                )
            ) >= 0.65
        ]

        if material_negative:
            return "HIGH"

        if commercial_health == "At Risk":
            return "HIGH"

        if commercial_health == "Uncertain":
            return "MEDIUM"

        return "LOW"


async def analyze_account(
    account_id: str,
    risk: dict,
    poc: dict | None = None,
    expansion: dict | None = None,
) -> dict:

    return await AccountAnalysisEngine().analyze(
        account_id=account_id,
        risk=risk,
        poc=poc,
        expansion=expansion,
    )
