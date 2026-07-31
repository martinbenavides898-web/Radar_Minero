from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

import streamlit as st

from data.mock_data import MARKET_ITEMS, NEWS_ITEMS
from ui.components import render_header, render_market_ticker, render_news_section
from ui.styles import apply_global_styles


st.set_page_config(
    page_title="Radar Minero",
    page_icon="⛏️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

apply_global_styles()

now = datetime.now(ZoneInfo("America/Santiago"))

render_header(
    title="Radar Minero",
    subtitle="Lo importante de la minería, en menos de cinco minutos.",
    updated_at=now,
    is_demo=True,
)

render_market_ticker(MARKET_ITEMS)

chile_news = [item for item in NEWS_ITEMS if item["region"] == "Chile"]
world_news = [item for item in NEWS_ITEMS if item["region"] == "Mundo"]

render_news_section("Chile", chile_news)
render_news_section("Mundo", world_news)

st.markdown(
    """
    <footer class="app-footer">
        Radar Minero · Versión 0.1 · Interfaz con contenido simulado
    </footer>
    """,
    unsafe_allow_html=True,
)
