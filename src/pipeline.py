from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from zoneinfo import ZoneInfo

from .ai_ranker import DEFAULT_GEMINI_MODEL, evaluate_with_gemini
from .deduplication import dedupe_news
from .ranking import (
    apply_editorial_scores,
    prefilter_candidates,
    select_balanced_feed,
)
from .source_registry import build_source_jobs


def fetch_daily_news(
    *,
    gemini_api_key: str = "",
    gemini_model: str = DEFAULT_GEMINI_MODEL,
) -> dict:
    now = datetime.now(ZoneInfo("America/Santiago"))
    errors: list[str] = []
    candidates: list[dict] = []
    source_stats: dict[str, int] = {}

    jobs = build_source_jobs(now)

    with ThreadPoolExecutor(max_workers=7) as executor:
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

    # First remove exact/near-exact duplicates deterministically. Then cap the
    # candidate pool before the AI call to control latency and token usage.
    unique = dedupe_news(candidates)
    prefiltered = prefilter_candidates(unique, now=now, max_per_region=16)

    ai_items, ranking_error = evaluate_with_gemini(
        prefiltered,
        now=now,
        api_key=gemini_api_key,
        model=gemini_model,
    )
    ai_active = bool(gemini_api_key and not ranking_error)

    scored = apply_editorial_scores(
        ai_items,
        now=now,
        ai_active=ai_active,
    )
    chile, world = select_balanced_feed(scored, total_limit=7)

    return {
        "chile": chile,
        "world": world,
        "fetched_at": now,
        "errors": errors,
        "source_stats": source_stats,
        "ranking_mode": "gemini" if ai_active else "local",
        "ranking_error": ranking_error,
        "candidate_count": len(prefiltered),
    }
