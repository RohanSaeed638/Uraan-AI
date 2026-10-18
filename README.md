# Uraan AI

AI-powered career learning. Users onboard with a career goal, get a generated
roadmap (phases → tasks → daily learning units), track progress, take
AI-generated quizzes and chat with an AI mentor.

## Layout

| Path | What |
|---|---|
| `apps/api` | FastAPI backend: async SQLAlchemy, Alembic, Supabase JWT auth, OpenAI |
| `apps/web` | Next.js 16 / React 19 / Tailwind v4 / shadcn frontend |

Backend layers: `api/routes` → `services` → `repositories` → `models`, with
`ai/` holding prompts, schemas and generators (roadmap, learning units, quiz,
mentor).

## Features

Auth and onboarding, roadmap generation, tasks and learning units, dashboard,
learning, progress, projects, settings, quizzes (generated on first open) and
the AI mentor.

## Setup

### API (`apps/api`)

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows; use source .venv/bin/activate elsewhere
pip install -r requirements.txt
```

Create `apps/api/.env` with: `DATABASE_URL`, `SUPABASE_URL`,
`SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`, `OPENAI_API_KEY`
(optionally `OPENAI_MODEL`).

```bash
alembic upgrade head
uvicorn app.main:app --reload     # http://localhost:8000/docs
pytest tests
```

### Web (`apps/web`)

Create `apps/web/.env.local` with `NEXT_PUBLIC_SUPABASE_URL`,
`NEXT_PUBLIC_SUPABASE_ANON_KEY` and `NEXT_PUBLIC_API_URL`
(e.g. `http://localhost:8000`).

```bash
npm install
npm run dev                       # http://localhost:3000
```

## Migrations

```bash
alembic revision --autogenerate -m "describe the change"
alembic upgrade head
alembic check                     # fails if models and migrations drift
```
