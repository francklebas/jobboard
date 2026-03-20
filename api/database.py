import os
from datetime import datetime, timedelta, timezone
from threading import Lock


CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "21600"))

_cache_lock = Lock()
_cached_jobs: list[dict] = []
_cached_until: datetime | None = None
_last_sync: str | None = None


def _clean_text(value: object) -> str:
    if value is None:
        return ""

    text = str(value).strip()
    if text.lower() in {"nan", "none", "null", "<na>"}:
        return ""
    return text


def _is_cache_expired(now: datetime) -> bool:
    return _cached_until is not None and now >= _cached_until


def _clear_cache() -> None:
    global _cached_jobs, _cached_until, _last_sync
    _cached_jobs = []
    _cached_until = None
    _last_sync = None


def init_db():
    return None


def get_db():
    return None


def store_jobs(jobs_data: list[dict]) -> int:
    global _cached_jobs, _cached_until
    now = datetime.now(timezone.utc)
    with _cache_lock:
        _cached_jobs = [
            {
                "title": _clean_text(job_data.get("title", "")),
                "company": _clean_text(job_data.get("company", "")),
                "location": _clean_text(job_data.get("location", "")),
                "url": _clean_text(job_data.get("url", "")),
                "source": _clean_text(job_data.get("source", "")),
                "date_posted": _clean_text(job_data.get("date_posted", "")),
                "description": _clean_text(job_data.get("description", "")),
            }
            for job_data in jobs_data
        ]
        _cached_until = now + timedelta(seconds=CACHE_TTL_SECONDS)
        return len(_cached_jobs)


def get_all_jobs() -> list[dict]:
    now = datetime.now(timezone.utc)
    with _cache_lock:
        if _is_cache_expired(now):
            _clear_cache()
            return []
        return list(_cached_jobs)


def get_last_sync() -> str | None:
    now = datetime.now(timezone.utc)
    with _cache_lock:
        if _is_cache_expired(now):
            _clear_cache()
            return None
        return _last_sync


def set_last_sync(ts: str):
    global _last_sync, _cached_until
    now = datetime.now(timezone.utc)
    with _cache_lock:
        _last_sync = ts
        if _cached_jobs:
            _cached_until = now + timedelta(seconds=CACHE_TTL_SECONDS)
