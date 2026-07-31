from __future__ import annotations

from datetime import datetime, timezone
import calendar

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


FEED_URLS = (
    "https://www.mining.com/feed/",
    "https://www.mining.com/commodity/copper/feed/",
)


def _entry_datetime(entry) -> datetime | None:
    parsed = entry.get("published_parsed") or entry.get("updated_parsed")
    if not parsed:
        return None
    return datetime.fromtimestamp(calendar.timegm(parsed), tz=timezone.utc)


def _entry_image(entry) -> str:
    for collection_name in ("media_content", "media_thumbnail"):
        collection = entry.get(collection_name) or []
        for item in collection:
            if item.get("url"):
                return str(item["url"])

    for enclosure in entry.get("enclosures", []) or []:
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


def _download_feed() -> feedparser.FeedParserDict:
    last_error: Exception | None = None

    for url in FEED_URLS:
        try:
            response = requests.get(url, headers=DEFAULT_HEADERS, timeout=15)
            response.raise_for_status()
            parsed = feedparser.parse(response.content)
            if parsed.entries:
                return parsed
        except Exception as exc:
            last_error = exc

    if last_error:
        raise last_error
    raise RuntimeError("MINING.com no devolvió publicaciones RSS.")


def fetch_mining_com_news(now: datetime, limit: int = 3) -> list[dict]:
    feed = _download_feed()
    news: list[dict] = []

    for entry in feed.entries[: max(limit * 3, limit)]:
        title = clean_text(entry.get("title", ""))
        url = str(entry.get("link", "")).strip()
        summary = truncate(entry.get("summary", "") or entry.get("description", ""))
        image_url = _entry_image(entry)
        published_at = _entry_datetime(entry)

        if not title or not url:
            continue

        # RSS entries sometimes omit the featured image. Fetch only what is missing.
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
                "region": "Mundo",
                "category": classify_category(title, summary),
                "title": title,
                "source": "MINING.com",
                "published": humanize_published(published_at, now),
                "published_at": published_at,
                "summary": summary or "Abre la publicación original para revisar el contenido completo.",
                "image_url": image_url,
                "url": url,
            }
        )

        if len(news) >= limit:
            break

    return news
