# Uraan AI: Status Report and Improvement Ideas

*How the product works today, how well it is verified, what is left, and what would make it better. 4 November 2026.*

---

## 1. Where things stand

The product is **feature-complete against the original plan** (13 phases) and the follow-up launch review. All work is committed (latest commit `ebcf861`, branch `feature/v2_with_claude`; `main` exists on GitHub). What remains is **deployment and launch set-up**, plus polish, not missing core features.

**Checked again today**

| Check | Result |
|---|---|
| Web type check and lint | clean (0 errors) |
| Web unit tests | 60 passed |
| 19 backend test files (services, AI generators, security, rate limits, errors, platform) | 294 passed in 24 s |
| Database migrations vs models (`alembic check`) | in step (37 migrations) |
| Working tree | clean, nothing uncommitted |

**Not re-run today:** the full backend suite (about 30 minutes; last full run 630 passed, 1 flaky, 83% coverage), the browser tests with real AI (last run passed on 1 November), and CI on GitHub (never run: see section 6).

---

## 2. How it works, from a learner's side

1. **Landing page and sign-up.** A visitor sees what the product does, careers, features, how it works and an FAQ. Sign-up needs agreement to the Terms and Privacy Policy, then a confirmation email (with a Resend button). Google and GitHub sign-in are also offered.
2. **Onboarding.** Under five minutes: goal, level, study time, education, device, preferred hours and pace, and the language (English, Urdu or Roman Urdu).
3. **Pick a career.** 14 curated careers with skills, free resources and Pakistan salary ranges; search, filter, compare, or "help me choose".
4. **Get a roadmap.** The AI builds a phased, week-by-week plan from the curated career, shaped by the learner's device, pace and goal. It takes about 40 seconds and runs in the background with a progress banner.
5. **Learn.** Each task opens a plan of readings, exercises and projects. The outline appears in about 18 seconds and the lessons fill in behind it (all 14 in about a minute). A failed lesson shows a Retry button.
6. **Practise.** Quizzes, coding exercises, an AI mentor chat (with context from the learner's own progress), code and project review, and mock interviews with scored feedback.
7. **Stay on track.** XP, levels, streaks, achievements, a monthly "boss" project, a leaderboard (opt-out), a career-readiness score, a planner with time blocks and drag-and-drop, reminders by email and browser push, and a calendar feed.
8. **Show results.** Resume and cover-letter drafting, and a public portfolio at a chosen address.
9. **Control.** Settings for language, theme, wording ("Classic" or "Gamified"), notifications, data download and password. Roadmaps can be paused, rebuilt, adapted, restored from versions, or deleted. A top-bar search finds roadmaps, lessons, documents, chats, careers and resources.

**For the operator:** a small admin portal (careers, resources, announcements, users, usage and AI-failure stats, audit log), error and usage monitoring that switches on when keys are set, and a script for deleting an account on request.

---

## 3. Evidence of quality

- **Security:** Row Level Security on every table (a test fails if one is missed), per-learner ownership checks on every personal endpoint (tested), rate limits, scrubbed error reports, signed unsubscribe links.
- **Accessibility:** automated checks on 30 page views at desktop and phone width found no serious issues; one main landmark per page, skip link, reduced-motion support, no sideways scroll on phones. (Not yet reviewed with a real screen reader.)
- **Real-browser tests:** sign-in, roadmap generation, lesson reading, sign-out, search (mouse, keyboard, phone), roadmap deletion, legal pages, sign-up consent and the resend flow all passed in Chrome against the real app.
- **Languages:** three languages across 1,640+ strings, with right-to-left layout for Urdu. All translations are AI drafts awaiting a native speaker's review.

---

## 4. Measured speed

| What | Result |
|---|---|
| Roadmap generation (real AI) | about 37 s |
| Lesson outline appears | about 18 s (target 5 to 15 s) |
| First lesson readable | about 14 s after the outline |
| All 14 lessons written | about 65 s |
| API response time | **cannot be confirmed from the development machine**: the database is in Seoul and each query takes 300 to 600 ms from here. Every endpoint uses only 1 to 10 queries, so with the API deployed next to the database it should be well under 500 ms. Re-measure after deploying. |

---

## 5. Known issues

1. **Calendar console warning** (React hydration error 418) in production builds for accounts with lessons. The page works; the cause was not found.
2. **Supabase's built-in email sender refuses real sign-ups** (HTTP 429, very low hourly limit). Real users cannot register until custom SMTP (Resend) is set in Supabase.
3. The lesson outline is a few seconds slower than its target.
4. The old `auth` routes in the API may be dead code (the web signs in through Supabase directly).

---

## 6. What is left before launch (owner's side)

| # | Task | Why |
|---|---|---|
| 1 | Open a pull request into `main` and watch the first CI run | CI and the Docker files have never run; expect a small fix |
| 2 | Custom SMTP (Resend) in Supabase, plus redirect URLs and Site URL | Without it sign-ups fail |
| 3 | Deploy the API (Railway or Render, **same region as the database**) and the web app (Vercel) | `docs/deployment.md` has every setting |
| 4 | Real secret key in `SUPABASE_SERVICE_ROLE_KEY`; set `ADMIN_EMAILS`, Resend key, `NEXT_PUBLIC_CONTACT_EMAIL`, reminder job | Listed in the deployment guide |
| 5 | Have the Terms and Privacy Policy reviewed by someone who can advise on Pakistani law | They were drafted, not legally reviewed |
| 6 | Native-speaker review of the Urdu and Roman Urdu text | AI drafts only |
| 7 | Turn on Supabase daily backups | Restore runbook is ready |
| 8 | After going live: run a real-account check and re-measure speed | The only way to confirm the 500 ms goal |

---

## 7. Ideas to make it a better product

**Trust in the content** *(highest value)*
- **Check every AI-supplied link** in a background job (status, redirects, "not found" pages); replace dead ones with catalogue resources; re-check weekly. Today links are saved as the model returns them.
- **Lesson feedback:** a "Was this helpful?" and "Report a problem" on every lesson, an admin list of the worst-rated lessons, and the ability to pin a corrected version. Learners become the quality team.
- **Mentor safety layer:** input checks, refusal of harmful or off-topic requests, and a short "I am an AI, please check" note on career and money advice.

**Learning effectiveness**
- A **placement quiz** so the starting level is measured, not chosen.
- **Spaced review:** re-quiz key points after 2, 7 and 21 days; it is the best-evidenced way to make learning stick and gives people a reason to return.
- **Streak freeze:** one earned grace day a week, so a single missed day does not erase weeks of effort.
- **Real code execution** for exercises (a sandbox service), or at least AI review of submitted answers.
- **Shareable progress:** completion certificates and a "Phase 1 done" card to post.

**Getting people started and back**
- Shorten the path to the first win: show a sample lesson during onboarding, and explain the wait while the roadmap builds.
- **Make it installable** (web app manifest): the browser-notification worker exists but the app cannot be added to the home screen.
- Offline reading of lessons already opened, for learners on slow connections.
- Weekly progress summary email with one clear next step.

**Knowing whether it works**
- An admin **funnel view**: sign-up, onboarding done, first lesson, back after 7 days, roadmap completed.
- An **AI cost view** and a per-learner spending cap with alerts.
- **Uptime monitoring** and a public status page; set up SPF, DKIM and DMARC for the sending domain and watch bounces, since reminders drive retention.

**Later, if the numbers justify it**
- Study groups and peer accountability; a Pakistani job feed and matching; a mentor marketplace.

**Suggested order:** lesson feedback and the link checker; the funnel view; installability and streak freeze; then spaced review and the placement quiz once there are a few hundred real learners.

---

## 8. Where to find things

`docs/PROJECT_REPORT.md` (the full build history), `docs/deployment.md` (go-live steps), `docs/runbooks/backup-and-restore.md`, `README.md` (setup, testing, settings), and `apps/api/openapi.json` (every endpoint).
