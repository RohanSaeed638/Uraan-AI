# Architecture

## The parts

| Part | Technology | Where |
|---|---|---|
| Web app | Next.js 16, React 19, Tailwind v4, next-intl, React Query, framer-motion, recharts | `apps/web` |
| API | FastAPI, async SQLAlchemy 2, Alembic, Pydantic | `apps/api` |
| Database and sign-in | Supabase (Postgres and Auth) | hosted |
| AI | OpenAI, Gemini, Anthropic behind one interface | `apps/api/app/ai` |
| Email | Resend | `apps/api/app/services/email*` |
| Push | Web Push (VAPID) | `apps/api/app/services/push*` |
| Monitoring | Sentry (errors), PostHog (product events) | optional |

```
Browser ──► Next.js (Vercel) ──► FastAPI (/api/v1) ──► Postgres (Supabase)
   │                                   │
   └── Supabase Auth (sign-in only)    ├── AI providers (OpenAI / Gemini / Anthropic)
                                       ├── Resend (email), Web Push
                                       └── background jobs (roadmap build, link repair)
```

The browser talks to Supabase **only to sign in**. All data goes through the API, which checks the Supabase token and then uses its own database connection.

## Request flow

1. The browser sends `Authorization: Bearer <Supabase token>` to `/api/v1/...`.
2. `app/core` verifies the token (cached for `AUTH_CACHE_SECONDS`), loads the profile, and applies rate limits.
3. A **route** (`app/api/routes`) validates input with a **schema** (`app/schemas`) and calls a **service** (`app/services`).
4. The service holds the rules and uses **repositories/models** (`app/models`) to read and write.
5. Errors leave as `{ "error_code": ..., "message": ... }`; the web app translates the code.

Rule of thumb: routes stay thin, services hold behaviour, models hold shape.

## The learning model

Career → **Roadmap** → Phases → **Tasks** (grouped by week) → **Learning units** (lessons). A task can have a quiz; roadmaps can have projects. Roadmaps keep **versions**, so a rebuild or adaptation can be undone. Lesson feedback (`lesson_feedback`) attaches to a learning unit and survives its deletion.

## The AI layer

`app/ai/llm` offers one `complete()` call. Providers are tried in the order of `AI_PROVIDERS`; if one fails or times out (`AI_REQUEST_TIMEOUT`), the next answers. Every call is recorded in `ai_requests` (latency, tokens, success), which feeds the admin cost view via `app/ai/pricing.py`.

Cross-cutting rules applied to every request:

- A global style rule: never use emoji.
- A per-learner daily token cap (`AI_DAILY_TOKENS_PER_USER`, `0` = off) raises `AIBudgetExceeded`.
- Prompts live in `app/ai/prompts` and are versioned with the content they generate.
- The mentor is screened first (`app/ai/safety.py`): messages about self-harm get a fixed caring reply with **no AI call**, and the prompt tells the model to treat pasted content as data, not instructions.

## Background jobs

| Job | How it runs |
|---|---|
| Roadmap generation, regeneration, adaptation | In-process background job (`roadmap_jobs.py`) with a status endpoint the UI polls. On success it also repairs dead resource links. |
| Reminders and weekly summaries | `app/workers/send_reminders.py`, every 15 minutes |
| Link sweep | `app/workers/check_links.py`, weekly (GitHub Actions: `.github/workflows/link-check.yml`) |

## The link checker

The AI writes resource links from memory and some are wrong. `link_checker.py` decides each link is `ok`, `dead` or `unknown`. A link is **dead** only on strong evidence (404/410, the site does not exist, a YouTube video that is gone, or a page title that says not found). Sites that block robots or are briefly down are `unknown` and left alone. It refuses private and internal addresses at every redirect hop (SSRF). `link_service.py` replaces dead task links and deactivates library resources after two dead checks.

## Gamification

`GamificationService` is the one place XP is awarded. It also advances streaks (with freezes), evaluates achievements, and computes career level. The numbers are in the [User guide](user-guide.md#xp-levels-and-titles).

## Internationalisation

Languages: English (`en`), Urdu (`ur`, right-to-left) and Roman Urdu (`ur-Latn`). UI text is in `apps/web/messages/*.json`; AI content is written in the learner's language. Career and error-message text has sync scripts (see [Development](development.md#translations)).

## Web app structure

`apps/web/app` uses route groups: `(auth)` for sign-in pages, `(app)` for the signed-in app, plus public pages (landing, careers, legal, public portfolios). See [web routes](reference/web-routes.md). The app is an installable PWA (`app/manifest.ts`, icons in `public/icons`).

## Accepted deviations from the original specification

- Phases → Tasks → Lessons instead of Phases → Modules → Lessons.
- Success responses are not wrapped in `{success, data}`.
- AI-written translations need human review before launch.
