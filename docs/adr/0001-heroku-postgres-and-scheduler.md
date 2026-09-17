# Heroku with Postgres and Heroku Scheduler instead of SQLite and in-process cron

We deploy to Heroku (existing platform credits) using the Python buildpack. Because dyno filesystems are wiped on every restart and Eco dynos sleep, state (Incidents, triage, Audit Run logs, cached Sectors API responses) lives in Heroku Postgres, not SQLite, and Audit Runs are triggered by the Heroku Scheduler add-on running a CLI command daily that exits unless it is Saturday — not APScheduler inside the web process. The web dyno is Basic (non-sleeping) so Telegram deep links open instantly. The HLD's SQLite, APScheduler and Dockerfile are superseded.

## Consequences

- Heroku Scheduler has no weekly cadence; the day-of-week guard lives in code, and the "Run now" button calls the same entry point.
- Postgres doubles as the API response cache, which is what keeps the 500-credit Sectors API budget viable: a quarter already stored is never fetched again.
