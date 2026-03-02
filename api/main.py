import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

import scheduler
from scraper import run_scrape
from redis_client import get_all_jobs, get_last_sync

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler.start()
    yield
    scheduler.shutdown()


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
            j for j in jobs
            if q_lower in j["title"].lower() or q_lower in j["description"].lower()
        ]

    if source:
        jobs = [j for j in jobs if j["source"].lower() == source.lower()]

    return {"count": len(jobs), "last_sync": get_last_sync(), "jobs": jobs}


@app.post("/jobs/sync")
def sync_jobs(background_tasks: BackgroundTasks, q: str = ""):
    background_tasks.add_task(run_scrape, search_query=q if q else None)
    return {"status": "sync started", "query": q}
