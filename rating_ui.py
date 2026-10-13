"""Cards, component bars and reconstructed history using public rating data."""
from html import escape

import plotly.graph_objects as go
import streamlit as st

from ui_components import render_html


def _number(value, digits=0):
    return "—" if value is None else f"{value:.{digits}f}".replace(".", ",")


def render_card(player_name, stats, is_cerchia=False):
    pg = stats.get("pg", 0)
    attrs = stats.get("attributes", {})
    status = "Non ancora valutato" if not pg else "OVR provvisorio" if stats.get("provisional") else f"Basato su {pg} partite"
    delta = stats.get("ovr_delta")
    delta_text = "Prima partita" if pg and delta is None else "" if delta is None else f"{delta:+d} dall'ultima partita"
    accent = "#F5D365" if is_cerchia else "#65E7EF"
    sample = stats.get("mvp_partite", 0)
    mvp_detail = f"{stats.get('titoli_mvp', 0)} MVP su {sample} partite votate" if sample else "Nessuna votazione conclusa"
    rows = [("GOL", "Gol", f"{_number(stats.get('media_gol', 0), 2)} gol / partita", "#FF83AC"),
            ("RIS", "Risultati", f"{_number(stats.get('win_rate', 0), 1)}% vittorie", "#64E6A3"),
            ("MVP", "MVP", mvp_detail, "#F5D365")]
    row_html = "".join(f"<div class='cambo-stat'><div><b>{label}</b><small>{escape(detail) if pg else 'Nessuna partita giocata'}</small></div><strong style='color:{color}'>{_number(attrs.get(key))}</strong></div>" for key, label, detail, color in rows)
    render_html(f"""
    <style>
    .cambo-card {{box-sizing:border-box;max-width:440px;margin:0 auto;padding:22px;border:1px solid {accent};border-radius:26px;background:linear-gradient(155deg,rgba(68,61,23,.98),rgba(12,20,33,.99) 72%);box-shadow:0 12px 32px #0006;color:#F8FAFC;font-family:Inter,sans-serif}}
    .cambo-card.cambo-blue {{background:linear-gradient(155deg,rgba(21,61,68,.98),rgba(12,20,33,.99) 72%)}}
    .cambo-top {{display:flex;justify-content:space-between;align-items:start;gap:12px}}
    .cambo-ovr {{font-size:64px;font-weight:900;line-height:1;letter-spacing:-3px}}
    .cambo-label {{font-size:11px;font-weight:800;letter-spacing:1px;color:{accent};margin-top:6px}}
    .cambo-status {{text-align:right;font-size:12px;line-height:1.5;color:#CBD5E1;padding-top:5px;max-width:155px}}
    .cambo-tag {{display:inline-block;font-size:10px;letter-spacing:.6px;color:{accent};border:1px solid {accent}66;background:{accent}15;border-radius:20px;padding:5px 9px;margin-bottom:8px}}
    .cambo-avatar {{display:grid;place-items:center;width:58px;height:58px;margin:15px auto 8px;border-radius:50%;border:1px solid {accent}88;background:#ffffff0a;font-size:28px}}
    .cambo-name {{text-align:center;font-family:Outfit,Inter,sans-serif;font-size:24px;font-weight:800;line-height:1.2;overflow-wrap:anywhere;text-transform:uppercase;margin:8px 0 18px}}
    .cambo-stats {{background:#080F1ABB;border-radius:16px;padding:2px 14px}}
    .cambo-stat {{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:10px 0;border-bottom:1px solid #ffffff0d}}
    .cambo-stat:last-child {{border-bottom:0}}
    .cambo-stat b {{font-size:12px;letter-spacing:.3px}}
    .cambo-stat small {{display:block;color:#B3BDCB;font-size:11px;margin-top:3px;line-height:1.35}}
    .cambo-stat strong {{font-family:Outfit,Inter,sans-serif;font-size:26px;line-height:1}}
    .cambo-footer {{display:flex;justify-content:center;gap:12px;flex-wrap:wrap;font-size:11px;color:#CBD5E1;margin-top:16px}}
    .cambo-delta {{font-size:11px;color:{accent};margin-top:5px}}
    @media(max-width:480px) {{.cambo-card {{padding:18px}} .cambo-ovr {{font-size:58px}}}}
    </style>
    <section class="cambo-card {'cambo-blue' if not is_cerchia else ''}" aria-label="Carta rendimento {escape(str(player_name))}">
      <div class="cambo-top"><div><div class="cambo-ovr">{_number(stats.get('ovr'))}</div><div class="cambo-label">OVR · RATING CAMBO</div></div>
      <div class="cambo-status"><span class="cambo-tag">{'★ CERCHIA' if is_cerchia else 'CALCETTO CAMBO'}</span><div>{status}</div><div class="cambo-delta">{escape(delta_text)}</div></div></div>
      <div class="cambo-avatar">⚽</div><div class="cambo-name">{escape(str(player_name))}</div>
      <div class="cambo-stats">{row_html}</div>
      <div class="cambo-footer"><span><b>{pg}</b> partite</span><span><b>{stats.get('gol_totali', 0)}</b> gol</span><span><b>{stats.get('vittorie', 0)}</b> vittorie</span></div>
    </section>
    """)


