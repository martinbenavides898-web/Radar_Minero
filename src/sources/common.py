from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup
import requests


USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) "
    "AppleWebKit/605.1.15 Version/18.0 Mobile/15E148 Safari/604.1 "
    "RadarMinero/0.2"
)

DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-CL,es;q=0.9,en;q=0.7",
}

KEYWORD_CATEGORIES = [
    ("MINERÍA SUBTERRÁNEA", ("subterránea", "subterraneo", "underground", "block cave")),
    ("GEOMECÁNICA", ("geomec", "roca", "sísmic", "sismic", "rockburst", "ground control")),
    ("AUTOMATIZACIÓN", ("autónom", "automatiza", "robot", "remote operation")),
    ("IA APLICADA", ("inteligencia artificial", "artificial intelligence", " machine learning", " ia ")),
    ("SEGURIDAD", ("seguridad", "accidente", "fatal", "safety")),
    ("LITIO", ("litio", "lithium")),
    ("COBRE", ("cobre", "copper")),
    ("PROYECTOS", ("proyecto", "inversión", "investment", "expansion", "expansión")),
]


def get_html(url: str, timeout: int = 15) -> tuple[str, str]:
    response = requests.get(
        url,
        headers=DEFAULT_HEADERS,
        timeout=timeout,
        allow_redirects=True,
    )
    response.raise_for_status()
    return response.text, response.url


def soup_from_url(url: str, timeout: int = 15) -> tuple[BeautifulSoup, str]:
    html, final_url = get_html(url, timeout=timeout)
    return BeautifulSoup(html, "html.parser"), final_url


def meta_content(soup: BeautifulSoup, *, property_name: str | None = None, name: str | None = None) -> str:
    tag = None
    if property_name:
        tag = soup.find("meta", attrs={"property": property_name})
    elif name:
        tag = soup.find("meta", attrs={"name": name})

    if tag and tag.get("content"):
        return str(tag["content"]).strip()
    return ""


def absolute_url(base_url: str, candidate: str) -> str:
    candidate = (candidate or "").strip()
    return urljoin(base_url, candidate) if candidate else ""


def clean_text(value: str) -> str:
    text = BeautifulSoup(value or "", "html.parser").get_text(" ", strip=True)
    return re.sub(r"\s+", " ", text).strip()


def truncate(text: str, limit: int = 430) -> str:
    text = clean_text(text)
    if len(text) <= limit:
        return text
    shortened = text[:limit].rsplit(" ", 1)[0].rstrip(" ,;:-")
    return shortened + "…"


def classify_category(title: str, summary: str = "") -> str:
    haystack = f" {title} {summary} ".lower()
    for category, keywords in KEYWORD_CATEGORIES:
        if any(keyword in haystack for keyword in keywords):
            return category
    return "INDUSTRIA MINERA"


def first_article_image(soup: BeautifulSoup, base_url: str) -> str:
    for property_name in ("og:image", "twitter:image", "twitter:image:src"):
        image = meta_content(soup, property_name=property_name)
        if image:
            return absolute_url(base_url, image)

    for selector in ("article img", "main img", ".noticia img", ".article img"):
        image_tag = soup.select_one(selector)
        if image_tag:
            image = image_tag.get("src") or image_tag.get("data-src") or image_tag.get("data-lazy-src")
            if image:
                return absolute_url(base_url, str(image))

    return ""


def parse_iso_datetime(value: str) -> datetime | None:
    if not value:
        return None

    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def humanize_published(value: datetime | None, now: datetime) -> str:
    if value is None:
        return "Publicación reciente"

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    delta_seconds = max(0, int((now.astimezone(timezone.utc) - value.astimezone(timezone.utc)).total_seconds()))
    minutes = delta_seconds // 60

    if minutes < 2:
        return "Ahora"
    if minutes < 60:
        return f"Hace {minutes} min"

    hours = minutes // 60
    if hours < 24:
        return f"Hace {hours} h"

    days = hours // 24
    if days == 1:
        return "Ayer"
    if days < 7:
        return f"Hace {days} días"

    return value.astimezone(now.tzinfo).strftime("%d/%m/%Y")


def extract_article_metadata(url: str) -> dict[str, Any]:
    soup, final_url = soup_from_url(url)

    title = (
        meta_content(soup, property_name="og:title")
        or meta_content(soup, name="twitter:title")
        or clean_text(soup.h1.get_text(" ", strip=True) if soup.h1 else "")
    )

    description = (
        meta_content(soup, property_name="og:description")
        or meta_content(soup, name="description")
        or meta_content(soup, name="twitter:description")
    )

    if not description:
        paragraphs = [
            clean_text(paragraph.get_text(" ", strip=True))
            for paragraph in soup.select("article p, main p")
        ]
        description = next((paragraph for paragraph in paragraphs if len(paragraph) > 80), "")

    published_raw = (
        meta_content(soup, property_name="article:published_time")
        or meta_content(soup, name="date")
        or meta_content(soup, name="pubdate")
    )

    return {
        "url": final_url,
        "title": clean_text(title),
        "summary": truncate(description),
        "image_url": first_article_image(soup, final_url),
        "published_at": parse_iso_datetime(published_raw),
    }
