"""
================================================================================
UI_COMPONENTS.PY - Presentation Layer & Responsive Design System
Stile: EA Sports FC / SofaScore / Dark Modern Stadium & Glassmorphism
Componenti: Theme Injection, FUT Card, Plotly Radar Chart, 2D Pitch, Scoreboard
================================================================================
"""

import base64
import json
from pathlib import Path
import textwrap
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
import plotly.graph_objects as go


def render_html(html_str: str) -> None:
    """
    Renderizza HTML in modo sicuro e pulito:
    1. Rimuove automaticamente tutti gli spazi/indentazioni di testa (textwrap.dedent)
       per impedire al parser Markdown di scambiare il codice per un blocco <pre><code>.
    2. Utilizza st.html() nativo di Streamlit (se disponibile) che esegue il rendering
       diretto senza passare dal compilatore markdown.
    3. Fallback su st.markdown(clean_html, unsafe_allow_html=True) se st.html non è presente.
    """
    clean_html = textwrap.dedent(html_str).strip()
    if hasattr(st, "html"):
        st.html(clean_html)
    else:
        st.markdown(clean_html, unsafe_allow_html=True)


# ==============================================================================
# 1. DESIGN SYSTEM GLOBALE: DARK STADIUM, RESPONSIVE & MATERIAL ICONS FIX
# ==============================================================================
def inject_custom_theme() -> None:
    """
    Inietta il Design System globale in stile Dark Modern Stadium & Glassmorphism.
    Garantisce:
    1. Risoluzione dei ligatures/glifi Google Material Icons (Sidebar arrow fix).
    2. Sfondo a tutto schermo con immagine UEFA Champions League e overlay Dark Glassmorphism.
    3. Ottimizzazione Mobile-First e media queries per smartphone (< 768px).
    4. Scroll orizzontale nativo per tabelle e dataframe.
    5. Adattamento fluido di tutti i componenti grafici.
    """
    bg_uri = get_ucl_background_base64()
    bg_css_rule = f", url('{bg_uri}')" if bg_uri else ""

    theme_css = """
    <style>
        /* ----------------------------------------------------------------------
           1. Google Fonts Import (Typography & Icons)
           ---------------------------------------------------------------------- */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700;800;900&family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Teko:wght@600;700&display=swap');
        @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');
        @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');

        /* ----------------------------------------------------------------------
           2. Sfondo Champions League Globale & Root Variables
           ---------------------------------------------------------------------- */
        [data-testid="stAppViewContainer"], .stApp {
            background: linear-gradient(180deg, rgba(8, 12, 22, 0.85) 0%, rgba(5, 8, 15, 0.94) 100%)__UCL_BG_RULE__ !important;
            background-size: cover !important;
            background-position: center !important;
            background-attachment: fixed !important;
            background-repeat: no-repeat !important;
        }

        [data-testid="stHeader"] {
            background: transparent !important;
        }

        :root {
            --bg-dark-core: #0B0E14;
            --bg-stadium-card: rgba(18, 24, 36, 0.85);
            --bg-glass-card: rgba(22, 30, 46, 0.75);
            --border-glass: rgba(255, 255, 255, 0.09);
            --border-glass-glow: rgba(0, 229, 255, 0.25);
            --neon-emerald: #00E676;
            --neon-gold: #FFD700;
            --neon-cyan: #00E5FF;
            --neon-red: #FF3D71;
            --neon-purple: #C084FC;
            --text-main: #F8FAFC;
            --text-muted: #94A3B8;
            --text-sub: #64748B;
            --font-display: 'Outfit', sans-serif;
            --font-luxury: 'Plus Jakarta Sans', 'Inter', sans-serif;
            --font-body: 'Inter', sans-serif;
            --font-stat: 'Teko', sans-serif;
        }

        /* ----------------------------------------------------------------------
           3. Typography Overrides (Scoped to prevent icon clobbering)
           ---------------------------------------------------------------------- */
        html, body, p, label, input, select, textarea {
            font-family: var(--font-body);
            color: var(--text-main);
        }

        h1, h2, h3, h4, .stTitle, .main-title {
            font-family: var(--font-display) !important;
            font-weight: 800 !important;
            letter-spacing: -0.5px;
        }

        /* ----------------------------------------------------------------------
           4. Fix Glifi / Icone Material Streamlit (Sidebar Collapse Button Fix)
           ---------------------------------------------------------------------- */
        [data-testid="stIconMaterial"], 
        [data-testid="stSidebarCollapseButton"] span,
        [data-testid="stSidebarCollapseButton"] button,
        [data-testid="stSidebarCollapseButton"] i,
        [data-testid="stIcon"],
        .material-symbols-rounded, 
        .material-symbols-outlined,
        span[data-testid="stIconMaterial"] {
            font-family: 'Material Symbols Rounded', 'Material Symbols Outlined' !important;
            font-weight: normal !important;
            font-style: normal !important;
            font-size: 24px;
            line-height: 1;
            letter-spacing: normal;
            text-transform: none;
            display: inline-block;
            white-space: nowrap;
            word-wrap: normal;
            direction: ltr;
            -webkit-font-feature-settings: 'liga';
            -webkit-font-smoothing: antialiased;
            text-rendering: optimizeLegibility;
        }

        /* ----------------------------------------------------------------------
           5. Header & Titoli Sezioni (Fluid & Responsive)
           ---------------------------------------------------------------------- */
        .main-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1rem;
            flex-wrap: wrap;
            gap: 12px;
        }
        .main-title {
            font-size: clamp(1.6rem, 4vw, 2.2rem);
            font-weight: 900;
            background: linear-gradient(135deg, #00E676 0%, #00E5FF 50%, #FFD700 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.15rem;
            text-shadow: 0 0 30px rgba(0, 230, 118, 0.25);
            word-break: break-word;
        }
        .sub-title {
            font-size: clamp(0.82rem, 2vw, 0.95rem);
            color: var(--text-muted);
            margin-bottom: 1.4rem;
            font-weight: 400;
            line-height: 1.4;
        }

        /* ----------------------------------------------------------------------
           6. Ruoli & Badges
           ---------------------------------------------------------------------- */
        .role-badge-admin {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: linear-gradient(135deg, rgba(0, 230, 118, 0.2) 0%, rgba(5, 150, 105, 0.3) 100%);
            color: #00E676;
            border: 1px solid rgba(0, 230, 118, 0.4);
            font-weight: 700;
            font-size: 0.78rem;
            padding: 5px 14px;
            border-radius: 30px;
            box-shadow: 0 0 15px rgba(0, 230, 118, 0.2);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .role-badge-viewer {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: linear-gradient(135deg, rgba(0, 229, 255, 0.15) 0%, rgba(29, 78, 216, 0.25) 100%);
            color: #00E5FF;
            border: 1px solid rgba(0, 229, 255, 0.35);
            font-weight: 700;
            font-size: 0.78rem;
            padding: 5px 14px;
            border-radius: 30px;
            box-shadow: 0 0 15px rgba(0, 229, 255, 0.15);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .badge-circle {
            display: inline-flex;
            align-items: center;
            gap: 4px;
            background: linear-gradient(135deg, rgba(255, 215, 0, 0.2) 0%, rgba(217, 119, 6, 0.3) 100%);
            color: #FFD700;
            border: 1px solid rgba(255, 215, 0, 0.45);
            font-weight: 700;
            font-size: 0.75rem;
            padding: 3px 10px;
            border-radius: 20px;
            box-shadow: 0 0 10px rgba(255, 215, 0, 0.2);
        }

        /* ----------------------------------------------------------------------
           7. Glassmorphism Card Container
           ---------------------------------------------------------------------- */
        .glass-card {
            background: var(--bg-glass-card);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            border: 1px solid var(--border-glass);
            border-radius: 16px;
            padding: clamp(1rem, 3vw, 1.3rem);
            margin-bottom: 1.2rem;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.35);
            transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
            box-sizing: border-box;
            width: 100%;
        }
        .glass-card:hover {
            border-color: rgba(255, 255, 255, 0.18);
            box-shadow: 0 12px 36px 0 rgba(0, 0, 0, 0.45);
        }

        /* Card MVP & Peggiore */
        .card-mvp {
            background: linear-gradient(135deg, rgba(255, 215, 0, 0.12) 0%, rgba(18, 24, 38, 0.85) 100%);
            border: 1px solid rgba(255, 215, 0, 0.4);
            border-radius: 16px;
            padding: clamp(1rem, 3vw, 1.4rem);
            text-align: center;
            box-shadow: 0 8px 24px rgba(255, 215, 0, 0.15);
            margin-bottom: 1rem;
            box-sizing: border-box;
        }
        .card-worst {
            background: linear-gradient(135deg, rgba(255, 61, 113, 0.12) 0%, rgba(18, 24, 38, 0.85) 100%);
            border: 1px solid rgba(255, 61, 113, 0.4);
            border-radius: 16px;
            padding: clamp(1rem, 3vw, 1.4rem);
            text-align: center;
            box-shadow: 0 8px 24px rgba(255, 61, 113, 0.15);
            margin-bottom: 1rem;
            box-sizing: border-box;
        }

        /* ----------------------------------------------------------------------
           8. Badge Esito & Forma Recente
           ---------------------------------------------------------------------- */
        .badge-v {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #00E676 0%, #00B0FF 100%);
            color: #061A14;
            font-weight: 800;
            font-size: 0.8rem;
            width: 26px;
            height: 26px;
            border-radius: 8px;
            margin-right: 5px;
            margin-bottom: 4px;
            box-shadow: 0 2px 8px rgba(0, 230, 118, 0.4);
        }
        .badge-p {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #FFD700 0%, #FF9100 100%);
            color: #1A1300;
            font-weight: 800;
            font-size: 0.8rem;
            width: 26px;
            height: 26px;
            border-radius: 8px;
            margin-right: 5px;
            margin-bottom: 4px;
            box-shadow: 0 2px 8px rgba(255, 215, 0, 0.4);
        }
        .badge-s {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            background: linear-gradient(135deg, #FF3D71 0%, #D50000 100%);
            color: #FFFFFF;
            font-weight: 800;
            font-size: 0.8rem;
            width: 26px;
            height: 26px;
            border-radius: 8px;
            margin-right: 5px;
            margin-bottom: 4px;
            box-shadow: 0 2px 8px rgba(255, 61, 113, 0.4);
        }

        /* ----------------------------------------------------------------------
           9. Pulsanti Streamlit Modernizzati
           ---------------------------------------------------------------------- */
        .stButton>button {
            border-radius: 12px !important;
            font-weight: 700 !important;
            font-family: var(--font-display) !important;
            letter-spacing: 0.3px;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            background: rgba(30, 41, 59, 0.8) !important;
            padding: 0.5rem 1rem !important;
        }
        .stButton>button:hover {
            transform: translateY(-2px) !important;
            border-color: var(--neon-emerald) !important;
            box-shadow: 0 4px 18px rgba(0, 230, 118, 0.25) !important;
        }
        .stButton>button[kind="primary"] {
            background: linear-gradient(135deg, #00E676 0%, #00B0FF 100%) !important;
            color: #061A14 !important;
            border: none !important;
            box-shadow: 0 4px 15px rgba(0, 230, 118, 0.35) !important;
        }
        .stButton>button[kind="primary"]:hover {
            box-shadow: 0 6px 22px rgba(0, 230, 118, 0.55) !important;
        }

        /* ----------------------------------------------------------------------
           10. Metriche Streamlit
           ---------------------------------------------------------------------- */
        div[data-testid="stMetric"] {
            background: rgba(22, 30, 46, 0.6);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.07);
            border-radius: 14px;
            padding: 0.8rem 1rem;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
            transition: border-color 0.2s ease;
        }
        div[data-testid="stMetric"]:hover {
            border-color: rgba(0, 229, 255, 0.3);
        }
        div[data-testid="stMetricValue"] {
            font-family: var(--font-display);
            font-weight: 800;
            color: #FFFFFF;
            font-size: clamp(1.3rem, 3.5vw, 1.8rem);
        }

        /* ----------------------------------------------------------------------
           11. Tabs Streamlit (Fluid con Scroll Orizzontale su Mobile)
           ---------------------------------------------------------------------- */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            padding-bottom: 6px;
            overflow-x: auto;
            white-space: nowrap;
            flex-wrap: nowrap;
            scrollbar-width: thin;
            -webkit-overflow-scrolling: touch;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 10px 10px 0 0;
            padding: 8px 16px;
            font-family: var(--font-display);
            font-weight: 600;
            color: var(--text-muted);
            background: transparent;
            transition: all 0.2s ease;
            white-space: nowrap;
            font-size: clamp(0.82rem, 2vw, 0.95rem);
        }
        .stTabs [aria-selected="true"] {
            color: var(--neon-emerald) !important;
            border-bottom: 2px solid var(--neon-emerald) !important;
            background: rgba(0, 230, 118, 0.06) !important;
        }

        /* ----------------------------------------------------------------------
           12. Componenti Specifici: FUT Card & Scoreboard & Pitch Classes
           ---------------------------------------------------------------------- */
        /* FUT Card Wrapper */
        .fut-card-wrapper {
            display: flex;
            justify-content: center;
            margin: 1.2rem auto;
            width: 100%;
            box-sizing: border-box;
        }
        .fut-card {
            width: 100%;
            max-width: 340px;
            margin: 0 auto;
            box-sizing: border-box;
            border-radius: 22px;
            background: #111723;
            background-image: linear-gradient(180deg, rgba(0, 229, 255, 0.2) 0%, rgba(18, 24, 38, 0.95) 70%);
            border: 2px solid rgba(0, 229, 255, 0.35);
            box-shadow: 0 16px 40px rgba(0, 0, 0, 0.6), 0 0 30px rgba(0, 229, 255, 0.2);
            padding: clamp(16px, 4vw, 20px) clamp(14px, 3.5vw, 18px);
            position: relative;
            overflow: hidden;
            font-family: var(--font-display);
            color: #FFFFFF;
            transition: transform 0.3s ease;
        }
        .fut-card.cerchia {
            background-image: linear-gradient(180deg, rgba(255, 215, 0, 0.25) 0%, rgba(18, 24, 38, 0.95) 70%);
            border: 2px solid rgba(255, 215, 0, 0.45);
            box-shadow: 0 16px 40px rgba(0, 0, 0, 0.6), 0 0 30px rgba(255, 215, 0, 0.25);
        }
        .fut-card-watermark {
            position: absolute;
            top: -30px;
            right: -30px;
            width: 140px;
            height: 140px;
            background: radial-gradient(circle, rgba(255,255,255,0.12) 0%, rgba(255,255,255,0) 70%);
            border-radius: 50%;
            pointer-events: none;
        }
        .fut-card-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 8px;
        }
        .fut-ovr-num {
            font-size: clamp(2.6rem, 7vw, 3.4rem);
            font-weight: 900;
            line-height: 0.9;
            color: #FFFFFF;
            text-shadow: 0 4px 12px rgba(0,0,0,0.5);
            font-family: var(--font-stat);
            letter-spacing: 1px;
        }
        .fut-ovr-label {
            font-size: 0.74rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .fut-player-name {
            text-align: center;
            font-size: clamp(1.1rem, 3.5vw, 1.35rem);
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: #FFFFFF;
            border-bottom: 1px solid rgba(255, 255, 255, 0.12);
            padding-bottom: 8px;
            margin-bottom: 12px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .fut-attrs-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 6px 12px;
            background: rgba(10, 14, 22, 0.65);
            padding: clamp(8px, 2.5vw, 10px) clamp(10px, 3vw, 14px);
            border-radius: 14px;
            border: 1px solid rgba(255, 255, 255, 0.06);
        }
        .fut-attr-item {
            display: flex;
            justify-content: space-between;
            align-items: baseline;
        }
        .fut-attr-val {
            font-size: clamp(1.1rem, 3vw, 1.25rem);
            font-weight: 800;
            font-family: var(--font-stat);
        }
        .fut-attr-lbl {
            font-size: clamp(0.65rem, 1.8vw, 0.72rem);
            font-weight: 700;
            color: #94A3B8;
        }
        .fut-summary-bar {
            display: flex;
            justify-content: space-around;
            align-items: center;
            margin-top: 12px;
            font-size: clamp(0.68rem, 2vw, 0.74rem);
            color: #94A3B8;
            flex-wrap: wrap;
            gap: 4px;
        }

        /* ----------------------------------------------------------------------
           13. Responsive Media Queries & Mobile-First Column Stacking
           ---------------------------------------------------------------------- */
        @media (max-width: 992px), (max-width: 768px), (max-width: 640px), (max-width: 480px) {
            /* Schermata Login: su mobile espandi il container al 100% e nascondi colonne laterali vuote */
            div[data-testid="stHorizontalBlock"]:has(#luxury-pin-marker) {
                display: flex !important;
                flex-direction: column !important;
                width: 100% !important;
            }
            div[data-testid="stHorizontalBlock"]:has(#luxury-pin-marker) > div[data-testid="column"]:empty {
                display: none !important;
            }
            div[data-testid="stHorizontalBlock"]:has(#luxury-pin-marker) > div[data-testid="column"] {
                min-width: 100% !important;
                width: 100% !important;
                flex: 1 1 100% !important;
                padding: 0 !important;
            }

            /* Container 4 slot PIN su mobile: assolutamente in riga senza mai andare a capo (zero wrap, ingombro < 200px) */
            [data-testid="stForm"] [data-testid="stHorizontalBlock"],
            div[data-testid="stForm"]:has(#luxury-pin-marker) [data-testid="stHorizontalBlock"],
            div[data-testid="stHorizontalBlock"]:has(input[aria-label="d1"]),
            div[data-testid="stHorizontalBlock"]:has(input[aria-label^="d"]) {
                display: flex !important;
                flex-direction: row !important;
                flex-wrap: nowrap !important;
                justify-content: center !important;
                align-items: center !important;
                gap: 6px !important;
                width: 100% !important;
                max-width: 210px !important;
                margin: 0 auto 16px auto !important;
                box-sizing: border-box !important;
            }

            /* Sovrascrivi il calc(50%) forzato da Streamlit Mobile: slot compatti a 44px */
            [data-testid="stForm"] [data-testid="stHorizontalBlock"] > div[data-testid="column"],
            div[data-testid="stForm"]:has(#luxury-pin-marker) [data-testid="stHorizontalBlock"] > div[data-testid="column"],
            div[data-testid="stHorizontalBlock"]:has(input[aria-label="d1"]) > div[data-testid="column"],
            div[data-testid="stHorizontalBlock"]:has(input[aria-label^="d"]) > div[data-testid="column"],
            [data-testid="stForm"] div[data-testid="column"],
            div[data-testid="column"]:has(input[aria-label="d1"]),
            div[data-testid="column"]:has(input[aria-label^="d"]) {
                width: 44px !important;
                min-width: 0 !important;
                max-width: 44px !important;
                height: 44px !important;
                flex: 0 0 44px !important;
                flex-basis: 44px !important;
                flex-grow: 0 !important;
                flex-shrink: 0 !important;
                margin: 0 !important;
                padding: 0 !important;
                box-sizing: border-box !important;
            }

            /* Dimensioni 44px su mobile per input e wrapper */
            [data-testid="stForm"] div[data-testid="column"] div[data-testid="stTextInput"],
            [data-testid="stForm"] div[data-testid="column"] [data-baseweb="input"],
            div[data-testid="stForm"]:has(#luxury-pin-marker) div[data-testid="column"] [data-baseweb="input"],
            div[data-testid="column"]:has(input[aria-label^="d"]) [data-baseweb="input"] {
                width: 44px !important;
                min-width: 0 !important;
                max-width: 44px !important;
                height: 44px !important;
                min-height: 44px !important;
                max-height: 44px !important;
                border-radius: 11px !important;
            }

            [data-testid="stForm"] div[data-testid="column"] input,
            div[data-testid="stForm"]:has(#luxury-pin-marker) div[data-testid="column"] input,
            div[data-testid="column"]:has(input[aria-label^="d"]) input {
                height: 44px !important;
                min-height: 44px !important;
                max-height: 44px !important;
                width: 44px !important;
                line-height: 44px !important;
                font-size: 1.65rem !important;
            }

            /* Layout Streamlit Columns Stacking generale (esclusi blocchi interni PIN) */
            div:not([data-testid="stForm"]) > [data-testid="stHorizontalBlock"]:not(:has(input[aria-label^="d"])) {
                flex-wrap: wrap !important;
                gap: 12px !important;
            }
            div:not([data-testid="stForm"]) > [data-testid="stHorizontalBlock"]:not(:has(input[aria-label^="d"])) > [data-testid="column"] {
                min-width: 100% !important;
                flex: 1 1 100% !important;
                width: 100% !important;
            }
            /* Scoreboard Mobile Layout */
            .scoreboard-score-grid {
                grid-template-columns: 1fr !important;
                text-align: center !important;
                gap: 8px !important;
                padding: 10px !important;
            }
            .score-team {
                text-align: center !important;
            }
            .score-pill {
                width: fit-content !important;
                margin: 0 auto !important;
                padding: 4px 16px !important;
            }
            .scoreboard-formations {
                grid-template-columns: 1fr !important;
                gap: 10px !important;
            }
            /* Pitch Header Stacking */
            .pitch-header {
                flex-direction: column !important;
                align-items: stretch !important;
                text-align: center !important;
                gap: 6px !important;
            }
            .pitch-team-badge {
                justify-content: center !important;
            }
            .pitch-delta-badge {
                margin: 0 auto !important;
            }
        }

        /* ----------------------------------------------------------------------
           14. Dataframe & Tabelle Native Horizontal Scrolling
           ---------------------------------------------------------------------- */
        [data-testid="stDataFrame"], [data-testid="stTable"], .stDataFrame {
            width: 100% !important;
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch !important;
            border-radius: 12px !important;
        }
        [data-testid="stDataFrame"] > div {
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch !important;
        }

        /* ----------------------------------------------------------------------
           15. Matte Dark Neumorphism / Luxury Dark UI Passcode Screen
           ---------------------------------------------------------------------- */
        .luxury-login-wrapper {
            display: flex;
            justify-content: center;
            align-items: center;
            width: 100%;
            padding: 1rem 0;
            box-sizing: border-box;
        }
        .luxury-login-card {
            width: 100%;
            max-width: 420px;
            margin: 0 auto;
            background: linear-gradient(145deg, #111522 0%, #0B0E17 100%);
            background-image: repeating-linear-gradient(180deg, rgba(255, 255, 255, 0.018) 0px, rgba(255, 255, 255, 0.018) 1px, transparent 1px, transparent 4px), linear-gradient(145deg, #111522 0%, #0B0E17 100%);
            border-radius: 28px;
            border: 1px solid rgba(255, 255, 255, 0.09);
            box-shadow: 0 30px 70px -10px rgba(0, 0, 0, 0.9), 0 0 40px rgba(37, 99, 235, 0.12), inset 0 1px 1px rgba(255, 255, 255, 0.12);
            padding: clamp(28px, 6vw, 38px) clamp(20px, 5vw, 30px) clamp(24px, 5vw, 30px) clamp(20px, 5vw, 30px);
            position: relative;
            overflow: hidden;
            text-align: center;
            box-sizing: border-box;
        }
        
        /* 1. UEFA Champions League Starball 3D Glow Header */
        .starball-glow-container {
            width: 120px;
            height: 120px;
            margin: 0 auto 12px auto;
            background: radial-gradient(circle, rgba(0, 240, 255, 0.22) 0%, rgba(59, 130, 246, 0.25) 35%, rgba(15, 23, 42, 0) 70%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 15px 35px -5px rgba(0, 0, 0, 0.8);
            position: relative;
        }
        .starball-glow-container::before {
            content: '';
            position: absolute;
            width: 130px;
            height: 130px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(0, 240, 255, 0.15) 0%, transparent 70%);
            pointer-events: none;
            z-index: 1;
        }
        .starball-img {
            width: 110px;
            height: 110px;
            border-radius: 50%;
            object-fit: cover;
            margin: 0 auto 12px auto;
            display: block;
            position: relative;
            z-index: 2;
            filter: drop-shadow(0 0 16px rgba(0, 240, 255, 0.45));
            transition: transform 0.35s cubic-bezier(0.4, 0, 0.2, 1);
        }
        .starball-img:hover {
            transform: scale(1.06) rotate(4deg);
        }

        .luxury-login-title {
            font-family: var(--font-luxury) !important;
            font-size: 1.65rem !important;
            font-weight: 700 !important;
            color: #FFFFFF !important;
            letter-spacing: -0.5px !important;
            margin: 10px 0 6px 0 !important;
            text-shadow: 0 2px 10px rgba(0, 0, 0, 0.5);
        }
        .luxury-login-subtitle {
            font-family: var(--font-luxury) !important;
            font-size: 0.85rem !important;
            color: #8F9CAE !important;
            font-weight: 400 !important;
            line-height: 1.45 !important;
            margin: 0 auto 24px auto !important;
            max-width: 320px !important;
        }

        /* Form Container Styled as the Floating Luxury Card */
        div[data-testid="stForm"]:has(#luxury-pin-marker) {
            background: linear-gradient(145deg, #111522 0%, #0B0E17 100%) !important;
            background-image: repeating-linear-gradient(180deg, rgba(255, 255, 255, 0.018) 0px, rgba(255, 255, 255, 0.018) 1px, transparent 1px, transparent 4px), linear-gradient(145deg, #111522 0%, #0B0E17 100%) !important;
            border-radius: 28px !important;
            border: 1px solid rgba(255, 255, 255, 0.09) !important;
            box-shadow: 0 30px 70px -10px rgba(0, 0, 0, 0.9), 0 0 40px rgba(37, 99, 235, 0.12), inset 0 1px 1px rgba(255, 255, 255, 0.12) !important;
            padding: clamp(24px, 5vw, 36px) clamp(16px, 4vw, 28px) clamp(20px, 4vw, 28px) clamp(16px, 4vw, 28px) !important;
            max-width: 400px !important;
            width: calc(100% - 24px) !important;
            margin: 1.5rem auto !important;
            position: relative !important;
            overflow: hidden !important;
            text-align: center !important;
            box-sizing: border-box !important;
        }

        /* 1. Neutralizzazione totale di testi parassiti, contatori ("0/1") e istruzioni di sottomissione */
        [data-testid="stForm"] div[data-testid="column"] [data-testid="stInputInstructions"],
        [data-testid="stForm"] div[data-testid="column"] [data-testid="InputInstructions"],
        [data-testid="stForm"] div[data-testid="column"] [data-testid="stInputInstruction"],
        [data-testid="stForm"] div[data-testid="column"] [data-testid="stCaptionContainer"],
        [data-testid="stForm"] div[data-testid="column"] div[data-testid="stTextInput"] label,
        [data-testid="stForm"] div[data-testid="column"] label,
        [data-testid="stForm"] div[data-testid="column"] small,
        [data-testid="stForm"] div[data-testid="column"] caption,
        [data-testid="stForm"] div[data-testid="column"] span:not([data-baseweb]),
        div[data-testid="column"]:has(input[aria-label="d1"]) [data-testid="stInputInstructions"],
        div[data-testid="column"]:has(input[aria-label^="d"]) [data-testid="stInputInstructions"],
        div[data-testid="column"]:has(input[aria-label^="d"]) [data-testid="InputInstructions"],
        div[data-testid="column"]:has(input[aria-label^="d"]) [data-testid="stInputInstruction"],
        div[data-testid="column"]:has(input[aria-label^="d"]) small,
        div[data-testid="column"]:has(input[aria-label^="d"]) label {
            display: none !important;
            visibility: hidden !important;
            height: 0 !important;
            min-height: 0 !important;
            max-height: 0 !important;
            width: 0 !important;
            min-width: 0 !important;
            max-width: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            border: none !important;
            overflow: hidden !important;
            position: absolute !important;
            pointer-events: none !important;
            font-size: 0 !important;
            line-height: 0 !important;
            opacity: 0 !important;
        }

        /* 2. Layout & Styling dei 4 Quadratini OTP Glassmorphism (Desktop Default: 48px, gap 8px) */
        [data-testid="stForm"] [data-testid="stHorizontalBlock"],
        div[data-testid="stForm"]:has(#luxury-pin-marker) [data-testid="stHorizontalBlock"],
        div[data-testid="stHorizontalBlock"]:has(input[aria-label="d1"]),
        div[data-testid="stHorizontalBlock"]:has(input[aria-label^="d"]) {
            display: flex !important;
            flex-direction: row !important;
            flex-wrap: nowrap !important;
            justify-content: center !important;
            align-items: center !important;
            gap: 8px !important;
            width: 100% !important;
            max-width: 240px !important;
            margin: 0 auto 16px auto !important;
            box-sizing: border-box !important;
        }

        /* Colonne PIN: fisse a 48px su desktop con min-width: 0 per sbloccare il box model */
        [data-testid="stForm"] [data-testid="stHorizontalBlock"] > div[data-testid="column"],
        div[data-testid="stForm"]:has(#luxury-pin-marker) [data-testid="stHorizontalBlock"] > div[data-testid="column"],
        div[data-testid="stHorizontalBlock"]:has(input[aria-label="d1"]) > div[data-testid="column"],
        div[data-testid="stHorizontalBlock"]:has(input[aria-label^="d"]) > div[data-testid="column"],
        [data-testid="stForm"] div[data-testid="column"],
        div[data-testid="column"]:has(input[aria-label="d1"]),
        div[data-testid="column"]:has(input[aria-label^="d"]) {
            width: 48px !important;
            min-width: 0 !important;
            max-width: 48px !important;
            height: 48px !important;
            flex: 0 0 48px !important;
            flex-basis: 48px !important;
            flex-grow: 0 !important;
            flex-shrink: 0 !important;
            box-sizing: border-box !important;
            margin: 0 !important;
            padding: 0 !important;
        }

        [data-testid="stForm"] div[data-testid="column"] div[data-testid="stTextInput"],
        div[data-testid="stForm"]:has(#luxury-pin-marker) div[data-testid="column"] div[data-testid="stTextInput"],
        div[data-testid="column"]:has(input[aria-label^="d"]) div[data-testid="stTextInput"],
        [data-testid="stForm"] div[data-testid="column"] div[data-testid="stTextInputRootElement"],
        div[data-testid="stForm"]:has(#luxury-pin-marker) div[data-testid="column"] div[data-testid="stTextInputRootElement"],
        div[data-testid="column"]:has(input[aria-label^="d"]) div[data-testid="stTextInputRootElement"] {
            width: 48px !important;
            min-width: 0 !important;
            max-width: 48px !important;
            height: 48px !important;
            margin: 0 auto !important;
            padding: 0 !important;
            box-sizing: border-box !important;
        }

        /* Contenitore di input: Dark Frosted Glassmorphism satinato (48x48px default) */
        [data-testid="stForm"] div[data-testid="column"] [data-baseweb="input"],
        div[data-testid="stForm"]:has(#luxury-pin-marker) div[data-testid="column"] [data-baseweb="input"],
        div[data-testid="column"]:has(input[aria-label^="d"]) [data-baseweb="input"] {
            width: 48px !important;
            min-width: 0 !important;
            max-width: 48px !important;
            height: 48px !important;
            min-height: 48px !important;
            max-height: 48px !important;
            border-radius: 12px !important;
            background: rgba(255, 255, 255, 0.04) !important;
            background-color: rgba(255, 255, 255, 0.04) !important;
            background-image: none !important;
            border: 1px solid rgba(255, 255, 255, 0.14) !important;
            backdrop-filter: blur(16px) !important;
            -webkit-backdrop-filter: blur(16px) !important;
            box-shadow: 
                inset 0 2px 4px rgba(0, 0, 0, 0.4),
                0 4px 12px rgba(0, 0, 0, 0.25) !important;
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
            overflow: hidden !important;
            padding: 0 !important;
            margin: 0 auto !important;
            box-sizing: border-box !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
        }

        /* Glow e Bagliore Satinato Neutro al Focus */
        [data-testid="stForm"] div[data-testid="column"] [data-baseweb="input"]:focus-within,
        div[data-testid="stForm"]:has(#luxury-pin-marker) div[data-testid="column"] [data-baseweb="input"]:focus-within,
        div[data-testid="column"]:has(input[aria-label^="d"]) [data-baseweb="input"]:focus-within {
            border-color: rgba(255, 255, 255, 0.5) !important;
            background: rgba(255, 255, 255, 0.08) !important;
            background-color: rgba(255, 255, 255, 0.08) !important;
            box-shadow: 
                0 0 16px rgba(255, 255, 255, 0.18),
                inset 0 1px 2px rgba(255, 255, 255, 0.25),
                0 6px 18px rgba(0, 0, 0, 0.45) !important;
            transform: translateY(-2px);
        }

        /* Reset totale figli interni per trasparenza uniforme */
        [data-testid="stForm"] div[data-testid="column"] [data-baseweb="base-input"],
        div[data-testid="stForm"]:has(#luxury-pin-marker) div[data-testid="column"] [data-baseweb="base-input"],
        div[data-testid="column"]:has(input[aria-label^="d"]) [data-baseweb="base-input"] {
            background: transparent !important;
            background-color: transparent !important;
            background-image: none !important;
            border: none !important;
            box-shadow: none !important;
            height: 100% !important;
            width: 100% !important;
            padding: 0 !important;
            margin: 0 !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
        }

        /* 3. INPUT NATIVO: Centratura geometrica assoluta e calibrazione cifre a 1.75rem (font-weight 800) */
        [data-testid="stForm"] div[data-testid="column"] input,
        div[data-testid="stForm"]:has(#luxury-pin-marker) div[data-testid="column"] input,
        div[data-testid="column"]:has(input[aria-label^="d"]) input {
            text-align: center !important;
            font-size: 1.75rem !important;
            font-weight: 800 !important;
            color: #FFFFFF !important;
            height: 48px !important;
            min-height: 48px !important;
            max-height: 48px !important;
            width: 48px !important;
            line-height: 48px !important;
            padding: 0 !important;
            padding-left: 0 !important;
            padding-right: 0 !important;
            padding-top: 0 !important;
            padding-bottom: 0 !important;
            margin: 0 !important;
            text-indent: 0 !important;
            letter-spacing: 0 !important;
            caret-color: #00E5FF !important;
            -webkit-appearance: none !important;
            -moz-appearance: none !important;
            appearance: none !important;
            font-family: var(--font-luxury), 'Outfit', sans-serif !important;
            vertical-align: middle !important;
            box-sizing: border-box !important;
            background: transparent !important;
            background-color: transparent !important;
            background-image: none !important;
            border: none !important;
            outline: none !important;
            box-shadow: none !important;
            -webkit-text-security: none !important;
        }

        [data-testid="stForm"] div[data-testid="column"] div[data-testid="stTextInput"] button,
        [data-testid="stForm"] div[data-testid="column"] div[data-testid="stTextInput"] svg,
        div[data-testid="stForm"]:has(#luxury-pin-marker) div[data-testid="column"] div[data-testid="stTextInput"] button,
        div[data-testid="stForm"]:has(#luxury-pin-marker) div[data-testid="column"] div[data-testid="stTextInput"] svg,
        div[data-testid="column"] button,
        div[data-testid="column"] svg {
            display: none !important;
            visibility: hidden !important;
        }

        /* 3. Pulsante Sblocca Accesso con Bordo Prisma Iridescente */
        div[data-testid="stForm"]:has(#luxury-pin-marker) button[kind="secondaryFormSubmit"],
        div[data-testid="stForm"]:has(#luxury-pin-marker) button[kind="primaryFormSubmit"],
        div[data-testid="stForm"]:has(#luxury-pin-marker) button {
            border: 1.5px solid transparent !important;
            background-image: 
                linear-gradient(rgba(18, 24, 38, 0.92), rgba(10, 14, 22, 0.92)), 
                conic-gradient(from 180deg at 50% 50%, #00F0FF 0deg, #3B82F6 70deg, #FFFFFF 140deg, #FFB800 200deg, #FF3B30 270deg, #00F0FF 360deg) !important;
            background-origin: border-box !important;
            background-clip: padding-box, border-box !important;
            border-radius: 16px !important;
            color: #FFFFFF !important;
            padding: 10px 20px !important;
            font-size: 0.95rem !important;
            font-weight: 700 !important;
            font-family: var(--font-luxury) !important;
            letter-spacing: 0.5px !important;
            box-shadow: 
                0 12px 28px -5px rgba(0, 0, 0, 0.75),
                0 0 18px rgba(0, 240, 255, 0.25),
                inset 0 1px 2px rgba(255, 255, 255, 0.35) !important;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
            width: 100% !important;
            max-width: 280px !important;
            margin: 18px auto 0 auto !important;
            display: block !important;
            height: 48px !important;
            cursor: pointer !important;
        }
        div[data-testid="stForm"]:has(#luxury-pin-marker) button:hover {
            background-image: 
                linear-gradient(rgba(24, 32, 50, 0.95), rgba(14, 20, 32, 0.95)), 
                conic-gradient(from 220deg at 50% 50%, #00F0FF 0deg, #60A5FA 70deg, #FFFFFF 140deg, #FCD34D 200deg, #F87171 270deg, #00F0FF 360deg) !important;
            transform: translateY(-2px) !important;
            box-shadow: 
                0 16px 35px -5px rgba(0, 0, 0, 0.85),
                0 0 25px rgba(0, 240, 255, 0.5),
                inset 0 1px 2px rgba(255, 255, 255, 0.5) !important;
        }
        div[data-testid="stForm"]:has(#luxury-pin-marker) button:active {
            transform: translateY(0px) !important;
        }

        .luxury-error-pill {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            background: rgba(239, 68, 68, 0.12);
            border: 1px solid rgba(239, 68, 68, 0.3);
            color: #FCA5A5;
            border-radius: 12px;
            padding: 10px 14px;
            font-size: 0.85rem;
            font-weight: 600;
            margin: 14px auto 0 auto;
            max-width: 280px;
            font-family: var(--font-luxury);
            text-align: center;
        }

        .luxury-help-text {
            font-family: var(--font-luxury);
            font-size: 0.8rem;
            color: #64748B;
            text-align: center;
            margin-top: 18px;
            line-height: 1.4;
            transition: color 0.2s ease;
        }
        .luxury-help-text span {
            color: #8F9CAE;
            text-decoration: underline;
            text-underline-offset: 2px;
            cursor: pointer;
            transition: color 0.2s ease;
        }
        .luxury-help-text span:hover {
            color: #38BDF8;
        }

        /* Styling ottimizzato per Streamlit Custom Components (iOS Keypad) */
        div[data-testid="stCustomComponentV1"] {
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            width: 100% !important;
            margin: 0 auto !important;
            padding: 0 !important;
            border: none !important;
            background: transparent !important;
        }
        div[data-testid="stCustomComponentV1"] iframe {
            border: none !important;
            background: transparent !important;
            width: 100% !important;
            max-width: 420px !important;
            margin: 0 auto !important;
            display: block !important;
        }
    </style>
    """
    render_html(theme_css.replace("__UCL_BG_RULE__", bg_css_rule))


