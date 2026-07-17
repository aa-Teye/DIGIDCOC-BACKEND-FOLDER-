# DigiDoc API

FastAPI backend for the DigiDoc / Dr. Korletey Platform. Companion to the [frontend repo](https://github.com/aa-Teye/DIGIDOC-FRONT-END-).

Stack: FastAPI, SQLAlchemy, JWT auth. Runs on a local SQLite file with zero setup;
swap `DATABASE_URL` to a Supabase/Neon Postgres connection string when ready (see
`.env.example`) — no code change needed.

## Local setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Visit `http://localhost:8000/docs` for interactive API docs (FastAPI's built-in
Swagger UI). On first startup, tables are created and an admin user is seeded from
`SEED_ADMIN_EMAIL`/`SEED_ADMIN_PASSWORD` in `.env` (defaults:
`admin@digidoc.app` / `DigiDocAdmin123!`).

## What's real vs. mocked

- **Real and wired to the frontend:** registration, phone OTP verification, login,
  patient profile save, provider credential submission, admin verification queue
  (list/approve/reject).
- **No SMS gateway yet** — `/auth/register` returns the OTP code directly in the
  response (`dev_otp_code`) instead of texting it. The frontend surfaces it via a
  toast so the flow is testable end to end. Swap for Twilio (or similar) before
  real launch.
- **`/admin/analytics`** returns real counts (`total_users`, `patients`,
  `providers`, `pending_verifications`) but nothing on the frontend dashboard
  consumes it yet — the dashboard's stat cards (consultations, response time,
  satisfaction, revenue) need appointments/messaging/billing data that doesn't
  exist in this schema yet.
- **No appointments, messaging, or billing tables yet** — those are later sprints.

## Local setup — verifying it works

```bash
curl http://localhost:8000/health
```

See the root `PROJECT.md` in the `DIGIDOC` project folder for the full sprint plan
and decisions log.
