from __future__ import annotations

from datetime import datetime
from typing import Callable

from .sources.generic import ListingSource, fetch_listing_source
from .sources.rss_source import fetch_rss_source


# Cochilco was intentionally removed: the source currently interrupts the reading
# flow with registration/access friction. The feed prioritizes direct, public URLs.
CHILE_LISTING_SOURCES = (
    ListingSource(
        name="Codelco",
        region="Chile",
        listing_urls=("https://www.codelco.com/prensa",),
        include_pattern=r"/prensa/20\d{2}/",
        limit=4,
        candidate_limit=10,
        source_priority=92,
    ),
    ListingSource(
        name="Ministerio de Minería",
        region="Chile",
        listing_urls=(
            "https://www.minmineria.gob.cl/?cat-noticias=noticias",
            "https://www.minmineria.cl/?cat-noticias=noticias",
        ),
        include_pattern=r"\?noticia=",
        limit=4,
        candidate_limit=10,
        source_priority=86,
    ),
    ListingSource(
        name="Reporte Minero",
        region="Chile",
        listing_urls=("https://www.reporteminero.cl/noticias/noticias",),
        include_pattern=r"/noticia/(noticias|reportajes|columnistas)/20\d{2}/",
        limit=4,
        candidate_limit=10,
        source_priority=78,
        allow_external_image=False,
    ),
    ListingSource(
        name="SONAMI",
        region="Chile",
        listing_urls=(
            "https://www.sonami.cl/v2/sala-de-prensa/",
            "https://www.sonami.cl/v2/noticias-prensa/",
        ),
        include_pattern=r"/v2/noticias/",
        limit=4,
        candidate_limit=10,
        source_priority=80,
    ),
)

WORLD_LISTING_SOURCES = (
    ListingSource(
        name="BHP",
        region="Mundo",
        listing_urls=("https://www.bhp.com/news/media-centre",),
        include_pattern=r"/news/media-centre/releases/20\d{2}/",
        limit=4,
        candidate_limit=10,
        source_priority=90,
        allow_external_image=False,
    ),
    ListingSource(
        name="Anglo American",
        region="Mundo",
        listing_urls=("https://www.angloamerican.com/media/press-releases/2026",),
        include_pattern=r"/media/press-releases/20\d{2}/",
        limit=4,
        candidate_limit=10,
        source_priority=89,
    ),
    ListingSource(
        name="Antofagasta plc",
        region="Mundo",
        listing_urls=("https://www.antofagasta.co.uk/investors/news/2026/",),
        include_pattern=r"/investors/news/20\d{2}/",
        exclude_patterns=(r"/email-alerts",),
        limit=4,
        candidate_limit=10,
        source_priority=88,
    ),
    ListingSource(
        name="Rio Tinto",
        region="Mundo",
        listing_urls=("https://www.riotinto.com/en/news/releases",),
        include_pattern=r"/news/releases/20\d{2}/",
        limit=4,
        candidate_limit=10,
        source_priority=89,
    ),
    ListingSource(
        name="Glencore",
        region="Mundo",
        listing_urls=("https://www.glencore.com/media-and-insights/news",),
        include_pattern=r"/media-and-insights/news/[a-z0-9][a-z0-9\-]+/?$",
        exclude_patterns=(r"/media-and-insights/news/?$",),
        limit=4,
        candidate_limit=10,
        source_priority=87,
    ),
)


def fetch_mch(now: datetime) -> list[dict]:
    return fetch_rss_source(
        name="Minería Chilena",
        region="Chile",
        feed_urls=(
            "https://www.mch.cl/feed/rss",
            "https://www.mch.cl/feed/",
        ),
        now=now,
        limit=5,
        source_priority=80,
    )


def fetch_mining_rss(now: datetime) -> list[dict]:
    return fetch_rss_source(
        name="MINING.com",
        region="Mundo",
        feed_urls=(
            "https://www.mining.com/feed/",
            "https://www.mining.com/commodity/copper/feed/",
        ),
        now=now,
        limit=6,
        source_priority=82,
    )


def build_source_jobs(now: datetime) -> list[tuple[str, Callable[[], list[dict]]]]:
    jobs: list[tuple[str, Callable[[], list[dict]]]] = []

    for config in CHILE_LISTING_SOURCES + WORLD_LISTING_SOURCES:
        jobs.append(
            (
                config.name,
                lambda config=config: fetch_listing_source(config, now),
            )
        )

    jobs.append(("Minería Chilena", lambda: fetch_mch(now)))
    jobs.append(("MINING.com", lambda: fetch_mining_rss(now)))

    return jobs
