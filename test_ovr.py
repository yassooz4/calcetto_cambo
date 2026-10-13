import json
import unittest

import pandas as pd

import logic
import ratings

PLAYERS = pd.DataFrame([
    {"id_giocatore": 1, "nome_completo": "Ada", "in_gruppo_ristretto": True},
    {"id_giocatore": 2, "nome_completo": "Beto", "in_gruppo_ristretto": True},
    {"id_giocatore": 3, "nome_completo": "Ciro", "in_gruppo_ristretto": False},
    {"id_giocatore": 4, "nome_completo": "Dina", "in_gruppo_ristretto": True},
])
CALIBRATION = {"season": "Test", "sample_matches": 3, "eligible_players": 3,
               "goal_reference": 4.0, "goal_prior": 2.0, "result_prior": .5,
               "prior_matches": 5.0, "mvp_prior_matches": 5.0}


def match(index=1, result="V", goals=2, team_b="Beto"):
    ga, gb = {"V": (5, 3), "P": (3, 3), "S": (3, 5)}[result]
    return {"id_partita": index, "data": "2026-10-01", "squadra_a_giocatori": "Ada",
            "squadra_b_giocatori": team_b, "gol_squadra_a": ga, "gol_squadra_b": gb,
            "marcatori": json.dumps({"Ada": goals})}


def final(index=1, names=None, worst=None):
    return {"id_partita": index, "mvp_names": names or ["Ada"],
            "worst_names": worst or ["Beto"], "mvp_votes": 2, "worst_votes": 1,
            "total_ballots": 3}


def record(goals=2, points=3, settled=False, mvp=False, factor=1):
    return {"goals": goals, "points": points, "adjusted_points": points * factor,
            "settled": settled, "mvp": mvp}


