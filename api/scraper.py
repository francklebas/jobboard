import logging
import math
from datetime import datetime, timezone
from jobspy import scrape_jobs
from database import store_jobs, set_last_sync

logger = logging.getLogger(__name__)

SEARCH_QUERIES = [
    "React developer",
    "Vue developer",
    "TypeScript developer",
    "Frontend developer",
]

STACK_KEYWORDS = {"react", "vue", "typescript", "nuxt", "next", "frontend", "front-end"}


def _matches_stack(title: str, description: str) -> bool:
    text = f"{title} {description}".lower()
    return any(kw in text for kw in STACK_KEYWORDS)


def _normalize_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and math.isnan(value):
        return ""

    text = str(value).strip()
    if text.lower() in {"nan", "none", "null"}:
        return ""
    return text


def _first_text(row, *keys: str) -> str:
    for key in keys:
        text = _normalize_text(row.get(key, ""))
        if text:
            return text
    return ""


def _truncate_description(text: str, max_chars: int = 200) -> str:
    value = _normalize_text(text)
    if len(value) <= max_chars:
        return value

    shortened = value[:max_chars].rstrip()
    if " " in shortened:
        shortened = shortened.rsplit(" ", 1)[0]
    return f"{shortened}..."


def run_scrape(search_query: str | None = None) -> int:
    """Scrape jobs from Indeed.
    
    If search_query is provided, scrapes only for that query and skips stack filtering.
    Otherwise, scrapes for default SEARCH_QUERIES and filters by stack.
    """
    logger.info("Starting job scrape...")
    all_jobs: list[dict] = []
    seen_urls: set[str] = set()

    queries = [search_query] if search_query else SEARCH_QUERIES
    should_filter = search_query is None

    for query in queries:
        try:
            logger.info(f"Scraping for query: {query}")
            df = scrape_jobs(
                site_name=["indeed"],
                search_term=query,
                location="Stockholm, Sweden",
                results_wanted=30,
                country_indeed="Sweden",
            )
            for _, row in df.iterrows():
                url = _first_text(row, "job_url", "job_url_direct")
                if not url:
                    continue
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                title = _first_text(row, "title")
                description = _first_text(row, "description", "company_description")

                if should_filter and not _matches_stack(title, description):
                    continue

                all_jobs.append({
                    "title": title,
                    "company": _first_text(row, "company_name", "company"),
                    "location": _first_text(row, "location"),
                    "url": url,
                    "source": _first_text(row, "site"),
                    "date_posted": _first_text(row, "date_posted"),
                    "description": _truncate_description(description),
                })
        except Exception:
            logger.exception("Scrape failed for query: %s", query)

    count = store_jobs(all_jobs)
    set_last_sync(datetime.now(timezone.utc).isoformat())
    logger.info("Stored %d jobs", count)
    return count
