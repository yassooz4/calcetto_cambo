"""
================================================================================
CALCETTO STATS & MANAGER - Web Application
Autenticazione PIN a doppio livello (Viewer / Admin)
Stack: Streamlit, Pandas, Google Sheets (gspread), Fallback CSV Locale
================================================================================
"""

import os
import json
from typing import Optional
from datetime import date, datetime
import pandas as pd
import streamlit as st

# Import dei moduli dedicati (Clean Architecture / DDD)
import logic
import storage
import ui_components

# ==============================================================================
# 1. CONFIGURAZIONE PAGINA & INIEZIONE DESIGN SYSTEM GLOBALE
# ==============================================================================
st.set_page_config(
    page_title="Calcetto Stats & Manager",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="auto"
)

# Iniezione Dark Modern Stadium & Glassmorphism Theme
ui_components.inject_custom_theme()


# ==============================================================================
# 2. SISTEMA DI AUTENTICAZIONE & CONTROLLO ACCESSI (PIN GATE)
# ==============================================================================
PIN_VIEWER = "5678"
PIN_ADMIN = "8765"

def render_pin_gate():
    """Mostra la schermata di login con verifica PIN (Sola Lettura vs Amministratore)."""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<div style='text-align: center; font-size: 3.5rem;'>⚽🔒</div>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: #10b981;'>Calcetto Stats & Manager</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #94a3b8;'>Inserisci il PIN per accedere alla piattaforma</p>", unsafe_allow_html=True)
        
        with st.form("pin_form", clear_on_submit=False):
            pin_input = st.text_input("PIN di Accesso", type="password", placeholder="••••", max_chars=10)
            submit_btn = st.form_submit_button("Sblocca Applicazione 🔓", use_container_width=True)
            
            if submit_btn:
                pin_clean = pin_input.strip()
                if pin_clean == PIN_ADMIN:
                    st.session_state["authenticated"] = True
                    st.session_state["user_role"] = "admin"
                    st.success("Accesso eseguito come **Amministratore** 🛡️")
                    st.rerun()
                elif pin_clean == PIN_VIEWER:
                    st.session_state["authenticated"] = True
                    st.session_state["user_role"] = "viewer"
                    st.success("Accesso eseguito in modalità **Sola Lettura** 👁️")
                    st.rerun()
                else:
                    st.error("❌ PIN non valido.")

        # Footer informativo e diagnostica rapida stato storage
        _, _, _, _, storage_source, storage_error = storage.load_data()
        st.markdown(f"<div style='text-align: center; font-size: 0.8rem; color: #64748b; margin-top: 1.5rem;'>Persistenza: <b>{storage_source}</b></div>", unsafe_allow_html=True)
        if storage_error and storage_source != "Google Sheets (Cloud)":
            with st.expander("⚠️ Diagnostica Connessione Google Sheets", expanded=False):
                st.warning(f"**Dettaglio Fallback:**\n\n{storage_error}")
                if st.button("🔄 Ricarica / Riprova GSheets", key="btn_retry_gsheets_pin", use_container_width=True):
                    st.cache_data.clear()
                    st.rerun()


