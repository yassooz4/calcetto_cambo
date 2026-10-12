"""Local UI test harness, using fictional players and in-memory ballots only."""
import streamlit as st
from unittest.mock import patch
from cryptography.fernet import Fernet
import voting
from voting_ui import render_votes, render_passwords
from test_voting import PLAYERS, MATCH
import pandas as pd
import ui_components

st.set_page_config(layout="wide")
ui_components.inject_custom_theme()
admin = st.session_state.get("fixture_admin", False)
st.session_state["authenticated"] = True
st.session_state["user_role"] = "admin" if admin else "viewer"
events = st.session_state.setdefault("fixture_events", [
    dict(type="credential", player_id=str(index + 1), player_name=name, code=f"{index:05d}", revision=f"test-{index}", version=1)
    for index, name in enumerate(PLAYERS["nome_completo"])
])
if "fixture_key" not in st.session_state:
    st.session_state["fixture_key"] = Fernet.generate_key()
codec = Fernet(st.session_state["fixture_key"])

def append_events(sh, added):
    events.extend(dict(event, version=1, time="2026-10-12T18:00:00Z") for event in added)

with patch.object(voting, "admin_pin", lambda: "2345"), patch.object(voting, "cipher", lambda: codec), \
     patch.object(voting, "load_events", lambda: events), patch.object(voting, "_backend", lambda: None), \
     patch.object(voting, "_read", lambda sh: events), patch.object(voting, "_append", append_events):
    st.session_state["admin_signature"] = voting.admin_signature() if admin else ""
    if st.session_state.get("fixture_page") == "passwords":
        render_passwords(PLAYERS)
    else:
        render_votes(PLAYERS, pd.DataFrame([MATCH]), admin)
