-- RECO Database Layer: Initial schema (16 core tables)
-- PostgreSQL / Supabase compatible.

BEGIN;

-- ---------------------------------------------------------------------------
-- Enumerated types
-- ---------------------------------------------------------------------------

CREATE TYPE merchant_status AS ENUM ('active', 'suspended', 'onboarding', 'churned');

CREATE TYPE consent_status AS ENUM ('granted', 'denied', 'unknown', 'withdrawn');

CREATE TYPE order_status AS ENUM ('created', 'attempted', 'paid', 'failed', 'cancelled', 'refunded');

CREATE TYPE transaction_status AS ENUM (
    'pending',
    'failed',
    'recovering',
    'recovered',
    'abandoned',
    'refunded',
    'disputed'
);

CREATE TYPE payment_method AS ENUM ('card', 'upi', 'netbanking', 'wallet', 'emi', 'other');

CREATE TYPE failure_reason AS ENUM (
    'insufficient_funds',
    'card_expired',
    'card_declined',
    'authentication_failed',
    'network_error',
    'limit_exceeded',
    'bank_declined',
    'invalid_card',
    'timeout',
    'unknown'
);

CREATE TYPE intervention_type AS ENUM (
    'do_nothing',
    'retry_payment',
    'send_reminder',
    'offer_incentive',
    'switch_payment_method',
    'manual_review'
);

CREATE TYPE candidate_eligibility AS ENUM ('eligible', 'rejected', 'deferred');

CREATE TYPE decision_status AS ENUM (
    'pending',
    'approved',
    'rejected',
    'executed',
    'failed',
    'superseded'
);

CREATE TYPE execution_status AS ENUM (
    'not_started',
    'queued',
    'in_progress',
    'succeeded',
    'failed',
    'cancelled'
);

CREATE TYPE experiment_status AS ENUM ('draft', 'running', 'paused', 'completed', 'archived');

CREATE TYPE experiment_outcome_type AS ENUM (
    'natural_recovery',
    'treated_recovery',
    'no_recovery',
    'partial_recovery',
    'refund'
);

CREATE TYPE budget_period_type AS ENUM ('daily', 'weekly', 'monthly', 'quarterly', 'custom');

CREATE TYPE budget_status AS ENUM ('active', 'exhausted', 'paused', 'expired');

CREATE TYPE policy_status AS ENUM ('draft', 'active', 'archived', 'pending_approval');

CREATE TYPE webhook_processing_status AS ENUM (
    'received',
    'verified',
    'processing',
    'processed',
    'failed',
    'quarantined',
    'dead_letter'
);

CREATE TYPE audit_actor_type AS ENUM ('system', 'user', 'worker', 'webhook', 'api');

-- ---------------------------------------------------------------------------
-- 1. merchants
-- ---------------------------------------------------------------------------

CREATE TABLE merchants (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    slug            TEXT NOT NULL,
    status          merchant_status NOT NULL DEFAULT 'onboarding',
    timezone        TEXT NOT NULL DEFAULT 'Asia/Kolkata',
    settings        JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT merchants_slug_unique UNIQUE (slug),
    CONSTRAINT merchants_name_not_empty CHECK (char_length(trim(name)) > 0)
);

COMMENT ON TABLE merchants IS 'Tenant organizations; root of multi-tenant isolation.';

-- ---------------------------------------------------------------------------
-- 2. customers
-- ---------------------------------------------------------------------------

CREATE TABLE customers (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    merchant_id         UUID NOT NULL REFERENCES merchants(id) ON DELETE RESTRICT,
    external_customer_id TEXT NOT NULL,
    email               TEXT,
    phone               TEXT,
    consent_status      consent_status NOT NULL DEFAULT 'unknown',
    consent_updated_at  TIMESTAMPTZ,
    contact_count_30d   INTEGER NOT NULL DEFAULT 0,
    metadata            JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT customers_merchant_external_unique
        UNIQUE (merchant_id, external_customer_id)
);

COMMENT ON TABLE customers IS 'Merchant-scoped customer identity and consent state.';

-- ---------------------------------------------------------------------------
-- 3. orders
-- ---------------------------------------------------------------------------