# ==============================================================================
# 3. VISTA A: TABELLONE & CLASSIFICHE (GENERAL, ELO, MARCATORI, COPPIE, STRISCE)
# ==============================================================================
def view_dashboard(df_giocatori: pd.DataFrame, df_partite: pd.DataFrame, df_voti: pd.DataFrame, storage_source: str):
    st.markdown("<div class='main-title'>🏆 Tabellone & Statistiche</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='sub-title'>Panoramica rendimento generale • Rating ELO dinamico • Sorgente: <b>{storage_source}</b></div>", unsafe_allow_html=True)

    # 1. Metriche Generali Superiori
    tot_partite = len(df_partite)
    tot_giocatori = len(df_giocatori)
    
    if tot_partite > 0:
        tot_gol = df_partite["gol_squadra_a"].sum() + df_partite["gol_squadra_b"].sum()
        media_gol = round(tot_gol / tot_partite, 1)
    else:
        media_gol = 0.0

    m1, m2, m3 = st.columns(3)
    m1.metric("⚽ Partite Disputate", f"{tot_partite}")
    m2.metric("👥 Giocatori Iscritti", f"{tot_giocatori}")
    m3.metric("🎯 Media Gol / Partita", f"{media_gol}")

    st.markdown("---")

    # 2. Calcolo ELO e Classifiche
    elo_ratings, elo_history = logic.calculate_elo_ratings(df_giocatori, df_partite)
    gruppo_set = set(df_giocatori[df_giocatori["in_gruppo_ristretto"] == True]["nome_completo"].dropna().tolist()) if not df_giocatori.empty and "in_gruppo_ristretto" in df_giocatori.columns else set()

    tab_classifica, tab_marcatori, tab_elo, tab_strisce, tab_coppie, tab_spotlight = st.tabs([
        "🥇 Classifica Generale",
        "⚽ Marcatori",
        "⚡ Rating ELO",
        "🔥 Strisce Vittorie",
        "🤝 Coppie & Rivali",
        "🔍 Scheda Giocatore"
    ])

    # TAB 1: CLASSIFICA GENERALE
    with tab_classifica:
        st.markdown("### 🥇 Classifica Rendimento")
        df_rank = logic.calculate_leaderboard(df_giocatori, df_partite, elo_ratings, df_voti=df_voti)
        
        if df_rank.empty:
            st.info("Nessun dato disponibile. Inizia registrando la prima partita!")
        else:
            df_display = df_rank.copy()
            df_display["Pos."] = range(1, len(df_display) + 1)
            df_display["Cerchia"] = df_display["Giocatore"].apply(lambda x: "⭐ Cerchia" if x in gruppo_set else "—")
            df_display["% Vittoria"] = df_display["% Vittoria"].apply(lambda x: f"{x:.1f}%")
            
            cols = ["Pos.", "Giocatore", "Cerchia", "Punti", "PG", "V", "P", "S", "% Vittoria", "ELO", "Titoli MVP", "Titoli Peggiore", "Media Voto"]
            st.dataframe(
                df_display[cols],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Pos.": st.column_config.NumberColumn("Pos.", width="small"),
                    "Giocatore": st.column_config.TextColumn("Giocatore", width="medium"),
                    "Cerchia": st.column_config.TextColumn("Gruppo", width="small", help="⭐ = Membro Gruppo Ristretto"),
                    "Punti": st.column_config.NumberColumn("Punti 🏆", help="3 per V, 1 per P, 0 per S"),
                    "PG": st.column_config.NumberColumn("PG", help="Partite Giocate"),
                    "V": st.column_config.NumberColumn("V", help="Vittorie"),
                    "P": st.column_config.NumberColumn("P", help="Pareggi"),
                    "S": st.column_config.NumberColumn("S", help="Sconfitte"),
                    "% Vittoria": st.column_config.TextColumn("% Vittoria", help="(Vittorie / PG) * 100"),
                    "ELO": st.column_config.NumberColumn("Rating ELO ⚡", help="Punteggio ELO dinamico (Inizio 1500)"),
                    "Titoli MVP": st.column_config.NumberColumn("👑 MVP", help="Titoli MVP conquistati"),
                    "Titoli Peggiore": st.column_config.NumberColumn("🧊 Peggiore", help="Menzioni peggiore in campo"),
                    "Media Voto": st.column_config.NumberColumn("⭐ Media Voto", help="Media complessiva voti ricevuti", format="%.2f"),
                }
            )

    # TAB 2: CLASSIFICA MARCATORI
    with tab_marcatori:
        st.markdown("### ⚽ Classifica Marcatori (Soli Gol Individuali)")
        st.caption("Conteggio rigoroso dei soli gol realizzati dal singolo giocatore (esclusi gli assist).")
        df_scorers = logic.calculate_scorers(df_giocatori, df_partite)

        if df_scorers.empty or df_scorers["Gol Totali"].sum() == 0:
            st.info("Nessun gol individuale registrato finora.")
        else:
            df_sc_disp = df_scorers.copy()
            df_sc_disp["Pos."] = range(1, len(df_sc_disp) + 1)
            df_sc_disp["Cerchia"] = df_sc_disp["Giocatore"].apply(lambda x: "⭐" if x in gruppo_set else "")
            cols = ["Pos.", "Giocatore", "Cerchia", "Gol Totali", "PG", "Media Gol"]
            st.dataframe(
                df_sc_disp[cols],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Pos.": st.column_config.NumberColumn("Pos.", width="small"),
                    "Giocatore": st.column_config.TextColumn("Giocatore", width="medium"),
                    "Cerchia": st.column_config.TextColumn("Cerchia", width="small", help="⭐ Membro gruppo ristretto"),
                    "Gol Totali": st.column_config.NumberColumn("⚽ Gol Totali", help="Somma gol individuali"),
                    "PG": st.column_config.NumberColumn("Partite", help="Presenze in campo"),
                    "Media Gol": st.column_config.NumberColumn("🎯 Media Gol/Gara", help="Gol / Partite Giocate", format="%.2f"),
                }
            )

    # TAB 3: RATING ELO DINAMICO
    with tab_elo:
        st.markdown("### ⚡ Rating ELO Dinamico")
        st.caption("Punteggio iniziale: **1500**. Ricalcolato match dopo match in base al livello medio della squadra e allo scarto reti.")
        
        elo_list = [{"Giocatore": k, "ELO Attuale": v, "Differenza da 1500": round(v - 1500, 1)} for k, v in elo_ratings.items()]
        df_elo_table = pd.DataFrame(elo_list).sort_values(by="ELO Attuale", ascending=False).reset_index(drop=True)
        df_elo_table["Pos."] = range(1, len(df_elo_table) + 1)
        df_elo_table["Cerchia"] = df_elo_table["Giocatore"].apply(lambda x: "⭐" if x in gruppo_set else "")

        st.dataframe(
            df_elo_table[["Pos.", "Giocatore", "Cerchia", "ELO Attuale", "Differenza da 1500"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Pos.": st.column_config.NumberColumn("Pos.", width="small"),
                "Giocatore": st.column_config.TextColumn("Giocatore", width="medium"),
                "Cerchia": st.column_config.TextColumn("Cerchia", width="small", help="⭐ Membro gruppo ristretto"),
                "ELO Attuale": st.column_config.NumberColumn("⚡ ELO", format="%.1f"),
                "Differenza da 1500": st.column_config.NumberColumn("Trend (+/-)", format="%+.1f"),
            }
        )

    # TAB 4: STRISCE DI VITTORIE
    with tab_strisce:
        st.markdown("### 🔥 Strisce di Vittorie Consecutive")
        st.caption("Tracciamento della striscia di vittorie attualmente aperta e del record storico personale.")
        df_streaks = logic.calculate_win_streaks(df_giocatori, df_partite)

        if df_streaks.empty:
            st.info("Nessuna serie di vittorie registrata.")
        else:
            df_st_disp = df_streaks.copy()
            df_st_disp["Pos."] = range(1, len(df_st_disp) + 1)
            st.dataframe(
                df_st_disp[["Pos.", "Giocatore", "Striscia Attuale", "Record Storico", "PG Totali"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Pos.": st.column_config.NumberColumn("Pos.", width="small"),
                    "Giocatore": st.column_config.TextColumn("Giocatore", width="medium"),
                    "Striscia Attuale": st.column_config.NumberColumn("🔥 Serie Aperta", help="Vittorie consecutive in corso"),
                    "Record Storico": st.column_config.NumberColumn("🏆 Record Personale", help="Miglior sequenza storica di vittorie consecutive"),
                    "PG Totali": st.column_config.NumberColumn("Partite Totali"),
                }
            )

    # TAB 5: COPPIE D'ORO & RIVALI
    with tab_coppie:
        st.markdown("### 🤝 Coppie d'Oro (Affinità Compagni)")
        st.caption("Percentuale di vittoria quando due giocatori giocano nello stesso schieramento (minimo **3 partite** insieme).")
        df_duos, df_rivals = logic.calculate_golden_duos_and_rivalries(df_partite, min_games_together=3)

        if df_duos.empty:
            st.info("Nessuna coppia ha ancora raggiunto la soglia minima di 3 partite giocate insieme.")
        else:
            df_duos_disp = df_duos.copy()
            df_duos_disp["Pos."] = range(1, len(df_duos_disp) + 1)
            df_duos_disp["% Vittoria Insieme"] = df_duos_disp["% Vittoria Insieme"].apply(lambda x: f"{x:.1f}%")
            st.dataframe(
                df_duos_disp[["Pos.", "Coppia", "PG Insieme", "V Insieme", "P Insieme", "S Insieme", "% Vittoria Insieme"]],
                use_container_width=True,
                hide_index=True
            )

        st.markdown("---")
        st.markdown("### ⚔️ Scontri Diretti (Testa a Testa)")
        st.caption("Statistiche storiche quando due giocatori si affrontano come avversari in squadre opposte.")

        if df_rivals.empty:
            st.info("Nessuno scontro diretto registrato finora.")
        else:
            lista_nomi = sorted(df_giocatori["nome_completo"].dropna().unique().tolist()) if not df_giocatori.empty else []
            if len(lista_nomi) >= 2:
                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    p1_sel = st.selectbox("Giocatore 1:", options=lista_nomi, key="rival_p1_sel")
                with col_r2:
                    p2_options = [p for p in lista_nomi if p != p1_sel]
                    p2_sel = st.selectbox("Giocatore 2 (Avversario):", options=p2_options, key="rival_p2_sel")

                # Cerca confronto
                found = False
                for _, r in df_rivals.iterrows():
                    ga = r["Giocatore A"]
                    gb = r["Giocatore B"]
                    if (ga == p1_sel and gb == p2_sel) or (ga == p2_sel and gb == p1_sel):
                        found = True
                        tot_scontri = r["Scontri Diretti"]
                        v_p1 = r.get(f"Vittorie {p1_sel}", 0)
                        v_p2 = r.get(f"Vittorie {p2_sel}", 0)
                        pareggi = r["Pareggi"]

                        rc1, rc2, rc3 = st.columns(3)
                        rc1.metric(f"Vittorie {p1_sel}", f"{v_p1}")
                        rc2.metric("Pareggi", f"{pareggi}")
                        rc3.metric(f"Vittorie {p2_sel}", f"{v_p2}")
                        st.caption(f"Totale sfide da avversari: **{tot_scontri}**")
                        break

                if not found:
                    st.info(f"Nessuno scontro diretto registrato tra **{p1_sel}** e **{p2_sel}**.")

    # TAB 6: SCHEDA SINGOLO GIOCATORE (FUT CARD & RADAR CHART)
    with tab_spotlight:
        st.markdown("### 🎴 Scheda Giocatore & FUT Ultimate Card")
        st.caption("Visualizzazione stile EA Sports FC con Overall Rating (OVR), 6 attributi chiave e confronto radar.")
        lista_giocatori = sorted(df_giocatori["nome_completo"].dropna().unique().tolist()) if not df_giocatori.empty else []
        
        if not lista_giocatori:
            st.info("Nessun giocatore registrato.")
        else:
            selected_player = st.selectbox("Seleziona un giocatore per visualizzare la Scheda FUT:", options=lista_giocatori, key="spotlight_player_sel")
            
            if selected_player:
                fifa_stats = logic.calculate_player_fifa_stats(
                    selected_player, df_giocatori, df_partite, df_voti, elo_ratings
                )
                radar_data = logic.calculate_radar_metrics(
                    selected_player, df_giocatori, df_partite, df_voti, elo_ratings
                )
                is_in_cerchia = (selected_player in gruppo_set)

                col_fut, col_radar = st.columns([1, 1.2])

                with col_fut:
                    ui_components.render_fut_card(selected_player, fifa_stats, is_cerchia=is_in_cerchia)

                with col_radar:
                    st.markdown("#### 📊 Radar Bilanciamento Abilità (vs Media)")
                    ui_components.render_player_radar_chart(selected_player, radar_data)

                    st.markdown("#### 🏃 Forma Recente (Ultime sfide)")
                    forma = fifa_stats.get("forma", [])
                    if forma:
                        badges_html = ""
                        for res in forma[:5]:
                            if res == "V":
                                badges_html += "<span class='badge-v'>V</span>"
                            elif res == "P":
                                badges_html += "<span class='badge-p'>P</span>"
                            else:
                                badges_html += "<span class='badge-s'>S</span>"
                        st.markdown(badges_html, unsafe_allow_html=True)
                        st.caption("Dalla più recente (sinistra) alla meno recente (destra).")
                    else:
                        st.caption("Nessuna partita disputata finora.")


# ==============================================================================
# 3B. VISTA: CLASSIFICA & STATISTICHE GRUPPO RISTRETTO (CERCHIA RISTRETTA)
# ==============================================================================
def view_gruppo_ristretto(
    df_giocatori: pd.DataFrame, 
    df_partite: pd.DataFrame, 
    df_voti: pd.DataFrame, 
    storage_source: str,
    is_admin: bool
):
    st.markdown("<div class='main-title'>🏆 Classifica Amici (Gruppo Ristretto)</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='sub-title'>Dashboard statistica dedicata esclusivamente ai membri storici e fissi del gruppo • Sorgente: <b>{storage_source}</b></div>", unsafe_allow_html=True)

    # 1. Recupero membri gruppo ristretto
    if df_giocatori.empty or "in_gruppo_ristretto" not in df_giocatori.columns:
        gruppo_names = []
    else:
        gruppo_df = df_giocatori[df_giocatori["in_gruppo_ristretto"] == True]
        gruppo_names = sorted(gruppo_df["nome_completo"].dropna().tolist())

    # 2. Pannello di Gestione Membri (Admin Only) o Riepilogo (Viewer)
    if is_admin:
        with st.expander("⚙️ Gestione Membri Cerchia Ristretta (Solo Admin)", expanded=(len(gruppo_names) == 0)):
            st.caption("Aggiungi o rimuovi giocatori dalla Cerchia Ristretta. Il salvataggio aggiorna istantaneamente tutte le statistiche e tabelle.")
            tutti_i_nomi = sorted(df_giocatori["nome_completo"].dropna().tolist()) if not df_giocatori.empty else []
            
            selected_members = st.multiselect(
                "Seleziona i membri del Gruppo Ristretto:",
                options=tutti_i_nomi,
                default=gruppo_names,
                key="admin_gruppo_multiselect"
            )
            
            col_b1, col_b2 = st.columns([1, 3])
            with col_b1:
                if st.button("💾 Salva Membri Cerchia", type="primary", use_container_width=True, key="btn_save_cerchia_members"):
                    ids_selezionati = df_giocatori[df_giocatori["nome_completo"].isin(selected_members)]["id_giocatore"].tolist()
                    storage.update_gruppo_ristretto_members(ids_selezionati)
                    st.success("✅ Membri del gruppo ristretto aggiornati con successo!")
                    st.rerun()
            with col_b2:
                st.caption(f"Giocatori selezionati: **{len(selected_members)}** su {len(tutti_i_nomi)} registrati.")
    else:
        with st.expander(f"👥 Membri Attivi della Cerchia Ristretta ({len(gruppo_names)})", expanded=False):
            if gruppo_names:
                pills_html = " ".join([f"<span class='badge-circle'>⭐ {n}</span>" for n in gruppo_names])
                st.markdown(pills_html, unsafe_allow_html=True)
            else:
                st.info("ℹ️ Nessun membro attualmente assegnato alla cerchia ristretta. La configurazione è riservata all'Amministratore.")

    if not gruppo_names:
        st.warning("⚠️ Nessun giocatore fa attualmente parte del Gruppo Ristretto. " + 
                   ("Usa il pannello amministratore sopra per selezionare i membri." if is_admin else "In attesa di configurazione da parte dell'Amministratore."))
        return

    # 3. Toggle Filtro Partite (Tutte le partite con membri vs Solo 100% cerchia)
    st.markdown("<br>", unsafe_allow_html=True)
    opzione_filtro = st.radio(
        "📐 **Modalità Calcolo Statistiche:**",
        options=[
            "🌐 Tutte le partite disputate dai membri (anche in presenza di esterni)",
            "🔒 Solo partite 100% Cerchia Ristretta (entrambi i team composti solo da membri)"
        ],
        index=0,
        horizontal=True,
        key="radio_filtro_partite_gruppo"
    )

    is_strict = ("Solo partite 100%" in opzione_filtro)
    if is_strict:
        df_partite_calc = logic.filter_internal_matches(df_partite, gruppo_names, strict=True)
    else:
        df_partite_calc = df_partite.copy()

    # 4. Metriche Principali Cerchia
    tot_partite_cerchia = len(df_partite_calc)
    tot_membri_cerchia = len(gruppo_names)

    if tot_partite_cerchia > 0:
        tot_gol_c = df_partite_calc["gol_squadra_a"].sum() + df_partite_calc["gol_squadra_b"].sum()
        media_gol_c = round(tot_gol_c / tot_partite_cerchia, 1)
    else:
        media_gol_c = 0.0

    # Calcolo ELO e Statistiche Filtrate
    elo_ratings_c, elo_history_c = logic.calculate_elo_ratings(df_giocatori, df_partite_calc, giocatori_filtrati=gruppo_names)
    elo_medio = round(sum(elo_ratings_c.values()) / len(elo_ratings_c), 1) if elo_ratings_c else 1500.0

    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("⭐ Membri Cerchia", f"{tot_membri_cerchia}")
    mc2.metric("⚽ Partite Valide", f"{tot_partite_cerchia}")
    mc3.metric("🎯 Media Gol / Match", f"{media_gol_c}")
    mc4.metric("⚡ ELO Medio Cerchia", f"{elo_medio}")

    st.markdown("---")

    # 5. Tabs Statistiche Ristrette
    tab_cl_g, tab_marc_g, tab_elo_g, tab_str_g, tab_coppie_g, tab_spot_g = st.tabs([
        "🥇 Classifica Rendimento",
        "⚽ Marcatori Cerchia",
        "⚡ Rating ELO Amici",
        "🔥 Strisce Vittorie",
        "🤝 Coppie & Rivali",
        "🔍 Scheda Membro & Sfide"
    ])

    # TAB 1: CLASSIFICA GENERALE CERCHIA
    with tab_cl_g:
        st.markdown("### 🥇 Classifica Rendimento (Cerchia Ristretta)")
        st.caption("Classifica calcolata esclusivamente sui membri del gruppo ristretto.")
        df_rank_g = logic.calculate_leaderboard(df_giocatori, df_partite_calc, elo_ratings_c, giocatori_filtrati=gruppo_names, df_voti=df_voti)

        if df_rank_g.empty:
            st.info("Nessuna statistica disponibile per i criteri selezionati.")
        else:
            df_disp_g = df_rank_g.copy()
            df_disp_g["Pos."] = range(1, len(df_disp_g) + 1)
            df_disp_g["% Vittoria"] = df_disp_g["% Vittoria"].apply(lambda x: f"{x:.1f}%")
            
            cols = ["Pos.", "Giocatore", "Punti", "PG", "V", "P", "S", "% Vittoria", "ELO", "Titoli MVP", "Titoli Peggiore", "Media Voto"]
            st.dataframe(
                df_disp_g[cols],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Pos.": st.column_config.NumberColumn("Pos.", width="small"),
                    "Giocatore": st.column_config.TextColumn("Giocatore ⭐", width="medium"),
                    "Punti": st.column_config.NumberColumn("Punti 🏆", help="3 per V, 1 per P, 0 per S"),
                    "PG": st.column_config.NumberColumn("PG", help="Partite Giocate"),
                    "V": st.column_config.NumberColumn("V", help="Vittorie"),
                    "P": st.column_config.NumberColumn("P", help="Pareggi"),
                    "S": st.column_config.NumberColumn("S", help="Sconfitte"),
                    "% Vittoria": st.column_config.TextColumn("% Vittoria", help="(Vittorie / PG) * 100"),
                    "ELO": st.column_config.NumberColumn("Rating ELO ⚡", help="Rating ELO dinamico"),
                    "Titoli MVP": st.column_config.NumberColumn("👑 MVP", help="Titoli MVP conquistati"),
                    "Titoli Peggiore": st.column_config.NumberColumn("🧊 Peggiore", help="Menzioni peggiore in campo"),
                    "Media Voto": st.column_config.NumberColumn("⭐ Media Voto", help="Media complessiva voti ricevuti", format="%.2f"),
                }
            )

    # TAB 2: MARCATORI CERCHIA
    with tab_marc_g:
        st.markdown("### ⚽ Classifica Marcatori (Cerchia Ristretta)")
        st.caption("Soli gol individuali realizzati dai membri storici del gruppo.")
        df_scorers_g = logic.calculate_scorers(df_giocatori, df_partite_calc, giocatori_filtrati=gruppo_names)

        if df_scorers_g.empty or df_scorers_g["Gol Totali"].sum() == 0:
            st.info("Nessun gol registrato finora per i membri del gruppo ristretto.")
        else:
            df_sc_disp_g = df_scorers_g.copy()
            df_sc_disp_g["Pos."] = range(1, len(df_sc_disp_g) + 1)
            cols = ["Pos.", "Giocatore", "Gol Totali", "PG", "Media Gol"]
            st.dataframe(
                df_sc_disp_g[cols],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Pos.": st.column_config.NumberColumn("Pos.", width="small"),
                    "Giocatore": st.column_config.TextColumn("Giocatore ⭐", width="medium"),
                    "Gol Totali": st.column_config.NumberColumn("⚽ Gol Totali"),
                    "PG": st.column_config.NumberColumn("Presenze"),
                    "Media Gol": st.column_config.NumberColumn("🎯 Media Gol/Gara", format="%.2f"),
                }
            )

    # TAB 3: RATING ELO CERCHIA
    with tab_elo_g:
        st.markdown("### ⚡ Rating ELO Dinamico (Cerchia Ristretta)")
        st.caption("Punteggio ELO ricalcolato per i membri del gruppo ristretto.")

        elo_list_g = [{"Giocatore": k, "ELO Attuale": v, "Differenza da 1500": round(v - 1500, 1)} for k, v in elo_ratings_c.items()]
        df_elo_table_g = pd.DataFrame(elo_list_g).sort_values(by="ELO Attuale", ascending=False).reset_index(drop=True)
        
        if not df_elo_table_g.empty:
            df_elo_table_g["Pos."] = range(1, len(df_elo_table_g) + 1)
            st.dataframe(
                df_elo_table_g[["Pos.", "Giocatore", "ELO Attuale", "Differenza da 1500"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Pos.": st.column_config.NumberColumn("Pos.", width="small"),
                    "Giocatore": st.column_config.TextColumn("Giocatore ⭐", width="medium"),
                    "ELO Attuale": st.column_config.NumberColumn("⚡ ELO", format="%.1f"),
                    "Differenza da 1500": st.column_config.NumberColumn("Trend (+/-)", format="%+.1f"),
                }
            )
        else:
            st.info("Nessun dato ELO disponibile.")

    # TAB 4: STRISCE VITTORIE
    with tab_str_g:
        st.markdown("### 🔥 Strisce di Vittorie Consecutive (Cerchia Ristretta)")
        st.caption("Serie aperta di vittorie e record personale dei membri abilitati.")
        df_streaks_g = logic.calculate_win_streaks(df_giocatori, df_partite_calc, giocatori_filtrati=gruppo_names)

        if df_streaks_g.empty:
            st.info("Nessuna serie registrata.")
        else:
            df_st_disp_g = df_streaks_g.copy()
            df_st_disp_g["Pos."] = range(1, len(df_st_disp_g) + 1)
            st.dataframe(
                df_st_disp_g[["Pos.", "Giocatore", "Striscia Attuale", "Record Storico", "PG Totali"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Pos.": st.column_config.NumberColumn("Pos.", width="small"),
                    "Giocatore": st.column_config.TextColumn("Giocatore ⭐", width="medium"),
                    "Striscia Attuale": st.column_config.NumberColumn("🔥 Serie Aperta"),
                    "Record Storico": st.column_config.NumberColumn("🏆 Record Personale"),
                    "PG Totali": st.column_config.NumberColumn("Partite Totali"),
                }
            )

    # TAB 5: COPPIE & RIVALI CERCHIA
    with tab_coppie_g:
        st.markdown("### 🤝 Coppie d'Oro tra Membri del Gruppo")
        st.caption("Percentuale di vittoria quando due membri del gruppo giocano nella stessa squadra (minimo 2 partite insieme).")
        df_duos_g, df_rivals_g = logic.calculate_golden_duos_and_rivalries(df_partite_calc, min_games_together=2, giocatori_filtrati=gruppo_names)

        if df_duos_g.empty:
            st.info("Nessuna coppia del gruppo ha ancora raggiunto la soglia minima di 2 partite insieme.")
        else:
            df_duos_disp_g = df_duos_g.copy()
            df_duos_disp_g["Pos."] = range(1, len(df_duos_disp_g) + 1)
            df_duos_disp_g["% Vittoria Insieme"] = df_duos_disp_g["% Vittoria Insieme"].apply(lambda x: f"{x:.1f}%")
            st.dataframe(
                df_duos_disp_g[["Pos.", "Coppia", "PG Insieme", "V Insieme", "P Insieme", "S Insieme", "% Vittoria Insieme"]],
                use_container_width=True,
                hide_index=True
            )

        st.markdown("---")
        st.markdown("### ⚔️ Scontri Diretti tra Membri (Testa a Testa)")
        st.caption("Statistiche storiche quando due membri del gruppo si affrontano da avversari.")

        if df_rivals_g.empty:
            st.info("Nessuno scontro diretto registrato tra i membri della cerchia.")
        else:
            if len(gruppo_names) >= 2:
                col_gr1, col_gr2 = st.columns(2)
                with col_gr1:
                    p1_g = st.selectbox("Membro 1:", options=gruppo_names, key="rival_g_p1_sel")
                with col_gr2:
                    p2_g_opts = [p for p in gruppo_names if p != p1_g]
                    p2_g = st.selectbox("Membro 2 (Avversario):", options=p2_g_opts, key="rival_g_p2_sel")

                found_g = False
                for _, r in df_rivals_g.iterrows():
                    ga = r["Giocatore A"]
                    gb = r["Giocatore B"]
                    if (ga == p1_g and gb == p2_g) or (ga == p2_g and gb == p1_g):
                        found_g = True
                        tot_sc = r["Scontri Diretti"]
                        v_1 = r.get(f"Vittorie {p1_g}", 0)
                        v_2 = r.get(f"Vittorie {p2_g}", 0)
                        pari = r["Pareggi"]

                        rc1, rc2, rc3 = st.columns(3)
                        rc1.metric(f"Vittorie {p1_g}", f"{v_1}")
                        rc2.metric("Pareggi", f"{pari}")
                        rc3.metric(f"Vittorie {p2_g}", f"{v_2}")
                        st.caption(f"Totale sfide da avversari: **{tot_sc}**")
                        break

                if not found_g:
                    st.info(f"Nessuno scontro diretto registrato tra **{p1_g}** e **{p2_g}**.")

    # TAB 6: SCHEDA MEMBRO (FUT CARD & RADAR CERCHIA)
    with tab_spot_g:
        st.markdown("### 🎴 Scheda Membro Cerchia & FUT Ultimate Card")
        st.caption("Analisi prestazionale del membro della cerchia ristretta con Overall Rating, 6 attributi FIFA e radar di confronto.")
        selected_member = st.selectbox("Seleziona un membro del gruppo:", options=gruppo_names, key="spotlight_member_sel")

        if selected_member:
            fifa_stats_g = logic.calculate_player_fifa_stats(
                selected_member, df_giocatori, df_partite_calc, df_voti, elo_ratings_c, giocatori_filtrati=gruppo_names
            )
            radar_data_g = logic.calculate_radar_metrics(
                selected_member, df_giocatori, df_partite_calc, df_voti, elo_ratings_c, giocatori_filtrati=gruppo_names
            )

            col_fut_g, col_radar_g = st.columns([1, 1.2])

            with col_fut_g:
                ui_components.render_fut_card(selected_member, fifa_stats_g, is_cerchia=True)

            with col_radar_g:
                st.markdown("#### 📊 Radar Rendimento (vs Media Cerchia)")
                ui_components.render_player_radar_chart(selected_member, radar_data_g)

                st.markdown("#### 🏃 Forma Recente (Partite Cerchia)")
                forma_g = fifa_stats_g.get("forma", [])
                if forma_g:
                    b_html = ""
                    for res in forma_g[:5]:
                        if res == "V":
                            b_html += "<span class='badge-v'>V</span>"
                        elif res == "P":
                            b_html += "<span class='badge-p'>P</span>"
                        else:
                            b_html += "<span class='badge-s'>S</span>"
                    st.markdown(b_html, unsafe_allow_html=True)
                    st.caption("Dalla più recente (sinistra) alla meno recente (destra).")
                else:
                    st.caption("Nessuna partita disputata finora per questo membro.")


# ==============================================================================
# 4. VISTA B: CONVOCAZIONI, PRESENZE & BILANCIAMENTO SQUADRE
# ==============================================================================
def view_convocazioni(
    df_giocatori: pd.DataFrame, 
    df_partite: pd.DataFrame, 
    df_convocazioni: pd.DataFrame, 
    is_admin: bool
):
    st.markdown("<div class='main-title'>📅 Convocazioni & Presenze</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>Gestisci le presenze per la prossima sfida e genera formazioni equilibrate con l'algoritmo ELO</div>", unsafe_allow_html=True)

    # 1. Trova sessione attiva o più recente
    sessione_attiva = None
    if not df_convocazioni.empty:
        # Cerca sessione con stato "Aperta"
        aperte = df_convocazioni[df_convocazioni["stato"] == "Aperta"]
        if not aperte.empty:
            sessione_attiva = aperte.iloc[-1]
        else:
            sessione_attiva = df_convocazioni.iloc[-1]

    if sessione_attiva is None:
        st.info("Nessuna sessione di convocazione attiva.")
        if is_admin:
            st.markdown("#### ➕ Crea Nuova Sessione di Convocazione")
            with st.form("form_nuova_convocazione", clear_on_submit=True):
                data_match = st.date_input("Data Partita", value=date.today())
                ora_match = st.time_input("Orario Partita", value=datetime.now().time())
                luogo_match = st.text_input("Luogo / Campo", value="Campo Comunale (Sintetico)")
                crea_btn = st.form_submit_button("📢 Apri Sessione Convocazioni", use_container_width=True)

                if crea_btn:
                    nuovo_id = 1
                    nuova_riga = {
                        "id_convocazione": nuovo_id,
                        "data_partita": data_match.strftime("%Y-%m-%d"),
                        "ora_partita": ora_match.strftime("%H:%M"),
                        "luogo": luogo_match.strip(),
                        "stato": "Aperta",
                        "presenti": "",
                        "assenti": ""
                    }
                    df_up = pd.DataFrame([nuova_riga])
                    storage.save_convocazioni(df_up)
                    st.success("✅ Nuova sessione aperta!")
                    st.rerun()
        else:
            st.warning("🔒 Solo l'amministratore può aprire una nuova sessione di convocazione.")
        return

    # Estrai dati sessione attiva
    id_conv = sessione_attiva.get("id_convocazione", 1)
    data_str = sessione_attiva.get("data_partita", "N/D")
    ora_str = sessione_attiva.get("ora_partita", "N/D")
    luogo_str = sessione_attiva.get("luogo", "Campo da Calcetto")
    stato_str = sessione_attiva.get("stato", "Aperta")

    presenti_raw = [p.strip() for p in str(sessione_attiva.get("presenti", "")).split(",") if p.strip()]
    assenti_raw = [p.strip() for p in str(sessione_attiva.get("assenti", "")).split(",") if p.strip()]

    num_presenti = len(presenti_raw)
    target = 10
    percentuale = min(1.0, num_presenti / target)

    # Box Riepilogo Sessione
    st.markdown(f"""
    <div class="glass-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
            <h3 style="margin: 0; color: #38bdf8;">🗓️ Prossima Partita: {data_str} ore {ora_str}</h3>
            <span style="background: {'#10b981' if stato_str == 'Aperta' else '#64748b'}; color: white; padding: 3px 10px; border-radius: 12px; font-weight: bold; font-size: 0.8rem;">
                {stato_str}
            </span>
        </div>
        <p style="margin: 0; color: #94a3b8;">📍 <b>Luogo:</b> {luogo_str}</p>
    </div>
    """, unsafe_allow_html=True)

    # Contatore Dinamico Target 10
    st.markdown(f"#### 🎯 Convocati Confermati: **{num_presenti} / {target}**")
    st.progress(percentuale)

    if num_presenti == 10:
        st.success("🎉 **Quota 10 raggiunta!** Il gruppo è completo per il 5 contro 5.")
    elif num_presenti > 10:
        st.warning(f"⚠️ Ci sono **{num_presenti}** giocatori confermati (più dei 10 necessari).")
    else:
        st.info(f"Mancano ancora **{target - num_presenti}** giocatori per completare il match.")

    # 2. Modulo Presenze per i Giocatori (Tutti possono confermare presenza/assenza)
    lista_tutti_giocatori = sorted(df_giocatori["nome_completo"].dropna().unique().tolist()) if not df_giocatori.empty else []

    st.markdown("---")
    st.markdown("### ✍️ Segna la tua Presenza")
    
    if not lista_tutti_giocatori:
        st.info("Nessun giocatore registrato nell'anagrafica.")
    elif stato_str != "Aperta":
        st.info("🔒 La sessione di convocazione è attualmente CHIUSA.")
    else:
        c_p1, c_p2, c_p3 = st.columns([2, 1, 1])
        with c_p1:
            nome_votante = st.selectbox("Seleziona il tuo nome:", options=lista_tutti_giocatori, key="presence_player_select")
        with c_p2:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            btn_pres = st.button("✅ Presente", use_container_width=True, type="primary")
        with c_p3:
            st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
            btn_ass = st.button("❌ Assente", use_container_width=True)

        if btn_pres:
            if nome_votante in presenti_raw:
                st.warning(f"Sei già segnato come presente!")
            else:
                nuovi_presenti = presenti_raw + [nome_votante]
                nuovi_assenti = [p for p in assenti_raw if p != nome_votante]
                
                # Aggiorna
                df_up = df_convocazioni.copy()
                idx_to_mod = df_up[df_up["id_convocazione"] == id_conv].index
                df_up.loc[idx_to_mod, "presenti"] = ", ".join(nuovi_presenti)
                df_up.loc[idx_to_mod, "assenti"] = ", ".join(nuovi_assenti)
                storage.save_convocazioni(df_up)
                st.success(f"Presenza confermata per **{nome_votante}**!")
                st.rerun()

        if btn_ass:
            if nome_votante in assenti_raw:
                st.warning(f"Sei già segnato come assente!")
            else:
                nuovi_assenti = assenti_raw + [nome_votante]
                nuovi_presenti = [p for p in presenti_raw if p != nome_votante]
                
                # Aggiorna
                df_up = df_convocazioni.copy()
                idx_to_mod = df_up[df_up["id_convocazione"] == id_conv].index
                df_up.loc[idx_to_mod, "presenti"] = ", ".join(nuovi_presenti)
                df_up.loc[idx_to_mod, "assenti"] = ", ".join(nuovi_assenti)
                storage.save_convocazioni(df_up)
                st.info(f"Assenza registrata per **{nome_votante}**.")
                st.rerun()

    # Visualizzazione Elenco Presenti e Assenti
    col_v_pres, col_v_ass = st.columns(2)
    with col_v_pres:
        st.markdown(f"#### 🟢 Presenti ({len(presenti_raw)})")
        if presenti_raw:
            for p in presenti_raw:
                st.write(f"- ⚽ **{p}**")
        else:
            st.caption("Nessun presente confermato.")

    with col_v_ass:
        st.markdown(f"#### 🔴 Assenti ({len(assenti_raw)})")
        if assenti_raw:
            for p in assenti_raw:
                st.write(f"- ❌ {p}")
        else:
            st.caption("Nessun assente segnalato.")

    # 3. GENERATORE AUTOMATICO SQUADRE EQUILIBRATE (SOLO ADMIN)
    st.markdown("---")
    st.markdown("### ⚖️ Generatore Automatico Squadre Equilibrate")
    
    if not is_admin:
        st.info("🔒 **Accesso Riservato:** La generazione delle formazioni equilibrate è riservata all'**Amministratore**.")
    else:
        st.caption("L'algoritmo combinatorio analizza tutte le 126 possibili suddivisioni dei 10 giocatori convocati per minimizzare lo scarto di forza ELO tra le due squadre.")
        
        # Scelta dei 10 giocatori
        if len(presenti_raw) == 10:
            selected_ten = presenti_raw
            st.success(f"Utilizzo automatico dei **10 convocati confermati**.")
        else:
            st.write("Seleziona manualmente i 10 giocatori da dividere:")
            selected_ten = st.multiselect(
                "Seleziona 10 giocatori:",
                options=lista_tutti_giocatori,
                default=presenti_raw[:10] if len(presenti_raw) >= 10 else presenti_raw,
                max_selections=10,
                key="manual_ten_select"
            )

        if st.button("⚡ Genera Formazioni Equilibrate", type="primary", use_container_width=True):
            if len(selected_ten) != 10:
                st.error(f"❌ Devi selezionare esattamente 10 giocatori (attualmente selezionati: {len(selected_ten)}).")
            else:
                elo_ratings, _ = logic.calculate_elo_ratings(df_giocatori, df_partite)
                balanced = logic.balance_teams(selected_ten, elo_ratings)
                
                st.session_state["last_balanced"] = balanced
                st.session_state["balanced_match_data"] = data_str

        if "last_balanced" in st.session_state and st.session_state["last_balanced"]:
            res = st.session_state["last_balanced"]
            elo_ratings, _ = logic.calculate_elo_ratings(df_giocatori, df_partite)
            
            st.markdown("#### 📋 Schieramento Tattico 2D & Bilanciamento Ottimale")
            
            # Rendering Campo da Calcio 2D
            ui_components.render_tactical_pitch(res["team_a"], res["team_b"], elo_ratings)
            
            b_col1, b_col2 = st.columns(2)
            with b_col1:
                st.markdown(f"""
                <div class="glass-card" style="border-top: 4px solid #FFD700;">
                    <h4 style="color: #FFD700; margin-top: 0;">🟨 Squadra A</h4>
                    <p><b>ELO Medio:</b> {res['elo_avg_a']} | <b>Totale:</b> {res['elo_sum_a']}</p>
                    <ul>
                        {''.join([f"<li><b>{p}</b> (ELO: {res['ratings_detail_a'].get(p, 1500)})</li>" for p in res['team_a']])}
                    </ul>
                </div>
                """, unsafe_allow_html=True)

            with b_col2:
                st.markdown(f"""
                <div class="glass-card" style="border-top: 4px solid #00E5FF;">
                    <h4 style="color: #00E5FF; margin-top: 0;">🟦 Squadra B</h4>
                    <p><b>ELO Medio:</b> {res['elo_avg_b']} | <b>Totale:</b> {res['elo_sum_b']}</p>
                    <ul>
                        {''.join([f"<li><b>{p}</b> (ELO: {res['ratings_detail_b'].get(p, 1500)})</li>" for p in res['team_b']])}
                    </ul>
                </div>
                """, unsafe_allow_html=True)

            st.info(f"⚖️ **Differenza ELO Totale:** {res['diff_elo']} punti (Diff. media per giocatore: {res['diff_avg_elo']} pt)")

            if st.button("🚀 Trasferisci formazioni per Registrare la Partita", use_container_width=True):
                st.session_state["prefill_team_a"] = res["team_a"]
                st.session_state["prefill_team_b"] = res["team_b"]
                st.session_state["nav_target"] = "➕ Aggiungi Nuova Partita"
                st.success("Formazioni pronte! Spostati nella sezione 'Aggiungi Nuova Partita'.")
                st.rerun()

    # 4. Pannello Gestione Sessione Admin
    if is_admin:
        st.markdown("---")
        with st.expander("⚙️ Gestione Convocazione (Pannello Admin)", expanded=False):
            c_adm1, c_adm2 = st.columns(2)
            with c_adm1:
                nuovo_stato = "Chiusa" if stato_str == "Aperta" else "Aperta"
                if st.button(f"{'🔒 Chiudi' if stato_str == 'Aperta' else '🔓 Riapri'} Sessione Convocazioni", use_container_width=True):
                    df_up = df_convocazioni.copy()
                    idx_to_mod = df_up[df_up["id_convocazione"] == id_conv].index
                    df_up.loc[idx_to_mod, "stato"] = nuovo_stato
                    storage.save_convocazioni(df_up)
                    st.success(f"Stato sessione impostato a **{nuovo_stato}**.")
                    st.rerun()

            with c_adm2:
                if st.button("🧹 Resetta Lista Presenze", use_container_width=True):
                    df_up = df_convocazioni.copy()
                    idx_to_mod = df_up[df_up["id_convocazione"] == id_conv].index
                    df_up.loc[idx_to_mod, "presenti"] = ""
                    df_up.loc[idx_to_mod, "assenti"] = ""
                    storage.save_convocazioni(df_up)
                    st.success("Elenco presenze azzerato.")
                    st.rerun()


# ==============================================================================
# 5. VISTA C: PAGELLE POST-PARTITA, REGISTRO VOTI & ELEZIONE MVP
# ==============================================================================
def view_pagelle(
    df_giocatori: pd.DataFrame, 
    df_partite: pd.DataFrame, 
    df_voti: pd.DataFrame, 
    is_admin: bool
):
    st.markdown("<div class='main-title'>⭐ Pagelle & Elezione MVP</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>Vota le prestazioni dei compagni di squadra, consulta il registro storico dei voti ed eleggi l'MVP del match</div>", unsafe_allow_html=True)

    if df_partite.empty:
        st.info("Nessuna partita disputata nello storico per cui assegnare voti.")
        return

    tab_vota, tab_registro, tab_mvp_season = st.tabs([
        "⭐ Pagelle Partita & Voto",
        "📜 Registro Storico Voti",
        "👑 Classifica MVP Stagione"
    ])

    # --------------------------------------------------------------------------
    # TAB 1: PAGELLE DELLA SINGOLA PARTITA & INSERIMENTO VOTI
    # --------------------------------------------------------------------------
    with tab_vota:
        # Selettore partita
        opzioni_partite = {}
        for _, m in df_partite.sort_values(by=["data", "id_partita"], ascending=[False, False]).iterrows():
            id_p = m.get("id_partita", "")
            d = m.get("data", "")
            g_a = m.get("gol_squadra_a", 0)
            g_b = m.get("gol_squadra_b", 0)
            lbl = f"Partita #{id_p} del {d} ({g_a} - {g_b})"
            opzioni_partite[lbl] = id_p

        scelta_p = st.selectbox("Seleziona la partita da esaminare:", options=list(opzioni_partite.keys()), key="pagelle_match_sel")
        selected_id_partita = opzioni_partite[scelta_p]

        # Dettagli partita
        match_row = df_partite[df_partite["id_partita"] == selected_id_partita].iloc[0]
        sq_a = [p.strip() for p in str(match_row.get("squadra_a_giocatori", "")).split(",") if p.strip()]
        sq_b = [p.strip() for p in str(match_row.get("squadra_b_giocatori", "")).split(",") if p.strip()]
        tutti_partecipanti = sorted(list(set(sq_a + sq_b)))

        # Calcolo valutazioni partita
        eval_res = logic.calculate_match_ratings(df_voti, selected_id_partita)

        st.markdown("---")

        # Resoconto Automatico MVP & Peggiore
        if eval_res["has_votes"]:
            c_mvp, c_worst = st.columns(2)
            with c_mvp:
                if eval_res["mvp"]:
                    st.markdown(f"""
                    <div class="card-mvp">
                        <div style="font-size: 2.2rem; margin-bottom: 5px;">👑</div>
                        <h3 style="color: #fbbf24; margin: 0;">MVP DELLA PARTITA</h3>
                        <h2 style="color: #ffffff; margin: 6px 0;">{eval_res['mvp']['giocatore']}</h2>
                        <p style="font-size: 1.15rem; color: #38bdf8; margin: 0;"><b>Media Voto: {eval_res['mvp']['media']} / 10</b></p>
                        <span style="font-size: 0.85rem; color: #94a3b8;">({eval_res['mvp']['voti_ricevuti']} valutazioni ricevute)</span>
                    </div>
                    """, unsafe_allow_html=True)

            with c_worst:
                if eval_res["worst"] and eval_res["worst"]["giocatore"] != eval_res["mvp"]["giocatore"]:
                    st.markdown(f"""
                    <div class="card-worst">
                        <div style="font-size: 2.2rem; margin-bottom: 5px;">🧊</div>
                        <h3 style="color: #ef4444; margin: 0;">MENZIONE PEGGIORE</h3>
                        <h2 style="color: #ffffff; margin: 6px 0;">{eval_res['worst']['giocatore']}</h2>
                        <p style="font-size: 1.15rem; color: #f87171; margin: 0;"><b>Media Voto: {eval_res['worst']['media']} / 10</b></p>
                        <span style="font-size: 0.85rem; color: #94a3b8;">({eval_res['worst']['voti_ricevuti']} valutazioni ricevute)</span>
                    </div>
                    """, unsafe_allow_html=True)

            # Tabella Pagelle Medie
            st.markdown("#### 📊 Medie Voto Giocatori")
            st.dataframe(
                eval_res["ratings"],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Giocatore": st.column_config.TextColumn("Giocatore", width="medium"),
                    "Media Voto": st.column_config.NumberColumn("⭐ Media Voto", format="%.2f"),
                    "Numero Voti": st.column_config.NumberColumn("N° Voti"),
                    "Min": st.column_config.NumberColumn("Min"),
                    "Max": st.column_config.NumberColumn("Max"),
                }
            )

            # Commenti ricevuti
            if eval_res["comments"]:
                st.markdown("#### 💬 Commenti e Pagelle della Community")
                for c in eval_res["comments"]:
                    st.markdown(f"""
                    <div class="glass-card" style="padding: 10px 14px; margin-bottom: 8px;">
                        <b>{c['votante']}</b> su <b>{c['giocatore']}</b> (Voto: <span style="color: #fbbf24; font-weight: bold;">{c['voto']}</span>):<br>
                        <span style="color: #cbd5e1; font-style: italic;">"{c['commento']}"</span>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.info("Nessuna votazione ancora inserita per questa partita. Compila le pagelle qui sotto per eleggere l'MVP!")

        st.markdown("---")

        # Form di Votazione Post-Partita
        st.markdown("### 📝 Compila la tua Pagella")
        lista_tutti_giocatori = sorted(df_giocatori["nome_completo"].dropna().unique().tolist()) if not df_giocatori.empty else []

        with st.form("form_voti_partita", clear_on_submit=False):
            votante = st.selectbox("Chi sta votando? (Seleziona il tuo nome):", options=lista_tutti_giocatori, key="votante_select")
            
            st.markdown("##### Assegna voto e commento ai protagonisti del match:")
            
            voti_input = {}
            commenti_input = {}

            for p in tutti_partecipanti:
                col_v1, col_v2 = st.columns([1, 2])
                with col_v1:
                    voti_input[p] = st.slider(f"Voto per **{p}**", min_value=1.0, max_value=10.0, value=6.0, step=0.5, key=f"voto_{p}")
                with col_v2:
                    commenti_input[p] = st.text_input(f"Commento per {p}", placeholder="es. Impeccabile in difesa", key=f"comm_{p}")

            submit_pagella = st.form_submit_button("🗳️ Invia Pagella e Salva Valutazioni", use_container_width=True, type="primary")

            if submit_pagella:
                nuovi_voti_list = []
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                # ID progressivo
                next_id = 1
                if not df_voti.empty and "id_voto" in df_voti.columns:
                    next_id = int(df_voti["id_voto"].max()) + 1

                for p in tutti_partecipanti:
                    v = voti_input[p]
                    comm = commenti_input[p].strip()
                    nuovi_voti_list.append({
                        "id_voto": next_id,
                        "id_partita": int(selected_id_partita),
                        "votante": votante,
                        "giocatore": p,
                        "voto": float(v),
                        "commento": comm,
                        "timestamp": now_str
                    })
                    next_id += 1

                df_updated_voti = pd.concat([df_voti, pd.DataFrame(nuovi_voti_list)], ignore_index=True)
                storage.save_voti(df_updated_voti)
                st.success("✅ Pagella inviata con successo! I voti e le medie sono stati ricalcolati.")
                st.rerun()

    # --------------------------------------------------------------------------
    # TAB 2: REGISTRO STORICO COMPLETO DEI VOTI & MODERAZIONE ADMIN
    # --------------------------------------------------------------------------
    with tab_registro:
        st.markdown("### 📜 Registro Storico Completo dei Voti Espressi")
        st.caption("Archivio dettagliato di tutte le singole votazioni registrate nel sistema.")

        # Pannello Moderazione Voti (Admin Only)
        if is_admin:
            with st.expander("🛡️ Pannello di Moderazione & Cancellazione Voti (Solo Admin)", expanded=False):
                st.caption("Elimina singoli voti errati/fasulli o ripulisci le votazioni di un intero match. L'eliminazione ricalcola istantaneamente le medie e i titoli MVP.")
                
                if df_voti.empty:
                    st.info("Nessun voto presente nel database da moderare.")
                else:
                    col_mod1, col_mod2 = st.columns(2)
                    
                    # 1. Cancellazione Singolo Voto
                    with col_mod1:
                        st.markdown("##### 🗑️ Elimina Singolo Voto")
                        opzioni_voti_dict = {}
                        for _, v_row in df_voti.sort_values(by=["id_voto"], ascending=False).iterrows():
                            v_id = int(v_row.get("id_voto", 0))
                            p_id = v_row.get("id_partita", "")
                            vot = v_row.get("votante", "")
                            gio = v_row.get("giocatore", "")
                            val = v_row.get("voto", "")
                            t_stamp = str(v_row.get("timestamp", ""))[:16]
                            label_v = f"Voto #{v_id} [Match #{p_id}] - Da: {vot} ➔ A: {gio} ({val}) ({t_stamp})"
                            opzioni_voti_dict[label_v] = v_id
                        
                        voto_scelto_str = st.selectbox("Seleziona il voto da eliminare:", options=list(opzioni_voti_dict.keys()), key="select_del_voto_admin")
                        id_voto_da_eliminare = opzioni_voti_dict[voto_scelto_str]
                        
                        # Mostra dettagli del voto selezionato
                        voto_dettaglio = df_voti[df_voti["id_voto"] == id_voto_da_eliminare].iloc[0]
                        comm_txt = voto_dettaglio.get("commento", "")
                        if comm_txt:
                            st.caption(f"💬 Commento associato: *\"{comm_txt}\"*")

                        if st.button("🗑️ Elimina Voto Selezionato", type="primary", use_container_width=True, key="btn_del_single_voto"):
                            storage.delete_voto(id_voto_da_eliminare)
                            st.success(f"✅ Voto #{id_voto_da_eliminare} eliminato con successo! Medie ricalcolate.")
                            st.rerun()

                    # 2. Cancellazione Voti per Partita
                    with col_mod2:
                        st.markdown("##### 🧹 Ripulisci Voti di una Partita")
                        opzioni_partite_voti = sorted(df_voti["id_partita"].unique().tolist())
                        partita_da_pulire = st.selectbox("Seleziona la partita da ripulire:", options=opzioni_partite_voti, key="select_del_voti_match_admin")
                        voti_partita_count = len(df_voti[df_voti["id_partita"] == partita_da_pulire])
                        st.caption(f"Voti registrati per Partita #{partita_da_pulire}: **{voti_partita_count}**")

                        if st.button(f"🧹 Elimina tutti i {voti_partita_count} voti di Partita #{partita_da_pulire}", use_container_width=True, key="btn_del_match_voti"):
                            storage.delete_voti_partita(partita_da_pulire)
                            st.success(f"✅ Tutti i voti della Partita #{partita_da_pulire} sono stati eliminati!")
                            st.rerun()

            st.markdown("---")

        # Visualizzazione Tabella Voti
        if df_voti.empty:
            st.info("Nessun voto registrato finora.")
        else:
            # Creazione vista arricchita con data partita se disponibile
            df_voti_view = df_voti.copy()
            if not df_partite.empty and "id_partita" in df_partite.columns and "data" in df_partite.columns:
                date_map = dict(zip(df_partite["id_partita"], df_partite["data"]))
                df_voti_view["Data Match"] = df_voti_view["id_partita"].map(date_map).fillna("N/D")
            else:
                df_voti_view["Data Match"] = "N/D"

            df_voti_view = df_voti_view.sort_values(by=["id_voto"], ascending=False).reset_index(drop=True)

            # Filtri consultazione
            c_f1, c_f2 = st.columns(2)
            with c_f1:
                filtro_giocatore_voti = st.selectbox("Filtra per Giocatore Votato:", options=["Tutti"] + sorted(df_voti_view["giocatore"].dropna().unique().tolist()), key="filtro_gio_voti")
            with c_f2:
                filtro_partita_voti = st.selectbox("Filtra per Partita:", options=["Tutte"] + [f"Partita #{p}" for p in sorted(df_voti_view["id_partita"].unique().tolist())], key="filtro_match_voti")

            if filtro_giocatore_voti != "Tutti":
                df_voti_view = df_voti_view[df_voti_view["giocatore"] == filtro_giocatore_voti]
            if filtro_partita_voti != "Tutte":
                p_id_filter = int(filtro_partita_voti.replace("Partita #", ""))
                df_voti_view = df_voti_view[df_voti_view["id_partita"] == p_id_filter]

            cols_reg = ["id_voto", "id_partita", "Data Match", "votante", "giocatore", "voto", "commento", "timestamp"]
            st.dataframe(
                df_voti_view[cols_reg],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id_voto": st.column_config.NumberColumn("ID Voto", width="small"),
                    "id_partita": st.column_config.NumberColumn("Partita #", width="small"),
                    "Data Match": st.column_config.TextColumn("Data Match", width="small"),
                    "votante": st.column_config.TextColumn("Votante", width="medium"),
                    "giocatore": st.column_config.TextColumn("Giocatore Votato", width="medium"),
                    "voto": st.column_config.NumberColumn("Voto", format="%.1f"),
                    "commento": st.column_config.TextColumn("Commento", width="large"),
                    "timestamp": st.column_config.TextColumn("Data/Ora Invio", width="medium"),
                }
            )

    # --------------------------------------------------------------------------
    # TAB 3: CLASSIFICA MVP STAGIONALE
    # --------------------------------------------------------------------------
    with tab_mvp_season:
        st.markdown("### 👑 Classifica Stagionale MVP")
        st.caption("Riepilogo generale dei titoli MVP conquistati e delle valutazioni medie stagionali.")
        df_season_mvp = logic.calculate_season_mvp_leaderboard(df_partite, df_voti)

        if df_season_mvp.empty:
            st.info("Nessuna valutazione registrata per stilare la classifica stagionale.")
        else:
            df_season_mvp["Pos."] = range(1, len(df_season_mvp) + 1)
            st.dataframe(
                df_season_mvp[["Pos.", "Giocatore", "Titoli MVP", "Media Voto Stagionale", "Voti Ricevuti"]],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Pos.": st.column_config.NumberColumn("Pos.", width="small"),
                    "Giocatore": st.column_config.TextColumn("Giocatore", width="medium"),
                    "Titoli MVP": st.column_config.NumberColumn("👑 Titoli MVP", help="Numero di volte MVP"),
                    "Media Voto Stagionale": st.column_config.NumberColumn("⭐ Media Voto", format="%.2f"),
                    "Voti Ricevuti": st.column_config.NumberColumn("Voti Totali"),
                }
            )


# ==============================================================================
# 6. VISTA D: AGGIUNGI NUOVA PARTITA (ADMIN ONLY)
# ==============================================================================
def view_add_match(
    df_giocatori: pd.DataFrame, 
    df_partite: pd.DataFrame, 
    is_admin: bool
):
    st.markdown("<div class='main-title'>➕ Registra Nuova Partita</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>Inserisci data, formazioni 5 vs 5 e gol individuali per i marcatori</div>", unsafe_allow_html=True)

    if not is_admin:
        st.warning("🔒 **Accesso Riservato:** Questa operazione è riservata all'Amministratore.")
        return

    lista_giocatori = sorted(df_giocatori["nome_completo"].dropna().unique().tolist()) if not df_giocatori.empty else []
    
    if len(lista_giocatori) < 10:
        st.warning(f"⚠️ Servono almeno 10 giocatori registrati nell'anagrafica per creare una partita 5 vs 5. Attualmente disponibili: **{len(lista_giocatori)}**.")
        st.info("👉 Vai nella sezione **'👥 Anagrafica Giocatori'** per iscrivere nuovi amici.")
        return

    # Prefill da Convocazioni se presente
    prefill_a = st.session_state.get("prefill_team_a", [])
    prefill_b = st.session_state.get("prefill_team_b", [])

    # Filtra solo quelli effettivamente esistenti in lista_giocatori
    valid_prefill_a = [p for p in prefill_a if p in lista_giocatori][:5]
    valid_prefill_b = [p for p in prefill_b if p in lista_giocatori][:5]

    data_partita = st.date_input("📅 Data Partita", value=date.today())

    st.markdown("---")
    st.markdown("#### 👥 Formazioni (Esattamente 5 giocatori per squadra)")
    
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        st.markdown("##### 🟦 Squadra A")
        sq_a = st.multiselect(
            "Seleziona i 5 giocatori di Squadra A:",
            options=lista_giocatori,
            default=valid_prefill_a,
            max_selections=5,
            key="multiselect_sq_a",
            help="Seleziona esattamente 5 giocatori"
        )
        st.caption(f"Selezionati: {len(sq_a)}/5")
        
    with f_col2:
        st.markdown("##### 🟥 Squadra B")
        sq_b = st.multiselect(
            "Seleziona i 5 giocatori di Squadra B:",
            options=lista_giocatori,
            default=valid_prefill_b,
            max_selections=5,
            key="multiselect_sq_b",
            help="Seleziona esattamente 5 giocatori"
        )
        st.caption(f"Selezionati: {len(sq_b)}/5")

    st.markdown("---")
    st.markdown("#### ⚽ Risultato Finale & Marcatori Individuali")

    r_col1, r_col2 = st.columns(2)
    with r_col1:
        gol_a = st.number_input("Gol Totali Squadra A 🟦", min_value=0, max_value=50, value=0, step=1, key="gol_tot_a")
    with r_col2:
        gol_b = st.number_input("Gol Totali Squadra B 🟥", min_value=0, max_value=50, value=0, step=1, key="gol_tot_b")

    # Inserimento Marcatori Individuali
    marcatori_dict = {}
    if len(sq_a) == 5 and len(sq_b) == 5:
        st.markdown("##### 🎯 Dettaglio Gol per Giocatore:")
        col_m_a, col_m_b = st.columns(2)
        with col_m_a:
            st.markdown("###### Gol Giocatori Squadra A:")
            for p in sq_a:
                marcatori_dict[p] = st.number_input(f"Gol di {p}", min_value=0, max_value=30, value=0, step=1, key=f"goals_a_{p}")

        with col_m_b:
            st.markdown("###### Gol Giocatori Squadra B:")
            for p in sq_b:
                marcatori_dict[p] = st.number_input(f"Gol di {p}", min_value=0, max_value=30, value=0, step=1, key=f"goals_b_{p}")

    st.markdown("---")
    submit_partita = st.button("💾 Salva Partita e Aggiorna Classifiche", use_container_width=True, type="primary")

    if submit_partita:
        errori = []
        
        if len(sq_a) != 5:
            errori.append(f"La Squadra A deve contenere esattamente 5 giocatori (selezionati: {len(sq_a)}).")
            
        if len(sq_b) != 5:
            errori.append(f"La Squadra B deve contenere esattamente 5 giocatori (selezionati: {len(sq_b)}).")
            
        duplicati = set(sq_a).intersection(set(sq_b))
        if duplicati:
            errori.append(f"I seguenti giocatori sono in entrambe le squadre: {', '.join(duplicati)}.")

        # Validazione quadratura gol individuali vs gol totali
        if len(sq_a) == 5 and len(sq_b) == 5:
            sum_gol_a = sum(marcatori_dict.get(p, 0) for p in sq_a)
            sum_gol_b = sum(marcatori_dict.get(p, 0) for p in sq_b)

            if sum_gol_a != gol_a:
                errori.append(f"La somma dei gol individuali di Squadra A ({sum_gol_a}) non coincide con i Gol Totali inseriti ({gol_a}).")
            if sum_gol_b != gol_b:
                errori.append(f"La somma dei gol individuali di Squadra B ({sum_gol_b}) non coincide con i Gol Totali inseriti ({gol_b}).")

        if errori:
            for err in errori:
                st.error(f"❌ {err}")
        else:
            if gol_a > gol_b:
                esito = "Vittoria Squadra A"
            elif gol_b > gol_a:
                esito = "Vittoria Squadra B"
            else:
                esito = "Pareggio"

            nuovo_id = 1
            if not df_partite.empty and "id_partita" in df_partite.columns:
                nuovo_id = int(df_partite["id_partita"].max()) + 1

            marcatori_json = logic.serialize_marcatori(marcatori_dict)

            nuova_riga = {
                "id_partita": nuovo_id,
                "data": data_partita.strftime("%Y-%m-%d"),
                "squadra_a_giocatori": ", ".join(sq_a),
                "squadra_b_giocatori": ", ".join(sq_b),
                "gol_squadra_a": int(gol_a),
                "gol_squadra_b": int(gol_b),
                "esito": esito,
                "marcatori": marcatori_json
            }

            df_updated = pd.concat([df_partite, pd.DataFrame([nuova_riga])], ignore_index=True)
            storage.save_partite(df_updated)
            
            # Svuota prefill se era attivo
            st.session_state.pop("prefill_team_a", None)
            st.session_state.pop("prefill_team_b", None)
            
            st.success("✅ Partita registrata con successo! Rating ELO e classifiche aggiornati.")
            st.balloons()
            st.rerun()


# ==============================================================================
# 7. VISTA E: ANAGRAFICA GIOCATORI (ADMIN ONLY MODIFICATIONS)
# ==============================================================================
def view_anagrafica(
    df_giocatori: pd.DataFrame, 
    df_partite: pd.DataFrame, 
    is_admin: bool
):
    st.markdown("<div class='main-title'>👤 Anagrafica Giocatori</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>Gestione del gruppo, anagrafica e appartenenza alla Cerchia Ristretta</div>", unsafe_allow_html=True)

    if not is_admin:
        st.info("👁️ **Modalità Sola Lettura:** Puoi consultare l'elenco dei giocatori iscritti. L'aggiunta o modifica è riservata all'Amministratore.")
    else:
        # Inserimento nuovo giocatore
        with st.form("form_nuovo_giocatore", clear_on_submit=True):
            col_n1, col_n2 = st.columns([3, 2])
            with col_n1:
                nome_input = st.text_input("Nome e Cognome del Giocatore", placeholder="es. Mario Rossi")
            with col_n2:
                st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
                in_gruppo_check = st.checkbox("⭐ Includi nella Cerchia Ristretta", value=False)

            submit_giocatore = st.form_submit_button("➕ Aggiungi Giocatore", use_container_width=True)

            if submit_giocatore:
                nome_clean = nome_input.strip()
                if not nome_clean:
                    st.error("❌ Il nome del giocatore non può essere vuoto.")
                else:
                    nomi_esistenti = [str(n).strip().lower() for n in df_giocatori["nome_completo"].dropna().tolist()] if not df_giocatori.empty else []
                    if nome_clean.lower() in nomi_esistenti:
                        st.error(f"❌ Esiste già un giocatore registrato con il nome '{nome_clean}'.")
                    else:
                        nuovo_id = 1
                        if not df_giocatori.empty and "id_giocatore" in df_giocatori.columns:
                            nuovo_id = int(df_giocatori["id_giocatore"].max()) + 1

                        nuova_riga = {
                            "id_giocatore": nuovo_id,
                            "nome_completo": nome_clean,
                            "data_creazione": date.today().strftime("%Y-%m-%d"),
                            "in_gruppo_ristretto": bool(in_gruppo_check)
                        }

                        df_updated = pd.concat([df_giocatori, pd.DataFrame([nuova_riga])], ignore_index=True)
                        storage.save_giocatori(df_updated)
                        st.success(f"✅ Giocatore **{nome_clean}** aggiunto con successo (ID #{nuovo_id})!")
                        st.rerun()

        # Gestione Rapida Cerchia Ristretta
        with st.expander("⭐ Gestione Rapida Cerchia Ristretta", expanded=False):
            st.caption("Attiva o disattiva l'appartenenza alla cerchia ristretta con un clic:")
            if not df_giocatori.empty:
                for _, p_row in df_giocatori.sort_values(by="nome_completo").iterrows():
                    p_id = int(p_row["id_giocatore"])
                    p_name = str(p_row["nome_completo"])
                    p_status = bool(p_row.get("in_gruppo_ristretto", False))
                    
                    cg1, cg2 = st.columns([3, 1])
                    with cg1:
                        badge_icon = "⭐ **Cerchia Ristretta**" if p_status else "👤 *Esterno / Occasionale*"
                        st.write(f"**{p_name}** — {badge_icon}")
                    with cg2:
                        btn_label = "Rimuovi ❌" if p_status else "Aggiungi ⭐"
                        if st.button(btn_label, key=f"anag_toggle_{p_id}", use_container_width=True):
                            storage.toggle_giocatore_gruppo_ristretto(p_id, not p_status)
                            st.rerun()

        # Eliminazione Giocatore
        with st.expander("🗑️ Elimina un Giocatore", expanded=False):
            if df_giocatori.empty:
                st.info("Nessun giocatore registrato da eliminare.")
            else:
                lista_nomi_del = sorted(df_giocatori["nome_completo"].dropna().unique().tolist())
                del_player = st.selectbox("Seleziona il giocatore da eliminare:", options=lista_nomi_del, key="select_del_player")
                
                partite_con_giocatore = 0
                if not df_partite.empty:
                    for _, m in df_partite.iterrows():
                        raw = str(m.get("squadra_a_giocatori", "")) + ", " + str(m.get("squadra_b_giocatori", ""))
                        if del_player in [p.strip() for p in raw.split(",")]:
                            partite_con_giocatore += 1
                
                if partite_con_giocatore > 0:
                    st.warning(f"⚠️ **{del_player}** è presente in **{partite_con_giocatore}** partita/e registrata/e.")

                btn_del_gio = st.button(f"🗑️ Elimina '{del_player}'", type="primary", use_container_width=True, key="btn_del_single_player")
                if btn_del_gio:
                    df_updated = df_giocatori[df_giocatori["nome_completo"] != del_player].copy()
                    storage.save_giocatori(df_updated)
                    st.success(f"✅ Giocatore **{del_player}** eliminato!")
                    st.rerun()

    st.markdown("---")
    st.markdown(f"### 📋 Elenco Giocatori Iscritti ({len(df_giocatori)})")
    
    if df_giocatori.empty:
        st.info("Nessun giocatore registrato.")
    else:
        df_view = df_giocatori.sort_values(by="id_giocatore", ascending=True).copy()
        if "in_gruppo_ristretto" in df_view.columns:
            df_view["Cerchia Ristretta"] = df_view["in_gruppo_ristretto"].apply(lambda x: "⭐ Membro Fisso" if bool(x) else "👤 Occasionale")
        else:
            df_view["Cerchia Ristretta"] = "👤 Occasionale"

        st.dataframe(
            df_view[["id_giocatore", "nome_completo", "Cerchia Ristretta", "data_creazione"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "id_giocatore": st.column_config.NumberColumn("ID", width="small"),
                "nome_completo": st.column_config.TextColumn("Nome Completo", width="medium"),
                "Cerchia Ristretta": st.column_config.TextColumn("Status Gruppo", width="medium", help="Appartenenza al Gruppo Ristretto"),
                "data_creazione": st.column_config.TextColumn("Data Iscrizione", width="small"),
            }
        )


# ==============================================================================
# 8. VISTA F: STORICO PARTITE (VIEW + ADMIN EDIT & DELETE)
# ==============================================================================
def view_match_history(
    df_giocatori: pd.DataFrame,
    df_partite: pd.DataFrame, 
    is_admin: bool,
    df_voti: Optional[pd.DataFrame] = None
):
    st.markdown("<div class='main-title'>📜 Storico Partite</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>Archivio in stile Champions League di tutte le sfide disputate con marcatori, formazioni e MVP</div>", unsafe_allow_html=True)

    if df_partite.empty:
        st.info("Nessuna partita presente nello storico.")
        return

    lista_tutti_giocatori = sorted(df_giocatori["nome_completo"].dropna().unique().tolist()) if not df_giocatori.empty else []

    # Sezione Funzionalità Amministratore (Modifica & Cancellazione)
    if is_admin:
        tab_admin_edit, tab_admin_del = st.tabs(["✏️ Modifica Partita Pregressa", "🗑️ Elimina Partita"])

        # TAB MODIFICA PARTITA
        with tab_admin_edit:
            st.caption("Modifica data, formazioni 5 vs 5, risultato e **assegna retroattivamente i marcatori individuali** per qualsiasi partita passata.")
            
            opzioni_edit_partite = {}
            for _, m in df_partite.sort_values(by=["data", "id_partita"], ascending=[False, False]).iterrows():
                id_p = m.get("id_partita", "")
                d = m.get("data", "")
                g_a = m.get("gol_squadra_a", 0)
                g_b = m.get("gol_squadra_b", 0)
                esito = m.get("esito", "")
                label = f"Partita #{id_p} del {d} — A ({g_a}) vs B ({g_b}) [{esito}]"
                opzioni_edit_partite[label] = id_p

            match_scelto_str = st.selectbox("Seleziona la partita da modificare:", options=list(opzioni_edit_partite.keys()), key="select_edit_match_admin")
            id_partita_da_modificare = opzioni_edit_partite[match_scelto_str]

            # Carica dati attuali partita
            match_curr = df_partite[df_partite["id_partita"] == id_partita_da_modificare].iloc[0]
            
            # Data di default
            try:
                data_curr = datetime.strptime(str(match_curr.get("data", "")), "%Y-%m-%d").date()
            except Exception:
                data_curr = date.today()

            sq_a_curr = [p.strip() for p in str(match_curr.get("squadra_a_giocatori", "")).split(",") if p.strip()]
            sq_b_curr = [p.strip() for p in str(match_curr.get("squadra_b_giocatori", "")).split(",") if p.strip()]
            gol_a_curr = int(match_curr.get("gol_squadra_a", 0))
            gol_b_curr = int(match_curr.get("gol_squadra_b", 0))
            marcatori_curr = logic.parse_marcatori(match_curr.get("marcatori", ""))

            # Form di modifica
            with st.form(f"form_edit_match_{id_partita_da_modificare}", clear_on_submit=False):
                data_mod = st.date_input("📅 Data Partita", value=data_curr, key=f"edit_data_{id_partita_da_modificare}")

                col_ed_a, col_ed_b = st.columns(2)
                with col_ed_a:
                    st.markdown("##### 🟨 Squadra A")
                    # Assicurati che i default siano nella lista opzioni
                    valid_sq_a_defs = [p for p in sq_a_curr if p in lista_tutti_giocatori][:5]
                    sq_a_mod = st.multiselect(
                        "5 Giocatori Squadra A:",
                        options=lista_tutti_giocatori,
                        default=valid_sq_a_defs,
                        max_selections=5,
                        key=f"edit_sq_a_{id_partita_da_modificare}"
                    )
                    st.caption(f"Selezionati: {len(sq_a_mod)}/5")
                    gol_a_mod = st.number_input("Gol Totali Squadra A 🟨", min_value=0, max_value=50, value=gol_a_curr, step=1, key=f"edit_gol_a_{id_partita_da_modificare}")

                with col_ed_b:
                    st.markdown("##### 🟦 Squadra B")
                    valid_sq_b_defs = [p for p in sq_b_curr if p in lista_tutti_giocatori][:5]
                    sq_b_mod = st.multiselect(
                        "5 Giocatori Squadra B:",
                        options=lista_tutti_giocatori,
                        default=valid_sq_b_defs,
                        max_selections=5,
                        key=f"edit_sq_b_{id_partita_da_modificare}"
                    )
                    st.caption(f"Selezionati: {len(sq_b_mod)}/5")
                    gol_b_mod = st.number_input("Gol Totali Squadra B 🟦", min_value=0, max_value=50, value=gol_b_curr, step=1, key=f"edit_gol_b_{id_partita_da_modificare}")

                st.markdown("##### 🎯 Assegnazione Gol Individuali Marcatori")
                marcatori_mod_dict = {}

                col_gm_a, col_gm_b = st.columns(2)
                with col_gm_a:
                    st.markdown("###### Gol Giocatori Squadra A:")
                    for p in sq_a_mod:
                        val_prev = int(marcatori_curr.get(p, 0))
                        marcatori_mod_dict[p] = st.number_input(f"Gol di {p}", min_value=0, max_value=30, value=val_prev, step=1, key=f"edit_goals_a_{id_partita_da_modificare}_{p}")

                with col_gm_b:
                    st.markdown("###### Gol Giocatori Squadra B:")
                    for p in sq_b_mod:
                        val_prev = int(marcatori_curr.get(p, 0))
                        marcatori_mod_dict[p] = st.number_input(f"Gol di {p}", min_value=0, max_value=30, value=val_prev, step=1, key=f"edit_goals_b_{id_partita_da_modificare}_{p}")

                salva_modifiche_btn = st.form_submit_button("💾 Salva Modifiche Partita", type="primary", use_container_width=True)

                if salva_modifiche_btn:
                    errs = []
                    if len(sq_a_mod) != 5:
                        errs.append(f"La Squadra A deve contenere esattamente 5 giocatori (selezionati: {len(sq_a_mod)}).")
                    if len(sq_b_mod) != 5:
                        errs.append(f"La Squadra B deve contenere esattamente 5 giocatori (selezionati: {len(sq_b_mod)}).")
                    
                    dupls = set(sq_a_mod).intersection(set(sq_b_mod))
                    if dupls:
                        errs.append(f"Giocatori assegnati a entrambe le squadre: {', '.join(dupls)}")

                    sum_gol_indiv = sum(marcatori_mod_dict.values())
                    tot_gol_dichiarati = gol_a_mod + gol_b_mod
                    if sum_gol_indiv > tot_gol_dichiarati:
                        errs.append(f"La somma dei gol individuali ({sum_gol_indiv}) supera il totale gol del match ({tot_gol_dichiarati}).")

                    if errs:
                        for e in errs:
                            st.error(f"❌ {e}")
                    else:
                        if gol_a_mod > gol_b_mod:
                            esito_mod = "Vittoria Squadra A"
                        elif gol_b_mod > gol_a_mod:
                            esito_mod = "Vittoria Squadra B"
                        else:
                            esito_mod = "Pareggio"

                        marcatori_clean = {k: int(v) for k, v in marcatori_mod_dict.items() if int(v) > 0}
                        marcatori_json_mod = logic.serialize_marcatori(marcatori_clean)

                        update_payload = {
                            "data": data_mod.strftime("%Y-%m-%d"),
                            "squadra_a_giocatori": ", ".join(sq_a_mod),
                            "squadra_b_giocatori": ", ".join(sq_b_mod),
                            "gol_squadra_a": int(gol_a_mod),
                            "gol_squadra_b": int(gol_b_mod),
                            "esito": esito_mod,
                            "marcatori": marcatori_json_mod
                        }

                        storage.update_partita(id_partita_da_modificare, update_payload)
                        st.success(f"✅ Partita #{id_partita_da_modificare} aggiornata con successo! Tutte le classifiche ed ELO sono stati ricalcolati.")
                        st.rerun()

        # TAB CANCELLAZIONE PARTITA
        with tab_admin_del:
            opzioni_del_partite = {}
            for _, m in df_partite.sort_values(by=["data", "id_partita"], ascending=[False, False]).iterrows():
                id_p = m.get("id_partita", "")
                d = m.get("data", "")
                g_a = m.get("gol_squadra_a", 0)
                g_b = m.get("gol_squadra_b", 0)
                esito = m.get("esito", "")
                label = f"Partita #{id_p} del {d} — A ({g_a}) vs B ({g_b}) [{esito}]"
                opzioni_del_partite[label] = id_p

            scelta_del_str = st.selectbox("Seleziona la partita da eliminare:", options=list(opzioni_del_partite.keys()), key="select_del_match_tab")
            id_da_eliminare = opzioni_del_partite[scelta_del_str]

            if st.button("🗑️ Elimina Partita Selezionata", type="primary", use_container_width=True, key="btn_del_match_tab"):
                df_updated = df_partite[df_partite["id_partita"] != id_da_eliminare].copy()
                storage.save_partite(df_updated)
                st.success("✅ Partita eliminata con successo!")
                st.rerun()

        st.markdown("---")

    # Ordinamento cronologico inverso e rendering Champions League Match Cards
    df_sorted = df_partite.sort_values(by=["data", "id_partita"], ascending=[False, False]).reset_index(drop=True)

    for idx, match in df_sorted.iterrows():
        id_p = match.get("id_partita", idx + 1)
        
        # Recupero MVP per il match
        mvp_name = None
        mvp_avg = None
        if df_voti is not None and not df_voti.empty:
            match_ratings = logic.calculate_match_ratings(df_voti, id_p)
            if match_ratings.get("has_votes") and match_ratings.get("mvp"):
                mvp_name = match_ratings["mvp"].get("giocatore")
                mvp_avg = match_ratings["mvp"].get("media")

        # Rendering Champions League Match Card
        ui_components.render_champions_scoreboard(match, mvp_name=mvp_name, mvp_avg=mvp_avg)


# ==============================================================================
# 9. MAIN ROUTER & APP
# ==============================================================================
def main():
    # Inizializzazione Session State
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "user_role" not in st.session_state:
        st.session_state["user_role"] = "viewer"

    # Controllo Autenticazione PIN Gate
    if not st.session_state["authenticated"]:
        render_pin_gate()
        return

    is_admin = (st.session_state.get("user_role") == "admin")

    # Caricamento Dati
    df_giocatori, df_partite, df_convocazioni, df_voti, storage_source, storage_error = storage.load_data()

    # Sidebar
    with st.sidebar:
        st.markdown("### ⚽ Calcetto Manager")
        
        # Badge Ruolo
        if is_admin:
            st.markdown("<span class='role-badge-admin'>🛡️ AMMINISTRATORE</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span class='role-badge-viewer'>👁️ SOLA LETTURA (VIEWER)</span>", unsafe_allow_html=True)

        st.caption(f"Persistenza: **{storage_source}**")

        # Diagnostica Fallback Google Sheets
        if storage_error and storage_source != "Google Sheets (Cloud)":
            with st.expander("⚠️ Diagnostica Fallback GSheets", expanded=True):
                st.warning(f"**Dettaglio Errore:**\n\n{storage_error}")
                if st.button("🔄 Riprova Connessione GSheets", key="btn_retry_gsheets_sidebar", use_container_width=True):
                    st.cache_data.clear()
                    st.rerun()

        st.markdown("---")

        opzioni_menu = [
            "🏆 Tabellone & Classifiche",
            "🏆 Classifica Amici (Gruppo Ristretto)",
            "📅 Convocazioni & Presenze",
            "⭐ Pagelle & MVP",
            "➕ Aggiungi Nuova Partita",
            "👤 Anagrafica Giocatori",
            "📜 Storico Partite"
        ]

        target_nav = st.session_state.pop("nav_target", None)
        default_index = opzioni_menu.index(target_nav) if target_nav in opzioni_menu else 0

        scelta_menu = st.radio(
            "Navigazione Sezioni:",
            options=opzioni_menu,
            index=default_index
        )

        st.markdown("---")

        # Gestione Admin / Reset (Solo Admin)
        if is_admin:
            with st.expander("⚙️ Gestione & Reset Dati", expanded=False):
                st.caption("Strumenti amministrativi per la gestione rapida dell'archivio.")
                
                # Reset Dati Demo
                if st.button("🔄 Ripristina Dati Esempio", use_container_width=True):
                    storage.reset_all_to_demo()
                    st.success("Dati demo ripristinati!")
                    st.rerun()

                # Svuota Partite
                if st.button("🧹 Svuota Tutte le Partite", use_container_width=True):
                    storage.save_partite(pd.DataFrame(columns=["id_partita", "data", "squadra_a_giocatori", "squadra_b_giocatori", "gol_squadra_a", "gol_squadra_b", "esito", "marcatori"]))
                    st.success("Tutte le partite sono state rimosse.")
                    st.rerun()

                # Svuota Giocatori
                if st.button("👥 Svuota Tutti i Giocatori", use_container_width=True):
                    storage.save_giocatori(pd.DataFrame(columns=["id_giocatore", "nome_completo", "data_creazione", "in_gruppo_ristretto"]))
                    st.success("Tutti i giocatori sono stati rimossi.")
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state["authenticated"] = False
            st.session_state["user_role"] = "viewer"
            st.rerun()

    # Router Viste
    if scelta_menu == "🏆 Tabellone & Classifiche":
        view_dashboard(df_giocatori, df_partite, df_voti, storage_source)
    elif scelta_menu == "🏆 Classifica Amici (Gruppo Ristretto)":
        view_gruppo_ristretto(df_giocatori, df_partite, df_voti, storage_source, is_admin)
    elif scelta_menu == "📅 Convocazioni & Presenze":
        view_convocazioni(df_giocatori, df_partite, df_convocazioni, is_admin)
    elif scelta_menu == "⭐ Pagelle & MVP":
        view_pagelle(df_giocatori, df_partite, df_voti, is_admin)
    elif scelta_menu == "➕ Aggiungi Nuova Partita":
        view_add_match(df_giocatori, df_partite, is_admin)
    elif scelta_menu == "👤 Anagrafica Giocatori":
        view_anagrafica(df_giocatori, df_partite, is_admin)
    elif scelta_menu == "📜 Storico Partite":
        view_match_history(df_giocatori, df_partite, is_admin, df_voti=df_voti)


if __name__ == "__main__":
    main()
