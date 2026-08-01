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
    get_html,
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
    sitemap_urls: tuple[str, ...] = field(default_factory=tuple)


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


def _default_sitemap_urls(listing_url: str) -> tuple[str, ...]:
    parts = urlsplit(listing_url)
    root = f"{parts.scheme}://{parts.netloc}"
    return (
        f"{root}/sitemap.xml",
        f"{root}/sitemap_index.xml",
        f"{root}/sitemap-index.xml",
    )


def _xml_locations(xml_text: str) -> list[str]:
    # Namespace-independent extraction works for both sitemap indexes and urlsets.
    return [
        clean_text(value)
        for value in re.findall(
            r"<loc>\s*(.*?)\s*</loc>",
            xml_text,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if clean_text(value)
    ]


def _collect_sitemap_candidates(
    config: ListingSource,
    *,
    include: re.Pattern,
    excludes: list[re.Pattern],
) -> list[tuple[str, str]]:
    sitemap_urls = list(config.sitemap_urls)

    if not sitemap_urls:
        for listing_url in config.listing_urls:
            sitemap_urls.extend(_default_sitemap_urls(listing_url))

    queue: list[tuple[str, int]] = [(url, 0) for url in dict.fromkeys(sitemap_urls)]
    visited: set[str] = set()
    candidates: list[tuple[str, str]] = []
    seen_articles: set[str] = set()

    while queue and len(visited) < 12 and len(candidates) < config.candidate_limit:
        sitemap_url, depth = queue.pop(0)
        canonical_map = canonical_url(sitemap_url)
        if canonical_map in visited:
            continue
        visited.add(canonical_map)

        try:
            xml_text, final_url = get_html(sitemap_url, timeout=10)
        except Exception:
            continue

        locations = _xml_locations(xml_text)
        if not locations:
            continue

        child_sitemaps = [
            location
            for location in locations
            if location.lower().split("?", 1)[0].endswith(".xml")
        ]

        if child_sitemaps and depth < 1:
            preferred = sorted(
                child_sitemaps,
                key=lambda value: (
                    0 if re.search(r"(news|press|release|article|post|2026)", value, re.I) else 1,
                    value,
                ),
            )
            queue.extend((url, depth + 1) for url in preferred[:7])
            continue

        for article_url in locations:
            if not _same_host(article_url, final_url):
                continue
            if not include.search(article_url):
                continue
            if any(pattern.search(article_url) for pattern in excludes):
                continue

            canonical = canonical_url(article_url)
            if canonical in seen_articles:
                continue

            seen_articles.add(canonical)
            candidates.append((article_url, ""))

            if len(candidates) >= config.candidate_limit:
                break

    return candidates


def fetch_listing_source(config: ListingSource, now: datetime) -> list[dict]:
    include = re.compile(config.include_pattern, re.IGNORECASE)
    excludes = [
        re.compile(pattern, re.IGNORECASE)
        for pattern in config.exclude_patterns
    ]

    candidates: list[tuple[str, str]] = []
    seen: set[str] = set()

    for listing_url in config.listing_urls:
        try:
            soup, final_listing_url = soup_from_url(listing_url)
        except Exception:
            continue

        for anchor in soup.find_all("a", href=True):
            raw_href = str(anchor.get("href", "")).strip()
            if not raw_href or raw_href.startswith(
                ("#", "mailto:", "tel:", "javascript:")
            ):
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

    # JS-heavy corporate newsrooms often expose no article links in the initial
    # HTML. Their public sitemaps provide a stable, official fallback.
    if len(candidates) < min(3, config.candidate_limit):
        for article_url, title in _collect_sitemap_candidates(
            config,
            include=include,
            excludes=excludes,
        ):
            canonical = canonical_url(article_url)
            if canonical in seen:
                continue
            seen.add(canonical)
            candidates.append((article_url, title))
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

        if not title or len(title) < 12 or not final_url:
            continue

        news.append(
            {
                "region": config.region,
                "category": classify_category(title, summary),
                "title": title,
                "source": config.name,
                "published": humanize_published(
                    metadata.get("published_at"),
                    now,
                ),
                "published_at": metadata.get("published_at"),
                "summary": summary or f"Revisa la publicación original de {config.name}.",
                "image_url": (
                    metadata.get("image_url", "")
                    if config.allow_external_image
                    else ""
                ),
                "url": final_url,
                "source_priority": config.source_priority,
                "is_fallback": False,
            }
        )

        if len(news) >= config.limit:
            break

    return news
