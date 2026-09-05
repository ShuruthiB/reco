-- RECO Database Layer: Triggers for updated_at and audit append-only enforcement

BEGIN;

-- updated_at triggers on all mutable tables
CREATE TRIGGER trg_merchants_updated_at
    BEFORE UPDATE ON merchants
    FOR EACH ROW EXECUTE FUNCTION reco_set_updated_at();

CREATE TRIGGER trg_customers_updated_at
    BEFORE UPDATE ON customers
    FOR EACH ROW EXECUTE FUNCTION reco_set_updated_at();

CREATE TRIGGER trg_orders_updated_at
    BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION reco_set_updated_at();

CREATE TRIGGER trg_transactions_updated_at
    BEFORE UPDATE ON transactions
    FOR EACH ROW EXECUTE FUNCTION reco_set_updated_at();

CREATE TRIGGER trg_payment_events_updated_at
    BEFORE UPDATE ON payment_events
    FOR EACH ROW EXECUTE FUNCTION reco_set_updated_at();

CREATE TRIGGER trg_webhook_events_updated_at
    BEFORE UPDATE ON webhook_events
    FOR EACH ROW EXECUTE FUNCTION reco_set_updated_at();

CREATE TRIGGER trg_intervention_candidates_updated_at
    BEFORE UPDATE ON intervention_candidates
    FOR EACH ROW EXECUTE FUNCTION reco_set_updated_at();

CREATE TRIGGER trg_agent_decisions_updated_at
    BEFORE UPDATE ON agent_decisions
    FOR EACH ROW EXECUTE FUNCTION reco_set_updated_at();

CREATE TRIGGER trg_intervention_decisions_updated_at
    BEFORE UPDATE ON intervention_decisions
    FOR EACH ROW EXECUTE FUNCTION reco_set_updated_at();

CREATE TRIGGER trg_experiments_updated_at
    BEFORE UPDATE ON experiments
    FOR EACH ROW EXECUTE FUNCTION reco_set_updated_at();

CREATE TRIGGER trg_experiment_assignments_updated_at
    BEFORE UPDATE ON experiment_assignments
    FOR EACH ROW EXECUTE FUNCTION reco_set_updated_at();

CREATE TRIGGER trg_experiment_outcomes_updated_at
    BEFORE UPDATE ON experiment_outcomes
    FOR EACH ROW EXECUTE FUNCTION reco_set_updated_at();

CREATE TRIGGER trg_recovery_budgets_updated_at
    BEFORE UPDATE ON recovery_budgets
    FOR EACH ROW EXECUTE FUNCTION reco_set_updated_at();

CREATE TRIGGER trg_policies_updated_at
    BEFORE UPDATE ON policies
    FOR EACH ROW EXECUTE FUNCTION reco_set_updated_at();

CREATE TRIGGER trg_policy_versions_updated_at
    BEFORE UPDATE ON policy_versions
    FOR EACH ROW EXECUTE FUNCTION reco_set_updated_at();

-- Append-only enforcement for audit_logs
CREATE OR REPLACE FUNCTION reco_prevent_audit_mutation()
RETURNS TRIGGER AS $$
BEGIN
    RAISE EXCEPTION 'audit_logs is append-only: % operations are not permitted', TG_OP;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_audit_logs_no_update
    BEFORE UPDATE ON audit_logs
    FOR EACH ROW EXECUTE FUNCTION reco_prevent_audit_mutation();

CREATE TRIGGER trg_audit_logs_no_delete
    BEFORE DELETE ON audit_logs
    FOR EACH ROW EXECUTE FUNCTION reco_prevent_audit_mutation();

COMMENT ON FUNCTION reco_prevent_audit_mutation() IS
    'Blocks UPDATE and DELETE on audit_logs to preserve immutable audit trail.';

COMMIT;