# ==============================================================================
# 2. SCHEDA GIOCATORE: FUT ULTIMATE TEAM 3D CARD (MOBILE-FIRST)
# ==============================================================================
def render_fut_card(
    player_name: str,
    fifa_stats: Dict[str, Any],
    is_cerchia: bool = False
) -> None:
    """
    Renderizza una card in stile EA Sports FC / FIFA Ultimate Team.
    Layout mobile-first responsive con Overall Rating (OVR) grande, Badge Cerchia ⭐,
    e la griglia dei 6 attributi chiave (VIT, GOL, MVP, VAL, ELO, AFF).
    """
    ovr = fifa_stats.get("ovr", 75)
    elo_val = fifa_stats.get("elo", 1500.0)
    attrs = fifa_stats.get("attributes", {})
    pg = fifa_stats.get("pg", 0)
    gol = fifa_stats.get("gol_totali", 0)
    mvp = fifa_stats.get("titoli_mvp", 0)
    media_voto = fifa_stats.get("media_voto")

    vit_val = attrs.get("VIT", 70)
    gol_val = attrs.get("GOL", 70)
    mvp_val = attrs.get("MVP", 70)
    val_val = attrs.get("VAL", 70)
    elo_stat = attrs.get("ELO", ovr)
    aff_val = attrs.get("AFF", 70)

    cerchia_class = "cerchia" if is_cerchia else ""
    role_badge_text = "⭐ CERCHIA RISTRETTA" if is_cerchia else "CALCETTO PLAYER"
    badge_color = "#FFD700" if is_cerchia else "#00E5FF"
    badge_bg = "rgba(255, 215, 0, 0.18)" if is_cerchia else "rgba(0, 229, 255, 0.15)"
    badge_border = "rgba(255, 215, 0, 0.5)" if is_cerchia else "rgba(0, 229, 255, 0.4)"
    avatar_border = "rgba(255, 215, 0, 0.6)" if is_cerchia else "rgba(0, 229, 255, 0.5)"

    card_html = f"""
    <div class="fut-card-wrapper">
        <div class="fut-card {cerchia_class}">
            <!-- Background Decorative Watermark -->
            <div class="fut-card-watermark"></div>

            <!-- Top Header: OVR + Position / Status -->
            <div class="fut-card-header">
                <div>
                    <div class="fut-ovr-num">{ovr}</div>
                    <div class="fut-ovr-label" style="color: {badge_color};">
                        OVR • FUT CARD
                    </div>
                </div>
                <div style="text-align: right;">
                    <span style="
                        display: inline-block;
                        background: {badge_bg};
                        border: 1px solid {badge_border};
                        color: {badge_color};
                        font-size: 0.68rem;
                        font-weight: 800;
                        padding: 3px 8px;
                        border-radius: 12px;
                        letter-spacing: 0.5px;
                    ">
                        {role_badge_text}
                    </span>
                    <div style="font-size: 0.75rem; color: #94A3B8; margin-top: 4px;">
                        ⚡ ELO: <b>{elo_val:.1f}</b>
                    </div>
                </div>
            </div>

            <!-- Avatar Silhouette / Player Emblem -->
            <div style="text-align: center; margin: 10px 0 8px 0;">
                <div style="
                    width: 72px;
                    height: 72px;
                    margin: 0 auto;
                    border-radius: 50%;
                    background: linear-gradient(135deg, rgba(255, 255, 255, 0.15) 0%, rgba(255, 255, 255, 0.03) 100%);
                    border: 2px solid {avatar_border};
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 2rem;
                    box-shadow: 0 6px 18px rgba(0,0,0,0.4);
                ">
                    ⚽
                </div>
            </div>

            <!-- Player Name -->
            <div class="fut-player-name" title="{player_name}">
                {player_name}
            </div>

            <!-- 6 FIFA Attributes Grid (2 Columns x 3 Rows) -->
            <div class="fut-attrs-grid">
                <div class="fut-attr-item">
                    <span class="fut-attr-val" style="color: #00E676;">{vit_val}</span>
                    <span class="fut-attr-lbl">VIT (% Vitt.)</span>
                </div>
                <div class="fut-attr-item">
                    <span class="fut-attr-val" style="color: #FF3D71;">{gol_val}</span>
                    <span class="fut-attr-lbl">GOL (Marc.)</span>
                </div>
                <div class="fut-attr-item">
                    <span class="fut-attr-val" style="color: #FFD700;">{mvp_val}</span>
                    <span class="fut-attr-lbl">MVP (Decis.)</span>
                </div>
                <div class="fut-attr-item">
                    <span class="fut-attr-val" style="color: #00E5FF;">{val_val}</span>
                    <span class="fut-attr-lbl">VAL (Voto)</span>
                </div>
                <div class="fut-attr-item">
                    <span class="fut-attr-val" style="color: #C084FC;">{elo_stat}</span>
                    <span class="fut-attr-lbl">ELO (Indice)</span>
                </div>
                <div class="fut-attr-item">
                    <span class="fut-attr-val" style="color: #38BDF8;">{aff_val}</span>
                    <span class="fut-attr-lbl">AFF (Pres.)</span>
                </div>
            </div>

            <!-- Card Bottom Bar: Summary Stats -->
            <div class="fut-summary-bar">
                <span>Partite: <b style="color: #FFFFFF;">{pg}</b></span>
                <span>Gol: <b style="color: #FFFFFF;">{gol}</b></span>
                <span>MVP: <b style="color: #FFD700;">{mvp}</b></span>
                <span>Media: <b style="color: #00E676;">{f'{media_voto:.2f}' if media_voto else 'N/D'}</b></span>
            </div>
        </div>
    </div>
    """
    render_html(card_html)


