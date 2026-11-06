# Uraan AI documentation

Uraan AI is a career-learning platform for learners in Pakistan. A learner picks a career, gets an AI-built roadmap, studies lesson by lesson, and earns XP, achievements and a career-readiness score along the way.

| You are... | Start here |
|---|---|
| A learner or support person | [User guide](user-guide.md) |
| An admin | [Admin guide](admin-guide.md) |
| A new developer | [Development guide](development.md), then [Architecture](architecture.md) |
| Running the service | [Operations](operations.md), [Deployment](deployment.md), [Backup and restore](runbooks/backup-and-restore.md) |
| Reviewing security or privacy | [Security and privacy](security.md) |
| Writing or running tests | [Testing](testing.md) |

## Guides

- [Architecture](architecture.md): the parts, how a request flows, the AI layer, background jobs.
- [User guide](user-guide.md): every learner feature, plus the XP, level and readiness rules.
- [Admin guide](admin-guide.md): the admin portal and the Insights page.
- [Development guide](development.md): setup, daily commands, conventions, migrations, translations.
- [Testing](testing.md): what is tested and how.
- [Security and privacy](security.md): who can see what, and why.
- [Operations](operations.md): scheduled jobs, health checks, monitoring, AI cost, account deletion.
- [Deployment](deployment.md): going live.

## Reference (generated)

These pages are written by `apps/api/scripts/generate_docs.py` from the code. Do not edit them by hand; re-run the script (see the [Development guide](development.md#documentation)).

- [API reference](reference/api.md): every endpoint, grouped by area.
- [Database reference](reference/database.md): every table and column.
- [Configuration](reference/configuration.md): every environment variable for the API and web app.
- [Web routes](reference/web-routes.md): every page of the web app.

## Reports

- [Project report](PROJECT_REPORT.md): what was built and why.
- [Status report](STATUS_REPORT.md): where the project stands and what remains.
