# Backups and restoring

Everything a learner owns (profiles, roadmaps, lessons, progress, notifications,
documents, the audit log) is in one Postgres database on Supabase. The sign-in
accounts live in the same database, in its `auth` schema. Nothing else needs a
backup: the web app and API hold no state, and the AI providers keep nothing.

## 1. Turn on Supabase's daily backups (you do this once)

In the Supabase dashboard for the project:

1. **Project Settings > Billing**: daily backups need the **Pro** plan (the Free
   plan has none). Pro keeps 7 daily backups.
2. **Database > Backups**: confirm the list shows a backup from the last 24 hours.
3. Optional, for a production launch: add the **Point in Time Recovery** add-on
   (restore to any second in the last 7 days) on the same page.

## 2. Your own copy (works on any plan)

`apps/api/scripts/backup_db.py` writes a compressed dump with `pg_dump`, so a
copy exists outside Supabase too. Install the PostgreSQL client tools (the
version must be at least the server's), then from `apps/api`:

```bash
python scripts/backup_db.py                 # writes backups/uraan-YYYYMMDD-HHMMSS.dump
python scripts/backup_db.py --keep 14       # also deletes all but the newest 14
```

Run it from a scheduler (a nightly cron job or a GitHub Actions workflow with
`DATABASE_URL` as a secret) and copy the file somewhere private: another cloud
bucket, not the same Supabase project. A dump holds learners' personal data, so
treat it like the database itself: encrypted storage, not in the repository.

## 3. Restoring

Practise this once before you need it. Restore into a **new, empty** Supabase
project (or a local Postgres), never straight over production.

1. Create the new project. Note its connection string.
2. Restore the dump:
   ```bash
   pg_restore --no-owner --no-privileges --clean --if-exists \
     --dbname "postgresql://USER:PASSWORD@HOST:5432/postgres" backups/uraan-XXXX.dump
   ```
   Errors about Supabase's own roles or extensions that already exist are
   expected and harmless; errors about `public` tables are not.
3. Check the schema matches the code: from `apps/api`, with `DATABASE_URL`
   pointing at the restored database, run `alembic current` (it must show the
   latest revision) and `alembic check` (must say no new operations).
4. Check Row Level Security: `pytest tests/test_rls.py`. Every table must have it.
5. Count the rows that matter and compare with the old database:
   `select count(*) from profiles;` and the same for `roadmaps` and
   `task_learning_units`.
6. Point the API's `DATABASE_URL` (and the web app's Supabase URL and keys, if
   you restored into a new Supabase project) at the new database and deploy.
   Learners may need to sign in again if the project's JWT secret changed.

## 4. After a bad change or deleted data

* Wrong data in a few rows: restore a backup into a **separate** database, copy
  the rows back with SQL, and leave production running.
* The whole database is damaged: restore as above and redeploy; tell learners
  anything done since the backup time is lost (with Point in Time Recovery, since
  the second you pick).
