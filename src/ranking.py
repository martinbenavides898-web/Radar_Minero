from __future__ import annotations

from datetime import datetime, timezone
import re

from .deduplication import normalized_title


PERSONAL_PRIORITY_TERMS = {
    "subterránea": 16,
    "subterraneo": 16,
    "underground": 16,
    "block cave": 18,
    "caving": 13,
    "cobre": 12,
    "copper": 12,
    "planificación": 14,
    "mine plan": 14,
    "scheduling": 11,
    "geomec": 16,
    "rock mechanics": 16,
    "ground control": 15,
    "automatización": 13,
    "autonomous": 13,
    "inteligencia artificial": 12,
    "artificial intelligence": 12,
    "seguridad": 11,
    "safety": 11,
    "litio": 7,
    "lithium": 7,
    "proyecto": 7,
    "inversión": 8,
    "investment": 8,
    "producción": 7,
    "production": 7,
}

LOW_VALUE_TERMS = (
    "premio",
    "reconoce a",
    "celebra",
    "aniversario",
    "encuentro anual",
    "nombramiento",
    "designa a",
    "webinar",
    "inscripciones",
)


def freshness_score(item: dict, now: datetime) -> float:
    published = item.get("published_at")
    if published is None:
        return 28.0

    if published.tzinfo is None:
        published = published.replace(tzinfo=timezone.utc)

    age_hours = max(
        0.0,
        (
            now.astimezone(timezone.utc)
            - published.astimezone(timezone.utc)
        ).total_seconds()
        / 3600,
    )

    if age_hours <= 3:
        return 100.0
    if age_hours <= 12:
        return 95.0 - (age_hours - 3) * 1.4
    if age_hours <= 24:
        return 82.0 - (age_hours - 12) * 1.8
    if age_hours <= 72:
        return 60.0 - (age_hours - 24) * 0.75
    if age_hours <= 168:
        return 24.0 - (age_hours - 72) * 0.18
    return 4.0


def keyword_relevance(item: dict) -> float:
    text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
    score = 0.0

    for term, weight in PERSONAL_PRIORITY_TERMS.items():
        if term in text:
            score += weight

    score -= sum(9 for term in LOW_VALUE_TERMS if term in text)
    return max(0.0, min(100.0, score))


def deterministic_score(item: dict, now: datetime) -> float:
    authority = float(item.get("source_priority", 50))
    freshness = freshness_score(item, now)
    relevance = keyword_relevance(item)
    summary_bonus = 6.0 if len(str(item.get("summary", ""))) >= 110 else 0.0

    return (
        authority * 0.26
        + freshness * 0.34
        + relevance * 0.34
        + summary_bonus
    )


def prefilter_candidates(
    items: list[dict],
    *,
    now: datetime,
    max_per_region: int = 16,
) -> list[dict]:
    selected: list[dict] = []

    for region in ("Chile", "Mundo"):
        regional = [
            dict(item, deterministic_score=deterministic_score(item, now))
            for item in items
            if item.get("region") == region
        ]
        regional.sort(key=lambda item: item["deterministic_score"], reverse=True)
        selected.extend(regional[:max_per_region])

    return selected


def apply_editorial_scores(
    items: list[dict],
    *,
    now: datetime,
    ai_active: bool,
) -> list[dict]:
    scored: list[dict] = []

    for item in items:
        candidate = dict(item)
        authority = float(candidate.get("source_priority", 50))
        freshness = freshness_score(candidate, now)
        local_score = float(candidate.get("deterministic_score", deterministic_score(candidate, now)))

        if ai_active and candidate.get("ai_global_importance") is not None:
            global_importance = float(candidate["ai_global_importance"])
            reader_relevance = float(candidate["ai_reader_relevance"])
            substantive_value = float(candidate["ai_substantive_value"])

            final_score = (
                global_importance * 0.40
                + reader_relevance * 0.30
                + substantive_value * 0.15
                + freshness * 0.10
                + authority * 0.05
            )
            event_key = str(candidate.get("ai_event_key") or normalized_title(candidate.get("title", "")))
        else:
            final_score = local_score
            event_key = normalized_title(candidate.get("title", ""))

        candidate["final_score"] = round(final_score, 3)
        candidate["event_key"] = _normalize_event_key(event_key)
        scored.append(candidate)

    scored.sort(key=lambda item: item["final_score"], reverse=True)
    return scored


def _normalize_event_key(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9áéíóúüñ\s\-]", " ", value)
    return re.sub(r"[\s\-]+", "-", value).strip("-")[:140]


def dedupe_ai_events(items: list[dict]) -> list[dict]:
    kept: list[dict] = []
    seen_events: set[str] = set()

    for item in items:
        event_key = str(item.get("event_key", "")).strip()
        if event_key and event_key in seen_events:
            continue
        if event_key:
            seen_events.add(event_key)
        kept.append(item)

    return kept


def _select_region(
    items: list[dict],
    *,
    region: str,
    limit: int,
    excluded_urls: set[str] | None = None,
) -> list[dict]:
    excluded_urls = set(excluded_urls or set())
    regional = [item for item in items if item.get("region") == region]
    selected: list[dict] = []
    selected_urls: set[str] = set(excluded_urls)
    source_counts: dict[str, int] = {}

    # One source each first; a second item from the same source is only allowed
    # when needed to complete the section.
    for per_source_limit in (1, 2, 99):
        for item in regional:
            if len(selected) >= limit:
                break

            url = str(item.get("url", ""))
            source = str(item.get("source", "Fuente"))

            if not url or url in selected_urls:
                continue
            if source_counts.get(source, 0) >= per_source_limit:
                continue

            selected.append(item)
            selected_urls.add(url)
            source_counts[source] = source_counts.get(source, 0) + 1

        if len(selected) >= limit:
            break

    return selected[:limit]


def select_balanced_feed(items: list[dict], total_limit: int = 7) -> tuple[list[dict], list[dict]]:
    unique_events = dedupe_ai_events(items)
    chile = _select_region(unique_events, region="Chile", limit=4)
    used_urls = {str(item.get("url", "")) for item in chile}
    world = _select_region(unique_events, region="Mundo", limit=3, excluded_urls=used_urls)

    # Flexible quota: preserve seven useful stories when one region has fewer
    # candidates, without forcing weak filler into the feed.
    missing = total_limit - len(chile) - len(world)
    if missing > 0:
        used_urls.update(str(item.get("url", "")) for item in world)
        remaining = [
            item
            for item in unique_events
            if str(item.get("url", "")) not in used_urls
        ]
        for item in remaining[:missing]:
            if item.get("region") == "Chile":
                chile.append(item)
            else:
                world.append(item)

    chile.sort(key=lambda item: item.get("final_score", 0), reverse=True)
    world.sort(key=lambda item: item.get("final_score", 0), reverse=True)
    return chile, world
