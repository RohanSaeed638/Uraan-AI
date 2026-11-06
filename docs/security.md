# Security and privacy

## Who can see what

- **The browser holds only the public Supabase key**, used for sign-in. **Row Level Security is on for every table with no public policies**, so that key reads nothing. `tests/test_rls.py` keeps this true for new tables.
- **All data goes through the API**, which verifies the Supabase token, then scopes every query to the signed-in profile. Another learner's roadmap, task or document returns not found (`test_task_ownership.py`).
- The Supabase **secret** key (`SUPABASE_SERVICE_ROLE_KEY`) exists only on the API server. Never put it in the web app.
- **Admin routes** require the `admin` role; others get 403. All admin actions are audit-logged.

## Hardening in place

| Area | Measure |
|---|---|
| Abuse | Rate limits per visitor, learner and address, plus tighter limits for AI chat and roadmap builds (429 with an error code). Use Redis storage when running several API processes. |
| AI cost | Optional per-learner daily token cap; failure fallback across providers. |
| AI safety | Mentor screens for self-harm and answers with a fixed caring message (no AI call); prompt rules against harmful advice and prompt injection from pasted content; no emoji. |
| SSRF | The link checker and the GitHub reviewer refuse private/internal addresses at every redirect hop; GitHub fetches are limited to github.com and size-capped. |
| Public links | Calendar feed and unsubscribe links use unguessable tokens; the feed token can be regenerated. Public portfolios are visible only if the owner chooses. |
| Email | One-click unsubscribe; configure SPF, DKIM and DMARC for the sending domain ([Deployment](deployment.md)). |
| Transport | CORS limited to `CORS_ORIGINS`; run behind HTTPS with `--proxy-headers`. |
| Errors | Sentry reports carry no names, emails or text; PostHog events carry a profile id only. |

## Privacy

- Learners can **export** all their data (`GET /account/export`).
- Deletion on request is done by an operator with `scripts/delete_account.py` (see [Operations](operations.md#deleting-an-account)); the Privacy Policy promises this within 30 days.
- Earned XP and achievements stay with the learner's data only until deletion; deleting an account removes everything.
- Legal pages (Terms, Privacy, Contact) show `NEXT_PUBLIC_CONTACT_EMAIL`. **Have them reviewed by a lawyer before launch.**

## Before going live

1. Real `SUPABASE_SERVICE_ROLE_KEY` set; rotate any key that was ever shared.
2. Supabase Site URL and redirect URLs set; custom SMTP configured (the default mailer only reaches team members).
3. `ADMIN_EMAILS` correct; `CORS_ORIGINS` limited to your sites.
4. Backups enabled and a restore tested ([runbook](runbooks/backup-and-restore.md)).
5. Urdu and Roman Urdu text and legal text reviewed by people.
