"""MVP election screens. Private widgets are built only for an authenticated admin."""

from html import escape

import pandas as pd
import streamlit as st

import ui_components
import voting


def _result_cards(result):
    left, right = st.columns(2)
    for container, field, title, icon, css in [
        (left, "mvp", "MVP DELLA PARTITA", "👑", "card-mvp"),
        (right, "worst", "PEGGIORE DELLA PARTITA", "🧊", "card-worst"),
    ]:
        with container:
            names = result.get(field + "_names", [])
            text = " · ".join(escape(name) for name in names) or "Nessun risultato"
            tie = "Ex aequo · " if len(names) > 1 else ""
            count = result.get(field + "_votes", 0)
            ui_components.render_html(f"""
            <div class="{css}" style="padding:24px;text-align:center;">
                <div style="font-size:2.2rem;">{icon}</div>
                <h3 style="margin:8px 0;">{title}</h3>
                <h2 style="margin:10px 0;color:#ffffff;">{text}</h2>
                <p>{tie}{count} voti</p>
            </div>
            """)


def _run(action, success):
    try:
        action()
    except voting.VotingError as error:
        st.error(str(error))
    else:
        st.session_state["voting_flash"] = success
        st.rerun()


def render_passwords(players):
    if not voting.is_private_admin():
        st.error("Accesso riservato all'amministratore.")
        return
    st.markdown("<div class='main-title'>🔐 Password Giocatori</div>", unsafe_allow_html=True)
    st.caption("Ogni giocatore ha una password personale di 5 cifre. Solo tu puoi vedere questo elenco.")
    if not voting.configured():
        st.info("Configura admin_pin e voting_key nella sezione auth dei Secrets di Streamlit.")
        return
    if players.empty:
        st.info("Aggiungi i giocatori all'anagrafica per assegnare le password.")
        return
    try:
        codes = voting.ensure_codes(players)
    except voting.VotingError as error:
        st.error(str(error))
        return
    flash = st.session_state.pop("voting_flash", None)
    if flash:
        st.success(flash)
    names = voting.players_by_id(players)
    rows = [{"Giocatore": name, "Password": codes[player_id]["code"]}
            for player_id, name in sorted(names.items(), key=lambda item: item[1].casefold())]
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    st.caption("Sono ammesse password che iniziano per zero: 100.000 combinazioni. Comunica a ciascun giocatore soltanto il proprio codice.")
    with st.expander("🔄 Rigenera una password"):
        target = st.selectbox("Giocatore", options=list(names), format_func=names.get, key="password_target")
        st.caption("Il vecchio codice smetterà di funzionare. I voti già inviati restano validi.")
        if st.button("Rigenera password", key="rotate_player_password"):
            _run(lambda: voting.rotate_code(players, target), "Password rigenerata. Il nuovo codice è nell'elenco.")


def render_votes(players, matches, is_admin):
    st.markdown("<div class='main-title'>👑 MVP & Peggiore</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>Due scelte, una votazione personale. I risultati vengono pubblicati alla chiusura.</div>", unsafe_allow_html=True)
    if not voting.configured():
        st.info("La nuova votazione sarà disponibile dopo la configurazione riservata dell'amministratore.")
        return
    if matches.empty:
        st.info("Nessuna partita disponibile. Registra una partita per aprire la votazione.")
        return
    try:
        events = voting.load_events()
    except voting.VotingError as error:
        st.error(str(error))
        return

    flash = st.session_state.pop("voting_flash", None)
    if flash:
        st.success(flash)
    match_rows = {int(match["id_partita"]): match for _, match in matches.sort_values(
        by=["data", "id_partita"], ascending=[False, False]).iterrows()}
    match_id = st.selectbox("Seleziona la partita:", options=list(match_rows),
        format_func=lambda value: f"Partita #{value} · {match_rows[value]['data']} · {match_rows[value]['gol_squadra_a']}–{match_rows[value]['gol_squadra_b']}",
        key="election_match")
    match = match_rows[match_id]
    state = voting.election(events, match_id)
    closed = state["type"] == "close"
    st.caption("🔒 Votazione chiusa · risultato ufficiale" if closed else "🟢 Votazione aperta · scelte riservate")

    admin = bool(is_admin and voting.is_private_admin())
    labels = ["🗳️ Il tuo voto", "🏆 Risultati"]
    if admin:
        labels.append("🔒 Registro riservato")
    tabs = st.tabs(labels)
    with tabs[0]:
        if closed:
            st.info("L'amministratore ha chiuso la votazione. Consulta i risultati ufficiali.")
        else:
            _ballot_form(players, match, events)
    with tabs[1]:
        if closed:
            _result_cards(state["result"])
            st.caption(f"Risultato pubblicato su {state['result']['total_ballots']} votazioni personali.")
            st.caption("In caso di parità, il titolo è assegnato ex aequo.")
        else:
            st.info("MVP e peggiore verranno annunciati quando l'amministratore chiuderà la votazione.")
        public_rows = []
        for id_value, historical in match_rows.items():
            final = voting.election(events, id_value)
            if final["type"] == "close":
                result = final["result"]
                public_rows.append({"Partita": id_value, "Data": historical["data"],
                                    "MVP": " · ".join(result["mvp_names"]),
                                    "Peggiore": " · ".join(result["worst_names"])})
        if public_rows:
            st.markdown("### Risultati pubblicati")
            st.dataframe(pd.DataFrame(public_rows), hide_index=True, use_container_width=True)
    if admin:
        with tabs[2]:
            _admin_election(players, match, events, closed)


