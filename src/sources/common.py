from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import json
import re
import unicodedata
from typing import Any
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup
import requests


USER_AGENT = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) "
    "AppleWebKit/605.1.15 Version/18.0 Mobile/15E148 Safari/604.1 "
    "RadarMinero/0.3"
)

DEFAULT_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-CL,es;q=0.9,en;q=0.7",
    "Cache-Control": "no-cache",
}

KEEP_QUERY_PARAMS = {"noticia"}

KEYWORD_CATEGORIES = [
    ("MINERÍA SUBTERRÁNEA", ("subterránea", "subterraneo", "underground", "block cave", "caving")),
    ("GEOMECÁNICA", ("geomec", "macizo rocoso", "sísmic", "sismic", "rockburst", "ground control")),
    ("AUTOMATIZACIÓN", ("autónom", "automatiza", "robot", "remote operation", "digitalización")),
    ("IA APLICADA", ("inteligencia artificial", "artificial intelligence", "machine learning", " ia ")),
    ("SEGURIDAD", ("seguridad", "accidente", "fatal", "safety", "riesgo operacional")),
    ("PLANIFICACIÓN", ("plan minero", "planificación", "mine plan", "scheduling")),
    ("LITIO", ("litio", "lithium")),
    ("COBRE", ("cobre", "copper")),
    ("PROYECTOS", ("proyecto", "inversión", "investment", "expansion", "expansión")),
]


def get_html(url: str, timeout: int = 14) -> tuple[str, str]:
    response = requests.get(
        url,
        headers=DEFAULT_HEADERS,
        timeout=timeout,
        allow_redirects=True,
    )
    response.raise_for_status()
    return response.text, response.url


def soup_from_url(url: str, timeout: int = 14) -> tuple[BeautifulSoup, str]:
    html, final_url = get_html(url, timeout=timeout)
    return BeautifulSoup(html, "html.parser"), final_url


def clean_text(value: str) -> str:
    text = BeautifulSoup(value or "", "html.parser").get_text(" ", strip=True)
    return re.sub(r"\s+", " ", text).strip()


def truncate(text: str, limit: int = 430) -> str:
    text = clean_text(text)
    if len(text) <= limit:
        return text
    shortened = text[:limit].rsplit(" ", 1)[0].rstrip(" ,;:-")
    return shortened + "…"


def strip_accents(value: str) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(char)
    )


def canonical_url(url: str) -> str:
    parts = urlsplit((url or "").strip())
    scheme = parts.scheme.lower() or "https"
    hostname = (parts.hostname or "").lower()
    if hostname.startswith("www."):
        hostname = hostname[4:]

    netloc = hostname
    if parts.port:
        netloc += f":{parts.port}"

    path = re.sub(r"/+", "/", parts.path or "/")
    if path != "/":
        path = path.rstrip("/")

    kept_query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=False)
        if key.lower() in KEEP_QUERY_PARAMS
    ]

    return urlunsplit((scheme, netloc, path, urlencode(kept_query), ""))


def absolute_url(base_url: str, candidate: str) -> str:
    candidate = (candidate or "").strip()
    return urljoin(base_url, candidate) if candidate else ""


def meta_content(
    soup: BeautifulSoup,
    *,
    property_name: str | None = None,
    name: str | None = None,
) -> str:
    tag = None
    if property_name:
        tag = soup.find("meta", attrs={"property": property_name})
    elif name:
        tag = soup.find("meta", attrs={"name": name})

    if tag and tag.get("content"):
        return str(tag["content"]).strip()
    return ""


def _json_ld_values(value: Any) -> list[dict]:
    found: list[dict] = []

    if isinstance(value, dict):
        found.append(value)
        for child in value.values():
            found.extend(_json_ld_values(child))
    elif isinstance(value, list):
        for child in value:
            found.extend(_json_ld_values(child))

    return found


def json_ld_objects(soup: BeautifulSoup) -> list[dict]:
    objects: list[dict] = []

    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        raw = script.string or script.get_text()
        if not raw:
            continue
        try:
            parsed = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            continue
        objects.extend(_json_ld_values(parsed))

    return objects


