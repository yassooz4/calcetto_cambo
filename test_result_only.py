import json
import unittest

import pandas as pd

import logic
import ratings

PLAYERS = pd.DataFrame([
    {"id_giocatore": 1, "nome_completo": "Ada", "in_gruppo_ristretto": True},
    {"id_giocatore": 2, "nome_completo": "Beto", "in_gruppo_ristretto": True},
])
CALIBRATION = {"season": "Test", "sample_matches": 3, "eligible_players": 3,
               "goal_reference": 4.0, "goal_prior": 2.0, "result_prior": .5,
               "prior_matches": 5.0, "mvp_prior_matches": 5.0}


def match(index, ga, gb, scorers):
    return {"id_partita": index, "data": f"2026-10-0{index}", "squadra_a_giocatori": "Ada",
            "squadra_b_giocatori": "Beto", "gol_squadra_a": ga, "gol_squadra_b": gb,
            "marcatori": json.dumps(scorers) if scorers else "{}"}


class ResultOnlyMatchTests(unittest.TestCase):
    def test_has_scorer_detail(self):
        self.assertTrue(logic.has_scorer_detail(0, 0, "{}"))
        self.assertTrue(logic.has_scorer_detail(2, 1, '{"Ada": 2}'))
        self.assertFalse(logic.has_scorer_detail(3, 1, "{}"))
        self.assertFalse(logic.has_scorer_detail(3, 1, ""))

    def test_scorers_ignore_result_only_matches_in_averages(self):
        frame = pd.DataFrame([match(1, 2, 0, {"Ada": 2}), match(2, 5, 3, None)])
        table = logic.calculate_scorers(PLAYERS, frame).set_index("Giocatore")
        self.assertEqual(table.loc["Ada", "Gol Totali"], 2)
        self.assertEqual(table.loc["Ada", "PG"], 1)
        self.assertEqual(table.loc["Ada", "Media Gol"], 2.0)
        self.assertEqual(table.loc["Beto", "PG"], 1)

    def test_ovr_goal_average_ignores_result_only_matches(self):
        with_detail = pd.DataFrame([match(1, 2, 0, {"Ada": 2})])
        both = pd.DataFrame([match(1, 2, 0, {"Ada": 2}), match(2, 5, 3, None)])
        awards = pd.DataFrame([])
        result = {}
        for label, frame in [("one", with_detail), ("both", both)]:
            context = ratings.build_context(PLAYERS, frame, awards, CALIBRATION)
            stats = ratings.calculate_player_stats("Ada", PLAYERS, frame, awards, None, rating_context=context)
            result[label] = stats["ovr_details"]["overall"]
        self.assertEqual(result["both"]["games"], 2)
        self.assertEqual(result["both"]["goals_per_match"], 2.0)
        self.assertEqual(result["both"]["estimated_goals"], result["one"]["estimated_goals"])
        self.assertEqual(result["both"]["scores"]["GOL"], result["one"]["scores"]["GOL"])


if __name__ == "__main__":
    unittest.main()

