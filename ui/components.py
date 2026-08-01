from __future__ import annotations

from datetime import date, datetime
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
    st.html(textwrap.dedent(html).strip())


def loading_skeleton_markup() -> str:
    return """
    <section class="loading-shell" aria-label="Cargando Radar Minero">
        <div class="skeleton skeleton-eyebrow"></div>
        <div class="skeleton skeleton-title"></div>
        <div class="skeleton skeleton-subtitle"></div>
        <div class="skeleton skeleton-ticker"></div>
        <div class="loading-caption">Revisando y priorizando las fuentes mineras…</div>
        <div class="skeleton-card">
            <div class="skeleton skeleton-image"></div>
            <div class="skeleton-card-body">
                <div class="skeleton skeleton-line skeleton-line-wide"></div>
                <div class="skeleton skeleton-line"></div>
                <div class="skeleton skeleton-line skeleton-line-short"></div>
            </div>
        </div>
        <div class="skeleton-card skeleton-card-secondary">
            <div class="skeleton skeleton-image"></div>
            <div class="skeleton-card-body">
                <div class="skeleton skeleton-line skeleton-line-wide"></div>
                <div class="skeleton skeleton-line"></div>
            </div>
        </div>
    </section>
    """


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
                <span>Contenido actualizado {escape(time_label)}</span>
            </div>
        </section>
        """
    )


def _format_market_date(value: str | None) -> str:
    if not value:
        return ""
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return ""
    return f"{parsed.day} de {SPANISH_MONTHS[parsed.month]}"


def render_market_ticker(
    items: Iterable[dict],
    *,
    source_label: str,
    data_date: str | None,
    status: str,
) -> None:
    items = list(items)

    if not items:
        _render_html(
            """
            <section class="market-shell market-shell-unavailable" aria-label="Indicadores mineros">
                <div class="market-label">
                    <span class="live-dot muted-dot"></span>
                    MERCADOS
                </div>
                <div class="market-unavailable">
                    Datos oficiales temporalmente no disponibles
                </div>
            </section>
            <p class="market-source-note">La app no mostrará valores simulados.</p>
            """
        )
        return

    ticker_items = "".join(_ticker_item(item) for item in items)
    ticker_track = ticker_items + ticker_items

    date_label = _format_market_date(data_date)
    note_parts = [source_label]
    if date_label:
        note_parts.append(f"datos al {date_label}")
    if status == "partial":
        note_parts.append("actualización parcial")
    elif status == "snapshot":
        note_parts.append("respaldo guardado")

    _render_html(
        f"""
        <section class="market-shell" aria-label="Indicadores mineros">
            <div class="market-label">
                <span class="live-dot"></span>
                MERCADOS
            </div>
            <div class="ticker-window">
                <div class="ticker-track">{ticker_track}</div>
            </div>
        </section>
        <p class="market-source-note">{escape(" · ".join(note_parts))}</p>
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


def render_news_section(
    title: str,
    items: list[dict],
    expected_count: int | None = None,
) -> None:
    _render_html(
        f"""
        <div class="section-heading">
            <h2>{escape(title)}</h2>
            <span>{len(items)} noticias</span>
        </div>
        """
    )

    if not items:
        _render_html(
            """
            <div class="empty-state">
                No fue posible cargar noticias de esta sección por ahora.
            </div>
            """
        )
        return

    for index, item in enumerate(items):
        render_news_card(item, eager=index == 0)

    if expected_count and len(items) < expected_count:
        source_count = len(
            {
                str(item.get("source", "")).strip()
                for item in items
                if str(item.get("source", "")).strip()
            }
        )

        if title.lower() == "mundo" and source_count <= 1:
            message = (
                "Solo una fuente internacional respondió con noticias válidas. "
                "Radar Minero muestra únicamente su historia más importante para no simular diversidad."
            )
        else:
            message = (
                "Esta actualización tiene menos noticias disponibles porque algunas fuentes "
                "no respondieron o publicaron contenido repetido."
            )

        _render_html(
            f'<p class="source-note section-availability-note">{escape(message)}</p>'
        )


