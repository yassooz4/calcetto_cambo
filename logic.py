"""
================================================================================
LOGIC.PY - Logica computazionale e algoritmi per Calcetto Stats
Modulo puro per calcoli statistici, ELO, bilanciamento squadre, pagelle/MVP
================================================================================
"""

import math
import json
import itertools
from typing import List, Dict, Tuple, Any, Optional
import pandas as pd


# ==============================================================================
# 1. PARSING MARCATORI & UTILITÀ
# ==============================================================================
def parse_marcatori(marcatori_raw: Any) -> Dict[str, int]:
    """
    Esegue il parsing della stringa marcatori (JSON o stringa formattata 'Nome: gol, Nome2: gol').
    Restituisce un dizionario {nome_giocatore: numero_gol}.
    """
    if pd.isna(marcatori_raw) or not marcatori_raw:
        return {}
    
    if isinstance(marcatori_raw, dict):
        return {str(k).strip(): int(v) for k, v in marcatori_raw.items() if int(v) > 0}
        
    raw_str = str(marcatori_raw).strip()
    if not raw_str:
        return {}

    # Prova parsing come JSON
    try:
        data = json.loads(raw_str)
        if isinstance(data, dict):
            return {str(k).strip(): int(v) for k, v in data.items() if int(v) > 0}
    except Exception:
        pass

    # Fallback su stringa 'Nome: Gol, Nome 2: Gol'
    res = {}
    parts = raw_str.split(",")
    for p in parts:
        if ":" in p:
            chunks = p.split(":")
            nome = chunks[0].strip()
            try:
                gol = int(chunks[1].strip())
                if gol > 0 and nome:
                    res[nome] = res.get(nome, 0) + gol
            except ValueError:
                continue
    return res


def serialize_marcatori(marcatori_dict: Dict[str, int]) -> str:
    """Serializza il dizionario marcatori in formato JSON compatto."""
    clean_dict = {k.strip(): int(v) for k, v in marcatori_dict.items() if int(v) > 0 and k.strip()}
    return json.dumps(clean_dict, ensure_ascii=False)


def filter_internal_matches(
    df_partite: pd.DataFrame, 
    gruppo_players: List[str], 
    strict: bool = True
) -> pd.DataFrame:
    """
    Filtra il DataFrame delle partite mantenendo solo quelle 'interne' al gruppo ristretto.
    - strict=True: TUTTI i giocatori scesi in campo in entrambi i team devono appartenere al gruppo ristretto.
    - strict=False: Almeno il 50% dei giocatori totali della partita appartiene al gruppo.
    """
    if df_partite.empty or not gruppo_players:
        return df_partite.copy() if not strict else pd.DataFrame(columns=df_partite.columns)

    gruppo_set = set(str(p).strip() for p in gruppo_players if str(p).strip())
    internal_indices = []

    for idx, match in df_partite.iterrows():
        raw_a = [p.strip() for p in str(match.get("squadra_a_giocatori", "")).split(",") if p.strip()]
        raw_b = [p.strip() for p in str(match.get("squadra_b_giocatori", "")).split(",") if p.strip()]
        all_p = raw_a + raw_b

        if not all_p:
            continue

        if strict:
            if all(p in gruppo_set for p in all_p):
                internal_indices.append(idx)
        else:
            in_group_count = sum(1 for p in all_p if p in gruppo_set)
            if in_group_count >= (len(all_p) / 2):
                internal_indices.append(idx)

    return df_partite.loc[internal_indices].copy().reset_index(drop=True)


