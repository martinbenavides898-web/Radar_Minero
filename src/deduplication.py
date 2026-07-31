from __future__ import annotations

from difflib import SequenceMatcher
import re

from .sources.common import canonical_url, strip_accents


STOPWORDS = {
    "a", "al", "ante", "con", "de", "del", "el", "en", "la", "las", "los",
    "para", "por", "que", "se", "su", "sus", "un", "una", "y",
    "and", "for", "in", "of", "on", "the", "to", "with",
    "mineria", "mining", "chile", "noticia", "news",
}


def normalized_title(title: str) -> str:
    value = strip_accents(title.lower())
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    tokens = [
        token
        for token in value.split()
        if token not in STOPWORDS and len(token) > 2
    ]
    return " ".join(tokens)


def title_tokens(title: str) -> set[str]:
    return set(normalized_title(title).split())


def similarity(left: str, right: str) -> float:
    left_normalized = normalized_title(left)
    right_normalized = normalized_title(right)

    sequence = SequenceMatcher(None, left_normalized, right_normalized).ratio()

    left_tokens = title_tokens(left)
    right_tokens = title_tokens(right)
    union = left_tokens | right_tokens
    jaccard = len(left_tokens & right_tokens) / len(union) if union else 0.0

    smaller = min(len(left_tokens), len(right_tokens))
    containment = (
        len(left_tokens & right_tokens) / smaller
        if smaller
        else 0.0
    )

    return max(sequence, jaccard, containment * 0.92)


def dedupe_news(items: list[dict]) -> list[dict]:
    ordered = sorted(
        items,
        key=lambda item: (
            item.get("source_priority", 0),
            item.get("published_at").timestamp()
            if item.get("published_at")
            else 0,
        ),
        reverse=True,
    )

    kept: list[dict] = []
    seen_urls: set[str] = set()

    for item in ordered:
        url = canonical_url(str(item.get("url", "")))
        if not url or url in seen_urls:
            continue

        duplicate = any(
            similarity(str(item.get("title", "")), str(existing.get("title", ""))) >= 0.78
            for existing in kept
        )
        if duplicate:
            continue

        seen_urls.add(url)
        kept.append(item)

    return kept