class OVRTests(unittest.TestCase):
    def stats(self, matches=None, finals=None, player="Ada", elo=None, context=None):
        frame = pd.DataFrame([match()] if matches is None else matches)
        awards = pd.DataFrame([] if finals is None else finals)
        context = ratings.build_context(PLAYERS, frame, awards, CALIBRATION) if context is None else context
        return ratings.calculate_player_stats(player, PLAYERS, frame, awards, elo, rating_context=context)

    def test_known_first_match_formula_and_exact_blend(self):
        stats = self.stats(finals=[final()])
        overall = stats["ovr_details"]["overall"]
        # Independent calculation: 2 goals/game, (1+.5*5)/6 results,
        # and one MVP out of (1+5) elections; no intermediate rounding.
        self.assertAlmostEqual(overall["scores"]["GOL"], 74.5)
        self.assertAlmostEqual(overall["scores"]["RIS"], 78.58333333333333)
        self.assertAlmostEqual(overall["scores"]["MVP"], 58.166666666666664)
        self.assertAlmostEqual(overall["ovr"], 74.70416666666667)
        self.assertEqual(stats["ovr"], 75)
        self.assertTrue(stats["provisional"])

    def test_one_exceptional_game_cannot_produce_99_ovr(self):
        self.assertLess(self.stats([match(goals=20)], [final()])["ovr"], 90)

    def test_mvp_small_sample_and_open_elections(self):
        stats = self.stats([match(i) for i in range(1, 11)], [final(1), final(99)])
        overall = stats["ovr_details"]["overall"]
        self.assertEqual(overall["mvp_matches"], 1)
        self.assertAlmostEqual(overall["scores"]["MVP"], 50 + 49 / 6)
        self.assertEqual(stats["ovr_details"]["recent"]["scores"]["MVP"], 50)

    def test_mvp_rate_uses_only_published_played_matches_and_ties(self):
        stats = self.stats([match(1), match(2)], [final(1, ["Ada", "Beto"]), final(2, ["Beto"])])
        self.assertEqual(stats["titoli_mvp"], 1)
        self.assertEqual(stats["mvp_partite"], 2)
        self.assertAlmostEqual(stats["ovr_details"]["overall"]["scores"]["MVP"], 57)

    def test_more_observations_strengthen_evidence_without_attendance_bonus(self):
        one = ratings.period_rating([record(goals=0, points=0)], CALIBRATION)
        many = ratings.period_rating([record(goals=0, points=0)] * 20, CALIBRATION)
        self.assertGreater(one["ovr"], many["ovr"])
        good_one = ratings.period_rating([record(goals=4)], CALIBRATION)
        good_many = ratings.period_rating([record(goals=4)] * 20, CALIBRATION)
        self.assertLess(good_one["ovr"], good_many["ovr"])

    def test_draw_loss_and_caps_are_bounded(self):
        no_prior = dict(CALIBRATION, prior_matches=0, mvp_prior_matches=0)
        draw = ratings.period_rating([record(goals=0, points=1)], no_prior)
        self.assertAlmostEqual(draw["scores"]["RIS"], 50 + 49 / 3)
        loss = ratings.period_rating([record(goals=0, points=0)], no_prior)
        self.assertEqual(loss["ovr"], 50)
        maximum = ratings.period_rating([record(goals=100, factor=1.5, settled=True, mvp=True)], no_prior)
        self.assertAlmostEqual(maximum["ovr"], 99)

    def test_underdog_win_rewards_more_than_favourite_win(self):
        warmup = [dict(match(i), squadra_a_giocatori="Beto", squadra_b_giocatori="Ciro", marcatori="{}") for i in range(1, 4)]
        underdog = self.stats(warmup + [match(4, team_b="Beto")])
        favourite = self.stats(warmup + [match(4, team_b="Ciro")])
        self.assertLess(underdog["last_match"]["expected"], .5)
        self.assertGreater(favourite["last_match"]["expected"], .5)
        self.assertGreater(underdog["ovr_details"]["overall"]["adjusted_points"], 3)
        self.assertGreater(underdog["ovr"], favourite["ovr"])

    def test_elo_replay_matches_existing_algorithm_and_never_uses_final_strength(self):
        frame = pd.DataFrame([match(i, "S" if i % 3 == 0 else "V", team_b="Beto" if i % 2 else "Ciro") for i in range(1, 9)])
        context = ratings.build_context(PLAYERS, frame, calibration=CALIBRATION)
        elo, _ = logic.calculate_elo_ratings(PLAYERS, frame)
        for name, value in context["elo"].items():
            self.assertEqual(value, elo[name])
        for end in range(1, 8):
            before, _ = logic.calculate_elo_ratings(PLAYERS, frame.iloc[:end])
            row = frame.iloc[end]
            expected = 1 / (1 + 10 ** ((before[row["squadra_b_giocatori"]] - before["Ada"]) / 400))
            self.assertAlmostEqual(context["by_player"]["Ada"][end]["expected"], expected)

    def test_appending_future_games_does_not_rewrite_pre_match_strength_or_previous_history(self):
        prefix = [match(i) for i in range(1, 4)]
        short, full = self.stats(prefix), self.stats(prefix + [match(4, "S", 0)])
        self.assertEqual(short["history"], full["history"][:3])

    def test_recent_form_uses_latest_five_played_games(self):
        matches = [match(i) for i in range(1, 7)]
        matches += [dict(match(i), squadra_a_giocatori="Ciro") for i in range(7, 12)]
        stats = self.stats(list(reversed(matches)))
        self.assertEqual(stats["pg"], 6)
        self.assertEqual(stats["ovr_details"]["recent"]["games"], 5)
        self.assertEqual([row["match_id"] for row in stats["history"]], list(range(1, 7)))

    def test_recent_improvement_is_reflected_in_ovr(self):
        declining = [match(i, "V" if i <= 4 else "S", 4 if i <= 4 else 0) for i in range(1, 9)]
        improving = [match(i, "V" if i >= 5 else "S", 4 if i >= 5 else 0) for i in range(1, 9)]
        low, high = self.stats(declining), self.stats(improving)
        self.assertGreater(high["attributes"]["FRM"], low["attributes"]["FRM"])
        self.assertGreater(high["ovr"], low["ovr"])
        for stats in [low, high]:
            d = stats["ovr_details"]
            self.assertEqual(stats["ovr"], round(.8 * d["overall"]["ovr"] + .2 * d["recent"]["ovr"]))

    def test_current_elo_worst_titles_and_unplayed_members_do_not_add_ovr_points(self):
        first = self.stats(finals=[final()], elo={"Ada": 1000})
        second = self.stats(finals=[final(worst=["Ada"])], elo={"Ada": 2000})
        self.assertEqual(first["ovr"], second["ovr"])
        self.assertEqual(second["titoli_peggiore"], 1)
        self.assertNotEqual(first["elo"], second["elo"])

    def test_no_games_have_no_fabricated_rating_history_or_comparison(self):
        stats = self.stats(player="Dina")
        self.assertIsNone(stats["ovr"])
        self.assertEqual(stats["history"], [])
        self.assertTrue(all(value is None for value in stats["attributes"].values()))
        comparison = ratings.calculate_comparison("Dina", PLAYERS, pd.DataFrame([match()]))
        self.assertEqual(comparison["player_values"], [])

    def test_benchmark_has_only_three_components_and_excludes_unplayed_members(self):
        frame = pd.DataFrame([match()])
        full = ratings.calculate_comparison("Ada", PLAYERS, frame)
        active = ratings.calculate_comparison("Ada", PLAYERS.iloc[:2], frame)
        self.assertEqual(full["avg_values"], active["avg_values"])
        self.assertEqual(full["categories"], ["Gol", "Risultati", "MVP"])
        self.assertEqual(full["active_players"], 2)

    def test_cerchia_filter_limits_awards_form_history_but_preserves_full_context(self):
        frame = pd.DataFrame([match(1, team_b="Ciro"), match(2)])
        awards = pd.DataFrame([final(1), final(2, ["Beto"])])
        context = ratings.build_context(PLAYERS, frame, awards, CALIBRATION)
        filtered = logic.filter_internal_matches(frame, ["Ada", "Beto", "Dina"])
        stats = ratings.calculate_player_stats("Ada", PLAYERS, filtered, awards, rating_context=context)
        self.assertEqual(stats["pg"], 1)
        self.assertEqual(stats["titoli_mvp"], 0)
        self.assertEqual(stats["mvp_partite"], 1)
        self.assertEqual([row["match_id"] for row in stats["history"]], [2])
        self.assertEqual(stats["last_match"]["expected"], context["by_player"]["Ada"][1]["expected"])
        self.assertEqual(stats["ovr_details"]["goal_reference"], CALIBRATION["goal_reference"])
        self.assertEqual(logic.calculate_player_vote_stats(filtered, awards).get("Ada", {}).get("titoli_mvp", 0), 0)

    def test_legacy_mvp_titles_remain_usable(self):
        legacy = [{"id_partita": 1, "giocatore": "Ada", "voto": 8}, {"id_partita": 1, "giocatore": "Beto", "voto": 5}]
        stats = self.stats(finals=legacy)
        self.assertEqual(stats["titoli_mvp"], 1)
        self.assertEqual(stats["mvp_partite"], 1)

    def test_history_delta_and_explanation_follow_last_played_game(self):
        stats = self.stats([match(1, "S", 0), match(2, "V", 4)])
        self.assertEqual(stats["ovr_delta"], stats["history"][-1]["ovr"] - stats["history"][-2]["ovr"])
        self.assertIn("in crescita", stats["trend_explanation"])
        self.assertIsNone(self.stats()["ovr_delta"])

    def test_calibration_uses_eligible_players_and_freezes_new_game_effects(self):
        games = [dict(match(i), squadra_a_giocatori="Ada, Ciro", squadra_b_giocatori="Beto, Dina",
                      marcatori=json.dumps({"Ada": 2, "Ciro": 1, "Dina": 3})) for i in range(1, 4)]
        frame = pd.DataFrame(games)
        config = ratings.calibrate_season(frame, "Test", "2026-10-13")
        self.assertEqual(config["goal_reference"], 3)
        self.assertEqual(config["goal_prior"], 1.5)
        self.assertEqual(config["sample_appearances"], 12)
        outlier = dict(match(4, goals=100), squadra_a_giocatori="Ena", squadra_b_giocatori="Fio", marcatori='{"Ena":100}')
        recalibrated = ratings.calibrate_season(pd.DataFrame(games + [outlier]), "Test", "2026-10-13")
        self.assertEqual(recalibrated["goal_reference"], config["goal_reference"])
        short = ratings.build_context(PLAYERS, frame, calibration=config)
        longer = ratings.build_context(PLAYERS, pd.DataFrame(games + [outlier]), calibration=config)
        self.assertEqual(short["calibration"], longer["calibration"])
        self.assertEqual(ratings.calculate_player_stats("Ada", PLAYERS, frame, rating_context=short)["ovr"],
                         ratings.calculate_player_stats("Ada", PLAYERS, pd.DataFrame(games + [outlier]), rating_context=longer)["ovr"])

    def test_insufficient_or_invalid_calibration_is_rejected(self):
        with self.assertRaises(ValueError):
            ratings.calibrate_season(pd.DataFrame([match()]), "Test", "2026-10-13")
        for field, value in [("goal_reference", 0), ("goal_prior", float("nan")), ("prior_matches", -1), ("result_prior", 2)]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                ratings.build_context(PLAYERS, pd.DataFrame([match()]), calibration=dict(CALIBRATION, **{field: value}))

    def test_compatibility_entry_points_use_new_model(self):
        frame = pd.DataFrame([match()])
        self.assertEqual(logic.calculate_player_fifa_stats("Ada", PLAYERS, frame)["ovr"],
                         ratings.calculate_player_stats("Ada", PLAYERS, frame)["ovr"])
        self.assertEqual(len(logic.calculate_radar_metrics("Ada", PLAYERS, frame)["categories"]), 3)


if __name__ == "__main__":
    unittest.main()
