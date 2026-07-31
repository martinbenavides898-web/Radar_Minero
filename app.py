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
    return fetch_daily_news()


now = datetime.now(ZoneInfo("America/Santiago"))

with st.spinner("Explorando fuentes mineras…"):
    result = load_news()

render_header(
    title="Radar Minero",
    subtitle="Lo importante de la minería, en menos de cinco minutos.",
    updated_at=result.get("fetched_at", now),
    is_demo=False,
)

render_market_ticker(MARKET_ITEMS, is_demo=True)

render_news_section("Chile", result.get("chile", []))
render_news_section("Mundo", result.get("world", []))

render_source_status(
    errors=result.get("errors", []),
    has_news=bool(result.get("chile") or result.get("world")),
    source_stats=result.get("source_stats", {}),
)

st.html(
    """
    <footer class="app-footer">
        Radar Minero · Versión 0.3 · Fuentes múltiples y noticias sin repetir
    </footer>
    """
)
