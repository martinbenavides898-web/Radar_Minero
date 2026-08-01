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
    """Keep strong candidates without letting one source monopolize Gemini's input."""
    selected: list[dict] = []

    for region in ("Chile", "Mundo"):
        regional = [
            dict(item, deterministic_score=deterministic_score(item, now))
            for item in items
            if item.get("region") == region
        ]
        regional.sort(key=lambda item: item["deterministic_score"], reverse=True)

        diversified: list[dict] = []
        source_counts: dict[str, int] = {}

        # First pass: one candidate per source.
        for item in regional:
            source = str(item.get("source", "Fuente"))
            if source_counts.get(source, 0) >= 1:
                continue
            diversified.append(item)
            source_counts[source] = 1
            if len(diversified) >= max_per_region:
                break

        # Second pass: at most four candidates from any one source.
        if len(diversified) < max_per_region:
            selected_urls = {str(item.get("url", "")) for item in diversified}
            for item in regional:
                if len(diversified) >= max_per_region:
                    break
                url = str(item.get("url", ""))
                source = str(item.get("source", "Fuente"))
                if url in selected_urls:
                    continue
                if source_counts.get(source, 0) >= 4:
                    continue
                diversified.append(item)
                selected_urls.add(url)
                source_counts[source] = source_counts.get(source, 0) + 1

        selected.extend(diversified[:max_per_region])

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
        local_score = float(
            candidate.get(
                "deterministic_score",
                deterministic_score(candidate, now),
            )
        )

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
            event_key = str(
                candidate.get("ai_event_key")
                or normalized_title(candidate.get("title", ""))
            )
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


def _take_with_source_cap(
    regional: list[dict],
    *,
    limit: int,
    source_cap: int,
    already_selected: list[dict] | None = None,
) -> list[dict]:
    selected = list(already_selected or [])
    selected_urls = {str(item.get("url", "")) for item in selected}
    source_counts: dict[str, int] = {}

    for item in selected:
        source = str(item.get("source", "Fuente"))
        source_counts[source] = source_counts.get(source, 0) + 1

    for item in regional:
        if len(selected) >= limit:
            break

        url = str(item.get("url", ""))
        source = str(item.get("source", "Fuente"))

        if not url or url in selected_urls:
            continue
        if source_counts.get(source, 0) >= source_cap:
            continue

        selected.append(item)
        selected_urls.add(url)
        source_counts[source] = source_counts.get(source, 0) + 1

    return selected[:limit]


def _select_region(
    items: list[dict],
    *,
    region: str,
    limit: int,
) -> list[dict]:
    regional = [item for item in items if item.get("region") == region]
    if not regional:
        return []

    sources = {
        str(item.get("source", "Fuente"))
        for item in regional
        if str(item.get("source", "")).strip()
    }
    source_count = len(sources)

    # First pass always gives each responding source a fair chance.
    selected = _take_with_source_cap(
        regional,
        limit=limit,
        source_cap=1,
    )

    if region == "Mundo":
        # Critical UX rule:
        # - One available international source => show only its best story.
        # - Two sources => a third card may repeat one source, never all three.
        # - Three or more sources => three different sources.
        if source_count <= 1:
            return selected[:1]
        if source_count == 2 and len(selected) < limit:
            return _take_with_source_cap(
                regional,
                limit=limit,
                source_cap=2,
                already_selected=selected,
            )
        return selected[:limit]

    # Chile may use a second story from a source only when fewer than four
    # distinct publishers are available. Never exceed two stories per source.
    if len(selected) < limit:
        selected = _take_with_source_cap(
            regional,
            limit=limit,
            source_cap=2,
            already_selected=selected,
        )

    return selected[:limit]


def select_balanced_feed(
    items: list[dict],
    total_limit: int = 7,
) -> tuple[list[dict], list[dict]]:
    del total_limit  # Kept in the public signature for backwards compatibility.

    unique_events = dedupe_ai_events(items)
    chile = _select_region(unique_events, region="Chile", limit=4)
    world = _select_region(unique_events, region="Mundo", limit=3)

    # Do not fill a missing international slot with a third item from the only
    # responding company. Fewer honest cards are better than fake diversity.
    chile.sort(key=lambda item: item.get("final_score", 0), reverse=True)
    world.sort(key=lambda item: item.get("final_score", 0), reverse=True)
    return chile, world
