## 1. High-level architecture

RECO should be a **modular monolith**: one FastAPI backend with clearly separated domain modules, one React frontend, PostgreSQL/Supabase, and asynchronous worker processes sharing the same codebase.

```text
React / TypeScript dashboard
            |
        FastAPI API
            |
 ┌──────────┼────────────────────────────────────────────┐
 | Merchant | Transactions | Decisioning | Experiments    |
 | Policies | Budget       | Audit        | Razorpay      |
 └──────────┼────────────────────────────────────────────┘
            |
 PostgreSQL / Supabase + Object Storage
            |
 Async worker / job queue
            |
 ML scoring | uplift estimation | webhook processing | execution
            |
 Razorpay Test Mode + LLM API
```

The decision path is deterministic and controlled:

```text
ML estimates → economic calculation → policy validation → action execution
                                            |
                                      LLM explanation
```

The LLM may explain a decision, but cannot choose, approve, or execute payment actions.

---

## 2. Component architecture

- **Frontend**
  - Merchant dashboard
  - Transaction explorer
  - Simulator
  - Decision center
  - Experimentation dashboard
  - Policy, budget, and audit views

- **API layer**
  - Authentication and tenant authorization
  - REST API for dashboard and integration workflows
  - Webhook endpoints

- **Decision engine**
  - Candidate intervention generation
  - Prediction and uplift lookup
  - Expected-net-contribution calculation
  - Guardrail and budget evaluation
  - Decision persistence

- **Execution engine**
  - Creates action commands only after approval by policy engine
  - Calls Razorpay or messaging-provider adapters
  - Tracks execution outcomes

- **ML subsystem**
  - Feature construction
  - Recovery-propensity prediction
  - Treatment/uplift estimation
  - Model registry and scoring metadata

- **Experimentation subsystem**
  - Assignment, holdouts, treatment arms
  - Outcome attribution
  - Incrementality reporting

- **Audit subsystem**
  - Immutable, append-only domain audit events
  - Records inputs, models, policies, decisions, executions, and overrides

---

## 3. Data flow

```text
Razorpay event / merchant event
        ↓
Webhook ingestion and verification
        ↓
Raw event persisted + deduplicated
        ↓
Transaction state projection updated
        ↓
Eligible transaction enters decision queue
        ↓
Feature assembly
        ↓
ML propensity + uplift estimates for every candidate action
        ↓
Economic calculation of net incremental contribution
        ↓
Policy, consent, frequency, budget, and risk validation
        ↓
Choose highest eligible positive-value action, otherwise DO NOTHING
        ↓
Persist decision and audit event
        ↓
Execute approved intervention asynchronously
        ↓
Receive payment/outcome events
        ↓
Update attribution, experiment outcomes, and training data
```

---

## 4. Request/response flow

For an API-triggered decision:

1. Frontend or merchant system requests a transaction decision.
2. API authenticates tenant and validates ownership.
3. API creates an idempotent `decision_request`.
4. Decision engine evaluates the transaction synchronously if data is available; otherwise returns `202 Accepted`.
5. Result includes:
   - selected action,
   - expected incremental recovery,
   - expected cost,
   - expected net contribution,
   - policy outcome,
   - model and policy versions,
   - human-readable explanation.
6. Execution is a separate explicit operation or an approved automated workflow.

A decision response must never expose internal sensitive features, raw payment credentials, or another tenant’s data.

---

## 5. Database entities

| Entity | Purpose |
|---|---|
| `merchant` | Tenant organization and operational settings |
| `merchant_user` | Dashboard users and roles |
| `payment_provider_connection` | Encrypted Razorpay credentials and connection metadata |
| `customer` | Merchant-scoped customer identity and consent state |
| `transaction` | Canonical payment/recovery lifecycle record |
| `payment_attempt` | Original and subsequent payment attempts |
| `payment_event` | Normalized provider and internal events |
| `webhook_receipt` | Raw webhook metadata, signature result, deduplication status |
| `intervention` | Catalog definition: retry, reminder, incentive, etc. |
| `intervention_candidate` | Candidate action evaluated for a transaction |
| `decision_request` | Idempotent decision request record |
| `decision` | Chosen action, values, versions, and status |
| `decision_evaluation` | Per-action predicted outcomes and economics |
| `action_execution` | Command, provider reference, attempts, and execution state |
| `recovery_outcome` | Attributed payment recovery result |
| `experiment` | Experiment definition, eligibility, arms, and dates |
| `experiment_assignment` | Transaction-to-arm assignment |
| `experiment_metric_snapshot` | Aggregated experiment results |
| `recovery_budget` | Merchant budget, period, and spending limits |
| `budget_reservation` | Reserved and consumed intervention budget |
| `policy` | Versioned merchant rules and guardrails |
| `policy_evaluation` | Why candidates passed or failed policy |
| `model_version` | Registered propensity/uplift model versions |
| `feature_snapshot` | Features used for a particular prediction |
| `prediction` | Model output and confidence metadata |
| `llm_explanation` | Generated explanation, prompt version, and output |
| `audit_event` | Append-only audit trail |
| `idempotency_key` | Request and command deduplication record |

