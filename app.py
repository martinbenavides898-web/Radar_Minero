from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st

from data.market_data import MARKET_ITEMS
from src.pipeline import fetch_daily_news
from ui.components import (
    render_header,
    render_market_ticker,
    render_news_section,
    render_source_status,
)
from ui.styles import apply_global_styles


st.set_page_config(
    page_title="Radar Minero",
    page_icon="⛏️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

apply_global_styles()


@st.cache_data(ttl=10_800, max_entries=1, show_spinner=False)
def load_news() -> dict:
    """Refresh the feed at most once every three hours."""
    return fetch_daily_news()


now = datetime.now(ZoneInfo("America/Santiago"))

with st.spinner("Explorando fuentes mineras…"):
    result = load_news()

updated_at = result.get("fetched_at", now)

render_header(
    title="Radar Minero",
    subtitle="Lo importante de la minería, en menos de cinco minutos.",
    updated_at=updated_at,
    is_demo=False,
)

render_market_ticker(MARKET_ITEMS, is_demo=True)

news = result.get("news", [])
chile_news = [item for item in news if item.get("region") == "Chile"][:4]
world_news = [item for item in news if item.get("region") == "Mundo"][:3]

render_news_section("Chile", chile_news)
render_news_section("Mundo", world_news)

render_source_status(result.get("errors", []), has_news=bool(news))

st.html(
    """
    <footer class="app-footer">
        Radar Minero · Versión 0.2 · Fuentes reales en desarrollo
    </footer>
    """
)