def render_breakdown(stats):
    with st.expander("Come si calcola l'OVR"):
        st.write("**45% gol · 45% risultati · 10% MVP.** L'OVR combina l'80% del rendimento complessivo con il 20% delle ultime cinque partite giocate.")
        st.caption("La forma recente usa gli stessi tre parametri. Gli indici sono sulla scala 50–99; soltanto l'OVR finale viene arrotondato.")
        if not stats.get("pg"):
            st.info("Nessuna partita giocata: nessun punteggio viene inventato.")
            return
        details = stats["ovr_details"]
        config, overall, recent = details["calibration"], details["overall"], details["recent"]
        st.write(f"**Scala gol della stagione {config['season']}:** riferimento {_number(config['goal_reference'], 2)} gol per partita, calibrato su {config['sample_matches']} partite e {config['eligible_players']} giocatori con almeno tre presenze. Rimane fisso quando arrivano nuove partite o cambia il filtro.")
        st.caption("Il riferimento usa il 95° percentile delle medie gol, arrotondato per eccesso a 0,25. È una regola del modello, non una misura scientifica della bravura.")
        st.write(f"**Pochi dati:** gol e risultati sono attenuati con {_number(config['prior_matches'])} partite equivalenti alla media del campione iniziale. Le medie iniziali sono {_number(config['goal_prior'], 2)} gol per partita e {_number(100 * config['result_prior'], 1)}% dei punti possibili. Le presenze non danno punti extra.")
        st.write(f"**Gol reali:** {_number(overall['goals_per_match'], 2)} per partita. **Media stimata prudente:** {_number(overall['estimated_goals'], 2)}. Indice gol: 50 + 49 × media stimata / riferimento, limitato a 99.")
        st.write(f"**Risultati:** {stats['punti']} punti su {3 * stats['pg']} possibili (vittoria 3, pareggio 1, sconfitta 0). I punti di ogni gara sono moltiplicati per 1,5 meno la probabilità ELO stimata prima della partita; una vittoria da sfavoriti pesa di più. Punti corretti totali: {_number(overall['adjusted_points'], 2)}.")
        st.write(f"**MVP:** {overall['mvp_titles']} MVP su {overall['mvp_matches']} partite votate. Il bonus usa titoli / (partite votate + {_number(config['mvp_prior_matches'])}), così un solo titolo non porta l'indice a 99. Le votazioni aperte non contano; i titoli ex aequo e quelli storici pubblicati sono inclusi.")
        st.write(f"**Complessivo:** {_number(overall['ovr'], 2)} · **Recente:** {_number(recent['ovr'], 2)} su {recent['games']} partite. OVR = 80% × complessivo + 20% × recente = **{stats['ovr']}**.")
        last = stats.get("last_match")
        if last:
            st.caption(f"Ultima gara: probabilità ELO prepartita {_number(100 * last['expected'], 1)}%, moltiplicatore risultati {_number(last['difficulty_factor'], 2)}. La forza prepartita usa l'archivio completo anche quando filtri la cerchia.")
        st.caption("La quantità di partite descrive i dati disponibili, senza certificare l'affidabilità. L'OVR misura il rendimento registrato: difesa e contributo dei portieri non sono misurati direttamente. Assenze, titoli di peggiore e assist non entrano nel calcolo.")


