# Uraan AI: Project Report

*What was built, how it was built, and how it was checked. Status as of 31 October 2026.*

---

## 1. What Uraan AI is

Uraan AI ("Uraan" means flight in Urdu) is a web platform that helps students and career changers in Pakistan **choose a career, get a personalised learning plan for it, and finish that plan**. A learner says what they want to become, how much time they have and how they like to learn. The platform builds a week-by-week roadmap from free resources, breaks every task into short lessons, exercises and projects, and keeps the learner moving with reminders, XP, streaks, an AI mentor, mock interviews, a resume builder and a public portfolio. It works in English, Urdu and Roman Urdu.

**At a glance**

| | |
|---|---|
| Careers in the catalogue | 14, each with skills, free resources and Pakistan salary ranges |
| Database tables | 39 (all with Row Level Security) |
| Database migrations | 37 |
| API | 95 paths, 117 operations, all under `/api/v1` |
| Web pages | 43 routes, 90 components |
| Interface text | 1,636 strings, in 3 languages |
| Backend code | about 21,500 lines (`apps/api/app`), plus about 11,800 lines of tests |
| Web code | about 22,800 lines of TypeScript |
| Tests | backend: 631 in the last full run, then 207 more added; web: 43 unit tests and 2 browser tests |
| Backend test coverage | 83% (measured on the last full run) |

---

## 2. Technology and structure

**Stack**

| Part | Technology |
|---|---|
| Web app | Next.js 16, React 19, Tailwind CSS 4, next-intl (languages), React Query, recharts |
| API | Python 3.12, FastAPI, SQLAlchemy 2 (async), Alembic (migrations), Pydantic |
| Database and sign-in | Supabase (Postgres and Auth) |
| AI | OpenAI, Gemini and Anthropic behind one interface, with automatic fallback |
| Email and push | Resend (email), Web Push (browser notifications) |
| Monitoring | Sentry (errors), PostHog (product events), JSON logs with request IDs |
| Tests | pytest, Vitest, Testing Library, Playwright, axe-core (accessibility) |
| Delivery | GitHub Actions, Docker, Vercel (web), Railway or Render (API) |

**Repository layout**

```
apps/api      FastAPI service: routes -> services -> repositories -> models, plus ai/ and core/
apps/web      Next.js app: app/ (pages), components/, lib/, messages/ (languages), tests/
docs/         this report, deployment guide, backup runbook
.github/      CI and scheduled-reminder workflows
docker-compose.yml, Dockerfiles, .env.example files
```

**How a request flows.** The browser signs in with Supabase and receives a token. Every data request goes to the API with that token. The API checks the token, then a *route* hands the work to a *service* (the rules), which uses *repositories* (the database queries) over *models* (the tables). The web app talks to Supabase only for sign-in. All other data goes through the API.

**AI layer.** One function (`complete`) sends a request to the first available provider and falls back to the next on failure. Every generator (roadmap, lessons, quiz, mentor, interview, resume, portfolio, planner, motivation, career recommendation) goes through it. Each saved AI output records which prompt version made it, and every call is logged (latency, tokens, success) in an `ai_requests` table.

---

## 3. How the project unfolded

**Foundations (July to August 2026).** Authentication endpoints and screens, onboarding, the first roadmap generation API, roadmap pages and the task completion dialog. This produced a working core flow: sign up, answer onboarding questions, receive an AI roadmap, open tasks and lessons, mark them done.

**Restructuring with Claude (17 to 19 October).** Two commits ("added claude changes for v1" and "add version 2 changes with claude") reworked the code and widened the app beyond the core flow. By the time of the audit below it also had lessons, quizzes, XP, an AI mentor, documents, interviews and a portfolio.

**An audit against the product documents.** All the planning documents (requirements, product, architecture, database, API, UI/UX, development plan) were compared with the running app. The result:

- 9 of the 10 acceptance criteria for the first release already passed.
- Of 39 functional requirements, only 9 were fully done, 16 were partial and 14 were missing.
- Several non-functional requirements were unbuilt (languages, email, rate limits, monitoring, accessibility).
- One serious security gap: **Row Level Security was off on all 25 tables, so the public browser key could read them.**

**A 13-phase completion plan.** The gaps were turned into a plan in three releases, ordered so risk is removed first, then missing product is built, then the system is hardened and shipped:

- **Release A, safe and functional:** phases 0 to 5.
- **Release B, the documented MVP complete:** phases 6 to 10.
- **Release C, harden and launch:** phases 11 to 13.

Each phase was done in turn, verified, and reported before the next one started. The 27 October commit is titled "working app before email, admin portal phase-10"; phases 11 to 13 and the extra tests came after it and are **not yet committed** (see section 9). Check `git status` for exactly what each commit holds.