# ==============================================================================
# 3. GRAFICO RADAR / SPIDER CHART INTERATTIVO (PLOTLY RESPONSIVE)
# ==============================================================================
def render_player_radar_chart(
    player_name: str,
    radar_data: Dict[str, Any]
) -> None:
    """
    Renderizza uno Spider / Radar Chart Plotly interattivo a tema scuro fluo.
    Confronta i parametri del giocatore con la media complessiva del gruppo.
    """
    categories = radar_data.get("categories", [])
    player_values = radar_data.get("player_values", [])
    avg_values = radar_data.get("avg_values", [])

    if not categories or not player_values:
        st.info("Dati insufficienti per generare il grafico radar.")
        return

    # Chiusura del poligono (ripetizione primo punto)
    cats_closed = categories + [categories[0]]
    player_closed = player_values + [player_values[0]]
    avg_closed = avg_values + [avg_values[0]]

    fig = go.Figure()

    # Serie Benchmark Media Gruppo
    fig.add_trace(go.Scatterpolar(
        r=avg_closed,
        theta=cats_closed,
        fill='toself',
        fillcolor='rgba(148, 163, 184, 0.12)',
        line=dict(color='rgba(255, 215, 0, 0.75)', width=2, dash='dot'),
        name='Media Gruppo',
        hoverinfo='r+name'
    ))

    # Serie Giocatore Selezionato
    fig.add_trace(go.Scatterpolar(
        r=player_closed,
        theta=cats_closed,
        fill='toself',
        fillcolor='rgba(0, 229, 255, 0.22)',
        line=dict(color='#00E5FF', width=3),
        name=player_name,
        hoverinfo='r+name'
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[40, 100],
                showticklabels=True,
                tickfont=dict(size=10, color='#64748B'),
                gridcolor='rgba(255, 255, 255, 0.08)',
                linecolor='rgba(255, 255, 255, 0.08)'
            ),
            angularaxis=dict(
                tickfont=dict(size=11, color='#F8FAFC', family='Outfit'),
                gridcolor='rgba(255, 255, 255, 0.08)',
                linecolor='rgba(255, 255, 255, 0.08)'
            ),
            bgcolor='rgba(15, 23, 42, 0.5)'
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.22,
            xanchor="center",
            x=0.5,
            font=dict(color='#94A3B8', size=11, family='Inter')
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=25, r=25, t=25, b=30),
        height=360
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ==============================================================================
# 4. CAMPO DA CALCIO 2D TATTICO (FORMAZIONI 5 VS 5 - RESPONSIVE 16:10)
# ==============================================================================
def render_tactical_pitch(
    team_a: List[str],
    team_b: List[str],
    elo_ratings: Dict[str, float],
    match_info: Optional[Dict[str, Any]] = None
) -> None:
    """
    Renderizza un campo da calcio 2D vettoriale/CSS fluido e responsive (aspect-ratio: 16/10).
    Posiziona graficamente i titolari di Squadra A e Squadra B con OVR e nomi scalabili.
    """
    from logic import elo_to_fifa_ovr

    # Calcolo medie ELO
    sum_a = sum(elo_ratings.get(p, 1500.0) for p in team_a)
    sum_b = sum(elo_ratings.get(p, 1500.0) for p in team_b)
    avg_a = sum_a / len(team_a) if team_a else 1500.0
    avg_b = sum_b / len(team_b) if team_b else 1500.0
    diff_elo = abs(sum_a - sum_b)

    # Posizioni tattiche (x%, y% sul campo) per formazioni 1-2-1
    pos_a = [
        {"x": 10, "y": 50, "role": "POR"},
        {"x": 23, "y": 26, "role": "DIF"},
        {"x": 23, "y": 74, "role": "DIF"},
        {"x": 35, "y": 50, "role": "CEN"},
        {"x": 45, "y": 50, "role": "ATT"}
    ]

    pos_b = [
        {"x": 90, "y": 50, "role": "POR"},
        {"x": 77, "y": 26, "role": "DIF"},
        {"x": 77, "y": 74, "role": "DIF"},
        {"x": 65, "y": 50, "role": "CEN"},
        {"x": 55, "y": 50, "role": "ATT"}
    ]

    # Generazione nodi giocatori Squadra A
    nodes_a_html = ""
    for idx, player in enumerate(team_a[:5]):
        p_elo = elo_ratings.get(player, 1500.0)
        p_ovr = elo_to_fifa_ovr(p_elo)
        coords = pos_a[idx] if idx < len(pos_a) else {"x": 20, "y": 50, "role": "CEN"}
        
        nodes_a_html += f"""
        <div style="
            position: absolute;
            left: {coords['x']}%;
            top: {coords['y']}%;
            transform: translate(-50%, -50%);
            display: flex;
            flex-direction: column;
            align-items: center;
            z-index: 10;
            pointer-events: none;
        ">
            <div style="
                width: clamp(26px, 5.5vw, 36px);
                height: clamp(26px, 5.5vw, 36px);
                border-radius: 50%;
                background: linear-gradient(135deg, #FFD700 0%, #FF9100 100%);
                border: 2px solid #FFFFFF;
                box-shadow: 0 0 10px rgba(255, 215, 0, 0.7);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: clamp(0.72rem, 2vw, 0.85rem);
                font-weight: 900;
                color: #0F172A;
                font-family: 'Teko', sans-serif;
            ">
                {p_ovr}
            </div>
            <div style="
                background: rgba(15, 23, 42, 0.88);
                border: 1px solid rgba(255, 215, 0, 0.4);
                padding: 1px 5px;
                border-radius: 6px;
                font-size: clamp(0.55rem, 1.6vw, 0.68rem);
                font-weight: 700;
                color: #FFFFFF;
                white-space: nowrap;
                margin-top: 2px;
                max-width: clamp(55px, 12vw, 85px);
                overflow: hidden;
                text-overflow: ellipsis;
                box-shadow: 0 2px 5px rgba(0,0,0,0.5);
                font-family: 'Inter', sans-serif;
                text-align: center;
            " title="{player}">
                {player}
            </div>
        </div>
        """

    # Generazione nodi giocatori Squadra B
    nodes_b_html = ""
    for idx, player in enumerate(team_b[:5]):
        p_elo = elo_ratings.get(player, 1500.0)
        p_ovr = elo_to_fifa_ovr(p_elo)
        coords = pos_b[idx] if idx < len(pos_b) else {"x": 80, "y": 50, "role": "CEN"}
        
        nodes_b_html += f"""
        <div style="
            position: absolute;
            left: {coords['x']}%;
            top: {coords['y']}%;
            transform: translate(-50%, -50%);
            display: flex;
            flex-direction: column;
            align-items: center;
            z-index: 10;
            pointer-events: none;
        ">
            <div style="
                width: clamp(26px, 5.5vw, 36px);
                height: clamp(26px, 5.5vw, 36px);
                border-radius: 50%;
                background: linear-gradient(135deg, #00E5FF 0%, #3B82F6 100%);
                border: 2px solid #FFFFFF;
                box-shadow: 0 0 10px rgba(0, 229, 255, 0.7);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: clamp(0.72rem, 2vw, 0.85rem);
                font-weight: 900;
                color: #0F172A;
                font-family: 'Teko', sans-serif;
            ">
                {p_ovr}
            </div>
            <div style="
                background: rgba(15, 23, 42, 0.88);
                border: 1px solid rgba(0, 229, 255, 0.4);
                padding: 1px 5px;
                border-radius: 6px;
                font-size: clamp(0.55rem, 1.6vw, 0.68rem);
                font-weight: 700;
                color: #FFFFFF;
                white-space: nowrap;
                margin-top: 2px;
                max-width: clamp(55px, 12vw, 85px);
                overflow: hidden;
                text-overflow: ellipsis;
                box-shadow: 0 2px 5px rgba(0,0,0,0.5);
                font-family: 'Inter', sans-serif;
                text-align: center;
            " title="{player}">
                {player}
            </div>
        </div>
        """

    pitch_html = f"""
    <div style="width: 100%; max-width: 600px; margin: 1.2rem auto; box-sizing: border-box;">
        <!-- Header Squadre Confronto -->
        <div class="pitch-header" style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(18, 24, 36, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px 14px 0 0;
            padding: 10px 14px;
            font-family: 'Outfit', sans-serif;
            gap: 6px;
        ">
            <div class="pitch-team-badge" style="color: #FFD700; font-weight: 800; font-size: clamp(0.8rem, 2vw, 0.95rem); display: flex; align-items: center; gap: 6px;">
                <span>🟨 SQUADRA A</span>
                <span style="font-size: 0.74rem; color: #94A3B8; font-weight: 500;">(ELO: <b>{avg_a:.1f}</b>)</span>
            </div>
            <div class="pitch-delta-badge" style="
                background: rgba(0, 230, 118, 0.15);
                border: 1px solid rgba(0, 230, 118, 0.4);
                color: #00E676;
                font-size: 0.72rem;
                font-weight: 800;
                padding: 3px 10px;
                border-radius: 20px;
                white-space: nowrap;
            ">
                ⚖️ DELTA: {diff_elo:.1f} pt
            </div>
            <div class="pitch-team-badge" style="color: #00E5FF; font-weight: 800; font-size: clamp(0.8rem, 2vw, 0.95rem); display: flex; align-items: center; gap: 6px;">
                <span style="font-size: 0.74rem; color: #94A3B8; font-weight: 500;">(ELO: <b>{avg_b:.1f}</b>)</span>
                <span>🟦 SQUADRA B</span>
            </div>
        </div>

        <!-- 2D Tactical Field Canvas (Fluid Aspect Ratio 16/10) -->
        <div style="
            position: relative;
            width: 100%;
            aspect-ratio: 16 / 10;
            min-height: 270px;
            background: linear-gradient(180deg, #103B2B 0%, #0D2E22 100%);
            background-image: repeating-linear-gradient(90deg, rgba(255,255,255,0.02) 0px, rgba(255,255,255,0.02) 40px, transparent 40px, transparent 80px);
            border-left: 1px solid rgba(255, 255, 255, 0.08);
            border-right: 1px solid rgba(255, 255, 255, 0.08);
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 0 0 14px 14px;
            overflow: hidden;
            box-shadow: 0 12px 30px rgba(0,0,0,0.5), inset 0 0 40px rgba(0,0,0,0.6);
            box-sizing: border-box;
        ">
            <!-- Perimeter White Line -->
            <div style="position: absolute; top: 10px; bottom: 10px; left: 10px; right: 10px; border: 2px solid rgba(255,255,255,0.45); border-radius: 4px;"></div>

            <!-- Halfway Line -->
            <div style="position: absolute; top: 10px; bottom: 10px; left: 50%; width: 2px; background: rgba(255,255,255,0.45); transform: translateX(-50%);"></div>

            <!-- Center Circle -->
            <div style="
                position: absolute;
                top: 50%;
                left: 50%;
                width: clamp(60px, 14vw, 84px);
                height: clamp(60px, 14vw, 84px);
                border: 2px solid rgba(255,255,255,0.45);
                border-radius: 50%;
                transform: translate(-50%, -50%);
            "></div>
            <!-- Center Spot -->
            <div style="
                position: absolute;
                top: 50%;
                left: 50%;
                width: 6px;
                height: 6px;
                background: rgba(255,255,255,0.8);
                border-radius: 50%;
                transform: translate(-50%, -50%);
            "></div>

            <!-- Penalty Area Left -->
            <div style="
                position: absolute;
                top: 25%;
                bottom: 25%;
                left: 10px;
                width: clamp(45px, 12vw, 75px);
                border: 2px solid rgba(255,255,255,0.45);
                border-left: none;
            "></div>

            <!-- Penalty Area Right -->
            <div style="
                position: absolute;
                top: 25%;
                bottom: 25%;
                right: 10px;
                width: clamp(45px, 12vw, 75px);
                border: 2px solid rgba(255,255,255,0.45);
                border-right: none;
            "></div>

            <!-- Goal Box Left -->
            <div style="
                position: absolute;
                top: 38%;
                bottom: 38%;
                left: 10px;
                width: clamp(20px, 5vw, 32px);
                border: 2px solid rgba(255,255,255,0.4);
                border-left: none;
            "></div>

            <!-- Goal Box Right -->
            <div style="
                position: absolute;
                top: 38%;
                bottom: 38%;
                right: 10px;
                width: clamp(20px, 5vw, 32px);
                border: 2px solid rgba(255,255,255,0.4);
                border-right: none;
            "></div>

            <!-- Players Nodes -->
            {nodes_a_html}
            {nodes_b_html}
        </div>
    </div>
    """
    render_html(pitch_html)


