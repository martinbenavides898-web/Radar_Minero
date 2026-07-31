from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from zoneinfo import ZoneInfo

from data.fallback_news import FALLBACK_NEWS
from .deduplication import dedupe_news
from .ranking import select_diverse
from .source_registry import build_source_jobs


def fetch_daily_news() -> dict:
    now = datetime.now(ZoneInfo("America/Santiago"))
    errors: list[str] = []
    candidates: list[dict] = []
    source_stats: dict[str, int] = {}

    jobs = build_source_jobs(now)

    with ThreadPoolExecutor(max_workers=6) as executor:
        future_map = {
            executor.submit(fetcher): source_name
            for source_name, fetcher in jobs
        }

        for future in as_completed(future_map):
            source_name = future_map[future]
            try:
                items = future.result()
                source_stats[source_name] = len(items)
                candidates.extend(items)
            except Exception as exc:
                source_stats[source_name] = 0
                errors.append(f"{source_name}: {type(exc).__name__}")

    candidates.extend(dict(item) for item in FALLBACK_NEWS)
    unique = dedupe_news(candidates)

    chile = select_diverse(
        unique,
        region="Chile",
        limit=4,
        now=now,
    )
    world = select_diverse(
        unique,
        region="Mundo",
        limit=3,
        now=now,
    )

    return {
        "chile": chile,
        "world": world,
        "fetched_at": now,
        "errors": errors,
        "source_stats": source_stats,
    }
