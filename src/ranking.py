from __future__ import annotations

from datetime import datetime, timezone


HIGH_PRIORITY_TERMS = (
    "subterránea",
    "underground",
    "cobre",
    "copper",
    "litio",
    "lithium",
    "automatización",
    "autonomous",
    "inteligencia artificial",
    "artificial intelligence",
    "planificación",
    "geomec",
    "seguridad",
    "safety",
    "proyecto",
    "inversión",
    "production",
    "producción",
)


def relevance_score(item: dict, now: datetime) -> float:
    score = float(item.get("source_priority", 50))
    text = f"{item.get('title', '')} {item.get('summary', '')}".lower()

    score += sum(7 for term in HIGH_PRIORITY_TERMS if term in text)

    published = item.get("published_at")
    if published:
        if published.tzinfo is None:
            published = published.replace(tzinfo=timezone.utc)
        age_hours = max(
            0,
            (
                now.astimezone(timezone.utc)
                - published.astimezone(timezone.utc)
            ).total_seconds() / 3600,
        )
        score += max(0, 38 - age_hours * 0.65)
    else:
        score += 5

    if item.get("is_fallback"):
        score -= 35

    return score


def select_diverse(
    items: list[dict],
    *,
    region: str,
    limit: int,
    now: datetime,
) -> list[dict]:
    candidates = [
        dict(item, relevance_score=relevance_score(item, now))
        for item in items
        if item.get("region") == region
    ]
    candidates.sort(key=lambda item: item["relevance_score"], reverse=True)

    selected: list[dict] = []
    selected_urls: set[str] = set()
    source_counts: dict[str, int] = {}

    for per_source_limit in (1, 2, 99):
        for item in candidates:
            if len(selected) >= limit:
                break

            url = str(item.get("url", ""))
            source = str(item.get("source", "Fuente"))

            if url in selected_urls:
                continue
            if source_counts.get(source, 0) >= per_source_limit:
                continue

            selected.append(item)
            selected_urls.add(url)
            source_counts[source] = source_counts.get(source, 0) + 1

        if len(selected) >= limit:
            break

    return selected[:limit]