All tenant-owned records must include `merchant_id`.

---

## 6. API boundaries

- `/auth/*` — identity and session management
- `/merchants/*` — merchant configuration and users
- `/transactions/*` — search, detail, timelines, manual decision requests
- `/decisions/*` — retrieve decisions, evaluate candidates, approve/reject overrides
- `/simulator/*` — hypothetical intervention comparisons; no execution
- `/experiments/*` — experiment creation, assignments, results
- `/budgets/*` — recovery budget configuration and utilization
- `/policies/*` — guardrail rules, versioning, approval, activation
- `/models/*` — model metadata, health, performance, version selection
- `/audit/*` — immutable audit-log queries
- `/integrations/razorpay/*` — setup and provider status
- `/webhooks/razorpay` — public inbound webhook endpoint
- `/internal/jobs/*` — worker-only internal command endpoints, if needed


The frontend must not call Razorpay directly for recovery decisioning. It only interacts with RECO APIs.

---

## 7. ML pipeline

### Online scoring

For each eligible transaction, calculate:

- Baseline probability of recovery with no intervention
- Probability of recovery for each intervention
- Incremental uplift per intervention
- Expected recovered amount
- Confidence/uncertainty estimate
- Eligibility flags and model fallback status

### Training pipeline

1. Ingest historical transaction, intervention, and outcome data.
2. Validate quality, tenant isolation, labels, and leakage risks.
3. Build point-in-time-safe features.
4. Train:
   - baseline recovery model,
   - treatment-response/uplift models,
   - calibration model where necessary.
5. Evaluate by merchant segment, payment method, failure reason, amount band, and treatment.
6. Register immutable model version and feature schema.
7. Shadow-score before activation.
8. Promote only after approval and measurable validation.

Initial implementation may use conservative segment-level uplift estimates where intervention data is insufficient. RECO must not present weak causal estimates as high-confidence individualized uplift.

---

## 8. Agent/decision pipeline

For every action `a`:

```text
baseline_recovery_probability = P(recover | do_nothing)
incremental_uplift(a) = P(recover | action a) - baseline_recovery_probability
expected_incremental_revenue(a) = amount × incremental_uplift(a)
expected_net_contribution(a) =
  expected_incremental_revenue(a)
  - intervention_cost(a)
  - incentive_cost(a)
  - operational_cost(a)
```

Decision stages:

1. Confirm transaction eligibility.
2. Generate valid candidate actions, including `DO_NOTHING`.
3. Score propensity and uplift for each candidate.
4. Calculate expected net incremental contribution.
5. Apply hard guardrails:
   - consent,
   - customer contact frequency,
   - maximum incentive,
   - retry limits,
   - payment-state validity,
   - regulatory constraints,
   - merchant recovery budget.
6. Rank eligible actions by expected net contribution.
7. Select the highest positive result; select `DO_NOTHING` if none qualify.
8. Persist all candidates, rejected candidates, calculations, versions, and rationale.
9. Generate an optional LLM explanation from the finalized decision record.
10. Send only the approved action command to execution.

---

## 9. Razorpay integration boundary

Razorpay is an external payment-event and payment-action adapter, not a decisioning authority.

RECO’s Razorpay adapter should:

- receive and verify Razorpay webhooks;
- normalize Razorpay payment, order, refund, and failure data;
- associate provider IDs with internal transactions;
- create permitted recovery-related actions where Razorpay supports them;
- reconcile provider status with RECO’s transaction projection.

Razorpay credentials are merchant-scoped, encrypted at rest, and never returned through the frontend API. Test-mode and live-mode credentials must be isolated at the schema and configuration level.

---

## 10. Webhook architecture

```text
Razorpay
   ↓
Public webhook endpoint
   ↓
Signature verification
   ↓
Persist raw receipt + provider event ID
   ↓
Return fast acknowledgement
   ↓
Async normalization worker
   ↓
Transaction update / decision eligibility / reconciliation
```

Rules:

- Verify Razorpay signature before processing.
- Persist raw payload metadata before asynchronous handling.
- Deduplicate by provider event ID and payload hash.
- Acknowledge quickly; do not perform ML scoring or payment execution in the webhook request.
- Send malformed, unverifiable, or repeatedly failing events to a quarantine/dead-letter workflow.
- Support replay of stored webhook receipts.

---

## 11. Security boundaries

- Tenant isolation enforced at API, service, query, and database-row-security layers.
- Role-based access control: merchant admin, analyst, operator, auditor.
- Separate operational authorization for policy activation, budget changes, and manual execution.
- Razorpay secrets encrypted with managed key encryption.
- Never store card data or payment credentials outside Razorpay-supported token/reference fields.
- Webhook signature verification and replay protection.
- PII minimization, masking in logs, and restricted audit access.
- Immutable audit events for decision and execution trails.
- Separate test and production environments, data, credentials, and webhook endpoints.
- LLM prompts contain only minimized, redacted decision context.

---

## 12. Failure-handling strategy

