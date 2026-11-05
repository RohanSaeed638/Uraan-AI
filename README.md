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
- **Achievements and titles:** 23 badges (`app/core/achievement_catalog.py`)
  unlock from what the learner actually does and each pays bonus XP once; a
  toast and confetti announce them as they happen. XP also sets a career title
  (Explorer, Apprentice, Builder, Professional, Master). Each month one pending
  project lesson becomes the **boss project**, worth 150 bonus XP if finished
  that month.
- **Career readiness (0 to 100):** tasks done 35, projects 20, consistency 15,
  mock interviews 15, portfolio 15 (`app/services/readiness.py`), with the three
  biggest gaps turned into next steps.
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

- **Careers:** a curated catalogue of 14 careers (`apps/api/data/careers.json`,
  loaded with `python scripts/seed_careers.py`) with skills, free resources,
  Pakistan salary ranges and demand. Browse, compare and get an AI
  recommendation (always picked from the catalogue). A roadmap is built from a
  career's curated skills and resources: the file decides what is taught, the
  AI decides order, pacing and projects.
- **Roadmap engine:** roadmaps are built **in the background** (`POST
  /roadmaps/generate` answers 202; poll `GET /roadmaps/{id}/status`). Each task
  has a week and each phase has milestones. A roadmap can be paused and
  resumed, rebuilt, or **adapted** (only the unfinished part is re-planned;
  finished work is kept). A copy of the plan is saved before every rebuild,
  adapt or restore, and can be restored from the version history. A failed or
  lost job puts the roadmap back as it was (or marks a first generation
  `failed`).

- **Resource library:** `/resources`, a searchable library of the catalogue's
  free resources (filter by career, type, level, free only), with bookmarks,
  1 to 5 star ratings and sharing. Each task page recommends the library
  resources that fit its topic. The library is filled from the same
  `careers.json` by `scripts/seed_careers.py`.
- **Coding exercises:** coding careers (software, data and AI, security and
  infrastructure) get 1 to 3 exercises per task: a problem, starter code, hints
  shown one at a time and a solution hidden behind a confirmation. Python is
  syntax-checked before saving; nothing is run. Project lessons also record a
  difficulty, the skills practised and their portfolio value.

- **AI mentor:** knows the learner (profile, language, level, current roadmap,
  phase, next lesson and recent progress) and talks in the tone they choose in
  Settings (friendly, Gen-Z or professional). Suggestion chips come from their
  own roadmap. "Review my code" gives structured feedback on a public GitHub
  repository (read through api.github.com only, with strict limits), pasted
  code, or their portfolio; 10 reviews a day. The dashboard shows a short daily
  message written from real progress, saved for the day and reused in the
  reminder.
- **AI providers:** every AI call goes through `app/ai/llm`. Providers are
  tried in `AI_PROVIDERS` order (OpenAI, Gemini, Anthropic) and a provider that
  fails is skipped for a minute after three failures. Each call is recorded in
  `ai_requests` (purpose, provider, model, latency, tokens, success), and the
  prompt version (`app/ai/versions.py`) is stored with the content it produced.

## Setup

### API (`apps/api`)

```bash
python -m venv .venv
.venv/Scripts/activate        # Windows; use source .venv/bin/activate elsewhere
pip install -r requirements.txt
```

Create `apps/api/.env` with: `DATABASE_URL`, `SUPABASE_URL`,
`SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_JWT_SECRET`, `OPENAI_API_KEY`
(optionally `OPENAI_MODEL`, and `CORS_ORIGINS`: the website addresses allowed to call the
API, comma separated, default `http://localhost:3000`).

Optional AI settings: `GEMINI_API_KEY` and `ANTHROPIC_API_KEY` enable the
fallback providers (with `GEMINI_MODEL` / `ANTHROPIC_MODEL`), `AI_PROVIDERS`
sets the order (default `openai,gemini,anthropic`; a provider without a key is
skipped) and `GITHUB_TOKEN` raises GitHub's rate limit for project reviews.

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

#### Email

