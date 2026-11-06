# User guide

How Uraan AI works for a learner. Useful for support staff answering questions.

## Getting started

1. **Sign up** with email and password, then confirm the email. If it did not arrive, use "Resend confirmation" on the sign-in page.
2. **Onboarding** (under five minutes): your name, language, education, device, goal (local job, remote job, freelancing, startup, study abroad), study hours and pace, and a career.
3. You land on the **Dashboard**.

Forgot your password? Use "Forgot password" on the sign-in page; the email link opens the reset page.

## Careers

`/careers` lists 14 careers: Backend, Frontend, Full-stack, Mobile app, AI engineer, Data scientist, Cyber security, UI/UX designer, DevOps, Cloud, Digital marketer, Graphic designer, Video editor, Content creator.

Each career shows difficulty, months to job-ready, Pakistan salary range in PKR, market demand, skills and free resources. You can **compare** careers side by side, or use **Help me choose**, where the AI recommends careers from the catalogue only (it never invents one).

## Roadmaps

**Generate my roadmap** builds a plan from your profile: phases, weekly milestones, tasks. It takes a little while and runs in the background; you can leave the page. It respects your device (a phone-only learner gets no local-install tasks), goal and pace.

You can:

- **Pause / resume** a roadmap (a paused one leaves the calendar).
- **Regenerate** it from scratch.
- **Adapt** it when your study time changes: only unfinished work is rewritten, finished work is kept.
- **Restore a version**: a snapshot is saved before every regenerate or adapt.
- **Delete** a roadmap.
- Have several roadmaps (one per goal); one is active.

## Lessons

Open a task and **Create learning plan** to get its lessons. Lessons come in kinds such as reading, video, coding exercise and project. Mark a lesson complete to earn XP. If lesson writing failed for some lessons, **Retry** writes only those.

Every lesson ends with **Was this lesson helpful?** Choosing "No" asks what went wrong (something is wrong, too hard, too easy, unclear, ...) and an optional comment. You can change or remove your vote. Staff use this to find weak lessons.

Resource links are checked automatically; a dead link is replaced or removed.

## Quizzes

Tasks can have a quiz. Passing earns bonus XP and counts toward achievements.

## Mentor

`/mentor` is an AI mentor that knows your profile, language, level, roadmap and recent progress. Features:

- Suggestion chips ("Explain...", "Review my code", "Interview questions").
- **Review my work**: a public GitHub link, pasted code or portfolio link gets structured feedback.
- A daily motivation message based on your real progress.
- Tone setting: Friendly, Gen-Z or Professional.
- Saved conversations you can delete.

The mentor can make mistakes (a reminder is shown on the page). If you write something that suggests you are in distress, it replies with a caring message pointing you to people who can help instead of a normal AI answer.

## Planner

The calendar places your lessons in time blocks that respect your preferred study hours and daily minutes. Views: month, week, day. You can move a lesson to another day (it stays pinned until you unpin it), reset preferences, or type something like "exams next week, evenings only" into **AI optimise**. Missed lessons move forward unless pinned. A private **.ics feed** lets you subscribe in Google or Apple Calendar; **regenerate** it to invalidate the old link.

## Interviews, documents and portfolio

- **Mock interviews**: pick a role, answer questions one by one, get feedback and a score. Finishing earns XP.
- **Documents**: AI-drafted resumes and cover letters you can edit.
- **Portfolio**: add projects (the AI can draft a description), tick the portfolio checklist, and optionally publish a public page at your own link.

## Resource library

`/resources`: search and filter free resources, bookmark them, rate them.

## Search

The top bar searches your roadmaps, tasks, lessons, documents and resources.

## Notifications and email

In-app notifications, push notifications (if you allow them in the browser) and email: daily reminder, weekly summary, streak and milestone messages. Every email has a one-click unsubscribe. Settings lets you turn each channel off.

## Settings

Language (English, Urdu, Roman Urdu), AI tone, wording (**Classic** or **Gamified**: Mission, Quest, Claim XP), notification channels, reminder time, and your calendar feed. **Export my data** downloads everything stored about you as JSON. **Delete account** is not self-service yet; see [Operations](operations.md#deleting-an-account).

---

## XP, levels and titles

| Action | XP |
|---|---|
| Complete a lesson | 10 |
| Complete a task | 25 |
| Pass a quiz | 30 |
| Finish a mock interview | 40 |
| Beat the monthly "boss" project | 150 bonus |

**100 XP = 1 level.** Your career title depends on total XP:

| Title | From XP |
|---|---|
| Explorer | 0 |
| Apprentice | 500 |
| Builder | 1,500 |
| Professional | 4,000 |
| Master | 10,000 |

## Streaks and freezes

Learn on consecutive days to build a streak. Every **7-day** streak earns one **streak freeze** (you hold at most **2**). If you miss a day, a freeze is spent automatically and the streak survives. The dashboard shows how many you hold.

## Achievements

There are 23 achievements worth 10 to 300 XP each, for things like first lesson, 7-day streak, first project, first quiz pass, first interview, portfolio published, 100 hours, and reaching levels. See them at `/achievements`; unlocking one sends a notification.

## Career readiness score (0-100)

| Part | Weight | Full marks when |
|---|---|---|
| Tasks completed | 35% | all roadmap tasks done |
| Projects | 20% | project work finished |
| Consistency | 15% | active on 20 of the last 28 days |
| Mock interviews | 15% | 3 interviews done |
| Portfolio | 15% | 3 portfolio projects |

Levels: **25+** building, **50+** almost there, **75+** job ready. The card shows a breakdown and tips for the weakest part.

## Leaderboard

Learners are ranked by XP. Only a display name and XP are shown.
