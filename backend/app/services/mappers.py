from app.domain.models import Transaction


def derive_risk_level(transaction: Transaction) -> str:
    metadata = transaction.metadata_ or {}
    if "risk_level" in metadata:
        return str(metadata["risk_level"])
    if transaction.amount_minor >= 100_000:
        return "high"
    if transaction.amount_minor >= 10_000:
        return "medium"
    return "low"


def customer_display_name(customer_email: str | None, external_id: str) -> str:
    if customer_email and "@" in customer_email:
        local = customer_email.split("@")[0]
        return local.replace(".", " ").replace("_", " ").title()
    return external_id


def map_intervention_to_action(intervention_type: str) -> str:
    mapping = {
        "do_nothing": "DO_NOTHING",
        "retry_payment": "RETRY",
        "send_reminder": "REMINDER_EMAIL",
        "offer_incentive": "INCENTIVE_10",
        "switch_payment_method": "SWITCH_METHOD",
        "manual_review": "MANUAL_REVIEW",
    }
    return mapping.get(intervention_type, intervention_type.upper())
