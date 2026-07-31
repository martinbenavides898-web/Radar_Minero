from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
import re
from urllib.parse import urljoin, urlsplit

from .common import (
    canonical_url,
    classify_category,
    clean_text,
    extract_article_metadata,
    humanize_published,
    soup_from_url,
    truncate,
)


@dataclass(frozen=True)
class ListingSource:
    name: str
    region: str
    listing_urls: tuple[str, ...]
    include_pattern: str
    exclude_patterns: tuple[str, ...] = field(default_factory=tuple)
    limit: int = 2
    candidate_limit: int = 8
    source_priority: int = 50
    allow_external_image: bool = True


def _same_host(left: str, right: str) -> bool:
    left_host = (urlsplit(left).hostname or "").removeprefix("www.")
    right_host = (urlsplit(right).hostname or "").removeprefix("www.")
    return left_host == right_host


def _candidate_title(anchor) -> str:
    title = clean_text(anchor.get_text(" ", strip=True))
    if len(title) >= 24:
        return title

    parent = anchor.find_parent(["article", "li", "div"])
    if parent:
        heading = parent.find(["h1", "h2", "h3", "h4", "h5", "h6"])
        if heading:
            return clean_text(heading.get_text(" ", strip=True))

    return title


def fetch_listing_source(config: ListingSource, now: datetime) -> list[dict]:
    include = re.compile(config.include_pattern, re.IGNORECASE)
    excludes = [re.compile(pattern, re.IGNORECASE) for pattern in config.exclude_patterns]

    candidates: list[tuple[str, str]] = []
    seen: set[str] = set()

    for listing_url in config.listing_urls:
        try:
            soup, final_listing_url = soup_from_url(listing_url)
        except Exception:
            continue

        for anchor in soup.find_all("a", href=True):
            raw_href = str(anchor.get("href", "")).strip()
            if not raw_href or raw_href.startswith(("#", "mailto:", "tel:", "javascript:")):
                continue

            article_url = urljoin(final_listing_url, raw_href)
            canonical = canonical_url(article_url)
            title = _candidate_title(anchor)

            if canonical == canonical_url(final_listing_url):
                continue
            if not _same_host(article_url, final_listing_url):
                continue
            if not include.search(article_url):
                continue
            if any(pattern.search(article_url) for pattern in excludes):
                continue
            if len(title) < 24 or len(title) > 260:
                continue
            if canonical in seen:
                continue

            seen.add(canonical)
            candidates.append((article_url, title))

            if len(candidates) >= config.candidate_limit:
                break

        if len(candidates) >= config.candidate_limit:
            break

    news: list[dict] = []

    for article_url, listing_title in candidates:
        try:
            metadata = extract_article_metadata(article_url)
        except Exception:
            continue

        title = metadata.get("title") or listing_title
        summary = truncate(metadata.get("summary", ""))
        final_url = metadata.get("url") or article_url

        if not title or not final_url:
            continue

        news.append(
            {
                "region": config.region,
                "category": classify_category(title, summary),
                "title": title,
                "source": config.name,
                "published": humanize_published(metadata.get("published_at"), now),
                "published_at": metadata.get("published_at"),
                "summary": summary or f"Revisa la publicación original de {config.name}.",
                "image_url": metadata.get("image_url", "") if config.allow_external_image else "",
                "url": final_url,
                "source_priority": config.source_priority,
                "is_fallback": False,
            }
        )

        if len(news) >= config.limit:
            break

    return news
