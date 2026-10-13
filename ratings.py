"""Public performance ratings: fixed seasonal scales, cautious estimates and history.

Only match rosters, goals, scores and published MVP summaries enter this module.
It never reads player passwords, individual ballots or production storage.
"""
from functools import lru_cache
from pathlib import Path
import json
import math

import pandas as pd

WEIGHTS = {"GOL": 0.45, "RIS": 0.45, "MVP": 0.10}
RECENT_MATCHES = 5


def _names(raw):
    if raw is None or pd.isna(raw):
        return []
    return list(dict.fromkeys(name.strip() for name in str(raw).split(",") if name.strip()))


def _ordered(matches):
    return matches.sort_values(["data", "id_partita"]) if not matches.empty else matches


def calibrate_season(matches, season, calibrated_at):
    """Prepare a public aggregate snapshot; caller saves it once for the season.

    Use the 95th percentile of player goal averages with >=3 games, rounded up
    to a quarter goal. These are explicit design rules, not validated constants.
    An individual one-game outlier cannot set the goal reference.
    """
    from logic import parse_marcatori
    totals, appearances, points = {}, {}, 0
    ids = []
    for _, match in _ordered(matches).iterrows():
        a, b = _names(match.get("squadra_a_giocatori")), _names(match.get("squadra_b_giocatori"))
        if not a or not b or set(a) & set(b):
            continue
        goals = parse_marcatori(match.get("marcatori", ""))
        ga, gb = int(match["gol_squadra_a"]), int(match["gol_squadra_b"])
        ids.append(int(match["id_partita"]))
        for roster, own, other in [(a, ga, gb), (b, gb, ga)]:
            for name in roster:
                appearances[name] = appearances.get(name, 0) + 1
                totals[name] = totals.get(name, 0) + goals.get(name, 0)
                points += 3 if own > other else 1 if own == other else 0
    eligible = [totals[name] / n for name, n in appearances.items() if n >= 3]
    if len(ids) < 3 or len(eligible) < 3:
        raise ValueError("Servono almeno tre partite e tre giocatori con tre presenze per calibrare la stagione.")
    count = sum(appearances.values())
    return {"season": str(season), "calibrated_at": str(calibrated_at),
            "sample_matches": len(ids), "sample_appearances": count,
            "sample_players": len(appearances), "eligible_players": len(eligible),
            "snapshot_match_ids": ids, "min_calibration_games": 3, "goal_quantile": 0.95,
            "goal_reference": max(0.5, math.ceil(float(pd.Series(eligible).quantile(0.95)) * 4) / 4),
            "goal_prior": sum(totals.values()) / count,
            "result_prior": points / (3 * count),
            "prior_matches": 5.0, "mvp_prior_matches": 5.0}


@lru_cache(maxsize=1)
def load_calibration():
    """A committed snapshot stays fixed across new matches, filters and reruns."""
    return json.loads(Path(__file__).with_name("rating_calibration.json").read_text(encoding="utf-8"))


def _validated_calibration(calibration):
    config = dict(load_calibration() if calibration is None else calibration)
    for field in ["goal_reference", "goal_prior", "result_prior", "prior_matches", "mvp_prior_matches"]:
        value = float(config[field])
        if not math.isfinite(value) or value < 0 or (field == "goal_reference" and value == 0):
            raise ValueError(f"Calibrazione non valida: {field}")
        config[field] = value
    if config["result_prior"] > 1:
        raise ValueError("Calibrazione risultati fuori scala.")
    return config


