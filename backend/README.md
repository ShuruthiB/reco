# RECO Backend

FastAPI backend for the RECO payment recovery decisioning platform.

## Setup

1. Apply database migrations (from repo root):

```bash
psql $DATABASE_URL -f backend/migrations/001_extensions_and_functions.sql
psql $DATABASE_URL -f backend/migrations/002_initial_schema.sql
psql $DATABASE_URL -f backend/migrations/003_indexes.sql
psql $DATABASE_URL -f backend/migrations/004_triggers.sql
```

2. Install dependencies:

```bash
cd backend
pip install -r requirements.txt
```

3. Copy environment config:

```bash
cp ../.env.example ../.env
```

4. Seed development data:

```bash
python db/seeds/seed.py
```

Set `DEFAULT_MERCHANT_ID` in `.env` to the merchant ID printed by the seed script.

## Run

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/dashboard/metrics` | Aggregated dashboard metrics |
| GET | `/api/transactions` | Paginated transaction list |
| GET | `/api/transactions/{id}` | Transaction detail |
| GET | `/api/transactions/{id}/events` | Payment events timeline |
| GET | `/api/transactions/{id}/decisions` | Decision history |
| POST | `/api/decisions/preview` | Preview decision for transaction |
| POST | `/api/simulations/run` | Run intervention simulation |
| GET | `/api/experiments` | List experiments |
| GET | `/api/experiments/{id}` | Experiment detail |
| GET | `/api/budgets` | Recovery budgets |
| GET | `/api/policies` | Policy list |
| GET | `/api/audit` | Paginated audit log |

Pass `X-Merchant-ID` header for tenant scoping, or set `DEFAULT_MERCHANT_ID`.

## Tests

```bash
cd backend
pytest
```

Skip database-dependent tests:

```bash
SKIP_DB_TESTS=1 pytest
```

Policy engine unit tests always run without a database.
