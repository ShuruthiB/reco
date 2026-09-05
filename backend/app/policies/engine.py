from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass
class PolicyEvaluationResult:
    approved: bool
    reject_reason: str | None = None
    evaluation: dict[str, Any] | None = None


class PolicyEngine:
    """Rule-based policy validation using stored policy_versions guardrails."""

    def evaluate_candidate(
        self,
        *,
        intervention_type: str,
        amount_minor: int,
        incentive_cost_minor: int,
        guardrails: dict[str, Any],
        contact_count_30d: int = 0,
    ) -> PolicyEvaluationResult:
        max_incentive_pct = Decimal(str(guardrails.get("max_incentive_pct", 20)))
        max_incentive_minor = int(
            Decimal(amount_minor) * max_incentive_pct / Decimal(100)
        )
        max_contacts = int(guardrails.get("max_contacts_30d", 5))
        blocked_actions = set(guardrails.get("blocked_actions", []))

        evaluation: dict[str, Any] = {
            "max_incentive_minor": max_incentive_minor,
            "max_contacts_30d": max_contacts,
            "blocked_actions": list(blocked_actions),
        }

        if intervention_type in blocked_actions:
            return PolicyEvaluationResult(
                approved=False,
                reject_reason=f"Action '{intervention_type}' is blocked by policy.",
                evaluation=evaluation,
            )

        if contact_count_30d >= max_contacts and intervention_type in {
            "send_reminder",
            "offer_incentive",
        }:
            return PolicyEvaluationResult(
                approved=False,
                reject_reason="Contact frequency cap exceeded for customer.",
                evaluation=evaluation,
            )

        if intervention_type == "offer_incentive" and incentive_cost_minor > max_incentive_minor:
            return PolicyEvaluationResult(
                approved=False,
                reject_reason="Incentive exceeds maximum allowed by policy.",
                evaluation=evaluation,
            )

        return PolicyEvaluationResult(approved=True, evaluation=evaluation)

    def extract_rule_strings(self, rules: dict[str, Any]) -> list[str]:
        if not rules:
            return []
        if isinstance(rules.get("items"), list):
            return [str(item) for item in rules["items"]]
        return [f"{key}: {value}" for key, value in rules.items()]
