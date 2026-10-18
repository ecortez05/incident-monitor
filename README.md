# Real-Time Incident Monitoring Platform

A dashboard that streams application events and incident alerts live over WebSockets. Services post events to the API; the React dashboard shows them as they arrive, and an incident is opened automatically when a service starts throwing errors.

**Stack:** React, FastAPI, PostgreSQL, Redis, WebSockets, Docker, GitHub Actions, AWS

## How it works

```
 your services ──POST /events──▶ FastAPI ──▶ PostgreSQL   (events, incidents)
                                   │
                                   ├──▶ Redis counters   (errors per source, 60s window)
                                   ├──▶ Redis cache      (dashboard stats)
                                   └──▶ Redis pub/sub ──▶ /ws ──▶ React dashboard
```

- **Events** are stored in PostgreSQL and published to a Redis channel. Each open WebSocket subscribes to that channel, so it keeps working if you run more than one API process.
- **Auto-detected incidents:** `error`/`critical` events bump a per-source counter in Redis (expires after 60s). Hitting 5 errors opens an incident, once per source until it's resolved. Thresholds are set with `ERROR_THRESHOLD` and `ERROR_WINDOW`.
- **Incident tracking:** create, acknowledge, resolve, and reopen incidents. Updates are pushed to every connected dashboard.
- **Filtering:** events by level, source, and message text; incidents by status, severity, and source.
- **Caching:** `/stats` (events and incidents by level/severity) is cached in Redis for 10 seconds and cleared whenever something is written.

## Running it

```bash
docker compose up --build
```

- Dashboard: http://localhost:3000
- API docs: http://localhost:8000/docs

Then send some traffic:

```bash
pip install httpx
python backend/scripts/simulate.py                 # steady stream of random events
python backend/scripts/simulate.py --burst auth    # 6 errors from "auth" -> opens an incident
```

Or by hand:

```bash
curl -X POST localhost:8000/events -H "Content-Type: application/json" \
  -d '{"source":"checkout","level":"error","message":"payment gateway timeout"}'
```

### Local development

```bash
# needs Postgres and Redis running locally
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

cd frontend
npm install
npm run dev     # http://localhost:5173, proxies /api to :8000
```

## API

| Method | Path | Description |
| --- | --- | --- |
| POST | `/events` | ingest an event (`source`, `level`, `message`, `context`) |
| GET | `/events` | `?level=error,critical&source=&q=&before_id=&limit=` |
| POST | `/incidents` | open an incident manually |
| GET | `/incidents` | `?status=&severity=&source=` (comma-separated values allowed) |
| GET | `/incidents/{id}` | |
| PATCH | `/incidents/{id}` | change `status`, `severity`, or `title` |
| GET | `/stats` | cached dashboard numbers |
| WS | `/ws` | live `event` and `incident` messages |

## Tests

```bash
cd backend
python -m pytest
```

Tests run against SQLite and fakeredis, so they don't need Postgres or Redis. They cover ingestion, filtering, incident lifecycle, auto-detection, stats caching, and the WebSocket stream.

## CI/CD

`.github/workflows/ci.yml` runs the backend tests and a frontend build on every push and PR. On `main` it builds both images, pushes them to Amazon ECR, and redeploys the compose stack on an EC2 instance over SSH.

Secrets needed: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `EC2_HOST`, `EC2_SSH_KEY`.

## Not included

No authentication on the API yet, so keep it behind a VPN or security group if you deploy it. Events are never pruned.
