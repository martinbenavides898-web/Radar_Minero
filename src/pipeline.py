from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from data.fallback_news import FALLBACK_NEWS
from .sources.codelco import fetch_codelco_news
from .sources.mining_com import fetch_mining_com_news


def _sort_key(item: dict) -> float:
    published = item.get("published_at")
    return published.timestamp() if published else 0.0


def fetch_daily_news() -> dict:
    now = datetime.now(ZoneInfo("America/Santiago"))
    errors: list[str] = []
    news: list[dict] = []

    try:
        news.extend(fetch_codelco_news(now=now, limit=4))
    except Exception as exc:
        errors.append(f"Codelco: {type(exc).__name__}")

    try:
        news.extend(fetch_mining_com_news(now=now, limit=3))
    except Exception as exc:
        errors.append(f"MINING.com: {type(exc).__name__}")

    chile_count = sum(item.get("region") == "Chile" for item in news)
    if chile_count < 4:
        existing_urls = {item.get("url") for item in news}
        for fallback in FALLBACK_NEWS:
            if fallback["url"] not in existing_urls:
                news.append(dict(fallback))
            if sum(item.get("region") == "Chile" for item in news) >= 4:
                break

    news.sort(key=_sort_key, reverse=True)

    return {
        "news": news,
        "fetched_at": now,
        "errors": errors,
    }
