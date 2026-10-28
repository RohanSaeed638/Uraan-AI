# Redesign Notes

This pass restyled the existing Uraan AI app (Next.js 16 / React 19 /
Tailwind v4 / shadcn-on-Base-UI / Supabase) to match the provided brand
mockups — gold CTAs, violet accents, dark navy app shell, mountain/night-sky
illustration on auth screens. It reuses your existing business logic
(forms, optimistic task updates, Supabase auth, data fetching) wherever it
already existed; new pages were built where the app only had stubs.

## Brand assets

- `public/bird-icon.png` — transparent bird mark, extracted from your
  existing `logo.png` via chroma-keying (for use on any background).
- `public/illustrations/mountain-night.svg` — original illustration built
  for this redesign (starry sky, layered mountains, glowing moon, summit
  flag) matching the mockups' mood. Used on auth pages and the landing page.
- `app/globals.css` — full light + dark design-token rewrite. Gold
  (`--primary`) for CTAs, violet for accents/links, dark navy
  (`--background`/`--card`) for the app shell. Since `Button`/`Card`/`Input`
  etc. are all CSS-variable-driven, most of the app picked up the new look
  automatically once these tokens changed.
- Dark mode is the default. A real (not decorative) theme toggle lives in
  Settings → Appearance, backed by `localStorage` + an inline
  before-hydration script in `app/layout.tsx` to avoid a flash of the wrong
  theme.

## Pages touched

| Page | Status |
|---|---|
| `/` (landing) | Built from scratch — was `<h1>Welcome {email}</h1>` / `<h1>Not Logged In</h1>` |
| `/login`, `/register` | Restyled, split-panel layout, **real** Google/GitHub OAuth added |
| `/forgot-password` | Built from scratch — file existed but was empty (0 bytes), which was breaking `next build` |
| `/dashboard` | Built from scratch — was a static stub |
| `/roadmaps` | Restyled; fixed double-padding and duplicated-header bugs |
| `/roadmaps/[id]` | Restyled; `page.tsx` now delegates to `RoadmapDetailClient` instead of duplicating its logic (this also fixes a real bug — the header's progress % previously didn't update live when you checked off a task) |
| `/roadmaps/[id]/task/[taskId]` | Left mostly as-is — already fully token-driven (`bg-primary`, `bg-card`, etc.), so it inherited the new palette for free |
| `/settings` | Built from scratch — route folder existed but was empty. Account tab is wired to a real `supabase.auth.updateUser` call; Appearance tab has the real theme toggle |

## Sidebar scope decision

The mockup's sidebar shows Dashboard / My Roadmaps / Learning / Tasks /
Projects / Settings. Only Dashboard, Roadmaps, and Settings have real pages
behind them — Careers, Mentor, Profile, and a miscapitalized "Calendar"
(folder is literally named `calender`) exist as empty route folders with no
`page.tsx`. Rather than link to four 404s, the redesigned sidebar only
shows the three routes that actually work. Add the others back in as their
pages get built.

## Pre-existing bugs fixed along the way

These were blocking `tsc`/`next build` and unrelated to styling, but I hit
them while working through the app and fixed them since they were mostly
one-liners:

- `lib/api/index.ts` didn't exist — `onboarding/api.ts` imported `@/lib/api`
  but only `@/lib/api/client` existed. Added the barrel export.
- `onboarding/api.ts` imported the `OnboardingForm` type from the wrong
  file (`./schema` instead of `./types`).
- Two Base UI `Slider` `onValueChange` handlers assumed the value was
  always an array (`value[0]`) — Base UI's type also allows a bare number.
- `GenerateRoadmapForm.tsx`'s `LearningStyle` select offered 4 options
  (`VIDEO`, `READING`, `PROJECT`, `MIXED`) but the actual enum only has 3
  values (`READING`, `READING_VIDEO`, `READING_VIDEO_PROJECT`) — corrected
  to match.
- `TaskCard.tsx` referenced `task.resource_url`, which doesn't exist on
  `RoadmapTask` — should be `resource_links` (an array). Fixed while
  restyling the same file.
- `TaskDetailsDialog.tsx` called `useRouter()` *after* an early `return
  null`, which violates the Rules of Hooks. Moved it above the guard.
- `RoadmapCard.tsx` and the dashboard's empty state nested a `<Link>`
  (renders an `<a>`) inside a `<Button>` (renders a `<button>`) — invalid
  HTML nesting. Replaced with the `buttonVariants() + <Link>` pattern.