# ==============================================================================
# 5. TABELLONE PARTITE STILE CHAMPIONS LEAGUE (MOBILE-FIRST SCOREBOARD CARD)
# ==============================================================================
def render_champions_scoreboard(
    match_row: pd.Series,
    mvp_name: Optional[str] = None,
    mvp_avg: Optional[float] = None
) -> None:
    """
    Renderizza una Match Scoreboard Card di altissimo livello grafico (stile UEFA Champions League / SofaScore).
    Completamente responsive per smartphone con grid fluida e formazioni/marcatori adattabili.
    """
    from logic import parse_marcatori

    id_p = match_row.get("id_partita", 1)
    data_str = match_row.get("data", "N/D")
    gol_a = match_row.get("gol_squadra_a", 0)
    gol_b = match_row.get("gol_squadra_b", 0)
    esito = match_row.get("esito", "")
    sq_a = [p.strip() for p in str(match_row.get("squadra_a_giocatori", "")).split(",") if p.strip()]
    sq_b = [p.strip() for p in str(match_row.get("squadra_b_giocatori", "")).split(",") if p.strip()]

    marcatori_dict = parse_marcatori(match_row.get("marcatori", ""))

    # Esito Badge Styling
    if "Squadra A" in esito:
        badge_border = "#FFD700"
        badge_bg = "rgba(255, 215, 0, 0.15)"
        badge_color = "#FFD700"
    elif "Squadra B" in esito:
        badge_border = "#00E5FF"
        badge_bg = "rgba(0, 229, 255, 0.15)"
        badge_color = "#00E5FF"
    else:
        badge_border = "#94A3B8"
        badge_bg = "rgba(148, 163, 184, 0.15)"
        badge_color = "#E2E8F0"

    # MVP Badge
    mvp_section_html = ""
    if mvp_name:
        mvp_score_text = f" (⭐ {mvp_avg:.2f})" if mvp_avg else ""
        mvp_section_html = f"""
        <div style="
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: linear-gradient(135deg, rgba(255, 215, 0, 0.15) 0%, rgba(217, 119, 6, 0.25) 100%);
            border: 1px solid rgba(255, 215, 0, 0.5);
            color: #FFD700;
            font-size: 0.78rem;
            font-weight: 800;
            padding: 4px 12px;
            border-radius: 20px;
            box-shadow: 0 2px 10px rgba(255, 215, 0, 0.25);
            margin-top: 4px;
        ">
            👑 MVP DEL MATCH: <b>{mvp_name}</b>{mvp_score_text}
        </div>
        """

    # Marcatori Formattati
    marcatori_badges = []
    if marcatori_dict:
        for p, g in marcatori_dict.items():
            marcatori_badges.append(f"<span style='background: rgba(255,255,255,0.06); padding: 3px 8px; border-radius: 6px; margin: 2px 3px; display: inline-block; font-size: 0.78rem; color: #F1F5F9;'>⚽ <b>{p}</b> ({g})</span>")
        marcatori_html = " ".join(marcatori_badges)
    else:
        marcatori_html = "<span style='color: #64748B; font-size: 0.78rem;'>Nessun marcatore individuale registrato per questa partita.</span>"

    card_html = f"""
    <div class="glass-card" style="padding: clamp(14px, 3vw, 20px); margin-bottom: 1.3rem;">
        <!-- Top Match Info Bar -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
            <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                <span style="background: rgba(255,255,255,0.08); color: #94A3B8; font-size: 0.72rem; font-weight: 800; padding: 3px 8px; border-radius: 8px; text-transform: uppercase; letter-spacing: 0.5px;">
                    MATCH #{id_p}
                </span>
                <span style="color: #94A3B8; font-size: 0.82rem; font-weight: 500;">
                    🗓️ <b>{data_str}</b>
                </span>
            </div>
            <div style="
                background: {badge_bg};
                border: 1px solid {badge_border};
                color: {badge_color};
                font-size: 0.75rem;
                font-weight: 800;
                padding: 3px 10px;
                border-radius: 20px;
                letter-spacing: 0.5px;
            ">
                {esito}
            </div>
        </div>

        <!-- Champions League Centered Scoreboard (Responsive Grid) -->
        <div class="scoreboard-score-grid" style="
            display: grid;
            grid-template-columns: 1fr auto 1fr;
            align-items: center;
            gap: 12px;
            padding: 12px 14px;
            background: rgba(11, 14, 20, 0.6);
            border-radius: 14px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            margin-bottom: 12px;
        ">
            <!-- Team A Left -->
            <div class="score-team" style="text-align: right;">
                <div style="font-size: clamp(0.95rem, 2.5vw, 1.15rem); font-weight: 800; color: #FFD700; letter-spacing: 0.5px;">
                    SQUADRA A 🟨
                </div>
            </div>

            <!-- Score Pill Center -->
            <div class="score-pill" style="
                background: #0B0E14;
                border: 1px solid rgba(255, 255, 255, 0.15);
                padding: 4px 18px;
                border-radius: 12px;
                font-size: clamp(1.4rem, 4vw, 1.8rem);
                font-weight: 900;
                color: #FFFFFF;
                font-family: 'Teko', sans-serif;
                letter-spacing: 2px;
                text-align: center;
                box-shadow: inset 0 2px 8px rgba(0,0,0,0.8);
            ">
                {gol_a} - {gol_b}
            </div>

            <!-- Team B Right -->
            <div class="score-team" style="text-align: left;">
                <div style="font-size: clamp(0.95rem, 2.5vw, 1.15rem); font-weight: 800; color: #00E5FF; letter-spacing: 0.5px;">
                    🟦 SQUADRA B
                </div>
            </div>
        </div>

        <!-- MVP Highlight (if available) -->
        <div style="text-align: center; margin-bottom: 10px;">
            {mvp_section_html}
        </div>

        <!-- Formations Breakdown -->
        <div class="scoreboard-formations" style="
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            padding: 10px 12px;
            background: rgba(255, 255, 255, 0.02);
            border-radius: 10px;
            font-size: 0.8rem;
            color: #CBD5E1;
            font-family: 'Inter', sans-serif;
        ">
            <div>
                <span style="color: #FFD700; font-weight: 700;">🟨 Titolari A:</span><br>
                {', '.join(sq_a)}
            </div>
            <div>
                <span style="color: #00E5FF; font-weight: 700;">🟦 Titolari B:</span><br>
                {', '.join(sq_b)}
            </div>
        </div>

        <!-- Goalscorers Footer -->
        <div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid rgba(255, 255, 255, 0.06);">
            <div style="font-size: 0.74rem; font-weight: 700; color: #94A3B8; margin-bottom: 4px; text-transform: uppercase;">
                🎯 Marcatori dell'Incontro:
            </div>
            {marcatori_html}
        </div>
    </div>
    """
    render_html(card_html)