CREATE TABLE orders (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    merchant_id         UUID NOT NULL REFERENCES merchants(id) ON DELETE RESTRICT,
    customer_id         UUID NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
    external_order_id   TEXT NOT NULL,
    amount_minor        BIGINT NOT NULL,
    currency            CHAR(3) NOT NULL,
    status              order_status NOT NULL DEFAULT 'created',
    line_items          JSONB NOT NULL DEFAULT '[]'::jsonb,
    metadata            JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT orders_merchant_external_unique
        UNIQUE (merchant_id, external_order_id),
    CONSTRAINT orders_amount_minor_non_negative CHECK (amount_minor >= 0),
    CONSTRAINT orders_currency_format CHECK (currency ~ '^[A-Z]{3}$')
);

COMMENT ON TABLE orders IS 'Commercial orders associated with customers; source for payment attempts.';

-- ---------------------------------------------------------------------------
-- 4. transactions
-- ---------------------------------------------------------------------------

CREATE TABLE transactions (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    merchant_id             UUID NOT NULL REFERENCES merchants(id) ON DELETE RESTRICT,
    customer_id             UUID NOT NULL REFERENCES customers(id) ON DELETE RESTRICT,
    order_id                UUID REFERENCES orders(id) ON DELETE SET NULL,
    external_transaction_id TEXT NOT NULL,
    provider_payment_id     TEXT,
    amount_minor            BIGINT NOT NULL,
    currency                CHAR(3) NOT NULL,
    status                  transaction_status NOT NULL DEFAULT 'pending',
    failure_reason          failure_reason,
    payment_method          payment_method,
    state_version           INTEGER NOT NULL DEFAULT 1,
    failed_at               TIMESTAMPTZ,
    recovered_at            TIMESTAMPTZ,
    metadata                JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT transactions_merchant_external_unique
        UNIQUE (merchant_id, external_transaction_id),
    CONSTRAINT transactions_amount_minor_non_negative CHECK (amount_minor >= 0),
    CONSTRAINT transactions_currency_format CHECK (currency ~ '^[A-Z]{3}$'),
    CONSTRAINT transactions_state_version_positive CHECK (state_version > 0)
);

COMMENT ON TABLE transactions IS 'Canonical payment/recovery lifecycle record per payment attempt.';

-- ---------------------------------------------------------------------------
-- 5. payment_events
-- ---------------------------------------------------------------------------

CREATE TABLE payment_events (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    merchant_id         UUID NOT NULL REFERENCES merchants(id) ON DELETE RESTRICT,
    transaction_id      UUID NOT NULL REFERENCES transactions(id) ON DELETE RESTRICT,
    webhook_event_id      UUID,
    event_type          TEXT NOT NULL,
    provider_event_id   TEXT,
    amount_minor        BIGINT,
    currency            CHAR(3),
    normalized_payload  JSONB NOT NULL DEFAULT '{}'::jsonb,
    occurred_at         TIMESTAMPTZ NOT NULL,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT payment_events_currency_format
        CHECK (currency IS NULL OR currency ~ '^[A-Z]{3}$'),
    CONSTRAINT payment_events_merchant_provider_event_unique
        UNIQUE (merchant_id, provider_event_id)
);

COMMENT ON TABLE payment_events IS 'Normalized provider and internal payment lifecycle events.';

-- ---------------------------------------------------------------------------
-- 6. webhook_events
-- ---------------------------------------------------------------------------

CREATE TABLE webhook_events (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    merchant_id             UUID NOT NULL REFERENCES merchants(id) ON DELETE RESTRICT,
    webhook_event_id        TEXT NOT NULL,
    provider                TEXT NOT NULL DEFAULT 'razorpay',
    event_type              TEXT NOT NULL,
    payload_hash            TEXT NOT NULL,
    raw_payload             JSONB NOT NULL,
    signature_verified      BOOLEAN NOT NULL DEFAULT FALSE,
    processing_status       webhook_processing_status NOT NULL DEFAULT 'received',
    processing_error        TEXT,
    received_at             TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at            TIMESTAMPTZ,
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT webhook_events_webhook_event_id_unique UNIQUE (webhook_event_id),
    CONSTRAINT webhook_events_provider_event_unique
        UNIQUE (merchant_id, provider, webhook_event_id)
);

COMMENT ON TABLE webhook_events IS 'Raw inbound webhook receipts; deduplicated by webhook_event_id.';

-- Add FK from payment_events to webhook_events after webhook_events exists.
ALTER TABLE payment_events
    ADD CONSTRAINT payment_events_webhook_event_fk
    FOREIGN KEY (webhook_event_id) REFERENCES webhook_events(id) ON DELETE SET NULL;

