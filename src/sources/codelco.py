from __future__ import annotations

from datetime import datetime
import re
from urllib.parse import urljoin

from .common import (
    classify_category,
    extract_article_metadata,
    soup_from_url,
    truncate,
    humanize_published,
)


LIST_URL = "https://www.codelco.com/noticias"
ARTICLE_PATTERN = re.compile(r"/prensa/\d{4}/", re.IGNORECASE)


def fetch_codelco_news(now: datetime, limit: int = 4) -> list[dict]:
    soup, final_url = soup_from_url(LIST_URL)

    candidates: list[tuple[str, str]] = []
    seen: set[str] = set()

    for anchor in soup.find_all("a", href=True):
        href = str(anchor.get("href", "")).strip()
        title = " ".join(anchor.get_text(" ", strip=True).split())
        article_url = urljoin(final_url, href)

        if not ARTICLE_PATTERN.search(article_url):
            continue
        if len(title) < 28:
            continue
        if article_url in seen:
            continue

        seen.add(article_url)
        candidates.append((article_url, title))

    news: list[dict] = []

    for article_url, listing_title in candidates[: max(limit * 2, limit)]:
        try:
            metadata = extract_article_metadata(article_url)
        except Exception:
            continue

        title = metadata.get("title") or listing_title
        summary = truncate(metadata.get("summary", ""))

        if not title or not metadata.get("url"):
            continue

        news.append(
            {
                "region": "Chile",
                "category": classify_category(title, summary),
                "title": title,
                "source": "Codelco",
                "published": humanize_published(metadata.get("published_at"), now),
                "published_at": metadata.get("published_at"),
                "summary": summary or "Revisa el comunicado completo publicado por Codelco.",
                "image_url": metadata.get("image_url", ""),
                "url": metadata["url"],
            }
        )

        if len(news) >= limit:
            break

    return news