# ==============================================================================
# 6. SCHERMATA LOGIN & PASSCODE: IOS LOCKSCREEN KEYPAD (APPLE PASSCODE UI)
# ==============================================================================
_STARBALL_BASE64_CACHE: Optional[str] = None
_UCL_BG_BASE64_CACHE: Optional[str] = None


def get_ucl_background_base64() -> str:
    """
    Recupera l'immagine di sfondo UEFA Champions League (ucl_bg.*) e la codifica in Data URI Base64.
    Utilizza una cache in memoria per evitare letture disco ripetute.
    """
    global _UCL_BG_BASE64_CACHE
    if _UCL_BG_BASE64_CACHE is not None:
        return _UCL_BG_BASE64_CACHE

    for ext in ["png", "jpg", "jpeg", "webp"]:
        p = Path(__file__).parent / f"assets/ucl_bg.{ext}"
        if p.exists():
            with open(p, "rb") as f:
                mime_type = "jpeg" if ext == "jpg" else ext
                _UCL_BG_BASE64_CACHE = f"data:image/{mime_type};base64,{base64.b64encode(f.read()).decode()}"
                return _UCL_BG_BASE64_CACHE
    
    _UCL_BG_BASE64_CACHE = ""
    return _UCL_BG_BASE64_CACHE