def parse_datetime(value: str) -> datetime | None:
    if not value:
        return None

    normalized = clean_text(value).replace("Z", "+00:00")

    try:
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except ValueError:
        pass

    try:
        parsed = parsedate_to_datetime(normalized)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed
    except (TypeError, ValueError, OverflowError):
        pass

    month_map = {
        "enero": "January",
        "febrero": "February",
        "marzo": "March",
        "abril": "April",
        "mayo": "May",
        "junio": "June",
        "julio": "July",
        "agosto": "August",
        "septiembre": "September",
        "octubre": "October",
        "noviembre": "November",
        "diciembre": "December",
    }

    lowered = normalized.lower()
    for spanish, english in month_map.items():
        lowered = lowered.replace(spanish, english)

    for format_string in (
        "%d %B %Y",
        "%d de %B de %Y",
        "%B %d, %Y",
        "%d/%m/%Y",
        "%Y-%m-%d",
    ):
        try:
            parsed = datetime.strptime(lowered, format_string)
            return parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    return None


def extract_published_at(soup: BeautifulSoup) -> datetime | None:
    candidates = [
        meta_content(soup, property_name="article:published_time"),
        meta_content(soup, name="date"),
        meta_content(soup, name="pubdate"),
        meta_content(soup, name="publish-date"),
        meta_content(soup, name="parsely-pub-date"),
    ]

    time_tag = soup.find("time")
    if time_tag:
        candidates.append(str(time_tag.get("datetime") or time_tag.get_text(" ", strip=True)))

    for item in json_ld_objects(soup):
        for key in ("datePublished", "dateCreated", "uploadDate"):
            if item.get(key):
                candidates.append(str(item[key]))

    for candidate in candidates:
        parsed = parse_datetime(candidate)
        if parsed:
            return parsed

    return None


def first_article_image(soup: BeautifulSoup, base_url: str) -> str:
    candidates = [
        meta_content(soup, property_name="og:image"),
        meta_content(soup, name="twitter:image"),
        meta_content(soup, name="twitter:image:src"),
    ]

    for item in json_ld_objects(soup):
        image = item.get("image")
        if isinstance(image, str):
            candidates.append(image)
        elif isinstance(image, dict) and image.get("url"):
            candidates.append(str(image["url"]))
        elif isinstance(image, list) and image:
            first = image[0]
            if isinstance(first, str):
                candidates.append(first)
            elif isinstance(first, dict) and first.get("url"):
                candidates.append(str(first["url"]))

    for candidate in candidates:
        if candidate:
            return absolute_url(base_url, candidate)

    for selector in ("article img", "main img", ".noticia img", ".article img", ".post img"):
        image_tag = soup.select_one(selector)
        if not image_tag:
            continue
        image = (
            image_tag.get("src")
            or image_tag.get("data-src")
            or image_tag.get("data-lazy-src")
        )
        if image:
            return absolute_url(base_url, str(image))

    return ""


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
            for paragraph in soup.select("article p, main p, .entry-content p, .post-content p")
        ]
        description = next(
            (
                paragraph
                for paragraph in paragraphs
                if 85 <= len(paragraph) <= 900
                and "cookies" not in paragraph.lower()
                and "suscr" not in paragraph.lower()
            ),
            "",
        )

    return {
        "url": final_url,
        "title": clean_text(title),
        "summary": truncate(description),
        "image_url": first_article_image(soup, final_url),
        "published_at": extract_published_at(soup),
    }


def classify_category(title: str, summary: str = "") -> str:
    haystack = f" {title} {summary} ".lower()
    for category, keywords in KEYWORD_CATEGORIES:
        if any(keyword in haystack for keyword in keywords):
            return category
    return "INDUSTRIA MINERA"


def humanize_published(value: datetime | None, now: datetime) -> str:
    if value is None:
        return "Publicación reciente"

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    seconds = max(
        0,
        int(
            (
                now.astimezone(timezone.utc)
                - value.astimezone(timezone.utc)
            ).total_seconds()
        ),
    )
    minutes = seconds // 60

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
