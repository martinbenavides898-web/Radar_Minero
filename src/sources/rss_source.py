from __future__ import annotations

import calendar
from datetime import datetime, timezone

from bs4 import BeautifulSoup
import feedparser
import requests

from .common import (
    DEFAULT_HEADERS,
    classify_category,
    clean_text,
    extract_article_metadata,
    humanize_published,
    truncate,
)


def _entry_datetime(entry) -> datetime | None:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed:
        return None
    return datetime.fromtimestamp(calendar.timegm(parsed), tz=timezone.utc)


def _entry_image(entry) -> str:
    for collection_name in ("media_content", "media_thumbnail"):
        for item in entry.get(collection_name) or []:
            if item.get("url"):
                return str(item["url"])

    for enclosure in entry.get("enclosures") or []:
        href = enclosure.get("href") or enclosure.get("url")
        mime = str(enclosure.get("type", ""))
        if href and (not mime or mime.startswith("image/")):
            return str(href)

    summary_html = entry.get("summary", "") or entry.get("description", "")
    soup = BeautifulSoup(summary_html, "html.parser")
    image = soup.find("img")
    if image:
        return str(image.get("src") or image.get("data-src") or "")

    return ""


def fetch_rss_source(
    *,
    name: str,
    region: str,
    feed_urls: tuple[str, ...],
    now: datetime,
    limit: int = 2,
    source_priority: int = 50,
) -> list[dict]:
    feed = None
    last_error: Exception | None = None

    for feed_url in feed_urls:
        try:
            response = requests.get(feed_url, headers=DEFAULT_HEADERS, timeout=14)
            response.raise_for_status()
            candidate = feedparser.parse(response.content)
            if candidate.entries:
                feed = candidate
                break
        except Exception as exc:
            last_error = exc

    if feed is None:
        if last_error:
            raise last_error
        raise RuntimeError(f"{name} no devolvió publicaciones.")

    news: list[dict] = []

    for entry in feed.entries[: max(limit * 4, limit)]:
        title = clean_text(entry.get("title", ""))
        url = str(entry.get("link", "")).strip()
        summary = truncate(entry.get("summary", "") or entry.get("description", ""))
        image_url = _entry_image(entry)
        published_at = _entry_datetime(entry)

        if not title or not url:
            continue

        if not image_url or not summary:
            try:
                metadata = extract_article_metadata(url)
                url = metadata.get("url") or url
                image_url = image_url or metadata.get("image_url", "")
                summary = summary or metadata.get("summary", "")
                published_at = published_at or metadata.get("published_at")
            except Exception:
                pass

        news.append(
            {
                "region": region,
                "category": classify_category(title, summary),
                "title": title,
                "source": name,
                "published": humanize_published(published_at, now),
                "published_at": published_at,
                "summary": summary or f"Revisa la publicación original de {name}.",
                "image_url": image_url,
                "url": url,
                "source_priority": source_priority,
                "is_fallback": False,
            }
        )

        if len(news) >= limit:
            break

    return news