---

## 4. What was built, phase by phase

### Release A: safe and functional

**Phase 0: security and correctness hotfixes**
- Row Level Security enabled on every table by a migration, with a test (`test_rls.py`) that fails if any future table lacks it. The backend connects as the table owner, so it is unaffected; only direct browser-key access is blocked.
- The missing `/reset-password` page was added, so the password-recovery email now lands somewhere.
- Bug fix: new roadmaps were being saved as "completed". They are now "active", and a data-fix migration corrected existing ones.
- "Remember me" now works: unchecked means the session ends when the browser closes.

**Phase 1: onboarding and profile data**
- New profile fields: age, education, device (laptop, desktop or mobile only), goal type, preferred study hours, learning pace, weekend study. Two new onboarding steps and matching profile editing.
- The AI prompts use these answers. For example, a phone-only learner gets phone-friendly resources and no local-install tasks.
- Interface text moved into message files from this point, so languages could be added later without rewriting.

**Phase 2: career discovery**
- A curated catalogue of 14 careers (`data/careers.json`, reviewed by the project owner) with skills, free resources (FreeCodeCamp, CS50, Saylani, PIAIC and others), difficulty, months to job-ready and Pakistan salary ranges.
- Public search and filter, career detail pages, side-by-side comparison, and a "help me choose" wizard where the AI may only pick from catalogue careers and must give reasons.
- Roadmap generation uses the curated skills and resources as a template that the AI personalises.

**Phase 3: roadmap engine**
- Weekly milestones; pause, resume and regenerate; version snapshots saved before every regenerate or adapt, with restore (the current state is saved first, so a restore can be undone); "adapt" re-plans only the unfinished part when study time changes or the learner falls behind, keeping completed work.
- Generation runs as a background job with a status endpoint. The page shows progress, keeps the learner's input if it fails, and a job that never reports back is given up on after a timeout.

**Phase 4: learning and resources**
- A resource library with search, filters, bookmarks, ratings and sharing; curated resources appear as "Recommended" on task pages.
- A coding-exercise lesson type (problem, starter code, hints), completed manually, with no code execution.
- Project lessons carry difficulty, skills covered and portfolio value.

**Phase 5: AI mentor and AI architecture**
- The mentor knows the learner's profile, level, current roadmap and recent progress, offers suggestion chips, and has a configurable tone (friendly, Gen-Z, professional).
- Project review for a public GitHub link, pasted code or a portfolio link (GitHub fetches are restricted to github.com, size-limited and protected against server-side request forgery).
- A personalised daily motivation message, cached per day.
- The provider abstraction with fallback, prompt versioning and the `ai_requests` log.

### Release B: the documented MVP, complete

**Phase 6: gamification and career readiness**
- XP, levels with career titles, streaks, a leaderboard (opt-out in settings), and an achievements system with seeded definitions, bonus XP, "unlocked" notifications and a monthly "boss" project.
- A 0 to 100 **career readiness score**, weighted from task completion (35%), projects (20%), consistency (15%), mock interviews (15%) and portfolio (15%), with tips for the next best step. The formula is unit-tested.

**Phase 7: planner**
- Time-of-day study blocks that respect preferred hours and daily minutes; week, day and month views; manual moves and drag-and-drop; an "AI optimise" action; missed tasks move automatically unless pinned; a calendar feed (`.ics`) that follows the same schedule.

**Phase 8: languages**
- English, Urdu and Roman Urdu across the whole interface (1,636 strings), with right-to-left layout for Urdu, an Urdu font, locale-aware dates and numbers, and AI output (lessons, roadmaps, mentor, resumes) written in the chosen language.
- Translations were drafted by AI with a glossary, then left for native-speaker review (still pending). Backend errors carry a code the web translates.
- A "Classic" versus "Gamified" wording switch (Tasks and Projects versus Missions and Quests).

**Phase 9: notifications and email**
- Resend email with templates (daily reminder, weekly summary, streak, milestone), a signed one-click unsubscribe page, an email switch in settings, a full notifications page and a reminder job meant to run every 15 minutes.
- Development mode writes emails to files instead of sending.

**Phase 10: minimal admin portal**
- Admin role with first admins taken from the `ADMIN_EMAILS` setting; careers and resources management, announcements (banner and notification), user list and counts, usage and AI-failure stats, and an audit-log viewer. Every admin action is recorded in `audit_logs`; non-admins get 403 (tested).

### Release C: harden and launch

