# Operations

Running the service day to day. For first-time setup see [Deployment](deployment.md).

## Scheduled jobs

| Job | Command | Frequency |
|---|---|---|
| Reminders, weekly summaries, streak messages | `python -m app.workers.send_reminders` | every 15 minutes |
| Link sweep (re-checks learning links, repairs dead ones) | `python -m app.workers.check_links` | weekly (`.github/workflows/link-check.yml`) |

If reminders stop, learners just stop getting them; nothing else breaks. Run the command by hand and read its output.

## Health and monitoring

- `GET /api/v1/health`: process is up (cheap; for load balancers).
- `GET /api/v1/health/ready`: also checks the database. Alert on this one.
- Logs are JSON in production (`LOG_FORMAT`); requests slower than `SLOW_REQUEST_MS` log a warning. Each request has an id.
- Sentry (`SENTRY_DSN`) for errors; PostHog (`POSTHOG_API_KEY`) for product events. Both are off when unset.
- Add an external uptime monitor on `/health/ready`.

## AI providers and cost

- Providers are tried in `AI_PROVIDERS` order; check the failure rate in **Admin → Insights → AI usage**. A sudden rise means a key, quota or outage.
- Costs shown there are estimates from `app/ai/pricing.py`; correct them with `AI_PRICES` if your plan differs.
- To contain spend set `AI_DAILY_TOKENS_PER_USER`. When a learner hits it they see a friendly "try again tomorrow" error (`AIBudgetExceeded`).
- Set a budget alert in each provider's dashboard as well.

## Database

- Schema changes: `alembic upgrade head` on deploy, then `alembic check` in CI.
- Backups: Supabase daily backups plus `scripts/backup_db.py`; restore steps in the [runbook](runbooks/backup-and-restore.md). Practise a restore.
- Tables are listed in the [database reference](reference/database.md).

## Common problems

| Symptom | Likely cause |
|---|---|
| Sign-up emails never arrive | Supabase custom SMTP not set up, or the sending domain is not verified |
| Every request returns 401 | Wrong `SUPABASE_URL`/`SUPABASE_JWT_SECRET`, or clock skew |
| Browser errors on API calls | `CORS_ORIGINS` missing the web address |
| Roadmap stuck "building" | AI providers failing or timing out; check Insights and logs, then use Regenerate |
| Many 429 responses | Limits too low for real traffic, or counters not shared (use `RATE_LIMIT_STORAGE_URI=redis://...` with several processes) |
| Resource links missing | The link sweep removed dead ones; see Insights → Learning links |
| No reminders | Worker not scheduled, `RESEND_API_KEY` unset, or push keys unset |

## Support requests

- **Forgot password / email not received:** use the sign-in page's reset and resend options; if still failing check the SMTP setting above.
- **Export my data:** the learner can download it from Settings (`GET /account/export`).
- **Wrong or broken lesson:** find the lesson's votes in Insights; regenerate the roadmap or retry lessons.

## Deleting an account

On a verified request from the account owner:

1. Take a backup if in doubt.
2. Preview: `python scripts/delete_account.py --email person@example.com` (changes nothing and lists what would go).
3. Delete: add `--yes`.
4. Reply to the person. The Privacy Policy promises completion within 30 days.