def build_context(players, matches, finals=None, calibration=None):
    """Replay full history once, recording the expectation BEFORE updating ELO.

    The ELO update matches logic.calculate_elo_ratings exactly (including its
    rounding and goal-margin multiplier). Final ELO is never used as hindsight.
    Build with the full archive even when the displayed card has a Cerchia filter.
    """
    from logic import parse_marcatori, calculate_match_ratings
    config = _validated_calibration(calibration)
    elo, by_player = {}, {}
    for _, match in _ordered(matches).iterrows():
        a, b = _names(match.get("squadra_a_giocatori")), _names(match.get("squadra_b_giocatori"))
        if not a or not b or set(a) & set(b):
            continue
        for name in a + b:
            elo.setdefault(name, 1500.0)
        avg_a = sum(elo[name] for name in a) / len(a)
        avg_b = sum(elo[name] for name in b) / len(b)
        # Clamp only the exponent to avoid numeric overflow for corrupt extremes.
        exponent = max(-300.0, min(300.0, (avg_b - avg_a) / 400.0))
        expected_a = 1 / (1 + 10 ** exponent)
        ga, gb = int(match["gol_squadra_a"]), int(match["gol_squadra_b"])
        match_id = int(match["id_partita"])
        goals = parse_marcatori(match.get("marcatori", ""))
        final = calculate_match_ratings(finals, match_id) if finals is not None else {"has_votes": False}
        mvp = final.get("mvp") or {}
        mvp_names = mvp.get("giocatori", [mvp.get("giocatore")])
        worst = final.get("worst") or {}
        worst_names = worst.get("giocatori", [worst.get("giocatore")])
        settled = bool(final.get("has_votes") and mvp_names and any(name is not None for name in mvp_names))
        for roster, own, other, expected in [(a, ga, gb, expected_a), (b, gb, ga, 1 - expected_a)]:
            result = "V" if own > other else "P" if own == other else "S"
            points = {"V": 3, "P": 1, "S": 0}[result]
            # Equal teams -> ordinary points; favourite wins -> smaller reward.
            factor = 1.5 - expected
            for name in roster:
                by_player.setdefault(name, []).append({"match_id": match_id, "date": str(match["data"]),
                    "result": result, "points": points, "adjusted_points": points * factor,
                    "expected": expected, "difficulty_factor": factor,
                    "goals": goals.get(name, 0), "settled": settled,
                    "mvp": settled and name in mvp_names, "worst": name in worst_names})
        score_a = 1.0 if ga > gb else 0.0 if ga < gb else 0.5
        delta = 32 * (1 + math.log(1 + abs(ga - gb))) * (score_a - expected_a)
        for name in a:
            elo[name] = round(elo[name] + delta, 1)
        for name in b:
            elo[name] = round(elo[name] - delta, 1)
    return {"calibration": config, "by_player": by_player, "elo": elo}


def period_rating(records, calibration):
    """Shrink goals/results towards frozen league means; shrink MVP to no bonus.

    Five equivalent matches temper small samples. Open elections contribute no
    observations. All actual counters remain untouched and visible to the user.
    """
    n = len(records)
    if not n:
        return {"ovr": None, "scores": {key: None for key in WEIGHTS}, "games": 0,
                "mvp_matches": 0, "mvp_titles": 0, "goals_per_match": 0.0,
                "points_rate": 0.0, "adjusted_points": 0.0}
    prior = calibration["prior_matches"]
    goals = sum(row["goals"] for row in records)
    adjusted = sum(row["adjusted_points"] for row in records)
    estimated_goals = (goals + prior * calibration["goal_prior"]) / (n + prior)
    estimated_results = (adjusted / 3 + prior * calibration["result_prior"]) / (n + prior)
    settled = [row for row in records if row["settled"]]
    titles = sum(row["mvp"] for row in settled)
    mvp_denom = len(settled) + calibration["mvp_prior_matches"]
    estimated_mvp = titles / mvp_denom if mvp_denom else 0.0
    clamp = lambda value: min(1.0, max(0.0, value))
    scores = {"GOL": 50 + 49 * clamp(estimated_goals / calibration["goal_reference"]),
              "RIS": 50 + 49 * clamp(estimated_results), "MVP": 50 + 49 * clamp(estimated_mvp)}
    return {"ovr": sum(WEIGHTS[key] * value for key, value in scores.items()),
            "scores": scores, "games": n, "goals_per_match": goals / n,
            "estimated_goals": estimated_goals, "estimated_results": estimated_results,
            "points_rate": sum(row["points"] for row in records) / (3 * n),
            "adjusted_points": adjusted, "mvp_titles": titles, "mvp_matches": len(settled),
            "estimated_mvp": estimated_mvp, "data_weight": n / (n + prior)}


def _snapshot(records, calibration):
    overall = period_rating(records, calibration)
    recent = period_rating(records[-RECENT_MATCHES:], calibration)
    exact = .8 * overall["ovr"] + .2 * recent["ovr"]
    return {"ovr": int(round(exact)), "exact": exact, "overall": overall, "recent": recent,
            "contributions": {key: .8 * overall["scores"][key] + .2 * recent["scores"][key] for key in WEIGHTS}}


