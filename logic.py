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
# 4. CLASSIFICA GENERALE RENDIMENTO
# ==============================================================================
def calculate_leaderboard(
    df_giocatori: pd.DataFrame, 
    df_partite: pd.DataFrame,
    elo_ratings: Optional[Dict[str, float]] = None,
    giocatori_filtrati: Optional[List[str]] = None
) -> pd.DataFrame:
    """
    Calcola la classifica generale dei giocatori:
    Punti (V*3 + P*1), Partite Giocate (PG), V, P, S, % Vittoria, ELO Attuale.
    Se passato 'giocatori_filtrati', include solo tali giocatori.
    """
    if elo_ratings is None:
        elo_ratings, _ = calculate_elo_ratings(df_giocatori, df_partite, giocatori_filtrati=giocatori_filtrati)

    if df_giocatori.empty:
        return pd.DataFrame(columns=["Giocatore", "Punti", "PG", "V", "P", "S", "% Vittoria", "ELO"])

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

        rows.append({
            "Giocatore": player,
            "Punti": punti,
            "PG": pg,
            "V": v,
            "P": p,
            "S": sc,
            "% Vittoria": win_rate,
            "ELO": round(current_elo, 1)
        })

    df_res = pd.DataFrame(rows)
    if not df_res.empty:
        df_res = df_res.sort_values(
            by=["Punti", "% Vittoria", "ELO", "PG", "Giocatore"],
            ascending=[False, False, False, False, True]
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
