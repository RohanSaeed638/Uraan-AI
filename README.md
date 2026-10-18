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

- **Core:** auth and onboarding, roadmap generation, tasks and learning units,
  dashboard, learning, progress, projects, settings, quizzes (generated on
  first open) and the AI mentor.
- **XP and streaks:** XP for lessons, tasks, passed quizzes and finished
  interviews (each awarded once); a daily streak on the learner's own
  timezone; levels every 100 XP.
- **Leaderboard:** weekly and all-time. Opt-in only (Settings), showing first
  name and last initial.
- **Notifications:** in-app bell plus optional web push, driven by a daily
  reminder script (below).
- **Calendar:** remaining study days laid out from today, with a subscribable
  `.ics` feed for Google, Apple and Outlook calendars.
- **Resume builder:** resume, cover letter and LinkedIn summary drafted from
  completed work. Missing facts become `[placeholders]`; nothing is invented.
- **Portfolio:** project showcase with an optional public page at `/p/<slug>`
  and a GitHub checklist.
- **Interview coach:** 5-question text mock interviews scored on technical,
  communication and confidence (confidence is judged from wording only).

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

#### Push notifications and reminders

Push is off until VAPID keys are set; the in-app bell works without them.

```bash
cd apps/api
python scripts/generate_vapid_keys.py
```

Paste the three printed lines into `apps/api/.env` (set `VAPID_SUBJECT` to your
own `mailto:` address) and restart the API. Keep the private key secret and
reuse the same pair afterwards: changing it invalidates existing browser
subscriptions.

Reminders are sent by a script, not a long-running worker. Run it every 15
minutes from any scheduler (Railway/Render cron, system cron, Task Scheduler):

```bash
python -m app.workers.send_reminders
```

It is safe to run more often or twice: each reminder is sent at most once per
day per user, at the reminder time and timezone set in Settings.

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