-- ---------------------------------------------------------------------------
-- 12. policies (before policy_versions and decision tables)
-- ---------------------------------------------------------------------------

CREATE TABLE policies (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    merchant_id         UUID NOT NULL REFERENCES merchants(id) ON DELETE RESTRICT,
    name                TEXT NOT NULL,
    description         TEXT,
    status              policy_status NOT NULL DEFAULT 'draft',
    current_version_id  UUID,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT policies_merchant_name_unique UNIQUE (merchant_id, name)
);

COMMENT ON TABLE policies IS 'Merchant guardrail policy definitions; versions stored separately.';

-- ---------------------------------------------------------------------------
-- 13. policy_versions
-- ---------------------------------------------------------------------------

CREATE TABLE policy_versions (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    policy_id           UUID NOT NULL REFERENCES policies(id) ON DELETE RESTRICT,
    merchant_id         UUID NOT NULL REFERENCES merchants(id) ON DELETE RESTRICT,
    version_number      INTEGER NOT NULL,
    version_label       TEXT NOT NULL,
    rules               JSONB NOT NULL DEFAULT '{}'::jsonb,
    guardrails          JSONB NOT NULL DEFAULT '{}'::jsonb,
    effective_from      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    effective_to        TIMESTAMPTZ,
    approved_by         TEXT,
    change_summary      TEXT,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT policy_versions_policy_version_unique
        UNIQUE (policy_id, version_number),
    CONSTRAINT policy_versions_version_number_positive CHECK (version_number > 0)
);

COMMENT ON TABLE policy_versions IS 'Immutable versioned policy rules and guardrails.';

ALTER TABLE policies
    ADD CONSTRAINT policies_current_version_fk
    FOREIGN KEY (current_version_id) REFERENCES policy_versions(id) ON DELETE SET NULL;

-- ---------------------------------------------------------------------------
-- 6. intervention_candidates
-- ---------------------------------------------------------------------------

CREATE TABLE intervention_candidates (
    id                                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    merchant_id                         UUID NOT NULL REFERENCES merchants(id) ON DELETE RESTRICT,
    transaction_id                      UUID NOT NULL REFERENCES transactions(id) ON DELETE RESTRICT,
    intervention_type                     intervention_type NOT NULL,
    intervention_id                     TEXT NOT NULL,
    action_id                           TEXT NOT NULL,
    eligibility_status                  candidate_eligibility NOT NULL DEFAULT 'eligible',
    rejection_reasons                   JSONB NOT NULL DEFAULT '[]'::jsonb,
    baseline_recovery_probability       NUMERIC(8, 7),
    treatment_recovery_probability      NUMERIC(8, 7),
    predicted_uplift                    NUMERIC(8, 7),
    expected_incremental_revenue_minor  BIGINT,
    intervention_cost_minor             BIGINT NOT NULL DEFAULT 0,
    incentive_cost_minor                  BIGINT NOT NULL DEFAULT 0,
    operational_cost_minor                BIGINT NOT NULL DEFAULT 0,
    expected_net_contribution_minor       BIGINT,
    currency                            CHAR(3) NOT NULL,
    model_version                       TEXT NOT NULL,
    feature_snapshot                    JSONB NOT NULL DEFAULT '{}'::jsonb,
    scoring_metadata                    JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at                          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT intervention_candidates_currency_format
        CHECK (currency ~ '^[A-Z]{3}$'),
    CONSTRAINT intervention_candidates_transaction_action_unique
        UNIQUE (transaction_id, action_id),
    CONSTRAINT intervention_candidates_probabilities_range
        CHECK (
            (baseline_recovery_probability IS NULL OR (baseline_recovery_probability >= 0 AND baseline_recovery_probability <= 1))
            AND (treatment_recovery_probability IS NULL OR (treatment_recovery_probability >= 0 AND treatment_recovery_probability <= 1))
            AND (predicted_uplift IS NULL OR (predicted_uplift >= -1 AND predicted_uplift <= 1))
        )
);

COMMENT ON TABLE intervention_candidates IS
    'Candidate interventions scored per transaction; includes ML predictions and economics.';

-- ---------------------------------------------------------------------------
-- 14. agent_decisions (ML decisions)
-- ---------------------------------------------------------------------------