def _trend_explanation(previous, current, last):
    if previous is None:
        return "Prima partita registrata: la stima è ancora provvisoria."
    diffs = {key: current["contributions"][key] - previous["contributions"][key] for key in WEIGHTS}
    labels = {"GOL": "rendimento nei gol", "RIS": "rendimento nei risultati", "MVP": "indice MVP"}
    parts = []
    for key in sorted(diffs, key=lambda item: abs(WEIGHTS[item] * diffs[item]), reverse=True)[:2]:
        if abs(diffs[key]) >= .05:
            parts.append(f"{labels[key].capitalize()} {'in crescita' if diffs[key] > 0 else 'in calo'}")
    if last["result"] == "V":
        parts.append(f"Vittoria {'da favorita' if last['expected'] > .55 else 'contro una squadra favorita' if last['expected'] < .45 else 'tra squadre equilibrate'}")
    return "; ".join(parts) + "." if parts else "Punteggio sostanzialmente stabile dopo l'ultima partita."


def calculate_player_stats(player_name, players, matches, finals=None, elo_ratings=None,
                           giocatori_filtrati=None, rating_context=None, include_history=True):
    """The match frame sets card scope; the context sets pre-match strength/scale."""
    name = str(player_name).strip()
    context = rating_context if rating_context is not None else build_context(players, matches, finals)
    config = context["calibration"]
    ids = set(int(value) for value in matches["id_partita"]) if not matches.empty else set()
    records = [row for row in context["by_player"].get(name, []) if row["match_id"] in ids]
    history, snapshots = [], []
    ends = range(1, len(records) + 1) if include_history else range(max(1, len(records) - 1), len(records) + 1)
    for end in ends:
        snapshot = _snapshot(records[:end], config)
        snapshots.append(snapshot)
        row = records[end - 1]
        if include_history:
            history.append({"match_id": row["match_id"], "date": row["date"], "ovr": snapshot["ovr"],
                            "result": row["result"], "goals": row["goals"], "expected": row["expected"]})
    current = snapshots[-1] if snapshots else None
    previous = snapshots[-2] if len(snapshots) > 1 else None
    pg = len(records)
    overall = current["overall"] if current else period_rating([], config)
    recent = current["recent"] if current else period_rating([], config)
    attrs = {key: int(round(score)) if score is not None else None for key, score in overall["scores"].items()}
    attrs["FRM"] = int(round(recent["ovr"])) if pg else None
    wins = sum(row["result"] == "V" for row in records)
    return {"giocatore": name, "ovr": current["ovr"] if current else None,
            "elo": round((elo_ratings or context["elo"]).get(name, 1500.0), 1),
            "pg": pg, "vittorie": wins, "pareggi": sum(row["result"] == "P" for row in records),
            "sconfitte": sum(row["result"] == "S" for row in records),
            "win_rate": round(100 * wins / pg, 1) if pg else 0.0,
            "punti": sum(row["points"] for row in records),
            "gol_totali": sum(row["goals"] for row in records), "media_gol": round(overall["goals_per_match"], 2),
            "titoli_mvp": overall["mvp_titles"], "mvp_partite": overall["mvp_matches"],
            "titoli_peggiore": sum(row["worst"] for row in records), "media_voto": None,
            "forma": [row["result"] for row in reversed(records)], "attributes": attrs,
            "provisional": 0 < pg < 5, "history": history,
            "ovr_delta": current["ovr"] - previous["ovr"] if previous else None,
            "trend_explanation": _trend_explanation(previous, current, records[-1]) if current else "",
            "last_match": dict(records[-1]) if records else None,
            "ovr_details": {"overall": overall, "recent": recent, "weights": dict(WEIGHTS),
                            "goal_reference": config["goal_reference"], "calibration": dict(config)}}


def calculate_comparison(player_name, players, matches, finals=None, elo_ratings=None,
                         giocatori_filtrati=None, rating_context=None):
    """Three independent components, with one equal-weight observation per player."""
    context = rating_context if rating_context is not None else build_context(players, matches, finals)
    selected = calculate_player_stats(player_name, players, matches, finals, elo_ratings,
                                      giocatori_filtrati, context)
    names = (giocatori_filtrati if giocatori_filtrati is not None else
             players["nome_completo"].dropna().unique().tolist() if not players.empty else [player_name])
    values = {key: [] for key in WEIGHTS}
    for name in names:
        stats = calculate_player_stats(name, players, matches, finals, elo_ratings, rating_context=context, include_history=False)
        if stats["pg"]:
            for key in WEIGHTS:
                values[key].append(stats["ovr_details"]["overall"]["scores"][key])
    averages = {key: round(sum(items) / len(items), 1) if items else None for key, items in values.items()}
    return {"categories": ["Gol", "Risultati", "MVP"],
            "player_values": [selected["attributes"][key] for key in WEIGHTS] if selected["pg"] else [],
            "avg_values": [averages[key] for key in WEIGHTS] if selected["pg"] else [],
            "player_stats": selected, "avg_stats": averages,
            "active_players": len(values["GOL"])}
