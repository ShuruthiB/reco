-- RECO Database Layer: Indexes for query performance

BEGIN;

-- merchants
CREATE INDEX idx_merchants_status ON merchants (status);

-- customers
CREATE INDEX idx_customers_merchant_id ON customers (merchant_id);
CREATE INDEX idx_customers_consent_status ON customers (merchant_id, consent_status);
CREATE INDEX idx_customers_created_at ON customers (created_at DESC);

-- orders
CREATE INDEX idx_orders_merchant_id ON orders (merchant_id);
CREATE INDEX idx_orders_customer_id ON orders (customer_id);
CREATE INDEX idx_orders_status ON orders (merchant_id, status);
CREATE INDEX idx_orders_created_at ON orders (merchant_id, created_at DESC);

-- transactions
CREATE INDEX idx_transactions_merchant_id ON transactions (merchant_id);
CREATE INDEX idx_transactions_customer_id ON transactions (customer_id);
CREATE INDEX idx_transactions_order_id ON transactions (order_id) WHERE order_id IS NOT NULL;
CREATE INDEX idx_transactions_status ON transactions (merchant_id, status);
CREATE INDEX idx_transactions_failure_reason ON transactions (merchant_id, failure_reason)
    WHERE failure_reason IS NOT NULL;
CREATE INDEX idx_transactions_payment_method ON transactions (merchant_id, payment_method)
    WHERE payment_method IS NOT NULL;
CREATE INDEX idx_transactions_failed_at ON transactions (merchant_id, failed_at DESC)
    WHERE failed_at IS NOT NULL;
CREATE INDEX idx_transactions_recovered_at ON transactions (merchant_id, recovered_at DESC)
    WHERE recovered_at IS NOT NULL;
CREATE INDEX idx_transactions_created_at ON transactions (merchant_id, created_at DESC);
CREATE INDEX idx_transactions_provider_payment_id ON transactions (provider_payment_id)
    WHERE provider_payment_id IS NOT NULL;

-- payment_events
CREATE INDEX idx_payment_events_merchant_id ON payment_events (merchant_id);
CREATE INDEX idx_payment_events_transaction_id ON payment_events (transaction_id);
CREATE INDEX idx_payment_events_event_type ON payment_events (merchant_id, event_type);
CREATE INDEX idx_payment_events_occurred_at ON payment_events (merchant_id, occurred_at DESC);
CREATE INDEX idx_payment_events_webhook_event_id ON payment_events (webhook_event_id)
    WHERE webhook_event_id IS NOT NULL;

-- webhook_events
CREATE INDEX idx_webhook_events_merchant_id ON webhook_events (merchant_id);
CREATE INDEX idx_webhook_events_processing_status ON webhook_events (merchant_id, processing_status);
CREATE INDEX idx_webhook_events_received_at ON webhook_events (merchant_id, received_at DESC);
CREATE INDEX idx_webhook_events_event_type ON webhook_events (merchant_id, event_type);
CREATE INDEX idx_webhook_events_payload_hash ON webhook_events (payload_hash);

-- intervention_candidates
CREATE INDEX idx_intervention_candidates_merchant_id ON intervention_candidates (merchant_id);
CREATE INDEX idx_intervention_candidates_transaction_id ON intervention_candidates (transaction_id);
CREATE INDEX idx_intervention_candidates_type ON intervention_candidates (merchant_id, intervention_type);
CREATE INDEX idx_intervention_candidates_model_version ON intervention_candidates (model_version);
CREATE INDEX idx_intervention_candidates_eligibility ON intervention_candidates (merchant_id, eligibility_status);

-- agent_decisions
CREATE INDEX idx_agent_decisions_merchant_id ON agent_decisions (merchant_id);
CREATE INDEX idx_agent_decisions_transaction_id ON agent_decisions (transaction_id);
CREATE INDEX idx_agent_decisions_model_version ON agent_decisions (model_version);
CREATE INDEX idx_agent_decisions_policy_version_id ON agent_decisions (policy_version_id);
CREATE INDEX idx_agent_decisions_created_at ON agent_decisions (merchant_id, created_at DESC);

-- intervention_decisions
CREATE INDEX idx_intervention_decisions_merchant_id ON intervention_decisions (merchant_id);
CREATE INDEX idx_intervention_decisions_transaction_id ON intervention_decisions (transaction_id);
CREATE INDEX idx_intervention_decisions_agent_decision_id ON intervention_decisions (agent_decision_id)
    WHERE agent_decision_id IS NOT NULL;
CREATE INDEX idx_intervention_decisions_policy_version_id ON intervention_decisions (policy_version_id);
CREATE INDEX idx_intervention_decisions_status ON intervention_decisions (merchant_id, status);
CREATE INDEX idx_intervention_decisions_execution_status ON intervention_decisions (merchant_id, execution_status);
CREATE INDEX idx_intervention_decisions_selected_action ON intervention_decisions (merchant_id, selected_action);
CREATE INDEX idx_intervention_decisions_executed_at ON intervention_decisions (executed_at DESC)
    WHERE executed_at IS NOT NULL;

-- experiments
CREATE INDEX idx_experiments_merchant_id ON experiments (merchant_id);
CREATE INDEX idx_experiments_status ON experiments (merchant_id, status);

-- experiment_assignments
CREATE INDEX idx_experiment_assignments_experiment_id ON experiment_assignments (experiment_id);
CREATE INDEX idx_experiment_assignments_transaction_id ON experiment_assignments (transaction_id);
CREATE INDEX idx_experiment_assignments_arm ON experiment_assignments (experiment_id, arm_name);
CREATE INDEX idx_experiment_assignments_holdout ON experiment_assignments (experiment_id, is_holdout);

-- experiment_outcomes
CREATE INDEX idx_experiment_outcomes_experiment_id ON experiment_outcomes (experiment_id);
CREATE INDEX idx_experiment_outcomes_merchant_id ON experiment_outcomes (merchant_id);
CREATE INDEX idx_experiment_outcomes_outcome_type ON experiment_outcomes (experiment_id, outcome_type);
CREATE INDEX idx_experiment_outcomes_transaction_id ON experiment_outcomes (transaction_id);

-- recovery_budgets
CREATE INDEX idx_recovery_budgets_merchant_id ON recovery_budgets (merchant_id);
CREATE INDEX idx_recovery_budgets_status ON recovery_budgets (merchant_id, status);
CREATE INDEX idx_recovery_budgets_period ON recovery_budgets (merchant_id, period_start, period_end);

-- policies
CREATE INDEX idx_policies_merchant_id ON policies (merchant_id);
CREATE INDEX idx_policies_status ON policies (merchant_id, status);

-- policy_versions
CREATE INDEX idx_policy_versions_policy_id ON policy_versions (policy_id);
CREATE INDEX idx_policy_versions_merchant_id ON policy_versions (merchant_id);
CREATE INDEX idx_policy_versions_effective ON policy_versions (merchant_id, effective_from, effective_to);

-- audit_logs (append-only queries)
CREATE INDEX idx_audit_logs_merchant_id ON audit_logs (merchant_id);
CREATE INDEX idx_audit_logs_entity ON audit_logs (entity_type, entity_id);
CREATE INDEX idx_audit_logs_occurred_at ON audit_logs (merchant_id, occurred_at DESC);
CREATE INDEX idx_audit_logs_action ON audit_logs (merchant_id, action);
CREATE INDEX idx_audit_logs_actor ON audit_logs (actor_type, actor_id);

COMMIT;
