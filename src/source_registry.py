from __future__ import annotations

from datetime import datetime

from .sources.generic import ListingSource, fetch_listing_source
from .sources.rss_source import fetch_rss_source


CHILE_LISTING_SOURCES = (
    ListingSource(
        name="Codelco",
        region="Chile",
        listing_urls=("https://www.codelco.com/prensa",),
        include_pattern=r"/prensa/20\d{2}/",
        limit=2,
        candidate_limit=6,
        source_priority=92,
    ),
    ListingSource(
        name="Cochilco",
        region="Chile",
        listing_urls=("https://www.cochilco.cl/web/noticias/",),
        include_pattern=r"cochilco\.cl/web/[^/?#]+/?$",
        exclude_patterns=(
            r"/web/noticias",
            r"/web/descripcion-general",
            r"/web/la-rueda-diaria",
            r"/web/politica",
            r"/web/mapa",
            r"/web/contact",
        ),
        limit=2,
        candidate_limit=6,
        source_priority=88,
    ),
    ListingSource(
        name="Ministerio de Minería",
        region="Chile",
        listing_urls=(
            "https://www.minmineria.gob.cl/?cat-noticias=noticias",
            "https://www.minmineria.cl/?cat-noticias=noticias",
        ),
        include_pattern=r"\?noticia=",
        limit=2,
        candidate_limit=6,
        source_priority=86,
    ),
    ListingSource(
        name="Reporte Minero",
        region="Chile",
        listing_urls=("https://www.reporteminero.cl/noticias/noticias",),
        include_pattern=r"/noticia/(noticias|reportajes|columnistas)/20\d{2}/",
        limit=2,
        candidate_limit=7,
        source_priority=76,
        allow_external_image=False,
    ),
)

WORLD_LISTING_SOURCES = (
    ListingSource(
        name="MINING.com",
        region="Mundo",
        listing_urls=(
            "https://www.mining.com/",
            "https://www.mining.com/commodity/copper/",
        ),
        include_pattern=r"mining\.com/[a-z0-9][a-z0-9\-]+/?$",
        exclude_patterns=(
            r"/about",
            r"/contact",
            r"/advertise",
            r"/newsletter",
            r"/subscriptions",
            r"/jobs",
            r"/markets",
            r"/category/",
            r"/commodity/",
        ),
        limit=2,
        candidate_limit=8,
        source_priority=78,
    ),
    ListingSource(
        name="BHP",
        region="Mundo",
        listing_urls=("https://www.bhp.com/news/media-centre",),
        include_pattern=r"/news/media-centre/releases/20\d{2}/",
        limit=2,
        candidate_limit=6,
        source_priority=90,
        allow_external_image=False,
    ),
    ListingSource(
        name="Anglo American",
        region="Mundo",
        listing_urls=("https://www.angloamerican.com/media/press-releases/2026",),
        include_pattern=r"/media/press-releases/20\d{2}/",
        limit=2,
        candidate_limit=6,
        source_priority=89,
    ),
    ListingSource(
        name="Antofagasta plc",
        region="Mundo",
        listing_urls=("https://www.antofagasta.co.uk/investors/news/2026/",),
        include_pattern=r"/investors/news/20\d{2}/",
        exclude_patterns=(r"/email-alerts",),
        limit=2,
        candidate_limit=6,
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
        limit=2,
        source_priority=79,
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
        limit=2,
        source_priority=78,
    )


def build_source_jobs(now: datetime):
    jobs: list[tuple[str, callable]] = []

    for config in CHILE_LISTING_SOURCES + WORLD_LISTING_SOURCES:
        jobs.append(
            (
                config.name,
                lambda config=config: fetch_listing_source(config, now),
            )
        )

    jobs.append(("Minería Chilena", lambda: fetch_mch(now)))
    jobs.append(("MINING.com RSS", lambda: fetch_mining_rss(now)))

    return jobs
