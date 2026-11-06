# Testing

## API (`apps/api/tests`, pytest)

About 60 test files. Run `cd apps/api && pytest tests`.

- **Real database, rolled back.** Tests that need Postgres open a transaction on a connection, bind the session with `join_transaction_mode="create_savepoint"`, insert needed `auth.users` rows, and roll everything back. Nothing persists.
- **RLS guard.** `test_rls.py` fails if any public table lacks Row Level Security.
- **No real network or AI.** AI providers, HTTP and email are faked. The link checker uses httpx's mock transport and a fake resolver.
- **Defaults set in `conftest.py`:** rate limiting off, auth cache off, link checking off, and `GamificationService.award` stubbed by an autouse fixture. To test the real award function use the captured `REAL_AWARD`.
- **Windows:** async tests need the selector event loop (already configured).

Areas covered: auth and security, profile and onboarding, careers, roadmap generation/engine/management/status, learning plans and lessons, quizzes, mentor (conversations, AI, safety), planner and calendar, interviews, documents, portfolio, library, gamification (XP, achievements, streak freezes, leaderboard), notifications/push/email/reminders, admin and insights, lesson feedback, link checker and link repair, search, rate limits, monitoring, account export and deletion, error codes, language.

Coverage: `pytest tests --cov=app`; CI fails under 75%.

## Web (`apps/web`)

- **Unit and component:** Vitest and Testing Library, `npm test` (72 tests). Animation libraries are mocked where jsdom cannot run them.
- **End-to-end:** Playwright, `npm run test:e2e` (sign-up → onboarding → roadmap → lesson → logout).
- **Static:** `npx tsc --noEmit` and `npm run lint` must be clean.
- **Accessibility:** axe audits of key pages at desktop and phone widths.

## Manual and browser checks

For UI changes, build with `NEXT_DIST_DIR=.next-test` (so a running dev server is not disturbed), point it at a test API, and drive it with a headless browser using a throwaway account. Look at desktop, tablet and 390 px phone widths, and the browser console for hydration errors.

## CI (`.github/workflows`)

Lint, type-check, tests, build, then `alembic upgrade head` and `alembic check` against a temporary Postgres. Separate scheduled workflows run reminders and the weekly link sweep.