def _ballot_form(players, match, events):
    identity = st.session_state.get("voting_identity")
    if identity:
        try:
            name = voting.identity_name(identity, players, events)
        except voting.VotingError:
            st.session_state.pop("voting_identity", None)
            identity = None
    if not identity:
        st.markdown("### 🔑 Accedi con la tua password")
        st.caption("Il codice identifica automaticamente il tuo nome. Non viene mostrato agli altri giocatori.")
        with st.form("voter_login", clear_on_submit=True):
            code = st.text_input("Password personale di 5 cifre", type="password", max_chars=5, key="voter_code")
            login = st.form_submit_button("Accedi alla votazione", type="primary", use_container_width=True)
        if login:
            try:
                st.session_state["voting_identity"] = voting.authenticate(code, players)
            except voting.VotingError as error:
                st.error(str(error))
            else:
                st.rerun()
        return

    st.success(f"Voti come **{name}**")
    if st.button("Cambia votante", key="change_voter"):
        st.session_state.pop("voting_identity", None)
        st.rerun()
    roster = voting.participants(match)
    if name not in roster:
        st.info("Puoi votare solo le partite in cui hai giocato.")
        return
    candidates = [player for player in roster if player != name]
    if len(candidates) < 2:
        st.info("Servono almeno due altri giocatori per votare.")
        return
    previous = voting.own_ballot(identity, events, match["id_partita"])
    if previous:
        st.info("Hai già votato. Puoi modificare le tue scelte finché la votazione è aperta.")
    else:
        st.caption("Scegli due giocatori diversi. Non puoi votare per te stesso.")
    widget_key = f"{match['id_partita']}_{identity['player_id']}_{identity['revision']}"
    options = [None] + candidates
    with st.form(f"ballot_{widget_key}"):
        left, right = st.columns(2)
        with left:
            st.markdown("### 👑 MVP")
            mvp_default = previous["mvp"] if previous and previous["mvp"] in candidates else None
            mvp = st.selectbox("Il migliore in campo", options=options, index=options.index(mvp_default),
                format_func=lambda value: value or "Scegli il giocatore", key=f"mvp_{widget_key}")
        with right:
            st.markdown("### 🧊 Peggiore")
            worst_default = previous["worst"] if previous and previous["worst"] in candidates else None
            worst = st.selectbox("Il peggiore in campo", options=options, index=options.index(worst_default),
                format_func=lambda value: value or "Scegli il giocatore", key=f"worst_{widget_key}")
        submit = st.form_submit_button("Aggiorna il tuo voto" if previous else "Invia il tuo voto", type="primary", use_container_width=True)
    if submit:
        _run(lambda: voting.submit_ballot(identity, players, match, mvp, worst), "Voto salvato. Le tue scelte sono visibili solo a te e all'amministratore.")


def _admin_election(players, match, events, closed):
    voting.require_admin()
    votes = voting.ballots(events, match["id_partita"])
    roster = voting.participants(match)
    st.markdown("### 🛡️ Gestione votazione")
    st.metric("Votazioni ricevute", f"{len(votes)} / {len(roster)}")
    st.progress(min(1.0, len(votes) / len(roster)) if roster else 0.0)
    st.caption("Puoi chiudere anche se qualcuno non ha ancora votato. La chiusura blocca le modifiche e pubblica i risultati.")
    if votes:
        rows = [{"Votante": vote["voter_name"], "MVP scelto": vote["mvp"], "Peggiore scelto": vote["worst"],
                 "Ultimo invio (UTC)": vote.get("time", "")} for vote in votes]
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
        missing = sorted(set(roster) - {vote["voter_name"] for vote in votes})
        if missing:
            st.write("Devono ancora votare: " + ", ".join(missing))
        if not closed:
            st.markdown("#### Conteggio provvisorio · riservato")
            _result_cards(voting.tally(votes))
    else:
        st.info("Nessun voto inviato per questa partita.")
    if closed:
        if st.button("Riapri votazione", key=f"reopen_{match['id_partita']}"):
            _run(lambda: voting.reopen_election(match["id_partita"]), "Votazione riaperta. Il risultato precedente torna provvisorio.")
    elif st.button("Chiudi votazione e pubblica risultato", type="primary", use_container_width=True,
                   disabled=not votes, key=f"close_{match['id_partita']}"):
        _run(lambda: voting.close_election(players, match), "Votazione chiusa. MVP e peggiore sono ora pubblicati.")