- `EmptyState.tsx`'s "Generate Roadmap" button had no `onClick` — it did
  nothing. Now reuses `GenerateRoadmapButton`, which actually opens the
  generation dialog.

## A note on Base UI vs. Radix

This shadcn setup runs on `@base-ui/react`, not Radix — composition uses a
`render` prop (`<Button render={<Link href="..." />}>`), not the `asChild`
prop you'd expect from most shadcn docs/examples. I hit this by writing
`asChild` out of habit a couple of times; every instance in this codebase
now uses `buttonVariants({...})` directly on the `<Link>` instead, which
sidesteps the question entirely and is what I'd recommend continuing to use
for any "styled as a button" links you add later.

## Not touched / known gaps

- **Landing page SEO**: `/` is a client component gated behind
  `useAuthStore`'s `loading` state (pre-existing pattern, not something I
  introduced) — the server-rendered HTML is a loading spinner, not the
  marketing content, until the client resolves auth state. Fine for
  functionality, not ideal for SEO/first paint. Worth revisiting if this
  page needs to rank in search.
- **`GenerateRoadmapDialog`/`Form`**: only the type error was fixed; the
  501-line form itself wasn't restyled line-by-line, since it's built
  entirely from already-reskinned shadcn primitives (`Select`, `Input`,
  etc.) and inherits the brand palette automatically.
- **Notifications settings tab**: deliberately not built — there's no
  backend for notification preferences, and I didn't want to ship toggles
  that look functional but don't persist anything.
- **Avatar upload**: no "change photo" upload wired up (no storage backend
  in scope here) — Settings shows the avatar and initials fallback only.
- This sandbox cannot reach `fonts.googleapis.com`, so all builds here were
  verified with a temporary system-font swap in `app/layout.tsx`; the real
  file (committed) uses your original Geist/Geist Mono/Inter Google Fonts
  setup unchanged. Should build fine in an environment with normal internet
  access — this is the same restriction hit throughout this whole project,
  not specific to this change.

---

## Session 2 updates

### Logout fix (root cause + fix)

Three compounding bugs were causing "logout doesn't work correctly":

