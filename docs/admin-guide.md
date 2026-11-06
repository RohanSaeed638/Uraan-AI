# Admin guide

## Becoming an admin

List your email in `ADMIN_EMAILS` (comma separated). You become an admin the first time you sign in. Admins can promote or demote others from **Users**. Everyone else gets a 403 from `/admin` and the admin API.

Every admin action is written to the audit log.

## The portal (`/admin`)

| Section | What you do |
|---|---|
| Overview | Counts of users, roadmaps, lessons, AI failures and usage |
| Users | Search users, change a role |
| Careers | Create and edit careers: skills, salary range, difficulty, demand, active flag |
| Resources | Manage the library of free learning resources |
| Announcements | Publish a banner (and notification) with a start and end time; switch off or edit |
| Audit log | Who did what and when |
| Insights | Quality and business numbers, below |

## Insights (`/admin/insights`)

**Sign-up funnel.** Sign-ups grouped by the week they joined (admins excluded), and how many reached each step: onboarded, built a roadmap, finished a first lesson, returned, and finished a roadmap. "Returned" means active at least 7 days after signing up, counted only among people who have been around that long.

**Lesson quality.** Votes from "Was this lesson helpful?": overall helpful rate, reasons given, comments, and the lessons with the most negative votes. Start with the lessons with repeated "Something is wrong" votes.

**AI usage and estimated cost.** Calls, tokens, failure rate and a cost estimate per model, from a built-in price table (`app/ai/pricing.py`). Prices are estimates; override them with `AI_PRICES`. Use `AI_DAILY_TOKENS_PER_USER` to cap a single learner.

**Learning links.** How many resource links are working, dead or unknown, and which were removed or replaced.

## Habits that keep quality high

- Review Insights weekly; fix or regenerate lessons with poor votes.
- Review the career catalogue when salaries or demand change.
- Check the AI failure rate; a spike usually means a provider key or quota problem (see [Operations](operations.md)).
- Review Urdu and Roman Urdu text before launch; they are AI-drafted.

Endpoints behind these screens are in the [API reference](reference/api.md) under the admin sections.