**Phase 11: platform hardening**
- Rate limits (anonymous 50 an hour, signed in 500 an hour, AI chat 100 a day, roadmap generation 10 a day, plus a per-address cap) with a clear 429 message; counters can be shared through Redis.
- `/api/v1` prefix and one error format (`detail`, `message`, `code`, `error_code`, `request_id`); every response carries `X-Request-ID`.
- Observability: Sentry on both web and API, PostHog events for the product's key numbers, JSON logs with request IDs, `/health` and a database-checking `/health/ready`. All of it is off until a key is set and never receives names, emails or text.
- Performance: the roadmap list no longer runs one query per roadmap, composite database indexes were added, and a verified sign-in token is remembered for 60 seconds instead of asking Supabase on every request.
- **Progressive lesson generation:** the lesson outline is saved first, in seconds, and the lesson text is written behind it, a few at a time. Each lesson shows pending, writing, ready or failed, with a retry button. A lesson that was claimed but never finished is taken over after five minutes.
- Accessibility: skip link, one `<main>` per page, reduced-motion support, and an automated axe audit at desktop and 390 px phone width, with all critical and serious findings fixed.
- Backups: a restore runbook and a `pg_dump` helper script.

**Phase 12: UI and UX completion**
- Brand colour changed to purple (as the design document specifies), with gold kept for XP and streaks.
- Mobile bottom navigation; a full landing page (hero, careers, features, how it works, FAQ, call to action), About and Pricing pages ("free during beta"), page titles, sitemap and robots file.
- A GitHub-style activity heatmap and weekly XP chart on the Progress page; dashboard cards for the upcoming project and recent achievements; skeleton loading screens; custom 404, 500 and offline pages.

**Phase 13: quality, CI/CD and deployment**
- GitHub Actions: lint, type check, tests with a coverage floor, build, migrations on a fresh Postgres plus a model-versus-migration check, and a check that generated API files are current. A separate scheduled workflow sends reminders.
- Dockerfiles for both apps, a compose file, `.env.example` files, a deployment guide, and a typed API description (`openapi.json` to generated TypeScript types).
- Vitest component and helper tests, and a Playwright browser journey.

---

## 5. How each piece was worked: from code to verification

Every phase followed the same loop. This is the main reason the result can be trusted rather than just demonstrated once.

1. **Read the requirement and the existing code** before changing anything.
2. **Change the database safely.** Models changed, a migration was auto-generated, then reviewed by hand. Every new table got Row Level Security in the same migration. The migration was applied and `alembic check` confirmed that the models and migrations agreed.
3. **Write the service logic and routes**, keeping the layers separate: routes only translate HTTP, services hold the rules, repositories hold the queries.
4. **Write unit tests with hand-made stand-ins** (fake sessions, fake AI replies). They run in milliseconds and cover each rule and each refusal: wrong owner, missing profile, invalid input, a failed save that must roll back.
5. **Write real-database tests that roll back.** A test opens a transaction against the real Supabase database, creates what it needs (including a user in the auth table), runs the real code, asserts, and rolls everything back. This catches mistakes fakes cannot: wrong SQL, constraints, types, column names.
6. **Test the AI-facing code without calling the AI.** Fake model replies check that prompts carry the right facts, that malformed or out-of-range replies are rejected rather than saved, and that fenced or non-JSON output is handled.
7. **Run it in a real browser with real AI.** A throwaway account was created, driven through the flow with Chrome (puppeteer, later Playwright), and then deleted with all its data. Visual checks were taken at desktop, tablet and 390 px phone width.
8. **Run the whole suite, lint and type check, then report.** Each report said what was done, what was measured, and what was left open.
9. **Clean up.** Test accounts, orphan log rows and test servers were removed after each run.

**Real problems that this process found** (all fixed): the Admin link did not appear until the admin page was visited; a brief Supabase connection drop returned a 503 instead of retrying; the admin layout showed "not found" on a server error; `/roadmaps/current` crashed with a 500 for a learner with no roadmap; a progress bar and checkbox without accessible names; two colour-contrast failures; a stale build served after a restart; and a corrupted dev build caused by test builds writing into the developer's `.next` folder (test builds now use their own folder).

---

## 6. Testing in detail

| Layer | What | Size |
|---|---|---|
| Backend unit tests | Services, rules, schemas and AI generators with stand-ins | the large majority of 48 test files |
| Backend real-database tests | Rolled-back transactions on the real database (account export, activity, roadmap engine, row-level security, lesson writer) | a few dozen tests |
| Backend platform tests | Request IDs, error shape, rate limiting, monitoring, token cache | across several files |
| Web unit tests | Components, date and error helpers, and that Urdu and Roman Urdu have every key and placeholder of the English text | 43 tests (Vitest) |
| Browser journey | Sign in, build a roadmap, open a lesson, sign out, signed-out redirect, public pages and the 404 page | 2 tests (Playwright, real AI) |
| Accessibility audit | axe on 30 page views (public and signed-in, desktop and phone) | 0 serious findings, 1 main landmark per page, no sideways scroll |

