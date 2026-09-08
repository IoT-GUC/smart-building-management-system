# Smart Building Management System

FastAPI-based smart-building platform for LoRaWAN provisioning, telemetry,
floor maps, alarms, gateways, client access and firmware tooling.

## Requirements

- Python **3.10+**
- pip

## Install and run

### Windows

```powershell
.\windows\install.ps1
.\windows\run.bat
```

### Linux

```bash
bash linux/install.sh
bash linux/run.sh
```

Direct entry point:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Configuration

Copy `.env.example` to `.env` and edit it for your environment.

The active names include `DB_FILE`, TTN settings, `TB_USERNAME`, `TB_PASSWORD`,
`ALERT_EMAIL_FROM`, `ALERT_EMAIL_TO`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`,
`COOKIE_SECURE`, and `LOCAL_TEST_MODE`.

Two settings gate real security behaviour:

- **`TTN_WEBHOOK_SECRET` is required.** `/ttn-webhook` returns 503 to every
  request while it is empty. Set the same value in the TTN webhook's
  `X-Webhook-Secret` header.
- **`CORS_ORIGINS`** is a comma-separated list of front-end origins. Empty
  means same-origin only; there is no wildcard.

Set `COOKIE_SECURE=true` for any deployment served over HTTPS.

## Portals

- Admin: `/admin`
- Client: `/client-portal`
- API docs: `/docs`

## Database

SQLite is the default. Startup bootstraps the current compatibility schema and
then runs tracked non-destructive migrations in `app/db/migrations/`.

The project is migrating incrementally to the canonical hierarchy:

`Client -> Site -> Building -> Floor -> Room -> Device`

Legacy location columns/tables are intentionally retained until all routes use
relational joins and migration tests pass against a copy of real data.

## Verification

```bash
python -m compileall -q app
pytest -q
ruff check app tests
```

These are the same three commands CI runs (`.github/workflows/ci.yml`).
