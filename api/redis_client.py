import os
import json
import redis

_redis = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"), decode_responses=True)

JOBS_KEY = "jobs"


def store_jobs(jobs: list[dict]) -> int:
    """Replace all stored jobs with new ones. Returns count stored."""
    pipe = _redis.pipeline()
    pipe.delete(JOBS_KEY)
    for job in jobs:
        pipe.rpush(JOBS_KEY, json.dumps(job, default=str))
    pipe.execute()
    return len(jobs)


def get_all_jobs() -> list[dict]:
    raw = _redis.lrange(JOBS_KEY, 0, -1)
    return [json.loads(r) for r in raw]


def get_last_sync() -> str | None:
    return _redis.get("last_sync")


def set_last_sync(ts: str):
    _redis.set("last_sync", ts)