# ==============================================================================
# 2. RATING ELO DINAMICO CON SCARTO RETI
# ==============================================================================
def calculate_elo_ratings(
    df_giocatori: pd.DataFrame, 
    df_partite: pd.DataFrame, 
    k_factor: float = 32.0, 
    initial_elo: float = 1500.0,
    giocatori_filtrati: Optional[List[str]] = None
) -> Tuple[Dict[str, float], Dict[str, List[Tuple[str, float]]]]:
    """
    Calcola il rating ELO dinamico per ogni giocatore basandosi sulla cronologia delle partite.
    Se specificato 'giocatori_filtrati', restituisce il rating e lo storico limitati a tali giocatori.
    """
    elo_ratings: Dict[str, float] = {}
    elo_history: Dict[str, List[Tuple[str, float]]] = {}

    # Inizializza tutti i giocatori registrati con 1500
    if not df_giocatori.empty and "nome_completo" in df_giocatori.columns:
        for nome in df_giocatori["nome_completo"].dropna().unique():
            nome_clean = str(nome).strip()
            if nome_clean:
                elo_ratings[nome_clean] = float(initial_elo)
                elo_history[nome_clean] = [("Inizio", float(initial_elo))]

    if not df_partite.empty:
        # Ordina cronologicamente in senso crescente (dalla più vecchia alla più recente)
        df_sorted = df_partite.copy()
        if "data" in df_sorted.columns and "id_partita" in df_sorted.columns:
            df_sorted = df_sorted.sort_values(by=["data", "id_partita"], ascending=[True, True])

        for _, match in df_sorted.iterrows():
            raw_a = str(match.get("squadra_a_giocatori", ""))
            raw_b = str(match.get("squadra_b_giocatori", ""))
            sq_a = [p.strip() for p in raw_a.split(",") if p.strip()]
            sq_b = [p.strip() for p in raw_b.split(",") if p.strip()]

            if not sq_a or not sq_b:
                continue

            # Inizializza eventuali giocatori non presenti nell'anagrafica
            for p in sq_a + sq_b:
                if p not in elo_ratings:
                    elo_ratings[p] = float(initial_elo)
                    elo_history[p] = [("Inizio", float(initial_elo))]

            gol_a = int(match.get("gol_squadra_a", 0))
            gol_b = int(match.get("gol_squadra_b", 0))

            # Media ELO dei team
            avg_elo_a = sum(elo_ratings[p] for p in sq_a) / len(sq_a)
            avg_elo_b = sum(elo_ratings[p] for p in sq_b) / len(sq_b)

            # Expected score
            exp_a = 1.0 / (1.0 + 10.0 ** ((avg_elo_b - avg_elo_a) / 400.0))

            # Actual score
            if gol_a > gol_b:
                score_a = 1.0
            elif gol_a < gol_b:
                score_a = 0.0
            else:
                score_a = 0.5

            # Scarto reti factor
            goal_diff = abs(gol_a - gol_b)
            margin_multiplier = 1.0 + math.log(1.0 + goal_diff)

            # Variazione ELO
            delta_elo = k_factor * margin_multiplier * (score_a - exp_a)

            # Aggiornamento
            label = f"{match.get('data', '')} (#{match.get('id_partita', '')})"
            for p in sq_a:
                elo_ratings[p] = round(elo_ratings[p] + delta_elo, 1)
                elo_history[p].append((label, elo_ratings[p]))

            for p in sq_b:
                elo_ratings[p] = round(elo_ratings[p] - delta_elo, 1)
                elo_history[p].append((label, elo_ratings[p]))

    if giocatori_filtrati is not None:
        filter_set = set(str(p).strip() for p in giocatori_filtrati if str(p).strip())
        elo_ratings = {k: v for k, v in elo_ratings.items() if k in filter_set}
        elo_history = {k: v for k, v in elo_history.items() if k in filter_set}

    return elo_ratings, elo_history


# ==============================================================================
# 3. GENERATORE SQUADRE EQUILIBRATE (ALGORITMO COMBINATORIO)
# ==============================================================================
def balance_teams(
    selected_players: List[str], 
    elo_ratings: Dict[str, float]
) -> Dict[str, Any]:
    """
    Dato un elenco di esattamente 10 giocatori e i relativi rating ELO,
    esegue una ricerca esaustiva tra tutte le C(10,5)/2 = 126 suddivisioni possibili in 2 squadre da 5.
    Minimizza la differenza assoluta tra la somma degli ELO di Squadra A e Squadra B.
    
    Restituisce un dizionario con la migliore configurazione trovata.
    """
    if len(selected_players) != 10:
        return {
            "error": f"Servono esattamente 10 giocatori per il bilanciamento (selezionati: {len(selected_players)})."
        }

    players = list(selected_players)
    first_player = players[0]
    remaining_players = players[1:]

    best_diff = float("inf")
    best_team_a = []
    best_team_b = []
    best_sum_a = 0.0
    best_sum_b = 0.0

    # C(9, 4) = 126 combinazioni univoche fissando first_player in Squadra A
    for combo in itertools.combinations(remaining_players, 4):
        team_a = [first_player] + list(combo)
        team_b = [p for p in players if p not in team_a]

        sum_a = sum(elo_ratings.get(p, 1500.0) for p in team_a)
        sum_b = sum(elo_ratings.get(p, 1500.0) for p in team_b)
        diff = abs(sum_a - sum_b)

        if diff < best_diff:
            best_diff = diff
            best_team_a = team_a
            best_team_b = team_b
            best_sum_a = sum_a
            best_sum_b = sum_b

    avg_a = best_sum_a / 5.0
    avg_b = best_sum_b / 5.0

    return {
        "team_a": sorted(best_team_a),
        "team_b": sorted(best_team_b),
        "elo_sum_a": round(best_sum_a, 1),
        "elo_sum_b": round(best_sum_b, 1),
        "elo_avg_a": round(avg_a, 1),
        "elo_avg_b": round(avg_b, 1),
        "diff_elo": round(best_diff, 1),
        "diff_avg_elo": round(abs(avg_a - avg_b), 1),
        "ratings_detail_a": {p: elo_ratings.get(p, 1500.0) for p in best_team_a},
        "ratings_detail_b": {p: elo_ratings.get(p, 1500.0) for p in best_team_b},
    }


