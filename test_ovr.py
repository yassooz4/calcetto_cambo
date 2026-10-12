import json
import unittest

import pandas as pd

import logic


PLAYERS = pd.DataFrame([
    {"id_giocatore": 1, "nome_completo": "Ada", "in_gruppo_ristretto": True},
    {"id_giocatore": 2, "nome_completo": "Beto", "in_gruppo_ristretto": True},
    {"id_giocatore": 3, "nome_completo": "Ciro", "in_gruppo_ristretto": False},
    {"id_giocatore": 4, "nome_completo": "Dina", "in_gruppo_ristretto": True},
])


def match(index=1, result="V", goals=2, team_b="Beto"):
    score_a, score_b = {"V": (5, 3), "P": (3, 3), "S": (3, 5)}[result]
    return {"id_partita": index, "data": "2026-10-01", "squadra_a_giocatori": "Ada",
            "squadra_b_giocatori": team_b, "gol_squadra_a": score_a,
            "gol_squadra_b": score_b, "marcatori": json.dumps({"Ada": goals})}


def final(index=1, names=None, worst=None):
    return {"id_partita": index, "mvp_names": names or ["Ada"],
            "worst_names": worst or ["Beto"], "mvp_votes": 2, "worst_votes": 1,
            "total_ballots": 3}


class OVRTests(unittest.TestCase):
    def stats(self, matches=None, finals=None, player="Ada", elo=1500):
        return logic.calculate_player_fifa_stats(player, PLAYERS,
            pd.DataFrame(matches if matches is not None else [match()]),
            pd.DataFrame(finals if finals is not None else []), {player: elo})

    def test_agreed_weights_and_unrounded_blend(self):
        stats = self.stats(finals=[final()])
        # Goals 2/game = 78; winning and receiving MVP = 99 each.
        self.assertAlmostEqual(stats["ovr_details"]["overall"]["ovr"], 89.55)
        self.assertAlmostEqual(stats["ovr_details"]["recent"]["ovr"], 89.55)
        self.assertEqual(stats["ovr"], 90)
        self.assertEqual(stats["attributes"], {"GOL": 78, "RIS": 99, "MVP": 99, "FRM": 90})
        self.assertTrue(stats["provisional"])

    def test_draws_losses_and_goal_ceiling(self):
        self.assertEqual(self.stats([match(result="P", goals=0)])["ovr"], 57)
        self.assertEqual(self.stats([match(result="S", goals=0)])["ovr"], 50)
        self.assertEqual(self.stats([match(result="S", goals=100)])["attributes"]["GOL"], 99)
        self.assertEqual(self.stats([match(goals=4)], [final()])["ovr"], 99)

    def test_recent_form_can_raise_or_lower_same_overall_record(self):
        declining = [match(i, "V" if i <= 4 else "S", 3 if i <= 4 else 0) for i in range(1, 9)]
        improving = [match(i, "V" if i >= 5 else "S", 3 if i >= 5 else 0) for i in range(1, 9)]
        low, high = self.stats(declining), self.stats(improving)
        self.assertAlmostEqual(low["ovr_details"]["overall"]["ovr"], 70.475)
        self.assertAlmostEqual(high["ovr_details"]["overall"]["ovr"], 70.475)
        self.assertAlmostEqual(low["ovr_details"]["recent"]["ovr"], 58.19)
        self.assertAlmostEqual(high["ovr_details"]["recent"]["ovr"], 82.76)
        self.assertEqual((low["ovr"], high["ovr"]), (68, 73))
        self.assertEqual(low["ovr_details"]["recent"]["games"], 5)
        self.assertEqual(low["ovr"], self.stats(list(reversed(declining)))["ovr"])

    def test_recent_window_counts_only_played_matches(self):
        matches = [match(i) for i in range(1, 4)]
        matches += [dict(match(i), squadra_a_giocatori="Ciro") for i in range(4, 10)]
        stats = self.stats(matches)
        self.assertEqual(stats["pg"], 3)
        self.assertEqual(stats["ovr_details"]["recent"]["games"], 3)
        self.assertEqual(stats["forma"], ["V", "V", "V"])

    def test_mvp_denominator_uses_published_participant_matches_and_ties(self):
        matches = [match(i) for i in range(1, 11)]
        votes = [final(1, ["Ada", "Beto"]), final(2, ["Beto"]), final(99, ["Ada"])]
        stats = self.stats(matches, votes)
        self.assertEqual(stats["titoli_mvp"], 1)
        self.assertEqual(stats["ovr_details"]["overall"]["mvp_matches"], 2)
        self.assertAlmostEqual(stats["ovr_details"]["overall"]["scores"]["MVP"], 74.5)
        self.assertEqual(stats["ovr_details"]["recent"]["mvp_matches"], 0)
        self.assertEqual(self.stats(matches, votes, "Dina")["titoli_mvp"], 0)

    def test_elo_worst_titles_and_unplayed_matches_do_not_change_ovr(self):
        first = self.stats(finals=[final()], elo=1000)
        second = self.stats(finals=[final(worst=["Ada"])], elo=2000)
        self.assertEqual(first["ovr"], second["ovr"])
        self.assertEqual(second["titoli_peggiore"], 1)
        self.assertNotEqual(first["elo"], second["elo"])

    def test_no_games_have_no_fabricated_ovr_or_radar(self):
        stats = self.stats(player="Dina")
        self.assertIsNone(stats["ovr"])
        self.assertTrue(all(value is None for value in stats["attributes"].values()))
        self.assertFalse(stats["provisional"])
        radar = logic.calculate_radar_metrics("Dina", PLAYERS, pd.DataFrame([match()]), pd.DataFrame())
        self.assertEqual(radar["player_values"], [])

    def test_radar_benchmark_excludes_unplayed_members(self):
        matches = pd.DataFrame([match()])
        subset = PLAYERS[PLAYERS["nome_completo"].isin(["Ada", "Beto"])]
        full = logic.calculate_radar_metrics("Ada", PLAYERS, matches, pd.DataFrame())
        played_only = logic.calculate_radar_metrics("Ada", subset, matches, pd.DataFrame())
        self.assertEqual(full["avg_values"], played_only["avg_values"])
        self.assertEqual(len(full["categories"]), 4)

    def test_cerchia_filter_applies_to_titles_and_recent_period(self):
        matches = pd.DataFrame([match(1), match(2, team_b="Ciro")])
        votes = pd.DataFrame([final(1, ["Beto"]), final(2, ["Ada"])])
        strict = logic.filter_internal_matches(matches, ["Ada", "Beto", "Dina"])
        stats = logic.calculate_player_fifa_stats("Ada", PLAYERS, strict, votes)
        self.assertEqual(stats["pg"], 1)
        self.assertEqual(stats["titoli_mvp"], 0)
        self.assertEqual(stats["ovr_details"]["recent"]["mvp_matches"], 1)
        titles = logic.calculate_player_vote_stats(strict, votes)
        self.assertEqual(titles.get("Ada", {}).get("titoli_mvp", 0), 0)

    def test_legacy_titles_remain_usable_without_numeric_votes_in_ovr(self):
        legacy = pd.DataFrame([{"id_partita": 1, "giocatore": "Ada", "voto": 8},
                               {"id_partita": 1, "giocatore": "Beto", "voto": 5}])
        stats = logic.calculate_player_fifa_stats("Ada", PLAYERS, pd.DataFrame([match()]), legacy)
        self.assertEqual(stats["titoli_mvp"], 1)
        self.assertEqual(stats["ovr"], 90)


if __name__ == "__main__":
    unittest.main()
