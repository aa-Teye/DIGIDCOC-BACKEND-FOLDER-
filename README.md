# DigiDoc API

FastAPI backend for the DigiDoc / Dr. Korletey Platform. Companion to the [frontend repo](https://github.com/aa-Teye/DIGIDOC-FRONT-END-).

Stack: FastAPI, PostgreSQL (Supabase/Neon), SQLAlchemy, JWT auth, Paystack for payments — per the project proposal's zero-cost tech stack.

## Local setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Status: scaffold only. Business logic lands sprint-by-sprint alongside the frontend — see the root `PROJECT.md` in the DIGIDOC project folder for the sprint plan.
