"""
================================================================================
UI_COMPONENTS.PY - Presentation Layer & Design System
Stile: EA Sports FC / SofaScore / Dark Modern Stadium & Glassmorphism
Componenti: Theme Injection, FUT Card, Plotly Radar Chart, 2D Pitch, Scoreboard
================================================================================
"""

import json
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import streamlit as st
import plotly.graph_objects as go


# ==============================================================================
# 1. DESIGN SYSTEM GLOBALE: DARK STADIUM & GLASSMORPHISM
# ==============================================================================
def inject_custom_theme() -> None:
    """
    Inietta il Design System globale in stile Dark Modern Stadium & Glassmorphism.
    Importa font Google (Outfit, Inter, Teko) e applica la palette scura profonda
    con accenti neon (Smeraldo, Oro MVP, Cyan ELO, Rosso Fuoco).
    """
    st.markdown("""
    <style>
        /* Import Font Google */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@400;500;600;700;800;900&family=Teko:wght@600;700&display=swap');

        /* Root Variables */
        :root {
            --bg-dark-core: #0B0E14;
            --bg-stadium-card: rgba(18, 24, 36, 0.75);
            --bg-glass-card: rgba(22, 30, 46, 0.65);
            --border-glass: rgba(255, 255, 255, 0.09);
            --border-glass-glow: rgba(0, 229, 255, 0.25);
            --neon-emerald: #00E676;
            --neon-gold: #FFD700;
            --neon-cyan: #00E5FF;
            --neon-red: #FF3D71;
            --text-main: #F8FAFC;
            --text-muted: #94A3B8;
            --text-sub: #64748B;
            --font-display: 'Outfit', sans-serif;
            --font-body: 'Inter', sans-serif;
            --font-stat: 'Teko', sans-serif;
        }

        /* Typography & Body Overrides */
        html, body, [class*="st-"] {
            font-family: var(--font-body);
            color: var(--text-main);
        }

        h1, h2, h3, h4, .stTitle, .main-title {
            font-family: var(--font-display) !important;
            font-weight: 800 !important;
            letter-spacing: -0.5px;
        }

        /* Titoli e Header Sezioni */
        .main-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1rem;
            flex-wrap: wrap;
            gap: 12px;
        }
        .main-title {
            font-size: 2.1rem;
            font-weight: 900;
            background: linear-gradient(135deg, #00E676 0%, #00E5FF 50%, #FFD700 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.15rem;
            text-shadow: 0 0 30px rgba(0, 230, 118, 0.25);
        }
        .sub-title {
            font-size: 0.95rem;
            color: var(--text-muted);
            margin-bottom: 1.4rem;
            font-weight: 400;
        }

        /* Ruolo & Badges */
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

        /* Glassmorphism Card Container */
        .glass-card {
            background: var(--bg-glass-card);
            backdrop-filter: blur(14px);
            -webkit-backdrop-filter: blur(14px);
            border: 1px solid var(--border-glass);
            border-radius: 16px;
            padding: 1.3rem;
            margin-bottom: 1.2rem;
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.35);
            transition: transform 0.25s ease, border-color 0.25s ease, box-shadow 0.25s ease;
        }
        .glass-card:hover {
            border-color: rgba(255, 255, 255, 0.18);
            box-shadow: 0 12px 36px 0 rgba(0, 0, 0, 0.45);
        }

        /* Badge Esito & Forma */
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
            box-shadow: 0 2px 8px rgba(255, 61, 113, 0.4);
        }

        /* Streamlit Button Restyling */
        .stButton>button {
            border-radius: 12px !important;
            font-weight: 700 !important;
            font-family: var(--font-display) !important;
            letter-spacing: 0.3px;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
            border: 1px solid rgba(255, 255, 255, 0.1) !important;
            background: rgba(30, 41, 59, 0.8) !important;
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

        /* Streamlit Metrics */
        div[data-testid="stMetric"] {
            background: rgba(22, 30, 46, 0.6);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.07);
            border-radius: 14px;
            padding: 0.9rem 1.1rem;
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
        }

        /* Tabs Styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            padding-bottom: 6px;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 10px 10px 0 0;
            padding: 8px 18px;
            font-family: var(--font-display);
            font-weight: 600;
            color: var(--text-muted);
            background: transparent;
            transition: all 0.2s ease;
        }
        .stTabs [aria-selected="true"] {
            color: var(--neon-emerald) !important;
            border-bottom: 2px solid var(--neon-emerald) !important;
            background: rgba(0, 230, 118, 0.06) !important;
        }
    </style>
    """, unsafe_allow_html=True)


