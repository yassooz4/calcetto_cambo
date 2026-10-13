"""OVR preview with fictional data only; no production storage or secrets."""
import pandas as pd
import streamlit as st

import logic
import ui_components
import ratings
import rating_ui
from test_ovr import PLAYERS, final, match

st.set_page_config(page_title="Anteprima Rating Cambo", layout="wide")
ui_components.inject_custom_theme()
st.markdown("### 🎴 Scheda Membro · Rating Cambo")
st.caption("Gol, risultati e MVP · Stima prudente con pochi dati · Forma delle ultime cinque partite")
name = st.selectbox("Giocatore", PLAYERS["nome_completo"], index=0)
strict = st.checkbox("Solo partite 100% Cerchia")
matches = pd.DataFrame([match(i, "V" if i >= 5 else "S", 3 if i >= 5 else 0,
                               team_b="Ciro" if i == 8 else "Beto") for i in range(1, 9)])
awards = pd.DataFrame([final(2, ["Beto"]), final(6, ["Ada"]), final(8, ["Ada", "Ciro"])])
context = ratings.build_context(PLAYERS, matches, awards)
if strict:
    matches = logic.filter_internal_matches(matches, ["Ada", "Beto", "Dina"])
if st.session_state.get("full_page"):
    import app
    if st.session_state["full_page"] == "cerchia":
        app.view_gruppo_ristretto(PLAYERS, matches, awards, "Dati fittizi", False)
    else:
        app.view_dashboard(PLAYERS, matches, awards, "Dati fittizi")
    st.stop()
stats = ratings.calculate_player_stats(name, PLAYERS, matches, awards, rating_context=context)
comparison = ratings.calculate_comparison(name, PLAYERS, matches, awards,
                                     giocatori_filtrati=["Ada", "Beto", "Dina"] if strict else None,
                                     rating_context=context)
rating_ui.render_player_sheet(name, stats, comparison, is_cerchia=True)
