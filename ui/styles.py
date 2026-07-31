import streamlit as st


GLOBAL_CSS = r"""
<style>
    :root {
        --background: #07090D;
        --surface: #10141B;
        --surface-strong: #141A22;
        --surface-soft: #0D1117;
        --text: #F2F4F7;
        --text-soft: #B3BAC5;
        --text-muted: #747E8C;
        --copper: #D58445;
        --copper-light: #F0A868;
        --border: rgba(255, 255, 255, 0.075);
        --positive: #85D6A2;
        --negative: #F59A9A;
    }

    html {
        background: var(--background);
    }

    body,
    [data-testid="stAppViewContainer"],
    [data-testid="stMain"],
    .stApp {
        background:
            radial-gradient(circle at 50% -10%, rgba(213, 132, 69, 0.10), transparent 27rem),
            var(--background);
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
        padding: 1.15rem 1rem 4rem;
    }

    .app-header {
        padding: 0.65rem 0 1rem;
    }

    .brand-row {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 1rem;
    }

    .eyebrow {
        margin: 0 0 0.34rem;
        color: var(--copper-light);
        font-size: 0.68rem;
        font-weight: 800;
        letter-spacing: 0.16em;
    }

    .app-header h1 {
        margin: 0;
        color: var(--text);
        font-size: clamp(2rem, 8vw, 3.2rem);
        line-height: 0.98;
        letter-spacing: -0.055em;
        font-weight: 790;
    }

    .demo-badge {
        margin-top: 0.1rem;
        padding: 0.38rem 0.56rem;
        border: 1px solid rgba(213, 132, 69, 0.32);
        border-radius: 999px;
        color: var(--copper-light);
        background: rgba(213, 132, 69, 0.08);
        font-size: 0.59rem;
        line-height: 1;
        font-weight: 800;
        letter-spacing: 0.08em;
        white-space: nowrap;
    }

    .app-subtitle {
        max-width: 31rem;
        margin: 0.82rem 0 0.72rem;
        color: var(--text-soft);
        font-size: 0.98rem;
        line-height: 1.45;
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
        min-height: 3.2rem;
        margin: 0.6rem 0 0;
        overflow: hidden;
        border: 1px solid var(--border);
        border-radius: 0.95rem;
        background: rgba(16, 20, 27, 0.92);
        box-shadow: 0 12px 38px rgba(0, 0, 0, 0.22);
    }

    .market-label {
        z-index: 2;
        display: flex;
        align-items: center;
        gap: 0.45rem;
        padding: 0 0.82rem;
        border-right: 1px solid var(--border);
        background: var(--surface-strong);
        color: var(--text);
        font-size: 0.65rem;
        font-weight: 850;
        letter-spacing: 0.11em;
    }

    .live-dot {
        width: 7px;
        height: 7px;
        border-radius: 50%;
        background: var(--copper-light);
        box-shadow: 0 0 0 4px rgba(213, 132, 69, 0.11);
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
        min-height: 3.2rem;
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
        border-right: 1px solid var(--border);
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

    .ticker-delta.up {
        color: var(--positive);
    }

    .ticker-delta.down {
        color: var(--negative);
    }

    .ticker-delta.flat {
        color: var(--text-muted);
    }

    .demo-market-note {
        margin: 0.4rem 0 1.6rem;
        color: var(--text-muted);
        font-size: 0.65rem;
        text-align: right;
    }

    @keyframes ticker-scroll {
        from { transform: translateX(0); }
        to { transform: translateX(-50%); }
    }

    @media (prefers-reduced-motion: reduce) {
        .ticker-track {
            animation: none;
        }

        .ticker-window {
            overflow-x: auto;
        }
    }

    .section-heading {
        display: flex;
        align-items: flex-end;
        justify-content: space-between;
        margin: 1.7rem 0 0.78rem;
    }

    .section-heading h2 {
        margin: 0;
        color: var(--text);
        font-size: 1.28rem;
        letter-spacing: -0.025em;
    }

    .section-heading span {
        color: var(--text-muted);
        font-size: 0.72rem;
    }

    .news-card-link {
        display: block;
        margin: 0 0 1.15rem;
        color: inherit !important;
        text-decoration: none !important;
        -webkit-tap-highlight-color: transparent;
    }

    .news-card {
        overflow: hidden;
        border: 1px solid var(--border);
        border-radius: 1.18rem;
        background: linear-gradient(155deg, rgba(20, 26, 34, 0.98), rgba(13, 17, 23, 0.98));
        box-shadow: 0 18px 45px rgba(0, 0, 0, 0.20);
        transform: translateZ(0);
        transition:
            transform 160ms ease,
            border-color 160ms ease,
            box-shadow 160ms ease;
    }

    .news-card-link:hover .news-card {
        transform: translateY(-2px);
        border-color: rgba(213, 132, 69, 0.32);
        box-shadow: 0 22px 55px rgba(0, 0, 0, 0.28);
    }

    .news-card-link:active .news-card {
        transform: scale(0.992);
    }

    .news-card-link:focus-visible {
        outline: 2px solid var(--copper-light);
        outline-offset: 4px;
        border-radius: 1.18rem;
    }

    .news-image-wrap {
        position: relative;
        aspect-ratio: 16 / 8.7;
        overflow: hidden;
        background: var(--surface-soft);
    }

    .news-image {
        width: 100%;
        height: 100%;
        display: block;
        object-fit: cover;
        filter: saturate(0.78) contrast(1.04) brightness(0.78);
        transition: transform 350ms ease, filter 350ms ease;
    }

    .news-card-link:hover .news-image {
        transform: scale(1.018);
        filter: saturate(0.9) contrast(1.05) brightness(0.84);
    }

    .image-shade {
        position: absolute;
        inset: 0;
        background:
            linear-gradient(to top, rgba(7, 9, 13, 0.56), transparent 55%),
            linear-gradient(to right, rgba(7, 9, 13, 0.12), transparent 50%);
    }

    .category-pill {
        position: absolute;
        left: 0.82rem;
        bottom: 0.72rem;
        padding: 0.4rem 0.56rem;
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 999px;
        background: rgba(7, 9, 13, 0.76);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        color: var(--copper-light);
        font-size: 0.62rem;
        font-weight: 830;
        letter-spacing: 0.075em;
    }

    .news-content {
        padding: 1rem 1rem 0.92rem;
    }

    .news-content h3 {
        margin: 0 0 0.65rem;
        color: var(--text);
        font-size: clamp(1.12rem, 4.6vw, 1.42rem);
        line-height: 1.16;
        letter-spacing: -0.032em;
        font-weight: 760;
    }

    .source-name {
        color: var(--copper-light);
        font-weight: 720;
    }

    .news-content p {
        margin: 0.85rem 0 0.95rem;
        color: var(--text-soft);
        font-size: 0.89rem;
        line-height: 1.53;
    }

    .read-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding-top: 0.78rem;
        border-top: 1px solid var(--border);
        color: var(--text);
        font-size: 0.76rem;
        font-weight: 720;
    }

    .external-arrow {
        color: var(--copper-light);
        font-size: 1rem;
        transition: transform 160ms ease;
    }

    .news-card-link:hover .external-arrow {
        transform: translate(2px, -2px);
    }

    .app-footer {
        padding: 2rem 0 1rem;
        color: var(--text-muted);
        font-size: 0.66rem;
        text-align: center;
    }

    @media (max-width: 480px) {
        [data-testid="stMainBlockContainer"] {
            padding: 0.82rem 0.78rem 3rem;
        }

        .app-subtitle {
            font-size: 0.91rem;
        }

        .market-shell {
            grid-template-columns: 1fr;
        }

        .market-label {
            min-height: 1.9rem;
            border-right: 0;
            border-bottom: 1px solid var(--border);
            padding: 0 0.72rem;
        }

        .ticker-track {
            min-height: 2.75rem;
        }

        .ticker-item {
            padding: 0 0.82rem;
        }

        .news-content {
            padding: 0.9rem 0.88rem 0.82rem;
        }

        .news-content p {
            font-size: 0.85rem;
        }
    }
    .news-image-fallback {
        width: 100%;
        height: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        background:
            radial-gradient(circle at 70% 20%, rgba(213, 132, 69, 0.28), transparent 32%),
            linear-gradient(145deg, #1A2029, #090C11 72%);
        color: var(--copper-light);
    }

    .news-image-fallback span {
        font-size: clamp(3rem, 11vw, 5.5rem);
        font-weight: 850;
        letter-spacing: -0.08em;
        opacity: 0.9;
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
        border: 1px solid var(--border);
        border-radius: 1rem;
        color: var(--text-muted);
        background: var(--surface-soft);
        font-size: 0.82rem;
    }

    .source-note {
        margin: 1.5rem 0 0;
        color: var(--text-muted);
        font-size: 0.68rem;
        text-align: center;
    }

    .source-note-error {
        color: var(--negative);
    }

</style>
"""


def apply_global_styles() -> None:
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
