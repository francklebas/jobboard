import logging
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


def run_scrape(search_query: str | None = None) -> int:
    """Scrape jobs from multiple sources.
    
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
                site_name=["indeed", "linkedin"],
                search_term=query,
                location="Stockholm, Sweden",
                results_wanted=30,
                country_indeed="Sweden",
            )
            for _, row in df.iterrows():
                url = str(row.get("job_url", ""))
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                title = str(row.get("title", ""))
                description = str(row.get("description", ""))

                if should_filter and not _matches_stack(title, description):
                    continue

                all_jobs.append({
                    "title": title,
                    "company": str(row.get("company_name", "")),
                    "location": str(row.get("location", "")),
                    "url": url,
                    "source": str(row.get("site", "")),
                    "date_posted": str(row.get("date_posted", "")),
                    "description": description[:2000],
                })
        except Exception:
            logger.exception("Scrape failed for query: %s", query)

    count = store_jobs(all_jobs)
    set_last_sync(datetime.now(timezone.utc).isoformat())
    logger.info("Stored %d jobs", count)
    return count