def render_comparison(player_name, comparison):
    if not comparison.get("player_values"):
        st.info("Dati insufficienti: gioca almeno una partita per vedere il confronto.")
        return
    categories = comparison["categories"]
    values = comparison["player_values"]
    fig = go.Figure()
    fig.add_trace(go.Bar(y=categories, x=[value - 50 for value in values], base=50,
                        orientation="h", name=str(player_name), customdata=values,
                        marker_color=["#FF83AC", "#64E6A3", "#F5D365"],
                        text=values, textposition="outside", cliponaxis=False,
                        hovertemplate="%{y}: %{customdata}<extra>%{fullData.name}</extra>"))
    fig.add_trace(go.Scatter(y=categories, x=comparison["avg_values"], mode="markers",
                            name="Media gruppo", marker=dict(symbol="line-ns", size=25, color="#F8FAFC", line=dict(width=3, color="#F8FAFC")),
                            hovertemplate="Media gruppo · %{y}: %{x:.1f}<extra></extra>"))
    fig.update_layout(height=260, bargap=.48, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      margin=dict(l=5, r=32, t=5, b=30), font=dict(color="#CBD5E1", family="Inter"),
                      xaxis=dict(range=[49, 104], tickvals=[50, 60, 70, 80, 90, 99], gridcolor="rgba(255,255,255,.07)", title=None),
                      yaxis=dict(autorange="reversed", showgrid=False),
                      legend=dict(orientation="h", y=-.25, x=0), hovermode="closest")
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.caption(f"Indici 50–99 · media di {comparison['active_players']} giocatori che hanno giocato nel filtro selezionato.")


def render_recent_form(stats):
    recent = stats.get("ovr_details", {}).get("recent", {})
    if not stats.get("pg"):
        st.caption("Nessuna partita giocata.")
        return
    results = stats.get("forma", [])[:5]
    labels = {"V": "Vittoria", "P": "Pareggio", "S": "Sconfitta"}
    colors = {"V": "#64E6A3", "P": "#F5D365", "S": "#FF83AC"}
    badges = "".join(f"<span title='{labels[result]}' style='display:inline-grid;place-items:center;width:29px;height:29px;border-radius:9px;background:{colors[result]};color:#081321;font-weight:900'>{result}</span>" for result in results)
    render_html(f"""<div style="padding:16px;border:1px solid #65E7EF44;border-radius:16px;background:#0B1726E8;color:#E2E8F0;font-family:Inter,sans-serif">
    <div style="display:flex;justify-content:space-between;align-items:center;gap:12px"><div><b>Forma recente</b><div style="font-size:11px;color:#B3BDCB;margin-top:4px">Ultime {recent.get('games', len(results))} partite giocate</div></div><strong style="font-size:28px;color:#65E7EF">{_number(stats.get('attributes', {}).get('FRM'))}</strong></div>
    <div style="display:flex;gap:6px;margin-top:12px">{badges}</div></div>""")
    st.caption("Risultati dalla partita più recente alla meno recente. La forma è già compresa nell'OVR.")


def render_history(stats):
    history = stats.get("history", [])
    st.markdown("#### 📈 Andamento OVR")
    if not history:
        st.caption("L'andamento sarà disponibile dopo la prima partita.")
        return
    delta = stats.get("ovr_delta")
    if delta is not None:
        st.metric("OVR attuale", str(stats["ovr"]), delta=f"{delta:+d} dalla partita precedente")
    st.write(stats.get("trend_explanation", ""))
    labels = [f"#{row['match_id']} · {row['date']}" for row in history]
    fig = go.Figure(go.Scatter(x=list(range(len(history))), y=[row["ovr"] for row in history],
                              customdata=[[label, row["result"], row["goals"]] for label, row in zip(labels, history)],
                              mode="lines+markers", line=dict(color="#65E7EF", width=3), marker=dict(size=8),
                              hovertemplate="%{customdata[0]}<br>OVR %{y}<br>Risultato %{customdata[1]} · Gol %{customdata[2]}<extra></extra>"))
    # Show every label for short histories, selected labels for longer ones.
    ticks = list(range(len(history))) if len(history) <= 7 else sorted(set([0, len(history) - 1] + list(range(0, len(history), max(1, len(history) // 5)))))
    fig.update_layout(height=230, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      margin=dict(l=20, r=15, t=5, b=30), font=dict(color="#CBD5E1", family="Inter"),
                      xaxis=dict(tickvals=ticks, ticktext=[f"#{history[i]['match_id']}" for i in ticks], title=None, showgrid=False),
                      yaxis=dict(range=[49, 100], gridcolor="rgba(255,255,255,.07)", title="OVR"), showlegend=False)
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
    st.caption("Storico ricostruito con il modello attuale e gli MVP oggi pubblicati; può cambiare se correggi una partita o riapri una votazione.")


def render_player_sheet(player_name, stats, comparison, is_cerchia=False):
    left, right = st.columns([1, 1.2])
    with left:
        render_card(player_name, stats, is_cerchia)
        render_breakdown(stats)
    with right:
        st.markdown("#### 📊 Confronto con il gruppo")
        render_comparison(player_name, comparison)
        render_recent_form(stats)
    render_history(stats)
