# JobBoard Stockholm

Aggregates frontend job listings in Stockholm, filtered by stack (React, Vue, TypeScript).

## Stack

- **FastAPI** — REST API + job scraping via [python-jobspy](https://github.com/Bunsly/JobSpy)
- **APScheduler** — Automated scraping on a configurable interval
- **Redis** — Job storage
- **Nuxt** — SSR frontend with full-text search and source filtering

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

- Frontend: http://localhost:3000
- API: http://localhost:8000

## API

| Method | Endpoint      | Description                  |
|--------|---------------|------------------------------|
| GET    | `/jobs`       | List jobs (`?q=` `&source=`) |
| POST   | `/jobs/sync`  | Trigger manual scrape        |

## Configuration

See `.env.example` for available environment variables.

| Variable                 | Default               | Description                    |
|--------------------------|-----------------------|--------------------------------|
| `REDIS_URL`              | `redis://redis:6379`  | Redis connection string        |
| `SCRAPE_INTERVAL_HOURS`  | `6`                   | Hours between automatic scrapes|
| `NUXT_PUBLIC_API_URL`    | `http://localhost:8000` | API URL (client-side)        |
| `NITRO_API_URL`          | `http://api:8000`     | API URL (server-side proxy)    |

## Sources

Jobs are scraped from Indeed and LinkedIn, filtered by keywords: `react`, `vue`, `typescript`, `nuxt`, `next`, `frontend`, `front-end`.