**Coverage.** The last full backend run took 31 minutes: 630 passed and 1 failed. The failure was a lesson-writer test that passed on its own twice in a row, so it was most likely a timing flake (not reproduced). Overall coverage was 83%. After that run, 207 more backend tests were added for the weakest areas (progress, settings, projects, dashboard, push, the reminder job, account export, mentor, roadmap management, quizzes, notifications, documents, portfolio, and the roadmap and interview AI generators). Code those tests exercise went from roughly 17 to 60% before, to 85 to 100% after. The full suite has not been re-run since, so the new overall figure is not yet measured.

**Safety nets built into the tests.** A test fails if any table lacks Row Level Security; if the web has no translation entry for a fixed API message; and, in CI, if the committed API description is out of date or the models and migrations disagree.

---

## 7. Measured results

- **Lesson generation (real AI):** roadmap built in 37 s; the outline of 14 lessons returned in 17.9 s (slightly above the 5 to 15 s target); the first lesson was readable about 14 s later; all 14 were done by 65 s with none failed.
- **API speed.** Every endpoint runs only 1 to 10 database queries. From the developer's machine each query takes about 300 to 600 ms, because the database is in Seoul. That makes single-query endpoints take about 650 ms *from here*; the `/careers` list (4 queries) took about 4 s and `/achievements` (10 queries) about 3 s. The 500 ms goal therefore **could not be confirmed on this machine**. It should be re-measured after deployment with the API in the same region as the database, where each query costs a few milliseconds.
- **Accessibility:** all pages pass automated WCAG 2 A and AA checks for critical and serious issues (automated checks do not replace a manual review with a screen reader).

---

## 8. Decisions and accepted deviations

Decisions made with the project owner:

- Translations are AI-drafted and then reviewed by a person (review still to do).
- Email through Resend; a minimal admin portal in English only; the careers file written by the AI and reviewed by the owner.
- No account deletion and no avatar upload.
- Brand colour changed to purple.

Deviations from the original documents, kept on purpose:

- The API keeps plain success responses instead of wrapping each in `{success, data}`. It would be a large change with no user benefit.
- The plan has Phases, Tasks and Lessons rather than Phases, Modules and Lessons.
- Coding exercises are completed manually; there is no code execution.
- Not built: community and study groups, notes and flashcards, a mentor marketplace, job feed and matching, certificates, payments, account deletion, avatar upload, full admin moderation.

---

## 9. Current state and what remains

**Not yet committed.** Phases 11 to 13 and all the additional tests are in the working folder only (about 158 changed or new paths on branch `feature/v2_with_claude`). They should be committed and pushed so CI can run.

**Written but never run:** the Docker images and compose file (no Docker on the development machine), and both GitHub workflows. Expect to fix small things on their first run (the CI database stand-in for Supabase's auth table is the likeliest).

**Known open items**
- One calendar hydration warning (React error 418) appeared once and did not recur; its cause was not found.
- The language selector on the landing page still highlights the active language in gold.
- Parts still lightly tested: the repositories (covered only through real-database tests), the lesson generator's own functions, and the old `auth` routes (which may be dead code, because the web app signs in through Supabase directly).
- Only the first lesson-outline step is slightly slower than its 15 s target.

**What only the project owner can do**
1. Push to GitHub and watch the first CI run.
2. Create the hosting projects (Vercel for web; Railway or Render for the API, in the database's region) and follow `docs/deployment.md`.
3. Set Supabase redirect URLs and custom email (SMTP) so sign-up confirmation emails reach real users.
4. Put the real secret key in `SUPABASE_SERVICE_ROLE_KEY` (it once held the public one), set `ADMIN_EMAILS`, and turn on Supabase daily backups.
5. Create Resend, Sentry and PostHog accounts and add their keys.
6. Have a native speaker review the Urdu and Roman Urdu translations.

---

## 10. Where to find things

| Need | Look at |
|---|---|
| How to run and set up | `README.md`, `apps/api/.env.example`, `apps/web/.env.example` |
| How to deploy | `docs/deployment.md` |
| How to back up and restore | `docs/runbooks/backup-and-restore.md` |
| The API description | `apps/api/openapi.json` (live at `/docs` when running) |
| Database rules | README, "Database rules"; `apps/api/tests/test_rls.py` |
| Languages and error codes | README, "Languages"; `apps/api/scripts/translate_messages.py` |
| Run all backend tests | `cd apps/api && pytest tests` |
| Run web tests | `npm test --workspace apps/web` |
| Run the browser journey | `npm run test:e2e --workspace apps/web` (needs a confirmed test account) |