# ==============================================================================
# 2. SCHEDA GIOCATORE: FUT ULTIMATE TEAM 3D CARD
# ==============================================================================
def render_fut_card(
    player_name: str,
    fifa_stats: Dict[str, Any],
    is_cerchia: bool = False
) -> None:
    """
    Renderizza una card 3D in stile EA Sports FC / FIFA Ultimate Team.
    Include Overall Rating (OVR) grande derivato dall'ELO, Badge Cerchia ⭐,
    e la griglia dei 6 attributi chiave (VIT, GOL, MVP, VAL, ELO, AFF).
    """
    ovr = fifa_stats.get("ovr", 75)
    elo_val = fifa_stats.get("elo", 1500.0)
    attrs = fifa_stats.get("attributes", {})
    forma = fifa_stats.get("forma", [])
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

    role_badge_text = "⭐ CERCHIA RISTRETTA" if is_cerchia else "CALCETTO PLAYER"
    card_border_glow = "rgba(255, 215, 0, 0.45)" if is_cerchia else "rgba(0, 229, 255, 0.35)"
    card_top_grad = "linear-gradient(180deg, rgba(255, 215, 0, 0.25) 0%, rgba(18, 24, 38, 0.95) 70%)" if is_cerchia else "linear-gradient(180deg, rgba(0, 229, 255, 0.2) 0%, rgba(18, 24, 38, 0.95) 70%)"

    card_html = f"""
    <div style="display: flex; justify-content: center; margin: 1.5rem 0;">
        <div style="
            width: 320px;
            border-radius: 22px;
            background: #111723;
            background-image: {card_top_grad};
            border: 2px solid {card_border_glow};
            box-shadow: 0 16px 40px rgba(0, 0, 0, 0.6), 0 0 30px {card_border_glow};
            padding: 20px 18px;
            position: relative;
            overflow: hidden;
            font-family: 'Outfit', sans-serif;
            color: #FFFFFF;
            transition: transform 0.3s ease;
        ">
            <!-- Background Decorative Watermark -->
            <div style="
                position: absolute;
                top: -30px;
                right: -30px;
                width: 140px;
                height: 140px;
                background: radial-gradient(circle, rgba(255,255,255,0.12) 0%, rgba(255,255,255,0) 70%);
                border-radius: 50%;
                pointer-events: none;
            "></div>

            <!-- Top Header: OVR + Position / Status -->
            <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px;">
                <div>
                    <div style="font-size: 3.4rem; font-weight: 900; line-height: 0.9; color: #FFFFFF; text-shadow: 0 4px 12px rgba(0,0,0,0.5); font-family: 'Teko', sans-serif; letter-spacing: 1px;">
                        {ovr}
                    </div>
                    <div style="font-size: 0.78rem; font-weight: 800; color: {'#FFD700' if is_cerchia else '#00E5FF'}; text-transform: uppercase; letter-spacing: 1px;">
                        OVR • FUT CARD
                    </div>
                </div>
                <div style="text-align: right;">
                    <span style="
                        display: inline-block;
                        background: {'rgba(255, 215, 0, 0.18)' if is_cerchia else 'rgba(0, 229, 255, 0.15)'};
                        border: 1px solid {'rgba(255, 215, 0, 0.5)' if is_cerchia else 'rgba(0, 229, 255, 0.4)'};
                        color: {'#FFD700' if is_cerchia else '#00E5FF'};
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
            <div style="text-align: center; margin: 12px 0 10px 0;">
                <div style="
                    width: 76px;
                    height: 76px;
                    margin: 0 auto;
                    border-radius: 50%;
                    background: linear-gradient(135deg, rgba(255, 255, 255, 0.15) 0%, rgba(255, 255, 255, 0.03) 100%);
                    border: 2px solid {'rgba(255, 215, 0, 0.6)' if is_cerchia else 'rgba(0, 229, 255, 0.5)'};
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 2.2rem;
                    box-shadow: 0 6px 18px rgba(0,0,0,0.4);
                ">
                    ⚽
                </div>
            </div>

            <!-- Player Name -->
            <div style="
                text-align: center;
                font-size: 1.35rem;
                font-weight: 900;
                text-transform: uppercase;
                letter-spacing: 1px;
                color: #FFFFFF;
                border-bottom: 1px solid rgba(255, 255, 255, 0.12);
                padding-bottom: 8px;
                margin-bottom: 12px;
            ">
                {player_name}
            </div>

            <!-- 6 FIFA Attributes Grid (2 Columns x 3 Rows) -->
            <div style="
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 8px 16px;
                font-family: 'Outfit', sans-serif;
                background: rgba(10, 14, 22, 0.65);
                padding: 10px 14px;
                border-radius: 14px;
                border: 1px solid rgba(255, 255, 255, 0.06);
            ">
                <div style="display: flex; justify-content: space-between; align-items: baseline;">
                    <span style="font-size: 1.25rem; font-weight: 800; color: #00E676; font-family: 'Teko', sans-serif;">{vit_val}</span>
                    <span style="font-size: 0.72rem; font-weight: 700; color: #94A3B8;">VIT (% Vitt.)</span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: baseline;">
                    <span style="font-size: 1.25rem; font-weight: 800; color: #FF3D71; font-family: 'Teko', sans-serif;">{gol_val}</span>
                    <span style="font-size: 0.72rem; font-weight: 700; color: #94A3B8;">GOL (Marc.)</span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: baseline;">
                    <span style="font-size: 1.25rem; font-weight: 800; color: #FFD700; font-family: 'Teko', sans-serif;">{mvp_val}</span>
                    <span style="font-size: 0.72rem; font-weight: 700; color: #94A3B8;">MVP (Decis.)</span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: baseline;">
                    <span style="font-size: 1.25rem; font-weight: 800; color: #00E5FF; font-family: 'Teko', sans-serif;">{val_val}</span>
                    <span style="font-size: 0.72rem; font-weight: 700; color: #94A3B8;">VAL (Voto)</span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: baseline;">
                    <span style="font-size: 1.25rem; font-weight: 800; color: #C084FC; font-family: 'Teko', sans-serif;">{elo_stat}</span>
                    <span style="font-size: 0.72rem; font-weight: 700; color: #94A3B8;">ELO (Indice)</span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: baseline;">
                    <span style="font-size: 1.25rem; font-weight: 800; color: #38BDF8; font-family: 'Teko', sans-serif;">{aff_val}</span>
                    <span style="font-size: 0.72rem; font-weight: 700; color: #94A3B8;">AFF (Pres.)</span>
                </div>
            </div>

            <!-- Card Bottom Bar: Summary Stats -->
            <div style="
                display: flex;
                justify-content: space-around;
                align-items: center;
                margin-top: 12px;
                font-size: 0.74rem;
                color: #94A3B8;
            ">
                <span>Partite: <b style="color: #FFFFFF;">{pg}</b></span>
                <span>Gol: <b style="color: #FFFFFF;">{gol}</b></span>
                <span>MVP: <b style="color: #FFD700;">{mvp}</b></span>
                <span>Media: <b style="color: #00E676;">{f'{media_voto:.2f}' if media_voto else 'N/D'}</b></span>
            </div>
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)


# ==============================================================================
# 3. GRAFICO RADAR / SPIDER CHART INTERATTIVO (PLOTLY)
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
            y=-0.18,
            xanchor="center",
            x=0.5,
            font=dict(color='#94A3B8', size=11, family='Inter')
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=40, r=40, t=30, b=40),
        height=380
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# ==============================================================================
# 4. CAMPO DA CALCIO 2D TATTICO (FORMAZIONI 5 VS 5)
# ==============================================================================
def render_tactical_pitch(
    team_a: List[str],
    team_b: List[str],
    elo_ratings: Dict[str, float],
    match_info: Optional[Dict[str, Any]] = None
) -> None:
    """
    Renderizza un campo da calcio 2D vettoriale/CSS ad alta definizione.
    Posiziona graficamente i 5 titolari di Squadra A (Pettorina Oro/Gialla)
    e i 5 di Squadra B (Pettorina Blu/Crimson) con i rispettivi Overall e nomi.
    """
    from logic import elo_to_fifa_ovr

    # Calcolo medie
    sum_a = sum(elo_ratings.get(p, 1500.0) for p in team_a)
    sum_b = sum(elo_ratings.get(p, 1500.0) for p in team_b)
    avg_a = sum_a / len(team_a) if team_a else 1500.0
    avg_b = sum_b / len(team_b) if team_b else 1500.0
    diff_elo = abs(sum_a - sum_b)

    # Posizioni tattiche (x%, y% sul campo) per formazioni 1-2-1
    # Campo orizzontale 100% larghezza x 100% altezza
    # Squadra A (sinistra -> attacca a destra)
    pos_a = [
        {"x": 10, "y": 50, "role": "POR"},
        {"x": 24, "y": 26, "role": "DIF"},
        {"x": 24, "y": 74, "role": "DIF"},
        {"x": 36, "y": 50, "role": "CEN"},
        {"x": 45, "y": 50, "role": "ATT"}
    ]

    # Squadra B (destra -> attacca a sinistra)
    pos_b = [
        {"x": 90, "y": 50, "role": "POR"},
        {"x": 76, "y": 26, "role": "DIF"},
        {"x": 76, "y": 74, "role": "DIF"},
        {"x": 64, "y": 50, "role": "CEN"},
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
        ">
            <div style="
                width: 38px;
                height: 38px;
                border-radius: 50%;
                background: linear-gradient(135deg, #FFD700 0%, #FF9100 100%);
                border: 2px solid #FFFFFF;
                box-shadow: 0 0 12px rgba(255, 215, 0, 0.7);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 0.85rem;
                font-weight: 900;
                color: #0F172A;
                font-family: 'Teko', sans-serif;
            ">
                {p_ovr}
            </div>
            <div style="
                background: rgba(15, 23, 42, 0.85);
                border: 1px solid rgba(255, 215, 0, 0.4);
                padding: 2px 7px;
                border-radius: 8px;
                font-size: 0.72rem;
                font-weight: 700;
                color: #FFFFFF;
                white-space: nowrap;
                margin-top: 3px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.5);
                font-family: 'Inter', sans-serif;
            ">
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
        ">
            <div style="
                width: 38px;
                height: 38px;
                border-radius: 50%;
                background: linear-gradient(135deg, #00E5FF 0%, #3B82F6 100%);
                border: 2px solid #FFFFFF;
                box-shadow: 0 0 12px rgba(0, 229, 255, 0.7);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 0.85rem;
                font-weight: 900;
                color: #0F172A;
                font-family: 'Teko', sans-serif;
            ">
                {p_ovr}
            </div>
            <div style="
                background: rgba(15, 23, 42, 0.85);
                border: 1px solid rgba(0, 229, 255, 0.4);
                padding: 2px 7px;
                border-radius: 8px;
                font-size: 0.72rem;
                font-weight: 700;
                color: #FFFFFF;
                white-space: nowrap;
                margin-top: 3px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.5);
                font-family: 'Inter', sans-serif;
            ">
                {player}
            </div>
        </div>
        """

    pitch_html = f"""
    <div style="margin: 1.5rem 0;">
        <!-- Header Squadre Confronto -->
        <div style="
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(18, 24, 36, 0.85);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px 14px 0 0;
            padding: 12px 20px;
            font-family: 'Outfit', sans-serif;
        ">
            <div style="color: #FFD700; font-weight: 800; font-size: 1rem; display: flex; align-items: center; gap: 8px;">
                <span>🟨 SQUADRA A</span>
                <span style="font-size: 0.8rem; color: #94A3B8; font-weight: 500;">(ELO Med: <b>{avg_a:.1f}</b>)</span>
            </div>
            <div style="
                background: rgba(0, 230, 118, 0.15);
                border: 1px solid rgba(0, 230, 118, 0.4);
                color: #00E676;
                font-size: 0.75rem;
                font-weight: 800;
                padding: 4px 12px;
                border-radius: 20px;
            ">
                ⚖️ DELTA ELO: {diff_elo:.1f} pt
            </div>
            <div style="color: #00E5FF; font-weight: 800; font-size: 1rem; display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 0.8rem; color: #94A3B8; font-weight: 500;">(ELO Med: <b>{avg_b:.1f}</b>)</span>
                <span>🟦 SQUADRA B</span>
            </div>
        </div>

        <!-- 2D Tactical Field Canvas -->
        <div style="
            position: relative;
            width: 100%;
            height: 380px;
            background: linear-gradient(180deg, #103B2B 0%, #0D2E22 100%);
            background-image: repeating-linear-gradient(90deg, rgba(255,255,255,0.02) 0px, rgba(255,255,255,0.02) 40px, transparent 40px, transparent 80px);
            border-left: 1px solid rgba(255, 255, 255, 0.08);
            border-right: 1px solid rgba(255, 255, 255, 0.08);
            border-bottom: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 0 0 14px 14px;
            overflow: hidden;
            box-shadow: 0 12px 30px rgba(0,0,0,0.5), inset 0 0 40px rgba(0,0,0,0.6);
        ">
            <!-- Perimeter White Line -->
            <div style="position: absolute; top: 12px; bottom: 12px; left: 12px; right: 12px; border: 2px solid rgba(255,255,255,0.45); border-radius: 4px;"></div>

            <!-- Halfway Line -->
            <div style="position: absolute; top: 12px; bottom: 12px; left: 50%; width: 2px; background: rgba(255,255,255,0.45); transform: translateX(-50%);"></div>

            <!-- Center Circle -->
            <div style="
                position: absolute;
                top: 50%;
                left: 50%;
                width: 90px;
                height: 90px;
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
                left: 12px;
                width: 80px;
                border: 2px solid rgba(255,255,255,0.45);
                border-left: none;
            "></div>

            <!-- Penalty Area Right -->
            <div style="
                position: absolute;
                top: 25%;
                bottom: 25%;
                right: 12px;
                width: 80px;
                border: 2px solid rgba(255,255,255,0.45);
                border-right: none;
            "></div>

            <!-- Goal Box Left -->
            <div style="
                position: absolute;
                top: 38%;
                bottom: 38%;
                left: 12px;
                width: 35px;
                border: 2px solid rgba(255,255,255,0.4);
                border-left: none;
            "></div>

            <!-- Goal Box Right -->
            <div style="
                position: absolute;
                top: 38%;
                bottom: 38%;
                right: 12px;
                width: 35px;
                border: 2px solid rgba(255,255,255,0.4);
                border-right: none;
            "></div>

            <!-- Players Nodes -->
            {nodes_a_html}
            {nodes_b_html}
        </div>
    </div>
    """
    st.markdown(pitch_html, unsafe_allow_html=True)