def render_news_card(item: dict, eager: bool = False) -> None:
    loading = "eager" if eager else "lazy"
    url = escape(str(item["url"]), quote=True)
    title = escape(str(item["title"]))
    title_attribute = escape(str(item["title"]), quote=True)
    category = escape(str(item["category"]))
    source = escape(str(item["source"]))
    published = escape(str(item["published"]))
    summary = escape(str(item["summary"]))
    image_url = str(item.get("image_url", "")).strip()
    backup_badge = (
        '<span class="backup-badge">RESPALDO</span>'
        if item.get("from_snapshot")
        else ""
    )

    if image_url:
        image_block = (
            f'<img class="news-image" src="{escape(image_url, quote=True)}" '
            f'alt="" loading="{loading}" />'
        )
    else:
        initials = "".join(word[0] for word in str(item["source"]).split()[:2]).upper()
        image_block = (
            '<div class="news-image-fallback" aria-hidden="true">'
            f'<span>{escape(initials)}</span><small>RADAR MINERO</small>'
            "</div>"
        )

    _render_html(
        f"""
        <a
            class="news-card-link"
            href="{url}"
            target="_blank"
            rel="noopener noreferrer"
            aria-label="Abrir noticia: {title_attribute}"
        ><article class="news-card"><div class="news-image-wrap">{image_block}<div class="image-shade"></div><span class="category-pill">{category}</span>{backup_badge}</div><div class="news-content"><h3>{title}</h3><div class="news-meta"><span class="source-name">{source}</span><span class="meta-dot"></span><span>{published}</span></div><p>{summary}</p><div class="read-row"><span>Leer noticia original</span><span class="external-arrow">↗</span></div></div></article></a>
        """
    )


def _format_snapshot_age(hours: float | None) -> str:
    if hours is None:
        return ""
    if hours < 1:
        return "menos de 1 h"
    if hours < 24:
        return f"{int(round(hours))} h"
    return f"{int(round(hours / 24))} días"


def render_source_status(
    errors: list[str],
    has_news: bool,
    source_stats: dict[str, int] | None = None,
    source_health: dict[str, dict] | None = None,
    ranking_mode: str = "local",
    ranking_error: str | None = None,
    editorial_error: str | None = None,
    editorial_count: int = 0,
    editorial_enabled: bool = False,
    feed_mode: str = "live",
    snapshot_used_count: int = 0,
    snapshot_age_hours: float | None = None,
    elapsed_seconds: float | None = None,
) -> None:
    source_stats = source_stats or {}
    source_health = source_health or {}
    active = sum(1 for count in source_stats.values() if count > 0)
    total = len(source_stats)

    selection_label = (
        "Selección con Gemini"
        if ranking_mode == "gemini"
        else "Selección local"
    )

    status_parts = [selection_label]

    if editorial_count:
        status_parts.append(f"{editorial_count} resúmenes editados")
    elif editorial_enabled:
        status_parts.append("texto original de respaldo")

    if total:
        status_parts.append(f"{active}/{total} fuentes")
    if elapsed_seconds is not None:
        status_parts.append(f"{elapsed_seconds:.1f} s")

    if feed_mode == "mixed":
        status_parts.append(f"{snapshot_used_count} de respaldo")
    elif feed_mode == "snapshot":
        status_parts.append(
            f"último feed válido de hace {_format_snapshot_age(snapshot_age_hours)}"
        )
    elif feed_mode == "bootstrap":
        status_parts.append("respaldo inicial")

    if has_news:
        _render_html(
            f'<p class="source-note source-summary">{" · ".join(escape(part) for part in status_parts)}</p>'
        )

    failed = sum(
        1
        for health in source_health.values()
        if health.get("status") == "failed"
    )

    if ranking_error and has_news:
        _render_html(
            '<p class="source-note">Gemini no respondió al ranking; se aplicó la selección local automáticamente.</p>'
        )

    if editorial_error and has_news:
        _render_html(
            '<p class="source-note">Algunas tarjetas conservaron el texto original para evitar agregar información no respaldada.</p>'
        )

    if failed and has_news:
        _render_html(
            '<p class="source-note">Algunas fuentes no respondieron; el resto del radar siguió funcionando.</p>'
        )
    elif not has_news:
        _render_html(
            '<p class="source-note source-note-error">No fue posible cargar noticias ni un respaldo válido.</p>'
        )