def get_starball_base64() -> str:
    """
    Recupera l'immagine UEFA Champions League Starball (ucl_ball.*) e la codifica in Data URI Base64.
    Utilizza una cache in memoria per evitare letture disco ripetute.
    Se il file non esiste, restituisce un fallback vettoriale SVG 3D.
    """
    global _STARBALL_BASE64_CACHE
    if _STARBALL_BASE64_CACHE is not None:
        return _STARBALL_BASE64_CACHE

    for ext in ["png", "jpg", "jpeg", "webp"]:
        p = Path(__file__).parent / f"assets/ucl_ball.{ext}"
        if p.exists():
            with open(p, "rb") as f:
                mime_type = "jpeg" if ext == "jpg" else ext
                _STARBALL_BASE64_CACHE = f"data:image/{mime_type};base64,{base64.b64encode(f.read()).decode()}"
                return _STARBALL_BASE64_CACHE
    
    # Fallback SVG inline
    starball_raw_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="200" height="200">
      <defs>
        <radialGradient id="sphere" cx="35%" cy="30%" r="70%">
          <stop offset="0%" stop-color="#253550" /><stop offset="35%" stop-color="#121C2B" /><stop offset="75%" stop-color="#080E18" /><stop offset="100%" stop-color="#020408" />
        </radialGradient>
        <linearGradient id="star" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="#FFFFFF" /><stop offset="40%" stop-color="#F8FAFC" /><stop offset="75%" stop-color="#CBD5E1" /><stop offset="100%" stop-color="#94A3B8" />
        </linearGradient>
        <radialGradient id="rim" cx="50%" cy="50%" r="50%">
          <stop offset="85%" stop-color="transparent" /><stop offset="100%" stop-color="rgba(0,0,0,0.85)" />
        </radialGradient>
        <linearGradient id="spec" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stop-color="#FFFFFF" stop-opacity="0.6" /><stop offset="100%" stop-color="#FFFFFF" stop-opacity="0" />
        </linearGradient>
      </defs>
      <circle cx="100" cy="100" r="90" fill="url(#sphere)" stroke="rgba(255,255,255,0.22)" stroke-width="2" />
      <g fill="url(#star)" stroke="#060910" stroke-width="1.8" stroke-linejoin="round">
        <polygon points="100,55 110,78 135,78 115,93 122,118 100,103 78,118 85,93 65,78 90,78" />
        <polygon points="100,14 108,34 130,29 118,47 133,62 112,57 100,74 88,57 67,62 82,47 70,29 92,34" />
        <polygon points="163,40 160,60 180,68 162,82 168,102 148,88 135,102 133,80 113,73 132,62" />
        <polygon points="173,120 153,120 145,138 138,120 118,127 130,108 122,90 140,95 152,80 155,100" />
        <polygon points="100,186 92,166 70,171 82,153 67,138 88,143 100,126 112,143 133,138 118,153 130,171 108,166" />
        <polygon points="27,160 47,160 55,142 62,160 82,153 70,172 78,190 60,185 48,200 45,180" />
        <polygon points="37,80 57,80 65,62 72,80 92,73 80,92 88,110 70,105 58,120 55,100" />
        <polygon points="37,40 57,53 57,73 38,67 20,80 25,60 10,47 30,47 37,27 43,47" />
      </g>
      <circle cx="100" cy="100" r="90" fill="url(#rim)" />
      <path d="M 46 56 A 76 76 0 0 1 154 56" stroke="url(#spec)" stroke-width="3" stroke-linecap="round" fill="none" />
    </svg>"""
    _STARBALL_BASE64_CACHE = f"data:image/svg+xml;base64,{base64.b64encode(starball_raw_svg.strip().encode('utf-8')).decode('ascii')}"
    return _STARBALL_BASE64_CACHE


# Registrazione Custom Component iOS Keypad
_COMPONENT_KEYPAD_PATH = Path(__file__).parent / "assets" / "ios_keypad"
_ios_keypad_component = components.declare_component(
    "ios_pin_keypad",
    path=str(_COMPONENT_KEYPAD_PATH)
)


def render_ios_pin_keypad(
    admin_pin: str = "8765",
    viewer_pin: str = "5678",
    title: str = "Inserisci il codice PIN",
    subtitle: str = "4 digit code per sbloccare l'applicazione",
    storage_source: str = "Google Sheets (Cloud)",
    key: str = "ios_lockscreen_keypad"
) -> Optional[str]:
    """
    Renderizza il Tastierino Numerico interattivo in stile Apple iOS Lockscreen (Passcode UI).
    
    Elementi & Comportamento:
    1. Header con icona 3D UEFA Champions League Starball e bagliore azzurro.
    2. Titolo & Sottotitolo descrittivo.
    3. 4 Cerchietti Indicatori con animazione di riempimento al tap e Shake Effect in caso di errore.
    4. Tastierino circolare 3x4 in Dark Glassmorphism con lettere subordinate Apple (2 ABC, 3 DEF...).
    5. Tasto dinamico Cancella / Indietro (⌫).
    6. Indicatore di persistenza discreto integrato nel footer della card.
    7. Supporto Touch mobile 100% (nessuna tastiera a comparsa), click desktop e tastiera fisica PC.
    8. Validazione istantanea alla 4ª cifra con invio a Streamlit.
    """
    starball_src = get_starball_base64()
    
    val = _ios_keypad_component(
        admin_pin=admin_pin,
        viewer_pin=viewer_pin,
        title=title,
        subtitle=subtitle,
        starball_src=starball_src,
        storage_source=storage_source,
        default="",
        key=key
    )
    return str(val).strip() if val else None


def render_luxury_pin_header(
    title: str = "4 digit code",
    subtitle: str = "Inserisci il codice PIN di accesso a 4 cifre<br>per sbloccare statistiche e formazioni"
) -> None:
    """Header di compatibilità legacy."""
    starball_src = get_starball_base64()
    header_html = f"""
    <div id="luxury-pin-marker"></div>
    <div class="starball-glow-container">
        <img class="starball-img" src="{starball_src}" alt="UEFA Champions League Starball" />
    </div>
    <h2 class="luxury-login-title">{title}</h2>
    <p class="luxury-login-subtitle">{subtitle}</p>
    """
    render_html(header_html)


def render_luxury_pin_footer() -> None:
    """Footer di compatibilità legacy vuoto (non visualizza messaggi di supporto)."""
    pass


def render_luxury_pin_error(message: str = "Passcode non valido") -> None:
    """Badge di errore di compatibilità legacy."""
    error_html = f"""
    <div class="luxury-error-pill">
        <span>⚠️ {message}</span>
    </div>
    """
    render_html(error_html)