# ==============================================================================
# ==============================================================================
# 4. CLASSIFICA GENERALE RENDIMENTO & STATISTICHE VOTI
# ==============================================================================
def calculate_player_vote_stats(
    df_partite: pd.DataFrame, 
    df_voti: pd.DataFrame,
    giocatori_filtrati: Optional[List[str]] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Calcola per ciascun giocatore le metriche aggregate dei voti:
    - Titoli MVP (numero di volte in cui è risultato MVP del match)
    - Titoli Peggiore (numero di volte in cui è risultato peggiore in campo)
    - Media Voto Pagelle (media aritmetica complessiva di tutti i voti ricevuti)
    - Totale Voti Ricevuti
    """
    stats: Dict[str, Dict[str, Any]] = {}
    filter_set = set(str(p).strip() for p in giocatori_filtrati if str(p).strip()) if giocatori_filtrati is not None else None

    if df_voti is not None and "mvp_names" in df_voti.columns:
        match_ids = set(pd.to_numeric(df_partite.get("id_partita", pd.Series(dtype=float)), errors="coerce").dropna().astype(int))
        for _, final in df_voti.iterrows():
            if int(final["id_partita"]) not in match_ids:
                continue
            for field, count_field in [("mvp_names", "titoli_mvp"), ("worst_names", "titoli_peggiore")]:
                for name in final[field]:
                    if filter_set is not None and name not in filter_set:
                        continue
                    entry = stats.setdefault(name, {"titoli_mvp": 0, "titoli_peggiore": 0, "media_voto": None, "totale_voti": 0})
                    entry[count_field] += 1
        return stats

    if df_voti is None or df_voti.empty or "voto" not in df_voti.columns:
        return stats

    df_clean_voti = df_voti.copy()
    df_clean_voti["voto"] = pd.to_numeric(df_clean_voti["voto"], errors="coerce")
    df_clean_voti = df_clean_voti.dropna(subset=["voto"])

    mvp_counts: Dict[str, int] = {}
    worst_counts: Dict[str, int] = {}

    if not df_partite.empty and "id_partita" in df_partite.columns:
        for p_id in df_partite["id_partita"].unique():
            res = calculate_match_ratings(df_clean_voti, p_id)
            if res["has_votes"]:
                if res["mvp"] and res["mvp"].get("giocatore"):
                    m_name = str(res["mvp"]["giocatore"]).strip()
                    mvp_counts[m_name] = mvp_counts.get(m_name, 0) + 1
                if res["worst"] and res["worst"].get("giocatore"):
                    w_name = str(res["worst"]["giocatore"]).strip()
                    if res["mvp"] and w_name != str(res["mvp"]["giocatore"]).strip():
                        worst_counts[w_name] = worst_counts.get(w_name, 0) + 1

    # Calcolo medie complessive per giocatore
    if not df_clean_voti.empty and "giocatore" in df_clean_voti.columns:
        for player_name, group in df_clean_voti.groupby("giocatore"):
            p_str = str(player_name).strip()
            if filter_set is not None and p_str not in filter_set:
                continue
            votes_series = group["voto"]
            avg_rating = round(float(votes_series.mean()), 2)
            total_v = int(votes_series.count())
            stats[p_str] = {
                "titoli_mvp": mvp_counts.get(p_str, 0),
                "titoli_peggiore": worst_counts.get(p_str, 0),
                "media_voto": avg_rating,
                "totale_voti": total_v
            }

    # Assegna 0 e None per eventuali giocatori filtrati che non hanno voti
    if filter_set is not None:
        for p in filter_set:
            if p not in stats:
                stats[p] = {
                    "titoli_mvp": mvp_counts.get(p, 0),
                    "titoli_peggiore": worst_counts.get(p, 0),
                    "media_voto": None,
                    "totale_voti": 0
                }

    return stats


def calculate_leaderboard(
    df_giocatori: pd.DataFrame, 
    df_partite: pd.DataFrame,
    elo_ratings: Optional[Dict[str, float]] = None,
    giocatori_filtrati: Optional[List[str]] = None,
    df_voti: Optional[pd.DataFrame] = None
) -> pd.DataFrame:
    """
    Calcola la classifica generale dei giocatori:
    Punti (V*3 + P*1), Partite Giocate (PG), V, P, S, % Vittoria, ELO Attuale,
    Titoli MVP, Titoli Peggiore, Media Voto Pagelle.
    Se passato 'giocatori_filtrati', include solo tali giocatori.
    """
    if elo_ratings is None:
        elo_ratings, _ = calculate_elo_ratings(df_giocatori, df_partite, giocatori_filtrati=giocatori_filtrati)

    vote_stats = calculate_player_vote_stats(df_partite, df_voti, giocatori_filtrati=giocatori_filtrati) if df_voti is not None else {}

    cols_default = ["Giocatore", "Punti", "PG", "V", "P", "S", "% Vittoria", "ELO", "Titoli MVP", "Titoli Peggiore", "Media Voto"]
    if df_giocatori.empty:
        return pd.DataFrame(columns=cols_default)

    filter_set = set(str(p).strip() for p in giocatori_filtrati if str(p).strip()) if giocatori_filtrati is not None else None

    stats: Dict[str, Dict[str, int]] = {}
    for _, row in df_giocatori.iterrows():
        nome = str(row["nome_completo"]).strip()
        if nome:
            if filter_set is None or nome in filter_set:
                stats[nome] = {"PG": 0, "V": 0, "P": 0, "S": 0}

    if not df_partite.empty:
        for _, match in df_partite.iterrows():
            raw_a = str(match.get("squadra_a_giocatori", ""))
            raw_b = str(match.get("squadra_b_giocatori", ""))
            sq_a = [p.strip() for p in raw_a.split(",") if p.strip()]
            sq_b = [p.strip() for p in raw_b.split(",") if p.strip()]

            gol_a = int(match.get("gol_squadra_a", 0))
            gol_b = int(match.get("gol_squadra_b", 0))

            if gol_a > gol_b:
                esito_a, esito_b = "V", "S"
            elif gol_b > gol_a:
                esito_a, esito_b = "S", "V"
            else:
                esito_a, esito_b = "P", "P"

            for p in sq_a:
                if filter_set is not None and p not in filter_set:
                    continue
                if p not in stats:
                    stats[p] = {"PG": 0, "V": 0, "P": 0, "S": 0}
                stats[p]["PG"] += 1
                stats[p][esito_a] += 1

            for p in sq_b:
                if filter_set is not None and p not in filter_set:
                    continue
                if p not in stats:
                    stats[p] = {"PG": 0, "V": 0, "P": 0, "S": 0}
                stats[p]["PG"] += 1
                stats[p][esito_b] += 1

    rows = []
    for player, s in stats.items():
        pg = s["PG"]
        v = s["V"]
        p = s["P"]
        sc = s["S"]
        punti = (v * 3) + (p * 1)
        win_rate = round((v / pg * 100), 1) if pg > 0 else 0.0
        current_elo = elo_ratings.get(player, 1500.0)

        p_vote_info = vote_stats.get(player, {})
        mvp_titles = p_vote_info.get("titoli_mvp", 0)
        worst_titles = p_vote_info.get("titoli_peggiore", 0)
        media_voto = p_vote_info.get("media_voto", None)

        rows.append({
            "Giocatore": player,
            "Punti": punti,
            "PG": pg,
            "V": v,
            "P": p,
            "S": sc,
            "% Vittoria": win_rate,
            "ELO": round(current_elo, 1),
            "Titoli MVP": mvp_titles,
            "Titoli Peggiore": worst_titles,
            "Media Voto": media_voto
        })

    df_res = pd.DataFrame(rows)
    if not df_res.empty:
        df_res = df_res.sort_values(
            by=["Punti", "% Vittoria", "ELO", "Titoli MVP", "PG", "Giocatore"],
            ascending=[False, False, False, False, False, True]
        ).reset_index(drop=True)

    return df_res


# ==============================================================================
# 5. CLASSIFICA MARCATORI (SOLI GOL INDIVIDUALI, NO ASSIST)
# ==============================================================================
def calculate_scorers(
    df_giocatori: pd.DataFrame, 
    df_partite: pd.DataFrame,
    giocatori_filtrati: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Calcola la classifica dei marcatori basata esclusivamente sui gol individuali segnati.
    Metriche: Giocatore, Gol Totali, PG (Partite Giocate), Media Gol/Gara.
    Se passato 'giocatori_filtrati', limita il calcolo a tali giocatori.
    """
    if df_giocatori.empty and df_partite.empty:
        return pd.DataFrame(columns=["Giocatore", "Gol Totali", "PG", "Media Gol"])

    filter_set = set(str(p).strip() for p in giocatori_filtrati if str(p).strip()) if giocatori_filtrati is not None else None

    pg_dict: Dict[str, int] = {}
    gol_dict: Dict[str, int] = {}

    # Inizializza con giocatori registrati
    if not df_giocatori.empty:
        for nome in df_giocatori["nome_completo"].dropna().unique():
            nome_clean = str(nome).strip()
            if nome_clean:
                if filter_set is None or nome_clean in filter_set:
                    pg_dict[nome_clean] = 0
                    gol_dict[nome_clean] = 0

    if not df_partite.empty:
        for _, match in df_partite.iterrows():
            raw_a = str(match.get("squadra_a_giocatori", ""))
            raw_b = str(match.get("squadra_b_giocatori", ""))
            all_players = [p.strip() for p in (raw_a + "," + raw_b).split(",") if p.strip()]

            for p in set(all_players):
                if filter_set is not None and p not in filter_set:
                    continue
                pg_dict[p] = pg_dict.get(p, 0) + 1
                if p not in gol_dict:
                    gol_dict[p] = 0

            # Parsing marcatori
            marcatori_raw = match.get("marcatori", "")
            match_goals = parse_marcatori(marcatori_raw)
            for p, g in match_goals.items():
                if filter_set is not None and p not in filter_set:
                    continue
                gol_dict[p] = gol_dict.get(p, 0) + int(g)

    rows = []
    for player, total_gol in gol_dict.items():
        pg = pg_dict.get(player, 0)
        media = round(total_gol / pg, 2) if pg > 0 else 0.0
        rows.append({
            "Giocatore": player,
            "Gol Totali": int(total_gol),
            "PG": int(pg),
            "Media Gol": media
        })

    df_scorers = pd.DataFrame(rows)
    if not df_scorers.empty:
        # Ordina: Gol Totali DESC -> Media Gol DESC -> PG ASC
        df_scorers = df_scorers.sort_values(
            by=["Gol Totali", "Media Gol", "PG", "Giocatore"],
            ascending=[False, False, True, True]
        ).reset_index(drop=True)

    return df_scorers


# ==============================================================================
# 6. STRISCE DI VITTORIE CONSECUTIVE (APERTA & RECORD PERSONALE)
# ==============================================================================
def calculate_win_streaks(
    df_giocatori: pd.DataFrame, 
    df_partite: pd.DataFrame,
    giocatori_filtrati: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Calcola per ciascun giocatore:
    - Striscia di vittorie consecutive APERTA (attuale).
    - Record personale storico di vittorie consecutive.
    Se passato 'giocatori_filtrati', calcola solo per i giocatori indicati.
    """
    if df_giocatori.empty and df_partite.empty:
        return pd.DataFrame(columns=["Giocatore", "Striscia Attuale", "Record Storico", "PG Totali"])

    filter_set = set(str(p).strip() for p in giocatori_filtrati if str(p).strip()) if giocatori_filtrati is not None else None

    df_sorted = df_partite.copy()
    if not df_sorted.empty and "data" in df_sorted.columns and "id_partita" in df_sorted.columns:
        df_sorted = df_sorted.sort_values(by=["data", "id_partita"], ascending=[True, True])

    history_outcomes: Dict[str, List[str]] = {}

    if not df_giocatori.empty:
        for nome in df_giocatori["nome_completo"].dropna().unique():
            nome_clean = str(nome).strip()
            if nome_clean:
                if filter_set is None or nome_clean in filter_set:
                    history_outcomes[nome_clean] = []

    if not df_sorted.empty:
        for _, match in df_sorted.iterrows():
            raw_a = [p.strip() for p in str(match.get("squadra_a_giocatori", "")).split(",") if p.strip()]
            raw_b = [p.strip() for p in str(match.get("squadra_b_giocatori", "")).split(",") if p.strip()]
            gol_a = int(match.get("gol_squadra_a", 0))
            gol_b = int(match.get("gol_squadra_b", 0))

            if gol_a > gol_b:
                esito_a, esito_b = "V", "S"
            elif gol_b > gol_a:
                esito_a, esito_b = "S", "V"
            else:
                esito_a, esito_b = "P", "P"

            for p in raw_a:
                if filter_set is not None and p not in filter_set:
                    continue
                if p not in history_outcomes:
                    history_outcomes[p] = []
                history_outcomes[p].append(esito_a)

            for p in raw_b:
                if filter_set is not None and p not in filter_set:
                    continue
                if p not in history_outcomes:
                    history_outcomes[p] = []
                history_outcomes[p].append(esito_b)

    rows = []
    for player, outcomes in history_outcomes.items():
        max_streak = 0
        current_run = 0
        for out in outcomes:
            if out == "V":
                current_run += 1
                if current_run > max_streak:
                    max_streak = current_run
            else:
                current_run = 0

        open_streak = 0
        for out in reversed(outcomes):
            if out == "V":
                open_streak += 1
            else:
                break

        rows.append({
            "Giocatore": player,
            "Striscia Attuale": open_streak,
            "Record Storico": max_streak,
            "PG Totali": len(outcomes)
        })

    df_streaks = pd.DataFrame(rows)
    if not df_streaks.empty:
        df_streaks = df_streaks.sort_values(
            by=["Striscia Attuale", "Record Storico", "PG Totali", "Giocatore"],
            ascending=[False, False, False, True]
        ).reset_index(drop=True)

    return df_streaks


# ==============================================================================
# 7. COPPIE D'ORO & RIVALI (AFFINITÀ & SCONTRI DIRETTI H2H)
# ==============================================================================
def calculate_golden_duos_and_rivalries(
    df_partite: pd.DataFrame, 
    min_games_together: int = 3,
    giocatori_filtrati: Optional[List[str]] = None
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Calcola:
    1. Coppie d'Oro: Percentuale di vittoria quando due giocatori giocano nella stessa squadra (min_games >= 3).
    2. Rivali (Scontri Diretti / H2H): Vittorie, Pareggi, Sconfitte quando due giocatori si affrontano da avversari.
    Se passato 'giocatori_filtrati', calcola coppie e rivali solo per combinazioni di membri filtrati.
    """
    if df_partite.empty:
        empty_duos = pd.DataFrame(columns=["Coppia", "Giocatore 1", "Giocatore 2", "PG Insieme", "V Insieme", "% Vittoria Insieme"])
        empty_rivals = pd.DataFrame(columns=["Giocatore A", "Giocatore B", "Scontri Diretti", "Vittorie A", "Vittorie B", "Pareggi"])
        return empty_duos, empty_rivals

    filter_set = set(str(p).strip() for p in giocatori_filtrati if str(p).strip()) if giocatori_filtrati is not None else None

    duo_stats: Dict[Tuple[str, str], Dict[str, int]] = {}
    rival_stats: Dict[Tuple[str, str], Dict[str, int]] = {}

    for _, match in df_partite.iterrows():
        raw_a = sorted([p.strip() for p in str(match.get("squadra_a_giocatori", "")).split(",") if p.strip()])
        raw_b = sorted([p.strip() for p in str(match.get("squadra_b_giocatori", "")).split(",") if p.strip()])
        gol_a = int(match.get("gol_squadra_a", 0))
        gol_b = int(match.get("gol_squadra_b", 0))

        if filter_set is not None:
            raw_a_filtered = [p for p in raw_a if p in filter_set]
            raw_b_filtered = [p for p in raw_b if p in filter_set]
        else:
            raw_a_filtered = raw_a
            raw_b_filtered = raw_b

        # 1. Compagni in Squadra A
        for p1, p2 in itertools.combinations(raw_a_filtered, 2):
            pair = tuple(sorted([p1, p2]))
            if pair not in duo_stats:
                duo_stats[pair] = {"PG": 0, "V": 0, "P": 0, "S": 0}
            duo_stats[pair]["PG"] += 1
            if gol_a > gol_b:
                duo_stats[pair]["V"] += 1
            elif gol_a == gol_b:
                duo_stats[pair]["P"] += 1
            else:
                duo_stats[pair]["S"] += 1

        # 2. Compagni in Squadra B
        for p1, p2 in itertools.combinations(raw_b_filtered, 2):
            pair = tuple(sorted([p1, p2]))
            if pair not in duo_stats:
                duo_stats[pair] = {"PG": 0, "V": 0, "P": 0, "S": 0}
            duo_stats[pair]["PG"] += 1
            if gol_b > gol_a:
                duo_stats[pair]["V"] += 1
            elif gol_b == gol_a:
                duo_stats[pair]["P"] += 1
            else:
                duo_stats[pair]["S"] += 1

        # 3. Avversari Squadra A vs Squadra B
        for p1 in raw_a_filtered:
            for p2 in raw_b_filtered:
                pair = tuple(sorted([p1, p2]))
                if pair not in rival_stats:
                    rival_stats[pair] = {"PG": 0, "V_p1": 0, "V_p2": 0, "P": 0}
                rival_stats[pair]["PG"] += 1
                if gol_a > gol_b:
                    if pair[0] == p1:
                        rival_stats[pair]["V_p1"] += 1
                    else:
                        rival_stats[pair]["V_p2"] += 1
                elif gol_b > gol_a:
                    if pair[0] == p2:
                        rival_stats[pair]["V_p1"] += 1
                    else:
                        rival_stats[pair]["V_p2"] += 1
                else:
                    rival_stats[pair]["P"] += 1

    # Costruzione DataFrame Coppie d'Oro
    duo_rows = []
    for (p1, p2), s in duo_stats.items():
        if s["PG"] >= min_games_together:
            win_rate = round((s["V"] / s["PG"]) * 100, 1)
            duo_rows.append({
                "Coppia": f"{p1} & {p2}",
                "Giocatore 1": p1,
                "Giocatore 2": p2,
                "PG Insieme": s["PG"],
                "V Insieme": s["V"],
                "P Insieme": s["P"],
                "S Insieme": s["S"],
                "% Vittoria Insieme": win_rate
            })

    df_duos = pd.DataFrame(duo_rows)
    if not df_duos.empty:
        df_duos = df_duos.sort_values(
            by=["% Vittoria Insieme", "V Insieme", "PG Insieme"],
            ascending=[False, False, False]
        ).reset_index(drop=True)

    # Costruzione DataFrame Rivali
    rival_rows = []
    for (p1, p2), s in rival_stats.items():
        p_first = p1
        p_second = p2
        v_first = s["V_p1"]
        v_second = s["V_p2"]
        rival_rows.append({
            "Giocatore A": p_first,
            "Giocatore B": p_second,
            "Scontri Diretti": s["PG"],
            f"Vittorie {p_first}": v_first,
            f"Vittorie {p_second}": v_second,
            "Pareggi": s["P"],
        })

    df_rivals = pd.DataFrame(rival_rows)
    if not df_rivals.empty:
        df_rivals = df_rivals.sort_values(by=["Scontri Diretti"], ascending=False).reset_index(drop=True)

    return df_duos, df_rivals


# ==============================================================================
# 8. PAGELLE, MEDIE VOTI & PROCLAMAZIONE MVP
# ==============================================================================
def calculate_match_ratings(
    df_voti: pd.DataFrame, 
    id_partita: int
) -> Dict[str, Any]:
    """
    Calcola le statistiche dei voti per una determinata partita:
    - Media voto per ciascun giocatore sceso in campo
    - Proclamazione automatica MVP (media più alta)
    - Menzione peggiore in campo (media più bassa)
    - Lista commenti ricevuti
    """
    if df_voti.empty or "id_partita" not in df_voti.columns:
        return {"has_votes": False, "ratings": pd.DataFrame(), "mvp": None, "worst": None, "comments": []}

    df_match_votes = df_voti[df_voti["id_partita"].astype(str) == str(id_partita)].copy()
    if df_match_votes.empty:
        return {"has_votes": False, "ratings": pd.DataFrame(), "mvp": None, "worst": None, "comments": []}

    if "mvp_names" in df_match_votes.columns:
        final = df_match_votes.iloc[-1]
        def award(field):
            names = final[field + "_names"]
            return {"giocatore": " · ".join(names), "giocatori": names, "media": None,
                    "voti_ricevuti": int(final[field + "_votes"])} if names else None
        return {"has_votes": True, "ratings": pd.DataFrame(), "mvp": award("mvp"),
                "worst": award("worst"), "comments": []}

    df_match_votes["voto"] = pd.to_numeric(df_match_votes["voto"], errors="coerce")
    df_match_votes = df_match_votes.dropna(subset=["voto"])

    if df_match_votes.empty:
        return {"has_votes": False, "ratings": pd.DataFrame(), "mvp": None, "worst": None, "comments": []}

    # Raggruppa per giocatore
    grouped = df_match_votes.groupby("giocatore")["voto"].agg(["mean", "count", "min", "max"]).reset_index()
    grouped.columns = ["Giocatore", "Media Voto", "Numero Voti", "Min", "Max"]
    grouped["Media Voto"] = grouped["Media Voto"].round(2)
    grouped = grouped.sort_values(by=["Media Voto", "Numero Voti"], ascending=[False, False]).reset_index(drop=True)

    mvp_info = None
    worst_info = None
    if not grouped.empty:
        best_row = grouped.iloc[0]
        mvp_info = {
            "giocatore": best_row["Giocatore"],
            "media": best_row["Media Voto"],
            "voti_ricevuti": int(best_row["Numero Voti"])
        }

        worst_row = grouped.iloc[-1]
        worst_info = {
            "giocatore": worst_row["Giocatore"],
            "media": worst_row["Media Voto"],
            "voti_ricevuti": int(worst_row["Numero Voti"])
        }

    # Commenti
    comments = []
    if "commento" in df_match_votes.columns:
        df_comms = df_match_votes[df_match_votes["commento"].fillna("").astype(str).str.strip() != ""]
        for _, c_row in df_comms.iterrows():
            comments.append({
                "votante": c_row.get("votante", "Anonimo"),
                "giocatore": c_row.get("giocatore", ""),
                "voto": c_row.get("voto", ""),
                "commento": c_row.get("commento", "")
            })

    return {
        "has_votes": True,
        "ratings": grouped,
        "mvp": mvp_info,
        "worst": worst_info,
        "comments": comments
    }


def calculate_season_mvp_leaderboard(
    df_partite: pd.DataFrame, 
    df_voti: pd.DataFrame
) -> pd.DataFrame:
    """
    Calcola la classifica stagionale dei voti e degli MVP vinti.
    """
    if df_voti.empty or "voto" not in df_voti.columns:
        return pd.DataFrame(columns=["Giocatore", "Media Voto Stagionale", "Voti Ricevuti", "Titoli MVP"])

    df_clean = df_voti.copy()
    df_clean["voto"] = pd.to_numeric(df_clean["voto"], errors="coerce")
    df_clean = df_clean.dropna(subset=["voto"])

    if df_clean.empty:
        return pd.DataFrame(columns=["Giocatore", "Media Voto Stagionale", "Voti Ricevuti", "Titoli MVP"])

    mvp_counts: Dict[str, int] = {}
    if not df_partite.empty and "id_partita" in df_partite.columns:
        for p_id in df_partite["id_partita"].unique():
            res = calculate_match_ratings(df_voti, p_id)
            if res["has_votes"] and res["mvp"]:
                mvp_name = res["mvp"]["giocatore"]
                mvp_counts[mvp_name] = mvp_counts.get(mvp_name, 0) + 1

    grouped = df_clean.groupby("giocatore")["voto"].agg(["mean", "count"]).reset_index()
    grouped.columns = ["Giocatore", "Media Voto Stagionale", "Voti Ricevuti"]
    grouped["Media Voto Stagionale"] = grouped["Media Voto Stagionale"].round(2)
    grouped["Titoli MVP"] = grouped["Giocatore"].map(lambda x: mvp_counts.get(x, 0))

    grouped = grouped.sort_values(by=["Titoli MVP", "Media Voto Stagionale", "Voti Ricevuti"], ascending=[False, False, False]).reset_index(drop=True)
    return grouped


# ==============================================================================
# 9. ATTRIBUTI STILE FIFA / EA SPORTS FC & METRICHE RADAR CHART (DOMAIN PURE)
# ==============================================================================
OVR_WEIGHTS = {"GOL": 0.45, "RIS": 0.45, "MVP": 0.10}
OVR_GOALS_REFERENCE = 3.5
OVR_RECENT_MATCHES = 5


def _period_rating(records):
    """Use the same fixed 50–99 scales for full history and recent matches.

    A zero award rate is the neutral starting score (50), not a penalty.
    Unpublished elections do not enter the award-rate denominator.
    Keep full precision until the final displayed OVR is rounded.
    """
    if not records:
        return {"ovr": None, "scores": {key: None for key in OVR_WEIGHTS},
                "games": 0, "goals_per_match": 0.0, "points_rate": 0.0,
                "mvp_titles": 0, "mvp_matches": 0}
    games = len(records)
    goals_per_match = sum(row["goals"] for row in records) / games
    points_rate = sum(row["points"] for row in records) / (3 * games)
    settled = [row for row in records if row["settled"]]
    mvp_titles = sum(row["mvp"] for row in settled)
    mvp_rate = mvp_titles / len(settled) if settled else 0.0
    scores = {
        "GOL": 50 + 49 * min(1.0, max(0.0, goals_per_match / OVR_GOALS_REFERENCE)),
        "RIS": 50 + 49 * points_rate,
        "MVP": 50 + 49 * mvp_rate,
    }
    return {"ovr": sum(OVR_WEIGHTS[key] * score for key, score in scores.items()),
            "scores": scores, "games": games, "goals_per_match": goals_per_match,
            "points_rate": points_rate, "mvp_titles": mvp_titles,
            "mvp_matches": len(settled)}


def calculate_player_fifa_stats(
    player_name: str,
    df_giocatori: pd.DataFrame,
    df_partite: pd.DataFrame,
    df_voti: Optional[pd.DataFrame] = None,
    elo_ratings: Optional[Dict[str, float]] = None,
    giocatori_filtrati: Optional[List[str]] = None
) -> Dict[str, Any]:
    """OVR = 80% full-history rating + 20% last-five rating.

    Both ratings use 45% goals, 45% results and 10% published MVP titles.
    ELO is retained as separate match-balancing information only.
    df_partite defines the selected scope, including the Cerchia filter.
    """
    clean_name = str(player_name).strip()
    if elo_ratings is None:
        elo_ratings, _ = calculate_elo_ratings(df_giocatori, df_partite, giocatori_filtrati=giocatori_filtrati)
    p_elo = float(elo_ratings.get(clean_name, 1500.0))

    records = []
    if not df_partite.empty:
        ordered = df_partite.sort_values(by=["data", "id_partita"], ascending=[False, False])
        for _, match in ordered.iterrows():
            team_a = [name.strip() for name in str(match.get("squadra_a_giocatori", "")).split(",") if name.strip()]
            team_b = [name.strip() for name in str(match.get("squadra_b_giocatori", "")).split(",") if name.strip()]
            if clean_name not in team_a and clean_name not in team_b:
                continue
            goals_a = int(match.get("gol_squadra_a", 0))
            goals_b = int(match.get("gol_squadra_b", 0))
            own, other = (goals_a, goals_b) if clean_name in team_a else (goals_b, goals_a)
            result = "V" if own > other else "P" if own == other else "S"
            final = calculate_match_ratings(df_voti, int(match["id_partita"])) if df_voti is not None else {"has_votes": False}
            def awarded(category):
                award = final.get(category) or {}
                return clean_name in award.get("giocatori", [award.get("giocatore")])
            records.append({"match_id": int(match["id_partita"]), "result": result,
                            "points": {"V": 3, "P": 1, "S": 0}[result],
                            "goals": parse_marcatori(match.get("marcatori", "")).get(clean_name, 0),
                            "settled": final["has_votes"], "mvp": awarded("mvp"),
                            "worst": awarded("worst")})

    overall = _period_rating(records)
    recent = _period_rating(records[:OVR_RECENT_MATCHES])
    pg = len(records)
    ovr = int(round(0.80 * overall["ovr"] + 0.20 * recent["ovr"])) if pg else None
    attributes = {key: int(round(score)) if score is not None else None
                  for key, score in overall["scores"].items()}
    attributes["FRM"] = int(round(recent["ovr"])) if pg else None
    wins = sum(row["result"] == "V" for row in records)
    return {
        "giocatore": clean_name, "ovr": ovr, "elo": round(p_elo, 1),
        "pg": pg, "vittorie": wins,
        "pareggi": sum(row["result"] == "P" for row in records),
        "sconfitte": sum(row["result"] == "S" for row in records),
        "win_rate": round(100 * wins / pg, 1) if pg else 0.0,
        "punti": sum(row["points"] for row in records),
        "gol_totali": sum(row["goals"] for row in records),
        "media_gol": round(overall["goals_per_match"], 2),
        "titoli_mvp": overall["mvp_titles"],
        "titoli_peggiore": sum(row["worst"] for row in records),
        "media_voto": None, "forma": [row["result"] for row in records],
        "attributes": attributes, "provisional": 0 < pg < OVR_RECENT_MATCHES,
        "ovr_details": {"overall": overall, "recent": recent,
                        "goal_reference": OVR_GOALS_REFERENCE, "weights": dict(OVR_WEIGHTS)},
    }


def calculate_radar_metrics(
    player_name: str,
    df_giocatori: pd.DataFrame,
    df_partite: pd.DataFrame,
    df_voti: Optional[pd.DataFrame] = None,
    elo_ratings: Optional[Dict[str, float]] = None,
    giocatori_filtrati: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Compare the agreed OVR indices with players who have actually played."""
    p_stats = calculate_player_fifa_stats(
        player_name, df_giocatori, df_partite, df_voti, elo_ratings, giocatori_filtrati
    )
    if giocatori_filtrati is not None:
        all_players = list(giocatori_filtrati)
    elif not df_giocatori.empty and "nome_completo" in df_giocatori.columns:
        all_players = sorted(df_giocatori["nome_completo"].dropna().unique().tolist())
    else:
        all_players = [player_name]
    keys = ["GOL", "RIS", "MVP", "FRM"]
    all_attrs = {key: [] for key in keys}
    for name in all_players:
        stats = calculate_player_fifa_stats(name, df_giocatori, df_partite, df_voti, elo_ratings, giocatori_filtrati)
        if stats["pg"]:
            for key in keys:
                all_attrs[key].append(stats["attributes"][key])
    avg_attrs = {key: round(sum(values) / len(values), 1) if values else None
                 for key, values in all_attrs.items()}
    return {
        "categories": ["Gol · 45%", "Risultati · 45%", "MVP · 10%", "Rendimento recente"],
        "player_values": [p_stats["attributes"][key] for key in keys] if p_stats["pg"] else [],
        "avg_values": [avg_attrs[key] for key in keys] if p_stats["pg"] else [],
        "player_stats": p_stats, "avg_stats": avg_attrs,
    }
