# RECO: Revenue Experimentation & Conversion Optimizer

## The Problem
Merchants lose a significant portion of their revenue to failed payments. Standard retries and generic incentives are often applied indiscriminately to all failed transactions. This leads to two critical problems:
1. **Wasted Incentives:** Offering a 10% discount to a customer who would have naturally recovered wastes margin.
2. **Ignored Intervention Costs:** High-touch escalations (e.g., support calls) carry operational costs that can exceed the value of small transactions.

## The RECO Thesis
Maximizing raw "recovery rate" is mathematically incorrect. RECO's thesis is that payment recovery must be treated as a causal inference problem optimizing for **Net Incremental Contribution**.

## Key Differentiator
RECO is not a retry engine. It is a decision engine that:
1. Calculates **Revenue at Risk**.
2. Estimates the probability of **Natural Recovery** (would the user recover if left alone?).
3. Predicts the **Incremental Uplift** of candidate interventions (Retry, Reminder, Incentive, Alternative Method, Escalate).
4. Subtracts the **Intervention Cost** (both operational cost and discount margin).
5. Outputs a **Net Incremental Contribution** for each candidate action, choosing the highest valid option.

## Architecture
RECO is built around a deterministic Decision Engine supported by an ML-driven Policy Evaluator.
- **Decision Center:** The core engine that runs calculations and ranks interventions.
- **Guardrails:** A policy layer that blocks actions based on risk, fraud scores, cost limits, or retry exhaustion.
- **Action Executor:** Triggers asynchronous outbound communications or downstream integrations.
- **Webhook Processor:** A robust, idempotent handler for listening to Razorpay state changes and reconciling final financial metrics.

## Technology Stack
- **Backend:** Python, FastAPI, SQLAlchemy, Asyncpg, Pytest
- **Frontend:** React, TypeScript, Vite, TailwindCSS (Internal design system)
- **Database:** PostgreSQL (Production) / SQLite (Local Generation)
- **Payments:** Razorpay API & Webhooks
- **AI/LLM:** GPT-4 Turbo (strictly for explaining decisions, *never* for financial math)

## Setup Instructions

### Environment Variables
Duplicate `.env.example` to `.env` in the root directory. Fill in your test credentials:
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/reco
APP_ENV=development
DEFAULT_MERCHANT_ID=...
```

### Database Setup
Ensure PostgreSQL is running locally on port `5432`.
Apply the schema via SQLAlchemy by running the backend (FastAPI will autogenerate the schema on startup for local dev).

### Dataset Generation (Phase 19)
Generate the 10,000 transaction reproducible competition dataset:
```bash
cd backend
python -m ml.generation.generator --size 10000 --seed 42 --out ml/datasets/synthetic_competition.db
```
*Note: This generates a SQLite DB (`synthetic_competition.db`) explicitly for dataset simulation.*

### Model Training
*(Currently simulated via heuristics in the demo)*
If integrating actual ML models, the training module ingests the synthetic dataset to output pickeled Scikit-Learn pipelines stored in `ml/artifacts/`.

### Running the Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Running the Frontend
```bash
cd frontend
npm install
npm run dev
```

### Razorpay Test Mode Setup
1. Create a Razorpay account and switch to **Test Mode**.
2. Generate API Keys (Key ID and Key Secret) in Settings > API Keys.
3. Configure `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` in your backend environment (or secret manager).

### Webhook Setup
1. In Razorpay Test Mode, go to Settings > Webhooks.
2. Add a new webhook pointing to your exposed backend (e.g., via ngrok): `https://<your-ngrok-url>/api/webhooks/razorpay`
3. Subscribe to events: `payment.captured`, `payment.failed`, `payment.authorized`.
4. Copy the generated Webhook Secret and set it as `RAZORPAY_WEBHOOK_SECRET` in the backend.

## Demo Instructions (Phase 20)
To showcase RECO's unique thesis through 5 distinct "Hero Scenarios":
1. Open a terminal in the `backend/` directory.
2. Run `python demo_reset.py`. This deterministically seeds the 5 scenarios into the local SQLite database.
3. Query `GET /demo/report` to view the immediate financial breakdown of the 5 decisions.
4. Run `pytest tests/test_demo.py` to programmatically assert the logical correctness of the engine across all scenarios.

## Evaluation Metrics
The platform is evaluated by its ability to accurately measure:
- **Gross Recovered**: Total money salvaged from failed transactions.
- **Natural Recovery**: The portion of gross recovery that would have happened anyway.
- **Intervention Cost**: Operational costs + discount margins spent on interventions.
- **Net Incremental Contribution**: `Gross Recovered - Natural Recovery - Intervention Cost`.

A dynamic endpoint is available at `GET /api/metrics/competition` to fetch these metrics in real-time.

## Known Limitations
- Current predictive models rely on static heuristic functions rather than live ML inference.
- Authorization relies on a dummy `X-Merchant-ID` header instead of a full JWT flow.

---

## Why RECO is different
RECO does not optimize raw recovery rate. 

Standard engines view every recovered dollar as a success, blindly throwing expensive incentives at customers or wasting costly support tickets on small transactions. RECO understands that recovery comes with a cost. 

It mathematically estimates incremental recovery, accounts for intervention cost (operational and incentive margins), optimizes strictly for **net incremental contribution**, supports controlled experimentation (A/B testing holdout groups), enforces strict guardrails, and fundamentally understands that sometimes, the most profitable action is to deliberately choose **DO_NOTHING**.
