# Deploying Uraan AI

Three parts: **Supabase** (database and sign-in, already running), the **API** (Railway or Render),
and the **web app** (Vercel). Do them in this order, because each needs the address of the one before.

> Put the API in the **same region as the Supabase database** (check Supabase > Project Settings > Database).
> Every request makes a handful of database calls; across the world each one costs hundreds of
> milliseconds, in the same region it costs a few. This is the single biggest factor in speed.

## 1. Supabase

1. **Daily backups:** Project Settings > Database > Backups (Pro plan). Also see `runbooks/backup-and-restore.md`.
2. **Authentication > URL Configuration:**
   - Site URL: your web address, e.g. `https://app.example.com`.
   - Redirect URLs: `https://app.example.com/auth/callback` and `https://app.example.com/reset-password`
     (keep `http://localhost:3000/**` for development).
3. **Authentication > SMTP Settings:** your Resend SMTP details, otherwise sign-up confirmation emails
   only reach team members.
4. Keep Row Level Security on every table (`pytest tests/test_rls.py` checks this).

## 2. API (Railway, Render or any Docker host)

- **Build:** the Dockerfile at `apps/api/Dockerfile` (root directory `apps/api`).
- **Start:** the image already runs `uvicorn ... --proxy-headers`. Set `RUN_MIGRATIONS=1` to apply
  migrations on start (one instance), or run `alembic upgrade head` as a release/pre-deploy command.
- **Health check path:** `/health/ready` (checks the database too).
- **Variables:** everything in `apps/api/.env.example`. The ones that matter first:
  `APP_ENV=production`, `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` (the secret key, not the
  public one), `SUPABASE_JWT_SECRET`, at least one AI key, `CORS_ORIGINS` (your web address, no trailing
  slash), `WEB_URL`, `API_PUBLIC_URL`, `ADMIN_EMAILS`.
- **More than one instance:** set `RATE_LIMIT_STORAGE_URI` to a Redis address so the limits are shared.
- **Reminders:** run `python -m app.workers.send_reminders` every 15 minutes. Either a cron job on the
  host, or the `Send reminders` GitHub workflow (set repository variable `REMINDERS_ENABLED=true` and the
  secrets listed in `.github/workflows/reminders.yml`). Use one, not both.

## 3. Web (Vercel)

- Import the repository; **Root Directory** `apps/web`. The framework is detected as Next.js.
- **Environment variables** (Production): `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`,
  `NEXT_PUBLIC_API_URL` (the API's public address, no `/api/v1`), and optionally `NEXT_PUBLIC_SITE_URL`
  and `NEXT_PUBLIC_SENTRY_DSN`. They are fixed at build time: change one, redeploy.
- Back on the API, add the Vercel address to `CORS_ORIGINS`.

## 4. After the first deploy

- Open `<api>/health/ready` (should say `ready`) and `<api>/docs`.
- Sign up with a real address, confirm the email, finish onboarding, build a roadmap.
- Run the browser journey against it: `E2E_BASE_URL=... E2E_API_URL=... npm run test:e2e --workspace apps/web`.
- Add the accounts you want for monitoring: `SENTRY_DSN` / `NEXT_PUBLIC_SENTRY_DSN`, `POSTHOG_API_KEY`.

## Running everything in containers locally

`docker compose up --build` starts the API (with migrations), the web app and the reminder loop. It reads
`apps/api/.env` and needs `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` in the shell or a
root `.env`.

## Keeping the web types in step with the API

`apps/api/openapi.json` and `apps/web/types/api.generated.ts` are generated:

```bash
cd apps/api && python scripts/dump_openapi.py
cd ../web && npm run gen:api
```

CI re-runs both and fails when the committed files are stale, so an endpoint change either updates the
types or breaks the build. Use `import type { paths, components } from "@/types/api.generated"` in new code.
