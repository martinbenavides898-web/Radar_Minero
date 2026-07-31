from __future__ import annotations

from datetime import datetime
from html import escape
from typing import Iterable
import textwrap

import streamlit as st


SPANISH_WEEKDAYS = {
    0: "Lunes",
    1: "Martes",
    2: "Miércoles",
    3: "Jueves",
    4: "Viernes",
    5: "Sábado",
    6: "Domingo",
}

SPANISH_MONTHS = {
    1: "enero",
    2: "febrero",
    3: "marzo",
    4: "abril",
    5: "mayo",
    6: "junio",
    7: "julio",
    8: "agosto",
    9: "septiembre",
    10: "octubre",
    11: "noviembre",
    12: "diciembre",
}


def _render_html(html: str) -> None:
    """Render raw HTML without Markdown interpreting indented tags as code."""
    st.html(textwrap.dedent(html).strip())


def render_header(
    title: str,
    subtitle: str,
    updated_at: datetime,
    is_demo: bool = False,
) -> None:
    demo_badge = '<span class="demo-badge">MODO DISEÑO</span>' if is_demo else ""
    weekday = SPANISH_WEEKDAYS[updated_at.weekday()]
    month = SPANISH_MONTHS[updated_at.month]
    date_label = f"{weekday} {updated_at.day} de {month}"
    time_label = updated_at.strftime("%H:%M")

    _render_html(
        f"""
        <section class="app-header">
            <div class="brand-row">
                <div>
                    <p class="eyebrow">INTELIGENCIA MINERA DIARIA</p>
                    <h1>{escape(title)}</h1>
                </div>
                {demo_badge}
            </div>
            <p class="app-subtitle">{escape(subtitle)}</p>
            <div class="update-row">
                <span>{escape(date_label)}</span>
                <span class="update-dot"></span>
                <span>Actualizado {escape(time_label)}</span>
            </div>
        </section>
        """
    )


def render_market_ticker(items: Iterable[dict]) -> None:
    ticker_items = "".join(_ticker_item(item) for item in items)
    ticker_track = ticker_items + ticker_items

    _render_html(
        f"""
        <section class="market-shell" aria-label="Indicadores mineros">
            <div class="market-label">
                <span class="live-dot"></span>
                MERCADOS
            </div>
            <div class="ticker-window">
                <div class="ticker-track">
                    {ticker_track}
                </div>
            </div>
        </section>
        <p class="demo-market-note">Valores simulados en esta versión de diseño.</p>
        """
    )


def _ticker_item(item: dict) -> str:
    direction = item.get("direction", "flat")
    arrow = "▲" if direction == "up" else "▼" if direction == "down" else "•"

    return f"""
        <div class="ticker-item">
            <span class="ticker-name">{escape(str(item["label"]))}</span>
            <strong>{escape(str(item["value"]))}</strong>
            <span class="ticker-delta {escape(direction)}">
                {arrow} {escape(str(item["delta"]))}
            </span>
        </div>
    """


def render_news_section(title: str, items: list[dict]) -> None:
    _render_html(
        f"""
        <div class="section-heading">
            <h2>{escape(title)}</h2>
            <span>{len(items)} noticias</span>
        </div>
        """
    )

    for index, item in enumerate(items):
        render_news_card(item, eager=index == 0)


def render_news_card(item: dict, eager: bool = False) -> None:
    loading = "eager" if eager else "lazy"
    url = escape(str(item["url"]), quote=True)
    image_url = escape(str(item["image_url"]), quote=True)
    title = escape(str(item["title"]))
    title_attribute = escape(str(item["title"]), quote=True)
    category = escape(str(item["category"]))
    source = escape(str(item["source"]))
    published = escape(str(item["published"]))
    summary = escape(str(item["summary"]))

    # st.html avoids Markdown treating the multiline card markup as code.
    _render_html(
        f"""
        <a
            class="news-card-link"
            href="{url}"
            target="_blank"
            rel="noopener noreferrer"
            aria-label="Abrir noticia: {title_attribute}"
        ><article class="news-card"><div class="news-image-wrap"><img
            class="news-image"
            src="{image_url}"
            alt=""
            loading="{loading}"
        /><div class="image-shade"></div><span class="category-pill">{category}</span></div><div class="news-content"><h3>{title}</h3><div class="news-meta"><span class="source-name">{source}</span><span class="meta-dot"></span><span>{published}</span></div><p>{summary}</p><div class="read-row"><span>Leer noticia original</span><span class="external-arrow">↗</span></div></div></article></a>
        """
    )