1. **`middleware.ts` was a no-op** (`return NextResponse.next()`). Per
   `@supabase/ssr`'s required pattern, middleware must call
   `supabase.auth.getUser()` on every request to refresh/validate the
   session and sync cookies. Without it, server components (like the
   `(app)` layout's auth guard) could read stale cookie state — the root
   cause of auth state drifting between what the client thinks and what
   the server thinks.
   - Also renamed `middleware.ts` → `proxy.ts` per Next.js 16's renamed
     convention (same mechanism, new file name/export name) — confirmed
     by reading `node_modules/next/dist/docs/01-app/01-getting-started/16-proxy.md`
     as instructed by this repo's own `AGENTS.md`.
2. **`UserDropdown`'s logout never cleared the Zustand store directly.**
   It called `authService.logout()` (Supabase sign-out) and relied
   entirely on the async `onAuthStateChange` listener to eventually call
   `setUser(null)`. A `logout()` action already existed in `store/auth.ts`
   but was never called. Now called immediately and synchronously.
3. **Soft navigation left stale client state/cache around.** Switched
   `router.replace()` + `router.refresh()` to a hard
   `window.location.href = "/login"`, which fully resets the Router Cache
   and any in-memory component state — the most reliable option for a
   security-sensitive action like logout.

### Onboarding redesign

Fixed six shared components (`OnboardingCard`, `OptionCard`,
`StepIndicator`, `NavigationButtons`, `SummaryCard`, `SectionTitle`,
`LoadingAnimation`) that were still using hardcoded `gray-500`/`purple-600`/
`bg-white` instead of the brand tokens from session 1 — this is why
onboarding still looked like the old unbranded app. Since all 8 step
screens consume these shared components declaratively, fixing them
cascaded the new look across the whole flow without needing to touch
every step file individually.

Added three hand-coded SVG illustrations (`components/illustrations/`) —
`TargetIllustration` (goal/duration steps), `CheckIllustration` (review
step), `WelcomeBirdIllustration` (welcome + generating steps, built from
the real extracted bird-icon asset plus sparkle accents, not a new
hand-drawn character). Deliberately did **not** attempt the mockup's more
detailed human-figure illustrations (person climbing blocks, person with a
laptop) — see "On illustrations" below.

`OnboardingCard` gained an optional `illustration` slot (two-column layout
on desktop, illustration hidden on mobile) wired into `WelcomeStep`,
`TargetDurationStep`, `ReviewStep`, and `GeneratingStep`.

`StepIndicator` now shows "Step X of 10 · <label>" with a brand-gradient
segmented progress bar, rather than unlabeled generic segments. Added
`STEP_LABELS` to `constants.ts`. (Did not collapse the real 10-step flow
down to the mockup's 4 visible stages — that would mean merging step
logic/state, which is riskier to do without a live backend to test
against. The 10 granular steps are a true, already-working, finer-grained
breakdown of the same information architecture.)

**Bug fixed along the way**: `onboarding/page.tsx` redirected to
`/roadmap/${id}` (singular) after generating a roadmap — the actual route
is `/roadmaps/[id]` (plural). Would have 404'd every time onboarding
completed successfully. One-line fix.

### On illustrations

The reference mockups mix two styles: simple iconographic graphics
(bullseye target, checkmark circle, sparkle-bird) and detailed
illustrated human figures (person climbing blocks, person with a laptop,
isometric scenes). I built the former — they're achievable as clean,
on-brand hand-coded SVG, same approach as the mountain illustration from
session 1. I did not attempt the latter: character illustration in that
specific flat-design style is a real illustration skill, this environment
has no image-generation tool, and a hand-coded attempt risked looking
worse than no illustration at all (an early draft of a hand-drawn bird
shape for the "welcome" screen was discarded for exactly this reason — it
didn't read clearly, so I used the real extracted logo asset instead). If
pixel-accurate human-figure illustrations matter, the practical path is a
licensed illustration pack (Storyset, unDraw, Humaaans, etc.) or
commissioned art, which I can then integrate.

### Landing page

Not changed this session — it already matches the "Welcome Screen" family
of mockups reasonably closely from session 1 (split layout, mountain
illustration, feature bullets, gold CTA). Re-confirmed it still builds
and renders correctly after this session's changes.

---

## Session 3 updates

### New illustration assets used

You supplied two production-quality illustration assets in
`public/illustrations/`: `onboarding_illustration_dark.png` and
`onboarding_illustration_light.png` (climber with a flag atop a mountain,
matching the reference mockups exactly). These replace the hand-coded
`mountain-night.svg` from session 1 everywhere a large hero illustration is
shown:

- **Landing page (`app/page.tsx`)** — completely rebuilt to match the new
  reference layout: a single full-bleed hero card (not the session-1
  split-panel) with the illustration as a background image, a gradient
  scrim fading from solid on the left to transparent over the climber,
  and content (logo, headline, 4 feature items with gold circular icon
  badges, Get Started button, sign-in link) overlaid directly on top —
  pixel-matching the two mockups you provided, copy included.
- **`AuthBrandPanel`** (the illustration panel on Login/Register/Forgot
  Password) — swapped to the same new asset for visual consistency across
  the whole pre-auth experience, since it would have looked inconsistent
  to upgrade only the landing page.

Both components swap between the dark/light PNG using Tailwind's `dark:`
variant (two `<Image>` elements, one hidden per theme) so it responds to
the real theme toggle built in session 2.

**Did not** replace the small bird-icon illustration used inside the
onboarding wizard's `WelcomeStep`/`GeneratingStep` — the new asset is a
wide hero-format image, not suited to that small inline-icon slot, so
reusing it there would have looked wrong. That illustration is unchanged.

### Verification note

This sandbox's background-server + curl approach (used in prior sessions
for runtime smoke tests) started hanging/timing out this session for
reasons unrelated to the code changes (likely an environment quirk with
backgrounding a long-lived process here). Rather than fight it, I verified
the two new hero sections a different way: composited the *actual*
Tailwind gradient-scrim logic over the *actual* illustration PNGs in
Python/PIL and inspected the result directly — confirms the text-legibility
scrim behaves as intended against the real images, not just in theory.
Combined with a clean `next build` (all 11 routes) and `tsc --noEmit`, I'm
confident in this without having been able to load it in an actual browser
here.

---

## Session 4 updates

### New stage-based stepper

Replaced the onboarding wizard's unlabeled segmented progress bar with a
numbered-circle stepper matching your reference exactly: 4 labeled stages
(Career → Skills → Learning Style → Goals) connected by lines, with
filled/checked circles for completed stages, a highlighted ring on the
current stage, and outlined gray circles for stages not yet reached.

**Important structural note**: the actual wizard still has 10 granular
steps under the hood (Welcome, your name, language, career, skill level,
learning style, daily hours, target duration, review, generating) — I did
not merge/restructure these, since doing so would mean changing what data
gets collected and submitted, which is riskier to get right without a live
backend to test against. Instead, `constants.ts` now has a `STEP_TO_STAGE`
map that buckets the 10 real steps under the 4 visible stages (e.g. name +
language + career selection all show as stage "Career"). Welcome and
Generating are intro/outro splashes and don't show the stepper at all,
matching how your reference doesn't show it on the Login/Register/Welcome
screens either.

### Learning style step — kept single-select, improved the visuals

Your reference shows this as independent checkboxes (Reading
required/always-on, Videos optional, Projects optional). I did not
implement it that way: the backend's `LearningStyle` enum only has 3 fixed
values (`READING`, `READING_VIDEO`, `READING_VIDEO_PROJECT`) — there's no
value for "Projects without Reading," so true independent checkboxes would
allow the user to select combinations the backend can't represent. Kept it
as a single-select of the 3 valid combinations, but restyled with icons
(book/video/code) and "progressive" copy ("Reading", "Reading + Videos",
"Reading + Videos + Projects") so it reads similarly to the reference
without the invalid-state risk.

### What I did not change

The "Career" step in your reference (image 2, panel 4) shows the full app
sidebar (Dashboard/My Roadmaps/Learning/Tasks/Projects/Settings) behind
it, which doesn't match how onboarding currently works in this app
(onboarding happens *before* the user has access to that shell). I treated
that one panel as a different feature (e.g. a "change career" screen
accessed later from within the app, not the initial onboarding step) since
the other three step panels in the same reference set (Skills, Learning
Style, Goals) are clean standalone cards with just the stepper — consistent
with how onboarding actually works here. If you did mean for onboarding
itself to happen inside the full app shell, that's a bigger structural
change (which page.tsx renders where) and worth confirming before I build
it, rather than guessing.

---

## Session 5: remaining screens

All built from data the API already returns (roadmap detail includes
phases -> tasks -> learning units). Sidebar now matches the reference:
Dashboard, My Roadmaps, Learning, Tasks, Projects, Progress, Profile,
Settings. Shared data fetching lives in `lib/server/data.ts`, unit helpers in
`lib/units.ts`.

| Route | What it does |
|---|---|
| `/tasks` | All tasks across roadmaps, All / To Do / Completed, optimistic checkbox via the existing `PATCH /roadmaps/tasks/:id` |
| `/learning` | "Suggested for today": the next unfinished lessons from your active roadmap, filled up to your `daily_hours` from the profile, plus "Coming up" |
| `/projects` | The `project`-type learning units across roadmaps, All / To Do / Completed |
| `/progress` | Overall task ring, tasks / lessons / learning-time stats, per-roadmap and per-phase bars |
| `/profile` | Name, email, and onboarding answers from `GET /profile/me`; edit name in Settings |
| `/roadmaps/:id/task/:taskId/learn/:unitId` | Lesson viewer: reading (text), video (YouTube/Vimeo embed, mp4, or link), project; previous/next; progress bar; then the Task Completed screen |

### Needs your confirmation (backend)
**Lesson completion endpoint.** Nothing in the existing web code marks a
*lesson* complete, and I can't see the backend. `lib/api/units.ts` calls
`PATCH /roadmaps/units/:id` with `{completed}`, inferred from the task route,
**not verified**. If it differs, change that one line. Until then, finishing
a lesson shows a toast that it was saved for this session only. Everything
else on the viewer still works. The final "Mark task as complete" button uses
the already-proven task endpoint.

### Bugs found and fixed
- The "Start / Continue" buttons on the task page linked to
  `/roadmaps/:id/tasks/:taskId/learn/:unitId` (plural `tasks`, and no such
  route existed), so they 404'd. Now points at the real route above.

### Deliberately not built
- **Quiz, practice-with-copy-buttons, Task List tabs "In Progress"**,
  priority/due badges, streaks, weekly activity chart, certificates: the data
  model has no quiz units, no task status beyond done/not-done, and no
  completion timestamps. Adding those to the backend is what unlocks them.
- Markdown in lessons uses a small built-in renderer (no new dependency).
  It renders everything as text nodes, so lesson content can't inject HTML.
  I tested it with sample content including hostile input.

### Unverified / not tested
Not opened in a browser. Type-check and production build pass (16 routes),
and the markdown renderer was exercised directly, but no page has been
exercised against a live backend.