# ==============================================================================
# 5. TABELLONE PARTITE STILE CHAMPIONS LEAGUE (SCOREBOARD CARD)
# ==============================================================================
def render_champions_scoreboard(
    match_row: pd.Series,
    mvp_name: Optional[str] = None,
    mvp_avg: Optional[float] = None
) -> None:
    """
    Renderizza una Match Scoreboard Card di altissimo livello grafico (stile UEFA Champions League / SofaScore).
    Mostra il risultato grande a contrasto, badge MVP 👑 dorato, formazioni e dettaglio marcatori a scomparsa.
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
            margin-top: 6px;
        ">
            👑 MVP DEL MATCH: <b>{mvp_name}</b>{mvp_score_text}
        </div>
        """

    # Marcatori Formattati
    marcatori_badges = []
    if marcatori_dict:
        for p, g in marcatori_dict.items():
            marcatori_badges.append(f"<span style='background: rgba(255,255,255,0.06); padding: 3px 8px; border-radius: 6px; margin: 2px 4px; display: inline-block; font-size: 0.8rem; color: #F1F5F9;'>⚽ <b>{p}</b> ({g})</span>")
        marcatori_html = " ".join(marcatori_badges)
    else:
        marcatori_html = "<span style='color: #64748B; font-size: 0.8rem;'>Nessun marcatore individuale registrato per questa partita.</span>"

    card_html = f"""
    <div style="
        background: rgba(18, 24, 36, 0.75);
        backdrop-filter: blur(14px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 18px 20px;
        margin-bottom: 1.3rem;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.35);
        font-family: 'Outfit', sans-serif;
    ">
        <!-- Top Match Info Bar -->
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
            <div style="display: flex; align-items: center; gap: 10px;">
                <span style="background: rgba(255,255,255,0.08); color: #94A3B8; font-size: 0.75rem; font-weight: 800; padding: 3px 10px; border-radius: 8px; text-transform: uppercase; letter-spacing: 0.5px;">
                    MATCH #{id_p}
                </span>
                <span style="color: #94A3B8; font-size: 0.85rem; font-weight: 500;">
                    🗓️ <b>{data_str}</b>
                </span>
            </div>
            <div style="
                background: {badge_bg};
                border: 1px solid {badge_border};
                color: {badge_color};
                font-size: 0.78rem;
                font-weight: 800;
                padding: 4px 12px;
                border-radius: 20px;
                letter-spacing: 0.5px;
            ">
                {esito}
            </div>
        </div>

        <!-- Champions League Centered Scoreboard -->
        <div style="
            display: grid;
            grid-template-columns: 1fr auto 1fr;
            align-items: center;
            gap: 16px;
            padding: 14px 10px;
            background: rgba(11, 14, 20, 0.6);
            border-radius: 14px;
            border: 1px solid rgba(255, 255, 255, 0.05);
            margin-bottom: 14px;
        ">
            <!-- Team A Left -->
            <div style="text-align: right;">
                <div style="font-size: 1.15rem; font-weight: 800; color: #FFD700; letter-spacing: 0.5px;">
                    SQUADRA A 🟨
                </div>
            </div>

            <!-- Score Pill Center -->
            <div style="
                background: #0B0E14;
                border: 1px solid rgba(255, 255, 255, 0.15);
                padding: 6px 20px;
                border-radius: 12px;
                font-size: 1.8rem;
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
            <div style="text-align: left;">
                <div style="font-size: 1.15rem; font-weight: 800; color: #00E5FF; letter-spacing: 0.5px;">
                    🟦 SQUADRA B
                </div>
            </div>
        </div>

        <!-- MVP Highlight (if available) -->
        <div style="text-align: center; margin-bottom: 12px;">
            {mvp_section_html}
        </div>

        <!-- Formations Breakdown -->
        <div style="
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            padding: 12px 14px;
            background: rgba(255, 255, 255, 0.02);
            border-radius: 10px;
            font-size: 0.82rem;
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
        <div style="margin-top: 12px; padding-top: 10px; border-top: 1px solid rgba(255, 255, 255, 0.06);">
            <div style="font-size: 0.78rem; font-weight: 700; color: #94A3B8; margin-bottom: 6px; text-transform: uppercase;">
                🎯 Marcatori dell'Incontro:
            </div>
            {marcatori_html}
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)
