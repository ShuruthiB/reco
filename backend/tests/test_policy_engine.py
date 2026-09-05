from decimal import Decimal

from app.policies.engine import PolicyEngine


def test_policy_blocks_excessive_incentive():
    engine = PolicyEngine()
    result = engine.evaluate_candidate(
        intervention_type="offer_incentive",
        amount_minor=100_00,
        incentive_cost_minor=20_00,
        guardrails={"max_incentive_pct": 10, "max_contacts_30d": 5, "blocked_actions": []},
    )
    assert result.approved is False
    assert "Incentive exceeds" in (result.reject_reason or "")


def test_policy_allows_valid_reminder():
    engine = PolicyEngine()
    result = engine.evaluate_candidate(
        intervention_type="send_reminder",
        amount_minor=100_00,
        incentive_cost_minor=0,
        guardrails={"max_incentive_pct": 10, "max_contacts_30d": 5, "blocked_actions": []},
        contact_count_30d=1,
    )
    assert result.approved is True


def test_policy_blocks_contact_frequency():
    engine = PolicyEngine()
    result = engine.evaluate_candidate(
        intervention_type="send_reminder",
        amount_minor=100_00,
        incentive_cost_minor=0,
        guardrails={"max_incentive_pct": 10, "max_contacts_30d": 3, "blocked_actions": []},
        contact_count_30d=5,
    )
    assert result.approved is False
    assert "frequency" in (result.reject_reason or "").lower()


def test_extract_rule_strings_from_items():
    engine = PolicyEngine()
    rules = engine.extract_rule_strings({"items": ["Rule A", "Rule B"]})
    assert rules == ["Rule A", "Rule B"]


def test_extract_rule_strings_from_dict():
    engine = PolicyEngine()
    rules = engine.extract_rule_strings({"max_retry": 3})
    assert rules == ["max_retry: 3"]
