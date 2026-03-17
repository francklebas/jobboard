import asyncio
import logging
from contextlib import asynccontextmanager

from alembic import command
from alembic.config import Config
from database import get_all_jobs, get_last_sync
from fastapi import BackgroundTasks, FastAPI
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from scraper import run_scrape

logging.basicConfig(level=logging.INFO)


def run_migrations():
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Running Alembic migrations...")
    await asyncio.get_event_loop().run_in_executor(None, run_migrations)
    logging.info("Migrations done.")

    # Run an initial scrape in the background if the database is completely empty.
    # This prevents the "0 jobs" regression on the very first startup before the cron triggers.
    if not get_all_jobs():
        logging.info("Database is empty. Triggering an initial background scrape.")
        asyncio.create_task(run_in_threadpool(run_scrape))

    yield


app = FastAPI(title="JobBoard API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/jobs")
def list_jobs(q: str = "", source: str = ""):
    jobs = get_all_jobs()

    if q:
        q_lower = q.lower()
        jobs = [
            j
            for j in jobs
            if q_lower in j["title"].lower() or q_lower in j["description"].lower()
        ]

    if source:
        jobs = [j for j in jobs if j["source"].lower() == source.lower()]

    return {"count": len(jobs), "last_sync": get_last_sync(), "jobs": jobs}


@app.post("/jobs/sync")
def sync_jobs(background_tasks: BackgroundTasks, q: str = ""):
    import time
    start_time = time.time()
    background_tasks.add_task(run_scrape, search_query=q if q else None)
    return {"status": "sync started", "query": q, "started_at": start_time}


@app.get("/jobs/sync/status")
def get_sync_status():
    return {"last_sync": get_last_sync()}
