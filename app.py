from __future__ import annotations

from datetime import datetime
import os
from zoneinfo import ZoneInfo

import streamlit as st

from src.ai_ranker import DEFAULT_GEMINI_MODEL
from src.market_service import fetch_official_markets
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


def _read_secret(name: str, default: str = "") -> str:
    """Read Streamlit secrets first, then environment variables."""
    try:
        value = st.secrets.get(name, default)
    except (FileNotFoundError, KeyError):
        value = default
    return str(value or os.getenv(name, default)).strip()


GEMINI_API_KEY = _read_secret("GEMINI_API_KEY")
GEMINI_MODEL = _read_secret("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)


@st.cache_data(ttl=10_800, max_entries=1, show_spinner=False)
def load_news(ai_enabled: bool, model: str) -> dict:
    """Refresh sources and editorial selection at most every three hours."""
    return fetch_daily_news(
        gemini_api_key=GEMINI_API_KEY if ai_enabled else "",
        gemini_model=model,
    )


@st.cache_data(ttl=21_600, max_entries=1, show_spinner=False)
def load_markets() -> dict:
    """Refresh official market indicators at most every six hours."""
    return fetch_official_markets()


now = datetime.now(ZoneInfo("America/Santiago"))

with st.spinner("Analizando el radar minero…"):
    market_result = load_markets()
    result = load_news(bool(GEMINI_API_KEY), GEMINI_MODEL)

render_header(
    title="Radar Minero",
    subtitle="Lo importante de la minería, en menos de cinco minutos.",
    updated_at=result.get("fetched_at", now),
    is_demo=False,
)

render_market_ticker(
    market_result.get("items", []),
    source_label=market_result.get("source_label", "Banco Central de Chile"),
    data_date=market_result.get("data_date"),
    status=market_result.get("status", "unavailable"),
)

render_news_section(
    "Chile",
    result.get("chile", []),
    expected_count=4,
)
render_news_section(
    "Mundo",
    result.get("world", []),
    expected_count=3,
)

render_source_status(
    errors=result.get("errors", []),
    has_news=bool(result.get("chile") or result.get("world")),
    source_stats=result.get("source_stats", {}),
    ranking_mode=result.get("ranking_mode", "local"),
    ranking_error=result.get("ranking_error"),
    translation_error=result.get("translation_error"),
)

st.html(
    """
    <footer class="app-footer">
        Radar Minero · Versión 0.5 · Mercados oficiales
    </footer>
    """
)
