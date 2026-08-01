from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import time
from zoneinfo import ZoneInfo

from .ai_ranker import (
    DEFAULT_GEMINI_MODEL,
    evaluate_with_gemini,
    translate_selected_world_stories,
)
from .deduplication import dedupe_news
from .ranking import (
    apply_editorial_scores,
    prefilter_candidates,
    select_balanced_feed,
)
from .snapshot_store import (
    load_bootstrap_snapshot,
    load_news_snapshot,
    save_news_snapshot,
)
from .source_registry import build_source_jobs
from .sources.common import humanize_published


CHILE_TARGET = 4
WORLD_TARGET = 3


def _run_source(source_name: str, fetcher) -> tuple[str, list[dict], float]:
    started = time.monotonic()
    items = fetcher()
    duration = time.monotonic() - started
    return source_name, items, duration


def _refresh_published_labels(items: list[dict], now: datetime) -> list[dict]:
    refreshed: list[dict] = []

    for item in items:
        copy = dict(item)
        published_at = copy.get("published_at")
        if isinstance(published_at, str):
            try:
                published_at = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            except ValueError:
                published_at = None
            copy["published_at"] = published_at

        copy["published"] = humanize_published(published_at, now)
        refreshed.append(copy)

    return refreshed


def _snapshot_candidates(snapshot: dict, now: datetime) -> list[dict]:
    age_hours = float(snapshot.get("age_hours", 0.0))
    origin = str(snapshot.get("_origin", "runtime"))
    penalty = min(42.0, 10.0 + age_hours * 0.32)
    if origin == "bootstrap":
        penalty = max(penalty, 36.0)

    candidates: list[dict] = []
    for region_key in ("chile", "world"):
        for item in _refresh_published_labels(snapshot.get(region_key, []), now):
            copy = dict(item)
            copy["from_snapshot"] = True
            copy["snapshot_origin"] = origin
            copy["final_score"] = max(
                0.0,
                float(copy.get("final_score", 45.0)) - penalty,
            )
            copy["event_key"] = copy.get("event_key") or copy.get("title", "")
            candidates.append(copy)

    return candidates


def _merge_with_snapshot(
    *,
    current_items: list[dict],
    snapshot: dict,
) -> tuple[list[dict], list[dict], int]:
    snapshot_items = _snapshot_candidates(snapshot, datetime.now(ZoneInfo("America/Santiago")))
    combined = dedupe_news(current_items + snapshot_items)

    # dedupe_news preserves source-priority ordering, so re-sort by editorial score.
    combined.sort(
        key=lambda item: (
            0 if item.get("from_snapshot") else 1,
            float(item.get("final_score", 0.0)),
        ),
        reverse=True,
    )
    chile, world = select_balanced_feed(combined, total_limit=7)
    used = sum(1 for item in chile + world if item.get("from_snapshot"))
    return chile, world, used


def _select_live_feed(
    *,
    candidates: list[dict],
    now: datetime,
    gemini_api_key: str,
    gemini_model: str,
) -> tuple[list[dict], list[dict], str, str | None, str | None, int]:
    unique = dedupe_news(candidates)
    prefiltered = prefilter_candidates(
        unique,
        now=now,
        max_per_region=16,
    )

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

    translation_error: str | None = None
    if ai_active and world:
        world, translation_error = translate_selected_world_stories(
            world,
            api_key=gemini_api_key,
            model=gemini_model,
        )

    return (
        chile,
        world,
        "gemini" if ai_active else "local",
        ranking_error,
        translation_error,
        len(prefiltered),
    )


def fetch_daily_news(
    *,
    gemini_api_key: str = "",
    gemini_model: str = DEFAULT_GEMINI_MODEL,
) -> dict:
    started = time.monotonic()
    now = datetime.now(ZoneInfo("America/Santiago"))
    errors: list[str] = []
    candidates: list[dict] = []
    source_stats: dict[str, int] = {}
    source_health: dict[str, dict] = {}

    try:
        jobs = build_source_jobs(now)
        worker_count = max(1, min(8, len(jobs)))

        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            future_map = {
                executor.submit(_run_source, source_name, fetcher): source_name
                for source_name, fetcher in jobs
            }

            for future in as_completed(future_map):
                source_name = future_map[future]
                try:
                    _, items, duration = future.result()
                    source_stats[source_name] = len(items)
                    source_health[source_name] = {
                        "status": "ok" if items else "empty",
                        "count": len(items),
                        "duration_ms": int(duration * 1000),
                    }
                    candidates.extend(items)
                except Exception as exc:
                    source_stats[source_name] = 0
                    source_health[source_name] = {
                        "status": "failed",
                        "count": 0,
                        "duration_ms": None,
                        "error_type": type(exc).__name__,
                    }
                    errors.append(f"{source_name}: {type(exc).__name__}")

        (
            live_chile,
            live_world,
            ranking_mode,
            ranking_error,
            translation_error,
            candidate_count,
        ) = _select_live_feed(
            candidates=candidates,
            now=now,
            gemini_api_key=gemini_api_key,
            gemini_model=gemini_model,
        )
    except Exception as exc:
        live_chile = []
        live_world = []
        ranking_mode = "local"
        ranking_error = f"{type(exc).__name__}: {str(exc)[:120]}"
        translation_error = None
        candidate_count = 0
        errors.append(f"Pipeline: {type(exc).__name__}")

    live_items = live_chile + live_world
    feed_mode = "live"
    snapshot_used_count = 0
    snapshot_age_hours: float | None = None
    content_updated_at = now

    snapshot = load_news_snapshot(now=now, max_age_hours=96.0)
    if snapshot is None:
        snapshot = load_bootstrap_snapshot(now=now)

    needs_support = len(live_chile) < CHILE_TARGET or len(live_world) < WORLD_TARGET

    if needs_support and snapshot:
        chile, world, snapshot_used_count = _merge_with_snapshot(
            current_items=live_items,
            snapshot=snapshot,
        )
        snapshot_age_hours = round(float(snapshot.get("age_hours", 0.0)), 1)

        if live_items and snapshot_used_count:
            feed_mode = "mixed"
        elif snapshot_used_count:
            feed_mode = "bootstrap" if snapshot.get("_origin") == "bootstrap" else "snapshot"
            saved_at = snapshot.get("saved_at")
            if isinstance(saved_at, datetime):
                content_updated_at = saved_at
    else:
        chile, world = live_chile, live_world

    # Save only genuinely healthy, current feeds. A stale item must never reset
    # the snapshot age and masquerade as fresh content.
    if (
        len(live_chile) >= 3
        and len(live_world) >= 2
        and not any(item.get("from_snapshot") for item in live_items)
    ):
        save_news_snapshot(
            chile=live_chile,
            world=live_world,
            saved_at=now,
            ranking_mode=ranking_mode,
        )

    elapsed_seconds = round(time.monotonic() - started, 2)

    return {
        "chile": chile,
        "world": world,
        "fetched_at": now,
        "content_updated_at": content_updated_at,
        "errors": errors,
        "source_stats": source_stats,
        "source_health": source_health,
        "ranking_mode": ranking_mode,
        "ranking_error": ranking_error,
        "translation_error": translation_error,
        "candidate_count": candidate_count,
        "feed_mode": feed_mode,
        "snapshot_used_count": snapshot_used_count,
        "snapshot_age_hours": snapshot_age_hours,
        "elapsed_seconds": elapsed_seconds,
    }
