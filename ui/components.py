from __future__ import annotations

from datetime import datetime
from html import escape
from typing import Iterable

import streamlit as st


def render_header(
    title: str,
    subtitle: str,
    updated_at: datetime,
    is_demo: bool = False,
) -> None:
    demo_badge = '<span class="demo-badge">MODO DISEÑO</span>' if is_demo else ""
    date_label = updated_at.strftime("%A %d de %B").capitalize()
    time_label = updated_at.strftime("%H:%M")

    st.markdown(
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
        """,
        unsafe_allow_html=True,
    )


def render_market_ticker(items: Iterable[dict]) -> None:
    ticker_items = "".join(_ticker_item(item) for item in items)
    # Se duplica el contenido para lograr un desplazamiento continuo sin saltos.
    ticker_track = ticker_items + ticker_items

    st.markdown(
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
        """,
        unsafe_allow_html=True,
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
    st.markdown(
        f"""
        <div class="section-heading">
            <h2>{escape(title)}</h2>
            <span>{len(items)} noticias</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for index, item in enumerate(items):
        render_news_card(item, eager=index == 0)


def render_news_card(item: dict, eager: bool = False) -> None:
    loading = "eager" if eager else "lazy"
    url = escape(str(item["url"]), quote=True)
    image_url = escape(str(item["image_url"]), quote=True)

    st.markdown(
        f"""
        <a
            class="news-card-link"
            href="{url}"
            target="_blank"
            rel="noopener noreferrer"
            aria-label="Abrir noticia: {escape(str(item["title"]), quote=True)}"
        >
            <article class="news-card">
                <div class="news-image-wrap">
                    <img
                        class="news-image"
                        src="{image_url}"
                        alt=""
                        loading="{loading}"
                    />
                    <div class="image-shade"></div>
                    <span class="category-pill">{escape(str(item["category"]))}</span>
                </div>

                <div class="news-content">
                    <h3>{escape(str(item["title"]))}</h3>
                    <div class="news-meta">
                        <span class="source-name">{escape(str(item["source"]))}</span>
                        <span class="meta-dot"></span>
                        <span>{escape(str(item["published"]))}</span>
                    </div>
                    <p>{escape(str(item["summary"]))}</p>
                    <div class="read-row">
                        <span>Leer noticia original</span>
                        <span class="external-arrow">↗</span>
                    </div>
                </div>
            </article>
        </a>
        """,
        unsafe_allow_html=True,
    )
