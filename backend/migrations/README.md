# RECO Database Migrations

Apply in order against a PostgreSQL 14+ database (Supabase-compatible):

```bash
psql "$DATABASE_URL" -f backend/migrations/001_extensions_and_functions.sql
psql "$DATABASE_URL" -f backend/migrations/002_initial_schema.sql
psql "$DATABASE_URL" -f backend/migrations/003_indexes.sql
psql "$DATABASE_URL" -f backend/migrations/004_triggers.sql
```

## Files

| File | Purpose |
|------|---------|
| `001_extensions_and_functions.sql` | `pgcrypto`, shared `updated_at` trigger function |
| `002_initial_schema.sql` | 16 tables, enum types, foreign keys |
| `003_indexes.sql` | Query performance indexes |
| `004_triggers.sql` | `updated_at` triggers, append-only `audit_logs` enforcement |

## Seed data

After migrations:

```bash
cd backend
python db/seeds/seed.py
```

Set `DEFAULT_MERCHANT_ID` in `.env` to the merchant ID printed by the seed script.

Optional: `SEED_TRANSACTION_COUNT=10000` (default) controls transaction volume.
