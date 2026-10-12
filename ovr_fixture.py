"""OVR preview with fictional data only; no production storage or secrets."""
import pandas as pd
import streamlit as st

import logic
import ui_components
from test_ovr import PLAYERS, final, match

st.set_page_config(page_title="Anteprima Rating Cambo", layout="wide")
ui_components.inject_custom_theme()
st.markdown("### 🎴 Scheda Membro · Rating Cambo")
st.caption("45% gol · 45% risultati · 10% MVP | 80% complessivo · 20% ultime cinque partite")
name = st.selectbox("Giocatore", PLAYERS["nome_completo"], index=0)
strict = st.checkbox("Solo partite 100% Cerchia")
matches = pd.DataFrame([match(i, "V" if i >= 5 else "S", 3 if i >= 5 else 0,
                               team_b="Ciro" if i == 8 else "Beto") for i in range(1, 9)])
awards = pd.DataFrame([final(2, ["Beto"]), final(6, ["Ada"]), final(8, ["Ada", "Ciro"])])
if strict:
    matches = logic.filter_internal_matches(matches, ["Ada", "Beto", "Dina"])
if st.session_state.get("full_page"):
    import app
    if st.session_state["full_page"] == "cerchia":
        app.view_gruppo_ristretto(PLAYERS, matches, awards, "Dati fittizi", False)
    else:
        app.view_dashboard(PLAYERS, matches, awards, "Dati fittizi")
    st.stop()
stats = logic.calculate_player_fifa_stats(name, PLAYERS, matches, awards)
radar = logic.calculate_radar_metrics(name, PLAYERS, matches, awards,
                                     giocatori_filtrati=["Ada", "Beto", "Dina"] if strict else None)
left, right = st.columns([1, 1.2])
with left:
    ui_components.render_fut_card(name, stats, is_cerchia=True)
    ui_components.render_ovr_breakdown(stats)
with right:
    st.markdown("#### 📊 Rendimento (vs Media Membri Attivi)")
    ui_components.render_player_radar_chart(name, radar)
    st.markdown("#### 🏃 Forma recente")
    if stats["forma"]:
        ui_components.render_html(" ".join(f"<span class='badge-{value.lower()}'>{value}</span>" for value in stats["forma"][:5]))
        st.caption("Dalla più recente alla meno recente.")
    else:
        st.caption("Nessuna partita giocata.")