CREATE TABLE agent_decisions (
    id                              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    merchant_id                     UUID NOT NULL REFERENCES merchants(id) ON DELETE RESTRICT,
    transaction_id                  UUID NOT NULL REFERENCES transactions(id) ON DELETE RESTRICT,
    selected_candidate_id           UUID REFERENCES intervention_candidates(id) ON DELETE SET NULL,
    model_version                   TEXT NOT NULL,
    policy_version_id               UUID NOT NULL REFERENCES policy_versions(id) ON DELETE RESTRICT,
    decision_trigger                TEXT NOT NULL,
    transaction_state_version       INTEGER NOT NULL,
    ranked_candidates               JSONB NOT NULL DEFAULT '[]'::jsonb,
    feature_snapshot                JSONB NOT NULL DEFAULT '{}'::jsonb,
    scoring_metadata                JSONB NOT NULL DEFAULT '{}'::jsonb,
    rationale                       JSONB NOT NULL DEFAULT '{}'::jsonb,
    idempotency_key                 TEXT NOT NULL,
    created_at                      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT agent_decisions_idempotency_unique UNIQUE (idempotency_key),
    CONSTRAINT agent_decisions_tx_trigger_version_unique
        UNIQUE (transaction_id, decision_trigger, transaction_state_version)
);

COMMENT ON TABLE agent_decisions IS
    'ML agent decision snapshots; immutable record of scoring and ranking with model_version.';

-- ---------------------------------------------------------------------------
-- 7. intervention_decisions (financial / policy-approved decisions)
-- ---------------------------------------------------------------------------

CREATE TABLE intervention_decisions (
    id                              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    merchant_id                     UUID NOT NULL REFERENCES merchants(id) ON DELETE RESTRICT,
    transaction_id                  UUID NOT NULL REFERENCES transactions(id) ON DELETE RESTRICT,
    agent_decision_id               UUID REFERENCES agent_decisions(id) ON DELETE SET NULL,
    intervention_candidate_id       UUID REFERENCES intervention_candidates(id) ON DELETE SET NULL,
    policy_version_id               UUID NOT NULL REFERENCES policy_versions(id) ON DELETE RESTRICT,
    policy_version_label            TEXT NOT NULL,
    selected_action                 intervention_type NOT NULL,
    intervention_id                 TEXT,
    action_id                       TEXT,
    status                          decision_status NOT NULL DEFAULT 'pending',
    execution_status                execution_status NOT NULL DEFAULT 'not_started',
    expected_net_contribution_minor BIGINT,
    expected_incremental_revenue_minor BIGINT,
    total_cost_minor                BIGINT NOT NULL DEFAULT 0,
    currency                        CHAR(3) NOT NULL,
    decision_rationale              JSONB NOT NULL DEFAULT '{}'::jsonb,
    policy_evaluation               JSONB NOT NULL DEFAULT '{}'::jsonb,
    executed_at                     TIMESTAMPTZ,
    provider_reference              TEXT,
    idempotency_key                 TEXT NOT NULL,
    created_at                      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT intervention_decisions_idempotency_unique UNIQUE (idempotency_key),
    CONSTRAINT intervention_decisions_currency_format CHECK (currency ~ '^[A-Z]{3}$')
);

COMMENT ON TABLE intervention_decisions IS
    'Policy-validated financial decisions; stores policy_version and execution action identifiers.';

-- ---------------------------------------------------------------------------
-- 8. experiments
-- ---------------------------------------------------------------------------

CREATE TABLE experiments (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    merchant_id         UUID NOT NULL REFERENCES merchants(id) ON DELETE RESTRICT,
    name                TEXT NOT NULL,
    description         TEXT,
    status              experiment_status NOT NULL DEFAULT 'draft',
    holdout_percentage  NUMERIC(5, 4) NOT NULL DEFAULT 0.1000,
    arms                JSONB NOT NULL DEFAULT '[]'::jsonb,
    eligibility_rules   JSONB NOT NULL DEFAULT '{}'::jsonb,
    started_at          TIMESTAMPTZ,
    ended_at            TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT experiments_merchant_name_unique UNIQUE (merchant_id, name),
    CONSTRAINT experiments_holdout_range
        CHECK (holdout_percentage >= 0 AND holdout_percentage <= 1)
);

COMMENT ON TABLE experiments IS 'A/B and holdout experiment definitions for incrementality measurement.';