Email is off until a sender is set; in-app and push notifications work without
it. The API sends through [Resend](https://resend.com): create an account, verify
a sending domain, create an API key, then in `apps/api/.env`:

```
RESEND_API_KEY=re_...
EMAIL_FROM=Uraan AI <noreply@your-domain.com>
WEB_URL=https://your-web-app
API_PUBLIC_URL=https://your-api
```

`WEB_URL` and `API_PUBLIC_URL` are used for the links inside emails. For local
development set `EMAIL_OUTBOX_DIR=./outbox` instead of a key: each email is
written to a JSON file there, nothing is sent.

What is emailed (when the learner has email notifications on, the default):
the daily reminder, the Monday summary, achievements, the monthly boss project
and streak milestones (3, 7, 14, 30... days). Schedule updates stay in the app.
Emails use the learner's language (Urdu is right to left). Every email carries a
signed one-click unsubscribe link (the `/unsubscribe` page, and the
`List-Unsubscribe` header that mail apps use); it turns the Settings switch off
without signing in. The reminder script above sends the emails, so run it on a
schedule.

**Sign-up emails (Supabase Auth):** confirmation and password-reset mail comes
from Supabase, not from this API. Supabase's built-in mailer only delivers to
your own team, so before real users sign up set **custom SMTP** in the Supabase
dashboard: *Authentication > Emails > SMTP Settings*. For Resend: host
`smtp.resend.com`, port `465`, username `resend`, password your API key, sender
an address on your verified domain. Also set *Authentication > URL
Configuration > Site URL* and add `<WEB_URL>/auth/callback` to the redirect URLs.

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

## Database rules

- **Every table must have Row Level Security enabled.** Supabase exposes all
  `public` tables to the public browser key; with RLS on and no policies that
  key can read and write nothing. The API connects as the table owner, which
  bypasses RLS, so it is unaffected. A new table needs
  `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` in its migration;
  `pytest tests/test_rls.py` fails if one is missed.
- The web app talks to Supabase only for sign-in. All data goes through the API.

## Admin portal

`/admin` (staff only) has an overview (learners, activity, AI usage and failures
per feature and provider), a user list with email search and role changes,
careers and library resources you can add, edit and switch off, announcements
(a banner for everyone, optionally also a notification), and an audit log.

- **Who is an admin:** put the first admins' sign-in emails in `ADMIN_EMAILS`
  (comma separated, in `apps/api/.env`). An account with a listed address
  becomes an admin the first time it signs in. After that, admins promote or
  demote others in the portal's Users page. You cannot remove your own access.
- **Access:** every `/admin/*` API route needs an admin and answers `403` to
  anyone else; the web pages show the normal "not found" page, so the portal is
  not advertised. Admin text is English only.
- **Nothing is deleted:** careers, resources and announcements are switched
  off instead, because roadmaps, bookmarks and notifications point at them.
  Switching a career off hides it from learners and from new roadmaps.
- **Careers added in the portal** work everywhere: the profile check, roadmap
  generation and coding exercises read the database, not just
  `data/careers.json` (which still seeds the first careers).
- **Audit log:** every change writes a row to `audit_logs` in the same
  transaction (who, what, which item, and before/after values). Rows are never
  edited or removed by the app.

## Study planner

`/calendar` lays the active roadmap's lessons out on the days and times the
learner can study (week, day and month views).

- The pure packing logic is `app/services/planner.py`: lessons keep their order,
  each day is filled to that weekday's minutes, a lesson is never split, and
  completed lessons are left out. Availability comes from the profile
  (daily hours, weekend study, preferred time of day), overridden by the
  learner's `schedule_preferences`.
- **Moving a lesson** (drag and drop, or the Move button) pins it to a date in
  `schedule_overrides`; everything else flows around it. "Let the planner
  decide" removes the pin.
- **AI optimise** turns free text ("exams next week, 30 minutes a day") into
  validated rules (`PlannerRules`) saved as preferences; 10 requests a day.
- **Missed lessons**: unpinned ones are replanned from today by themselves and
  the learner gets a "schedule updated" notification (once a day, run by
  `reminder_service`); pinned ones that pass are flagged for rescheduling.
- The private `.ics` feed has one event per study day at the planned time.

## Design system

Brand gold marks selection and focus: filter chips, toggles, active navigation,
focus rings and links (`text-brand-gold-deep` on light). Violet stays a
secondary accent. Reusable pieces live in `components/shared/`: `FilterChips`,
`ToggleChip`, `SearchField`, `PageHeader`, `EmptyState`, `StatTile`,
`FilterGroup`; the `card-lift` utility gives cards a hover lift.

## Languages

The app, the AI-written content and the messages the server sends come in three
languages: **English (`en`)**, **Urdu in Urdu script (`ur`, right to left)** and
**Roman Urdu (`ur-Latn`)**, Urdu in English letters.

- **Choosing:** onboarding (Language step), Settings > Appearance, and the
  Profile page. The choice is saved on the account (`profiles.language`) and in
  the `NEXT_LOCALE` cookie; a new device picks it up on first visit
  (`LocaleSync`). There are no URL prefixes.
- **Messages:** the web app uses next-intl. **New UI text goes in
  `apps/web/messages/en.json`, never in the component**, read with
  `useTranslations("namespace")`. `ur.json` and `ur-Latn.json` are merged over
  the English file, so a missing translation shows the English text, never a
  key. `python <scratchpad>/check_keys.py`-style checks (see below) and
  `tests/test_error_codes.py` guard that every key exists.
- **Drafting translations:** `python scripts/translate_messages.py` (from
  `apps/api`) asks the AI layer to translate whatever is missing from `ur` and
  `ur-Latn`, with a glossary, and validates placeholders, plurals and tags.
  Existing translations are never overwritten (use `--force` to redo all), so a
  reviewer's edits are safe. **The drafts need a native speaker's review before
  launch.**
- **Right to left:** `ur` sets `dir="rtl"` on `<html>` and uses Noto Naskh
  Arabic. Styles use logical properties (`ms-`, `pe-`, `start-`, `text-start`),
  and direction arrows carry `rtl:rotate-180`. Roman Urdu is left to right.
- **Dates and numbers:** `lib/format.ts` (`intlLocale`) and `lib/planner.ts`
  format with `Intl` in the active language; Roman Urdu uses English forms.
- **AI content:** roadmaps, lessons, quizzes, career advice and project reviews
  are written in the learner's language (`complete()` adds a language rule from
  `app/ai/prompts/language.py`). The mentor and the daily motivation line follow
  the same language. Resumes, portfolios and mock interviews stay in English,
  the language employers read.