- Use durable queues for webhook processing, scoring, and action execution.
- Retry transient failures with exponential backoff and bounded attempts.
- Route terminal failures to a dead-letter queue with operator visibility.
- Fail closed for action execution: if prediction, policy, budget, or state is uncertain, choose `DO_NOTHING` or require manual review.
- Preserve decision snapshots so later model or policy changes do not rewrite history.
- Reconcile Razorpay events regularly to recover from missed webhooks.
- Provide dashboard-visible operational states: pending, delayed, failed, quarantined, reconciled.

---

## 13. Idempotency strategy

Every externally triggered command must carry or derive an idempotency key.

- Webhooks: `provider + provider_event_id`
- API requests: `merchant_id + endpoint + client_idempotency_key`
- Decisions: `transaction_id + decision_trigger + transaction_state_version`
- Execution commands: `decision_id + action_type + execution_sequence`
- Budget reservations: `decision_id + intervention_candidate_id`

Use unique database constraints and transactional inserts. A repeated request returns the original result; it must not create a second reminder, incentive, retry, or budget charge.

Use an outbox table so state changes and outbound execution commands are committed atomically.

---

## 14. Testing strategy

- Unit tests for economics, policy evaluation, idempotency, budget reservations, and action eligibility.
- Contract tests for Razorpay payload normalization and webhook signature handling.
- Integration tests using PostgreSQL and queue infrastructure.
- End-to-end tests for merchant workflows in Razorpay Test Mode.
- Property tests for decision invariants:
  - no action without policy approval;
  - no execution without persisted decision;
  - no duplicate execution for same idempotency key;
  - `DO_NOTHING` available in every decision.
- ML tests for data leakage, schema drift, calibration, fairness/segment stability, and model fallback.
- Experimentation tests for randomization, holdout isolation, and attribution correctness.
- Security tests for tenant isolation, authorization, secret exposure, and webhook forgery.
- Load tests for webhook bursts and transaction-explorer queries.

---

## 15. Deployment architecture

```text
Vercel
  └─ React + TypeScript frontend

Render / Railway / Cloud Run
  ├─ FastAPI web service
  ├─ Async worker service
  └─ Scheduled reconciliation / ML jobs

Supabase / PostgreSQL
  ├─ Primary relational database
  ├─ Row-level security
  └─ Object storage for model artifacts / exports

External
  ├─ Razorpay Test Mode
  └─ LLM provider API
```

Recommended environments:

- Local development
- Shared staging with Razorpay Test Mode
- Production

The worker and API deploy independently but share one repository, database schema, domain model, and release version.

---

## 16. Directory structure

```text
reco/
├── frontend/
│   ├── src/
│   │   ├── features/
│   │   │   ├── dashboard/
│   │   │   ├── transactions/
│   │   │   ├── decisions/
│   │   │   ├── simulator/
│   │   │   ├── experiments/
│   │   │   ├── budgets/
│   │   │   ├── policies/
│   │   │   └── audit/
│   │   ├── components/
│   │   ├── api/
│   │   └── routes/
│   └── tests/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── domains/
│   │   │   ├── merchants/
│   │   │   ├── transactions/
│   │   │   ├── decisioning/
│   │   │   ├── interventions/
│   │   │   ├── policies/
│   │   │   ├── budgets/
│   │   │   ├── experiments/
│   │   │   ├── integrations/
│   │   │   └── audit/
│   │   ├── ml/
│   │   ├── workers/
│   │   ├── llm/
│   │   └── observability/
│   ├── migrations/
│   └── tests/
├── ml/
│   ├── training/
│   ├── evaluation/
│   ├── feature_definitions/
│   └── model_registry/
├── infra/
│   ├── docker/
│   ├── deployment/
│   └── monitoring/
├── docs/
│   ├── architecture/
│   ├── api/
│   ├── decisioning/
│   └── runbooks/
└── contracts/
    ├── api/
    ├── events/
    └── razorpay/
```

## ARCHITECTURE DECISIONS TO FREEZE

1. Use a modular monolith, not microservices, for the initial product.
2. Use React + TypeScript, FastAPI, PostgreSQL/Supabase, and Python ML.
3. Model `DO_NOTHING` as a first-class decision candidate.
4. Select actions by expected net incremental contribution, not recovery rate.
5. Separate prediction, economic calculation, policy enforcement, explanation, and execution.
6. Treat policy and budget checks as hard gates after scoring.
7. Prohibit LLMs from selecting, authorizing, or executing financial actions.
8. Use Razorpay as a bounded external adapter; RECO owns decisioning and auditability.
9. Process webhooks asynchronously after signature verification and durable persistence.
10. Require idempotency for inbound events, decisions, executions, and budget reservations.
11. Use immutable decision snapshots with model and policy versions.
12. Use experimentation and holdouts to validate incrementality rather than relying solely on observational recovery data.
13. Fail closed: uncertainty or policy failure results in `DO_NOTHING` or manual review.
14. Deploy frontend separately, while API and workers remain one backend codebase.
15. Enforce merchant isolation at every layer, including database policies.