-- ---------------------------------------------------------------------------
-- 9. experiment_assignments
-- ---------------------------------------------------------------------------

CREATE TABLE experiment_assignments (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id       UUID NOT NULL REFERENCES experiments(id) ON DELETE RESTRICT,
    merchant_id         UUID NOT NULL REFERENCES merchants(id) ON DELETE RESTRICT,
    transaction_id      UUID NOT NULL REFERENCES transactions(id) ON DELETE RESTRICT,
    arm_name            TEXT NOT NULL,
    is_holdout          BOOLEAN NOT NULL DEFAULT FALSE,
    assigned_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT experiment_assignments_experiment_tx_unique
        UNIQUE (experiment_id, transaction_id)
);

COMMENT ON TABLE experiment_assignments IS 'Deterministic transaction-to-experiment-arm assignments.';

-- ---------------------------------------------------------------------------
-- 10. experiment_outcomes
-- ---------------------------------------------------------------------------

CREATE TABLE experiment_outcomes (
    id                          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    experiment_id               UUID NOT NULL REFERENCES experiments(id) ON DELETE RESTRICT,
    experiment_assignment_id    UUID NOT NULL REFERENCES experiment_assignments(id) ON DELETE RESTRICT,
    merchant_id                 UUID NOT NULL REFERENCES merchants(id) ON DELETE RESTRICT,
    transaction_id              UUID NOT NULL REFERENCES transactions(id) ON DELETE RESTRICT,
    outcome_type                experiment_outcome_type NOT NULL,
    recovered_amount_minor      BIGINT NOT NULL DEFAULT 0,
    intervention_cost_minor     BIGINT NOT NULL DEFAULT 0,
    currency                    CHAR(3) NOT NULL,
    attributed_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    attribution_metadata        JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT experiment_outcomes_currency_format CHECK (currency ~ '^[A-Z]{3}$'),
    CONSTRAINT experiment_outcomes_assignment_unique
        UNIQUE (experiment_assignment_id)
);

COMMENT ON TABLE experiment_outcomes IS
    'Attributed recovery outcomes for experiment analysis (natural vs treated recovery).';

-- ---------------------------------------------------------------------------
-- 11. recovery_budgets
-- ---------------------------------------------------------------------------

CREATE TABLE recovery_budgets (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    merchant_id         UUID NOT NULL REFERENCES merchants(id) ON DELETE RESTRICT,
    name                TEXT NOT NULL,
    period_type         budget_period_type NOT NULL,
    period_start        TIMESTAMPTZ NOT NULL,
    period_end          TIMESTAMPTZ NOT NULL,
    budget_limit_minor  BIGINT NOT NULL,
    reserved_minor      BIGINT NOT NULL DEFAULT 0,
    consumed_minor      BIGINT NOT NULL DEFAULT 0,
    currency            CHAR(3) NOT NULL,
    status              budget_status NOT NULL DEFAULT 'active',
    metadata            JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT recovery_budgets_merchant_name_period_unique
        UNIQUE (merchant_id, name, period_start),
    CONSTRAINT recovery_budgets_limit_non_negative CHECK (budget_limit_minor >= 0),
    CONSTRAINT recovery_budgets_reserved_non_negative CHECK (reserved_minor >= 0),
    CONSTRAINT recovery_budgets_consumed_non_negative CHECK (consumed_minor >= 0),
    CONSTRAINT recovery_budgets_currency_format CHECK (currency ~ '^[A-Z]{3}$'),
    CONSTRAINT recovery_budgets_period_valid CHECK (period_end > period_start)
);

COMMENT ON TABLE recovery_budgets IS 'Merchant recovery intervention budgets by period.';

-- ---------------------------------------------------------------------------
-- 15. audit_logs (append-only)
-- ---------------------------------------------------------------------------

CREATE TABLE audit_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    merchant_id     UUID REFERENCES merchants(id) ON DELETE RESTRICT,
    entity_type     TEXT NOT NULL,
    entity_id       UUID NOT NULL,
    action          TEXT NOT NULL,
    actor_type      audit_actor_type NOT NULL DEFAULT 'system',
    actor_id        TEXT,
    before_state    JSONB,
    after_state     JSONB,
    metadata        JSONB NOT NULL DEFAULT '{}'::jsonb,
    occurred_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

COMMENT ON TABLE audit_logs IS
    'Append-only immutable audit trail; no updated_at by design.';

COMMIT;
