#!/usr/bin/env python3
"""Seed RECO database with realistic synthetic data for development and testing."""

from __future__ import annotations

import json
import os
import random
import uuid
from datetime import UTC, datetime, timedelta

import psycopg2
from psycopg2.extras import execute_batch

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/reco",
).replace("postgresql+asyncpg://", "postgresql://")

FAILURE_REASONS = [
    "insufficient_funds",
    "card_expired",
    "card_declined",
    "authentication_failed",
    "network_error",
    "limit_exceeded",
    "bank_declined",
    "invalid_card",
    "timeout",
    "unknown",
]
PAYMENT_METHODS = ["card", "upi", "netbanking", "wallet", "emi"]
STATUSES = ["failed", "recovering", "recovered", "pending", "abandoned"]
INTERVENTION_TYPES = [
    "do_nothing",
    "retry_payment",
    "send_reminder",
    "offer_incentive",
    "switch_payment_method",
]
RISK_LEVELS = ["low", "medium", "high"]


def utcnow() -> datetime:
    return datetime.now(UTC)


def main() -> None:
    random.seed(42)
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = False
    cur = conn.cursor()

    merchant_id = uuid.uuid4()
    cur.execute(
        """
        INSERT INTO merchants (id, name, slug, status, timezone, settings, created_at, updated_at)
        VALUES (%s, %s, %s, 'active', 'Asia/Kolkata', '{}', NOW(), NOW())
        ON CONFLICT (slug) DO UPDATE SET updated_at = NOW()
        RETURNING id
        """,
        (merchant_id, "Acme Commerce", "acme-commerce"),
    )
    row = cur.fetchone()
    merchant_id = row[0] if row else merchant_id

    policy_id = uuid.uuid4()
    policy_version_id = uuid.uuid4()
    cur.execute(
        """
        INSERT INTO policies (id, merchant_id, name, description, status, created_at, updated_at)
        VALUES (%s, %s, 'Recovery Guardrails', 'Default recovery policy', 'active', NOW(), NOW())
        ON CONFLICT (merchant_id, name) DO UPDATE SET updated_at = NOW()
        RETURNING id
        """,
        (policy_id, merchant_id),
    )
    policy_id = cur.fetchone()[0]

    cur.execute(
        """
        INSERT INTO policy_versions (
            id, policy_id, merchant_id, version_number, version_label,
            rules, guardrails, effective_from, approved_by, change_summary, created_at, updated_at
        ) VALUES (
            %s, %s, %s, 1, 'v1.0.0',
            '{"items": ["Max 10%% incentive for standard segment", "Max 2 SMS per week"]}'::jsonb,
            '{"max_incentive_pct": 10, "max_contacts_30d": 5, "blocked_actions": []}'::jsonb,
            NOW() - INTERVAL '30 days', 'seed-script', 'Initial policy', NOW(), NOW()
        )
        ON CONFLICT (policy_id, version_number) DO NOTHING
        RETURNING id
        """,
        (policy_version_id, policy_id, merchant_id),
    )
    fetched = cur.fetchone()
    if fetched:
        policy_version_id = fetched[0]
    else:
        cur.execute(
            "SELECT id FROM policy_versions WHERE policy_id = %s AND version_number = 1",
            (policy_id,),
        )
        policy_version_id = cur.fetchone()[0]

    cur.execute(
        "UPDATE policies SET current_version_id = %s, updated_at = NOW() WHERE id = %s",
        (policy_version_id, policy_id),
    )

    customer_ids: list[uuid.UUID] = []
    for i in range(500):
        cid = uuid.uuid4()
        customer_ids.append(cid)
        cur.execute(
            """
            INSERT INTO customers (
                id, merchant_id, external_customer_id, email, phone,
                consent_status, contact_count_30d, metadata, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, 'granted', %s, '{}', NOW(), NOW())
            ON CONFLICT (merchant_id, external_customer_id) DO NOTHING
            """,
            (
                cid,
                merchant_id,
                f"cust_{i:05d}",
                f"user{i}@example.com",
                f"+9198{random.randint(10000000, 99999999)}",
                random.randint(0, 8),
            ),
        )

    cur.execute(
        "SELECT id FROM customers WHERE merchant_id = %s LIMIT 500",
        (merchant_id,),
    )
    customer_ids = [row[0] for row in cur.fetchall()]

    experiment_ids = []
    for idx, (name, arms) in enumerate(
        [
            (
                "Smart Retries vs Fixed Schedule",
                [
                    {"name": "Control (Fixed 24h)", "traffic_share": 0.1, "incremental_uplift": 0},
                    {"name": "Treatment (ML Timing)", "traffic_share": 0.9, "incremental_uplift": 0.12},
                ],
            ),
            (
                "Dynamic Incentives for High Risk",
                [
                    {"name": "Control (No Incentive)", "traffic_share": 0.5, "incremental_uplift": 0},
                    {"name": "Treatment (5-15% Dynamic)", "traffic_share": 0.5, "incremental_uplift": 0.28},
                ],
            ),
            (
                "Reminder Channel Test",
                [
                    {"name": "Email", "traffic_share": 0.5, "incremental_uplift": 0.08},
                    {"name": "SMS", "traffic_share": 0.5, "incremental_uplift": 0.15},
                ],
            ),
        ]
    ):
        exp_id = uuid.uuid4()
        experiment_ids.append(exp_id)
        started_at = utcnow() - timedelta(days=30 - idx * 5)
        cur.execute(
            """
            INSERT INTO experiments (
                id, merchant_id, name, description, status, holdout_percentage,
                arms, eligibility_rules, started_at, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, 'running', 0.10, %s::jsonb, '{}'::jsonb,
                %s, NOW(), NOW()
            )
            ON CONFLICT (merchant_id, name) DO UPDATE SET updated_at = NOW()
            RETURNING id
            """,
            (exp_id, merchant_id, name, f"Experiment {idx + 1}", json.dumps(arms), started_at),
        )
        fetched = cur.fetchone()
        if fetched:
            experiment_ids[idx] = fetched[0]

    budget_specs = [
        ("Monthly Incentive Budget", "monthly", 500_000_00, 120_000_00, 10_000_00),
        ("Weekly SMS Budget", "weekly", 50_000_00, 12_000_00, 2_000_00),
        ("Quarterly Recovery Cap", "quarterly", 2_000_000_00, 450_000_00, 50_000_00),
    ]
    for name, period, limit, consumed, reserved in budget_specs:
        cur.execute(
            """
            INSERT INTO recovery_budgets (
                id, merchant_id, name, period_type, period_start, period_end,
                budget_limit_minor, reserved_minor, consumed_minor, currency, status,
                metadata, created_at, updated_at
            ) VALUES (
                %s, %s, %s, %s, NOW() - INTERVAL '15 days', NOW() + INTERVAL '15 days',
                %s, %s, %s, 'USD', 'active', '{}', NOW(), NOW()
            )
            ON CONFLICT (merchant_id, name, period_start) DO NOTHING
            """,
            (uuid.uuid4(), merchant_id, name, period, limit, reserved, consumed),
        )

    tx_count = int(os.getenv("SEED_TRANSACTION_COUNT", "10000"))
    print(f"Seeding {tx_count} transactions for merchant {merchant_id}")

    transactions: list[tuple] = []
    for i in range(tx_count):
        tx_id = uuid.uuid4()
        customer_id = random.choice(customer_ids)
        status = random.choices(STATUSES, weights=[40, 10, 25, 20, 5])[0]
        failure = random.choice(FAILURE_REASONS) if status in {"failed", "recovering", "pending"} else None
        method = random.choice(PAYMENT_METHODS)
        amount_minor = random.randint(500, 500_000_00)
        risk = random.choice(RISK_LEVELS)
        created = utcnow() - timedelta(days=random.randint(0, 90), hours=random.randint(0, 23))
        failed_at = created + timedelta(hours=1) if failure else None
        recovered_at = (
            failed_at + timedelta(days=random.randint(1, 7))
            if status == "recovered" and failed_at
            else None
        )
        transactions.append(
            (
                tx_id,
                merchant_id,
                customer_id,
                None,
                f"txn_{i:08d}",
                f"pay_{uuid.uuid4().hex[:12]}",
                amount_minor,
                "USD",
                status,
                failure,
                method,
                1,
                failed_at,
                recovered_at,
                f'{{"risk_level": "{risk}"}}',
                created,
                created,
            )
        )

    execute_batch(
        cur,
        """
        INSERT INTO transactions (
            id, merchant_id, customer_id, order_id, external_transaction_id,
            provider_payment_id, amount_minor, currency, status, failure_reason,
            payment_method, state_version, failed_at, recovered_at, metadata,
            created_at, updated_at
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb,%s,%s)
        ON CONFLICT (merchant_id, external_transaction_id) DO NOTHING
        """,
        transactions,
        page_size=500,
    )

    cur.execute("SELECT id, amount_minor, currency, status, metadata FROM transactions WHERE merchant_id = %s", (merchant_id,))
    all_tx = cur.fetchall()

    # Payment events, candidates, decisions for subset
    sample_tx = random.sample(all_tx, min(3000, len(all_tx)))
    for tx_id, amount_minor, currency, status, metadata in sample_tx:
        cur.execute(
            """
            INSERT INTO payment_events (
                id, merchant_id, transaction_id, event_type, provider_event_id,
                amount_minor, currency, normalized_payload, occurred_at, created_at, updated_at
            ) VALUES (%s,%s,%s,'payment.failed',%s,%s,%s,'{}',NOW(),NOW(),NOW())
            ON CONFLICT (merchant_id, provider_event_id) DO NOTHING
            """,
            (uuid.uuid4(), merchant_id, tx_id, f"evt_{uuid.uuid4().hex}", amount_minor, currency),
        )

        risk = "medium"
        if metadata and "risk_level" in str(metadata):
            risk = metadata.get("risk_level", "medium") if isinstance(metadata, dict) else "medium"

        candidates = []
        for action_idx, itype in enumerate(INTERVENTION_TYPES):
            action_id = f"act_{itype}"
            baseline = {"low": 0.20, "medium": 0.12, "high": 0.05}[risk]
            uplift_map = {
                "do_nothing": 0.0,
                "retry_payment": 0.02,
                "send_reminder": 0.08,
                "offer_incentive": 0.25,
                "switch_payment_method": 0.06,
            }
            uplift = uplift_map[itype]
            incentive = int(amount_minor * 0.10) if itype == "offer_incentive" else 0
            op_cost = 50 if itype == "retry_payment" else (1 if itype == "send_reminder" else 0)
            rev = int(amount_minor * uplift)
            net = rev - incentive - op_cost
            cand_id = uuid.uuid4()
            candidates.append((cand_id, itype, net, uplift))
            cur.execute(
                """
                INSERT INTO intervention_candidates (
                    id, merchant_id, transaction_id, intervention_type, intervention_id,
                    action_id, eligibility_status, rejection_reasons,
                    baseline_recovery_probability, treatment_recovery_probability, predicted_uplift,
                    expected_incremental_revenue_minor, intervention_cost_minor, incentive_cost_minor,
                    operational_cost_minor, expected_net_contribution_minor, currency,
                    model_version, feature_snapshot, scoring_metadata, created_at, updated_at
                ) VALUES (
                    %s,%s,%s,%s,%s,%s,'eligible','[]'::jsonb,
                    %s,%s,%s,%s,%s,%s,%s,%s,%s,
                    'heuristic-v0', %s::jsonb, '{}'::jsonb, NOW(), NOW()
                )
                ON CONFLICT (transaction_id, action_id) DO NOTHING
                """,
                (
                    cand_id,
                    merchant_id,
                    tx_id,
                    itype,
                    f"int_{itype}",
                    action_id,
                    baseline,
                    baseline + uplift,
                    uplift,
                    rev,
                    op_cost,
                    incentive,
                    op_cost,
                    net,
                    currency,
                    f'{{"risk_profile": "{risk}"}}',
                ),
            )

        best = max(candidates, key=lambda c: c[2])
        agent_id = uuid.uuid4()
        cur.execute(
            """
            INSERT INTO agent_decisions (
                id, merchant_id, transaction_id, selected_candidate_id, model_version,
                policy_version_id, decision_trigger, transaction_state_version,
                ranked_candidates, feature_snapshot, scoring_metadata, rationale,
                idempotency_key, created_at, updated_at
            ) VALUES (
                %s,%s,%s,%s,'heuristic-v0',%s,'payment_failed',1,'[]','{}','{}',
                '{"summary": "Heuristic ranking"}', %s, NOW(), NOW()
            )
            ON CONFLICT (idempotency_key) DO NOTHING
            """,
            (agent_id, merchant_id, tx_id, best[0], policy_version_id, f"agent_{tx_id}"),
        )

        if random.random() < 0.6:
            executed = status == "recovered" and random.random() < 0.7
            cur.execute(
                """
                INSERT INTO intervention_decisions (
                    id, merchant_id, transaction_id, agent_decision_id,
                    intervention_candidate_id, policy_version_id, policy_version_label,
                    selected_action, intervention_id, action_id, status, execution_status,
                    expected_net_contribution_minor, expected_incremental_revenue_minor,
                    total_cost_minor, currency, decision_rationale, policy_evaluation,
                    executed_at, idempotency_key, created_at, updated_at
                ) VALUES (
                    %s,%s,%s,%s,%s,%s,'v1.0.0',%s,%s,%s,
                    %s,%s,%s,%s,%s,%s,
                    '{"summary": "Policy-approved action", "confidence": 0.75}',
                    '{"approved": true}', %s, %s, NOW(), NOW()
                )
                ON CONFLICT (idempotency_key) DO NOTHING
                """,
                (
                    uuid.uuid4(),
                    merchant_id,
                    tx_id,
                    agent_id,
                    best[0],
                    policy_version_id,
                    best[1],
                    f"int_{best[1]}",
                    f"act_{best[1]}",
                    "executed" if executed else "approved",
                    "succeeded" if executed else "not_started",
                    best[2],
                    int(amount_minor * best[3]),
                    50,
                    currency,
                    utcnow() if executed else None,
                    f"dec_{tx_id}",
                ),
            )

    # Experiment assignments and outcomes
    exp_sample = random.sample(all_tx, min(5000, len(all_tx)))
    for tx_id, amount_minor, currency, status, _ in exp_sample:
        exp_id = random.choice(experiment_ids)
        arm = random.choice(["control", "treatment"])
        is_holdout = arm == "control"
        assign_id = uuid.uuid4()
        cur.execute(
            """
            INSERT INTO experiment_assignments (
                id, experiment_id, merchant_id, transaction_id, arm_name,
                is_holdout, assigned_at, created_at, updated_at
            ) VALUES (%s,%s,%s,%s,%s,%s,NOW(),NOW(),NOW())
            ON CONFLICT (experiment_id, transaction_id) DO NOTHING
            RETURNING id
            """,
            (assign_id, exp_id, merchant_id, tx_id, arm, is_holdout),
        )
        fetched = cur.fetchone()
        if not fetched:
            continue
        assign_id = fetched[0]

        if status == "recovered":
            if is_holdout:
                outcome = "natural_recovery"
            else:
                outcome = "treated_recovery" if random.random() < 0.65 else "natural_recovery"
            recovered = amount_minor if outcome == "treated_recovery" else int(amount_minor * random.uniform(0.5, 1.0))
            cost = 0 if is_holdout else random.randint(100, 5000)
            cur.execute(
                """
                INSERT INTO experiment_outcomes (
                    id, experiment_id, experiment_assignment_id, merchant_id, transaction_id,
                    outcome_type, recovered_amount_minor, intervention_cost_minor, currency,
                    attributed_at, attribution_metadata, created_at, updated_at
                ) VALUES (
                    %s,%s,%s,%s,%s,%s,%s,%s,%s,NOW(),'{}',NOW(),NOW()
                )
                ON CONFLICT (experiment_assignment_id) DO NOTHING
                """,
                (uuid.uuid4(), exp_id, assign_id, merchant_id, tx_id, outcome, recovered, cost, currency),
            )
        elif random.random() < 0.3:
            cur.execute(
                """
                INSERT INTO experiment_outcomes (
                    id, experiment_id, experiment_assignment_id, merchant_id, transaction_id,
                    outcome_type, recovered_amount_minor, intervention_cost_minor, currency,
                    attributed_at, attribution_metadata, created_at, updated_at
                ) VALUES (
                    %s,%s,%s,%s,%s,'no_recovery',0,%s,%s,NOW(),'{}',NOW(),NOW()
                )
                ON CONFLICT (experiment_assignment_id) DO NOTHING
                """,
                (uuid.uuid4(), exp_id, assign_id, merchant_id, tx_id, random.randint(0, 500), currency),
            )

    audit_rows = [
        ("DECISION_EVALUATED", "transaction", "Evaluated failed payment for recovery."),
        ("ACTION_EXECUTED", "intervention_decision", "Dispatched recovery action."),
        ("BUDGET_ADJUSTED", "recovery_budget", "Budget consumption recorded."),
        ("POLICY_UPDATED", "policy", "Policy version activated."),
    ]
    for action, entity_type, summary in audit_rows:
        cur.execute(
            """
            INSERT INTO audit_logs (
                id, merchant_id, entity_type, entity_id, action,
                actor_type, actor_id, metadata, occurred_at, created_at
            ) VALUES (%s,%s,%s,%s,%s,'system','seed-script',%s,NOW(),NOW())
            """,
            (
                uuid.uuid4(),
                merchant_id,
                entity_type,
                uuid.uuid4(),
                action,
                f'{{"summary": "{summary}"}}',
            ),
        )

    conn.commit()
    cur.close()
    conn.close()
    print(f"Seed complete. Merchant ID: {merchant_id}")
    print(f"Set DEFAULT_MERCHANT_ID={merchant_id} in your .env file.")


if __name__ == "__main__":
    main()