- **Server messages:** notifications and the dashboard fallback line come from
  `app/core/texts.py` in all three languages.
- **API errors:** every error response carries an `error_code` (the message as
  lowercase words, `app/core/error_codes.py`). The web looks up
  `errors.<code>` and falls back to the English text. After adding a fixed
  message to the API, run `python scripts/sync_error_messages.py`.
- **Wording:** Settings > Preferences switches between *Classic* (Tasks,
  Projects) and *Gamified* (Missions, Quests, Claim XP) by merging a small
  overlay (`messages/gamified/<locale>.json`) over the messages. Saved on the
  account (`user_settings.wording`) and in the `NEXT_WORDING` cookie.
- **Not translated yet:** the careers catalogue text (`data/careers.json`),
  achievement titles inside notifications, and the AI's saved planner summaries.

## Running it for real (platform)

- **URLs:** every endpoint lives under `/api/v1` (the web reads the base from
  `NEXT_PUBLIC_API_URL`). `GET /health` says the process is up; `GET /health/ready`
  also checks the database (use it as the deploy health check).
- **Errors** have one shape: `detail`, `message`, `code` (e.g. `RATE_LIMIT_001`),
  `error_code` (see Languages) and `request_id`. Every response carries
  `X-Request-ID`; quote it when reporting a problem and find it in the logs.
- **Logs:** JSON lines (`LOG_FORMAT=text` for a readable terminal, `SQL_ECHO=true`
  to print each statement). Requests slower than `SLOW_REQUEST_MS` (default 1000)
  are logged as warnings.
- **Rate limits** (`RATE_LIMIT_*` in `apps/api/.env`): anonymous 50/h, signed in 500/h,
  AI chat 100/day, roadmap generation 10/day, plus a per-address cap so inventing
  accounts does not help. Refusals are a `429` with `Retry-After`. Counters live in
  memory; with more than one API process set `RATE_LIMIT_STORAGE_URI=redis://...`.
  Run uvicorn with `--proxy-headers` behind a proxy so addresses are the visitor's.
  `RATE_LIMIT_ENABLED=false` turns them off.
- **Sign-in checks:** the API remembers a verified token for `AUTH_CACHE_SECONDS`
  (default 60) instead of asking Supabase on every request; a sign-out is noticed
  within that time. `0` asks every time.
- **Monitoring:** set `SENTRY_DSN` (API) and `NEXT_PUBLIC_SENTRY_DSN` (web) for error
  reports, and `POSTHOG_API_KEY` / `POSTHOG_HOST` for product events. Both are off
  when unset, and neither receives names, emails or text.
- **Lessons** are written behind the plan: the outline appears in seconds and each
  lesson fills in as it is written; a lesson that fails shows a retry button.
- **Testing a build beside `npm run dev`:** `NEXT_DIST_DIR=.next-test npm run build`
  keeps it out of `.next`, so the dev server is not disturbed.
- **Backups:** see `docs/runbooks/backup-and-restore.md` (Supabase daily backups plus
  your own `python scripts/backup_db.py`, written to `backups/`, which git ignores).

## Tests, CI and deployment

- **API tests:** `cd apps/api && pytest tests` (about 630 tests; those that use the database roll back
  or clean up after themselves). Coverage: `pytest tests --cov=app` (83% when last measured; CI fails under 75%).
- **Web tests:** `npm test --workspace apps/web` (Vitest: components, helpers, and that the Urdu files have
  every key and placeholder of the English ones).
- **Browser journey:** `npm run test:e2e --workspace apps/web` signs in, builds a roadmap, opens a lesson and signs out
  against a running app. It needs a confirmed account (`E2E_EMAIL`, `E2E_PASSWORD`) and uses real AI calls, so it is
  run on demand. See `apps/web/playwright.config.ts` for the other variables.
- **CI** (`.github/workflows/ci.yml`) runs on every push and pull request: API migrations on a fresh Postgres plus
  `alembic check`, the API tests with coverage, web lint, types, unit tests and a production build, and checks that
  the generated API files are current. `reminders.yml` sends reminders every 15 minutes once enabled.
- **API types for the web:** after changing an endpoint, run `python scripts/dump_openapi.py` in `apps/api` and
  `npm run gen:api` in `apps/web`, and commit both outputs.
- **Docker:** `docker compose up --build` (see `docker-compose.yml`). **Deploying:** `docs/deployment.md`.
- **Environment files:** copy `apps/api/.env.example` and `apps/web/.env.example`.
