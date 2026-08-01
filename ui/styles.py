
import streamlit as st


GLOBAL_CSS = r"""
<style>
    :root {
        --background: #F3F0E9;
        --surface: #FCFAF6;
        --surface-strong: #ECE7DE;
        --surface-soft: #FFFFFF;
        --text: #1D2521;
        --text-soft: #53615A;
        --text-muted: #7C8781;
        --atacamite: #1F7A68;
        --atacamite-deep: #165B4D;
        --atacamite-soft: #E5F2EE;
        --copper: #C77843;
        --copper-light: #D99667;
        --border: rgba(29, 37, 33, 0.10);
        --positive: #1E9364;
        --negative: #B55E4A;
        --shadow-soft: 0 14px 38px rgba(44, 54, 48, 0.08);
        --shadow-card: 0 18px 52px rgba(44, 54, 48, 0.10);
    }

    html {
        background: var(--background);
    }

    body,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    .stApp {
        background:
            radial-gradient(circle at 12% 0%, rgba(199, 120, 67, 0.10), transparent 20rem),
            radial-gradient(circle at 88% 12%, rgba(31, 122, 104, 0.11), transparent 22rem),
            linear-gradient(180deg, #F6F3ED 0%, #F1EEE7 100%);
        color: var(--text);
    }

    [data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    #MainMenu,
    footer {
        display: none !important;
    }

    [data-testid="stMainBlockContainer"] {
        width: 100%;
        max-width: 760px;
        padding: 1.2rem 1rem 4rem;
    }

    .app-header {
        padding: 0.4rem 0 1rem;
    }

    .brand-row {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 1rem;
    }

    .eyebrow {
        margin: 0 0 0.4rem;
        color: var(--copper);
        font-size: 0.69rem;
        font-weight: 800;
        letter-spacing: 0.16em;
    }

    .app-header h1 {
        margin: 0;
        color: var(--text);
        font-size: clamp(2rem, 8vw, 3rem);
        line-height: 0.98;
        letter-spacing: -0.055em;
        font-weight: 790;
    }

    .title-accent {
        color: var(--atacamite);
    }

    .demo-badge {
        margin-top: 0.15rem;
        padding: 0.42rem 0.62rem;
        border: 1px solid rgba(199, 120, 67, 0.26);
        border-radius: 999px;
        color: var(--copper);
        background: rgba(199, 120, 67, 0.07);
        font-size: 0.59rem;
        line-height: 1;
        font-weight: 800;
        letter-spacing: 0.08em;
        white-space: nowrap;
    }

    .app-subtitle {
        max-width: 34rem;
        margin: 0.85rem 0 0.68rem;
        color: var(--text-soft);
        font-size: 0.99rem;
        line-height: 1.5;
    }

    .update-row,
    .news-meta {
        display: flex;
        align-items: center;
        gap: 0.46rem;
        color: var(--text-muted);
        font-size: 0.76rem;
        font-weight: 550;
    }

    .update-dot,
    .meta-dot {
        width: 3px;
        height: 3px;
        border-radius: 50%;
        background: var(--text-muted);
    }

    .market-shell {
        display: grid;
        grid-template-columns: auto minmax(0, 1fr);
        align-items: stretch;
        min-height: 3.15rem;
        margin: 0.75rem 0 0;
        overflow: hidden;
        border: 1px solid rgba(29, 37, 33, 0.08);
        border-radius: 1.1rem;
        background: rgba(255, 255, 255, 0.78);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        box-shadow: var(--shadow-soft);
    }

    .market-label {
        z-index: 2;
        display: flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0 0.9rem;
        border-right: 1px solid rgba(29, 37, 33, 0.08);
        background: rgba(255, 255, 255, 0.44);
        color: var(--text);
        font-size: 0.64rem;
        font-weight: 840;
        letter-spacing: 0.12em;
    }

    .live-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: var(--copper-light);
        box-shadow: 0 0 0 4px rgba(199, 120, 67, 0.12);
    }

    .ticker-window {
        min-width: 0;
        overflow: hidden;
        mask-image: linear-gradient(to right, transparent, black 5%, black 95%, transparent);
        -webkit-mask-image: linear-gradient(to right, transparent, black 5%, black 95%, transparent);
    }

    .ticker-track {
        display: flex;
        align-items: center;
        width: max-content;
        min-height: 3.15rem;
        animation: ticker-scroll 27s linear infinite;
        will-change: transform;
    }

    .ticker-track:hover {
        animation-play-state: paused;
    }

    .ticker-item {
        display: flex;
        align-items: baseline;
        gap: 0.48rem;
        padding: 0 1.05rem;
        border-right: 1px solid rgba(29, 37, 33, 0.08);
        white-space: nowrap;
        font-size: 0.77rem;
    }

    .ticker-name {
        color: var(--text-muted);
        font-size: 0.65rem;
        font-weight: 800;
        letter-spacing: 0.075em;
    }

    .ticker-item strong {
        color: var(--text);
        font-size: 0.78rem;
        font-weight: 760;
    }

    .ticker-delta {
        font-size: 0.67rem;
        font-weight: 760;
    }

    .ticker-delta.up { color: var(--positive); }
    .ticker-delta.down { color: var(--negative); }
    .ticker-delta.flat { color: var(--text-muted); }

    .section-heading {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin: 1.9rem 0 0.86rem;
    }

    .section-heading h2 {
        display: flex;
        align-items: center;
        gap: 0.55rem;
        margin: 0;
        color: var(--text);
        font-size: 1.3rem;
        letter-spacing: -0.025em;
        font-weight: 720;
    }

    .section-heading h2::before {
        content: "";
        width: 0.95rem;
        height: 2px;
        border-radius: 999px;
        background: linear-gradient(90deg, var(--atacamite), rgba(31, 122, 104, 0.18));
    }

    .section-heading span {
        color: var(--text-muted);
        font-size: 0.72rem;
    }

    .news-card-link {
        display: block;
        margin: 0 0 1rem;
        color: inherit !important;
        text-decoration: none !important;
        -webkit-tap-highlight-color: transparent;
    }

    .news-card {
        overflow: hidden;
        border: 1px solid rgba(29, 37, 33, 0.08);
        border-radius: 1.3rem;
        background: rgba(255, 255, 255, 0.94);
        box-shadow: var(--shadow-card);
        transform: translateZ(0);
        transition: transform 160ms ease, border-color 160ms ease, box-shadow 160ms ease;
    }

    .news-card-link:hover .news-card {
        transform: translateY(-2px);
        border-color: rgba(31, 122, 104, 0.18);
        box-shadow: 0 22px 60px rgba(44, 54, 48, 0.14);
    }

    .news-card-link:active .news-card {
        transform: scale(0.992);
    }

    .news-card-link:focus-visible {
        outline: 2px solid rgba(31, 122, 104, 0.42);
        outline-offset: 4px;
        border-radius: 1.3rem;
    }

    .news-image-wrap {
        position: relative;
        aspect-ratio: 16 / 8.7;
        overflow: hidden;
        background: #EAE8E1;
    }

    .news-image {
        width: 100%;
        height: 100%;
        display: block;
        object-fit: cover;
        filter: saturate(0.92) contrast(1.01) brightness(0.98);
        transition: transform 350ms ease, filter 350ms ease;
    }

    .news-card-link:hover .news-image {
        transform: scale(1.016);
        filter: saturate(0.98) contrast(1.03) brightness(1);
    }

    .image-shade {
        position: absolute;
        inset: 0;
        background: linear-gradient(to top, rgba(22, 31, 28, 0.22), transparent 58%);
    }

    .category-pill {
        position: absolute;
        left: 0.86rem;
        bottom: 0.76rem;
        padding: 0.42rem 0.6rem;
        border: 1px solid rgba(31, 122, 104, 0.22);
        border-radius: 999px;
        background: rgba(255, 250, 245, 0.90);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        color: var(--atacamite-deep);
        font-size: 0.62rem;
        font-weight: 830;
        letter-spacing: 0.075em;
    }

    .news-content { padding: 1.02rem 1rem 0.95rem; }

    .news-content h3 {
        margin: 0 0 0.66rem;
        color: var(--text);
        font-size: clamp(1.12rem, 4.5vw, 1.42rem);
        line-height: 1.16;
        letter-spacing: -0.032em;
        font-weight: 740;
    }

    .source-name {
        color: var(--atacamite-deep);
        font-weight: 720;
    }

    .news-content p {
        margin: 0.85rem 0 0.95rem;
        color: var(--text-soft);
        font-size: 0.89rem;
        line-height: 1.56;
    }

    .read-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding-top: 0.82rem;
        border-top: 1px solid rgba(29, 37, 33, 0.08);
        color: var(--atacamite-deep);
        font-size: 0.76rem;
        font-weight: 720;
    }

    .external-arrow {
        color: var(--copper);
        font-size: 1rem;
        transition: transform 160ms ease;
    }

    .news-card-link:hover .external-arrow { transform: translate(2px, -2px); }

    .app-footer {
        padding: 2rem 0 1rem;
        color: var(--text-muted);
        font-size: 0.66rem;
        text-align: center;
    }

    .news-image-fallback {
        width: 100%;
        height: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        background:
            radial-gradient(circle at 70% 20%, rgba(199, 120, 67, 0.18), transparent 32%),
            linear-gradient(145deg, #EEF4F1, #E7ECE7 72%);
        color: var(--atacamite);
    }

    .news-image-fallback span {
        font-size: clamp(3rem, 11vw, 5.5rem);
        font-weight: 850;
        letter-spacing: -0.08em;
        opacity: 0.84;
    }

    .news-image-fallback small {
        margin-top: 0.35rem;
        color: var(--text-muted);
        font-size: 0.58rem;
        font-weight: 800;
        letter-spacing: 0.19em;
    }

    .empty-state {
        padding: 1rem;
        border: 1px solid rgba(29, 37, 33, 0.08);
        border-radius: 1rem;
        color: var(--text-muted);
        background: rgba(255, 255, 255, 0.75);
        font-size: 0.82rem;
    }

    .source-note {
        margin: 1.5rem 0 0;
        color: var(--text-muted);
        font-size: 0.68rem;
        text-align: center;
    }

    .source-note-error { color: var(--negative); }

    .section-availability-note {
        max-width: 34rem;
        margin: -0.15rem auto 1.55rem;
        line-height: 1.5;
    }

    .market-source-note {
        margin: 0.44rem 0 1.5rem;
        color: var(--text-muted);
        font-size: 0.64rem;
        text-align: right;
    }

    .market-shell-unavailable { min-height: 3.15rem; }

    .market-unavailable {
        display: flex;
        align-items: center;
        padding: 0 1rem;
        color: var(--text-muted);
        font-size: 0.75rem;
    }

    .muted-dot {
        background: var(--text-muted);
        box-shadow: 0 0 0 4px rgba(124, 135, 129, 0.11);
    }

    .loading-shell { padding: 0.85rem 0 2rem; }

    .skeleton {
        position: relative;
        overflow: hidden;
        border-radius: 999px;
        background: rgba(29, 37, 33, 0.07);
    }

    .skeleton::after {
        content: "";
        position: absolute;
        inset: 0;
        transform: translateX(-100%);
        background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.55), transparent);
        animation: radar-shimmer 1.35s infinite;
    }

    @keyframes ticker-scroll {
        from { transform: translateX(0); }
        to { transform: translateX(-50%); }
    }

    @keyframes radar-shimmer {
        100% { transform: translateX(100%); }
    }

    .skeleton-eyebrow { width: 9.5rem; height: 0.65rem; margin: 0.8rem 0 0.65rem; }
    .skeleton-title { width: min(78%, 23rem); height: 2.8rem; border-radius: 0.75rem; }
    .skeleton-subtitle { width: min(68%, 20rem); height: 0.9rem; margin-top: 0.95rem; }
    .skeleton-ticker { width: 100%; height: 3.2rem; margin-top: 1.4rem; border-radius: 1rem; }

    .loading-caption {
        margin: 0.72rem 0 1.25rem;
        color: var(--text-muted);
        font-size: 0.7rem;
        text-align: center;
    }

    .skeleton-card {
        overflow: hidden;
        margin-bottom: 1rem;
        border: 1px solid rgba(29, 37, 33, 0.08);
        border-radius: 1.2rem;
        background: rgba(255, 255, 255, 0.72);
        box-shadow: var(--shadow-soft);
    }

    .skeleton-image { width: 100%; height: 13rem; border-radius: 0; }
    .skeleton-card-body { padding: 1rem; }
    .skeleton-line { width: 78%; height: 0.78rem; margin-bottom: 0.7rem; }
    .skeleton-line-wide { width: 94%; height: 1.15rem; }
    .skeleton-line-short { width: 48%; }
    .skeleton-card-secondary { opacity: 0.62; }

    .backup-badge {
        position: absolute;
        right: 0.82rem;
        bottom: 0.72rem;
        padding: 0.38rem 0.52rem;
        border: 1px solid rgba(199, 120, 67, 0.18);
        border-radius: 999px;
        background: rgba(255, 251, 246, 0.88);
        color: var(--copper);
        font-size: 0.56rem;
        font-weight: 820;
        letter-spacing: 0.08em;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
    }

    .source-summary {
        margin-top: 1.85rem;
        color: var(--text-soft);
        font-weight: 650;
    }

    @media (prefers-reduced-motion: reduce) {
        .ticker-track, .skeleton::after { animation: none; }
        .ticker-window { overflow-x: auto; }
    }

    @media (max-width: 480px) {
        [data-testid="stMainBlockContainer"] { padding: 0.82rem 0.78rem 3rem; }
        .app-subtitle { font-size: 0.91rem; }
        .market-shell { grid-template-columns: 1fr; }
        .market-label {
            min-height: 1.9rem;
            border-right: 0;
            border-bottom: 1px solid rgba(29, 37, 33, 0.08);
            padding: 0 0.72rem;
        }
        .ticker-track { min-height: 2.75rem; }
        .ticker-item { padding: 0 0.82rem; }
        .news-content { padding: 0.9rem 0.88rem 0.82rem; }
        .news-content p { font-size: 0.85rem; }
        .skeleton-image { height: 10.8rem; }
    }
</style>
"""


def apply_global_styles() -> None:
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
