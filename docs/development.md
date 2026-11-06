# Development guide

## Repository layout

```
apps/api      FastAPI service (app/, migrations/, scripts/, tests/, data/)
apps/web      Next.js app (app/, components/, messages/, tests/)
docs          this documentation
docker        container files; docker-compose.yml runs both apps
.github       CI and scheduled workflows
```

## First-time setup

Prerequisites: Python 3.12+, Node 20+, a Supabase project (database and Auth), and at least one AI key.

```bash
# API
cd apps/api
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # fill in DATABASE_URL, SUPABASE_*, an AI key, ADMIN_EMAILS
alembic upgrade head
python scripts/seed_careers.py
uvicorn app.main:app --reload   # http://localhost:8000/docs

# Web
cd apps/web
npm install
cp .env.example .env.local    # NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_ANON_KEY, NEXT_PUBLIC_API_URL
npm run dev                   # http://localhost:3000
```

Every setting is explained in [configuration](reference/configuration.md). `docker compose up --build` runs both apps in containers.

On Windows, psycopg needs the selector event loop; the app and tests already set this.

## Daily commands

| Task | Command |
|---|---|
| API tests | `cd apps/api && pytest tests` |
| API coverage | `pytest tests --cov=app` (CI fails under 75%) |
| Web unit tests | `cd apps/web && npm test` |
| Web end-to-end | `npm run test:e2e` |
| Lint / types | `npm run lint`, `npx tsc --noEmit` |
| New migration | `alembic revision --autogenerate -m "what changed"` |
| Apply / verify | `alembic upgrade head`, then `alembic check` |
| Refresh API types | `python scripts/dump_openapi.py` then `npm run gen:api` |
| Refresh these docs | `python scripts/generate_docs.py` |

## Scripts (`apps/api/scripts`)

| Script | Purpose |
|---|---|
| `seed_careers.py` | Load the 14 careers from `data/careers.json` |
| `dump_openapi.py` | Write `openapi.json` (the web app's types come from it) |
| `generate_docs.py` | Regenerate `docs/reference/*` |
| `translate_messages.py` | AI-draft Urdu and Roman Urdu UI text from English |
| `sync_career_messages.py`, `sync_error_messages.py` | Keep career and error translations in step |
| `generate_vapid_keys.py` | Make a web-push key pair |
| `backup_db.py` | Logical backup (see the [runbook](runbooks/backup-and-restore.md)) |
| `delete_account.py` | Delete one learner on request (see [Operations](operations.md#deleting-an-account)) |

Workers: `python -m app.workers.send_reminders` and `python -m app.workers.check_links`.

## Conventions

- **Routes thin, services thick.** New behaviour goes in `app/services`; routes validate and delegate.
- **New table = migration + RLS.** After autogenerate, review the file and add `ALTER TABLE ... ENABLE ROW LEVEL SECURITY`. `tests/test_rls.py` fails if a table lacks it. Never add public policies; the API connects as owner and the browser must never read tables directly.
- **Errors carry a code.** Raise API errors with an `error_code`; add its text to the translations (`sync_error_messages.py`).
- **All UI text in `messages/`.** Add keys to `en.json`; then run the translation script, and have Urdu text reviewed.
- **Logical CSS** (`ms-`, `me-`, `ps-`...) so right-to-left works.
- **No emoji** anywhere in the UI or AI output.
- **AI calls go through `app/ai/llm`**, never a provider SDK directly, so fallback, logging and the token cap apply.
- **Awarding XP only through `GamificationService.award`.**
- After changing a schema or route, regenerate `openapi.json` and the web types.

## Translations

`npm`-side keys live in `apps/web/messages/{en,ur,ur-Latn}.json`. Workflow: edit `en.json` → `python scripts/translate_messages.py` → review the diff of the other two → commit. Urdu renders right-to-left via the `dir` set from the locale.

## Documentation

`docs/reference/*` is generated and must not be edited by hand. The generator refuses to run if a new API setting or web variable has no description (add it to `API_SETTINGS` or `WEB_SETTINGS` in `scripts/generate_docs.py`). Re-run it whenever routes, models or settings change.
