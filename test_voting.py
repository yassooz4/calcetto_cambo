import os
import uuid
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace
from unittest.mock import patch

import pandas as pd
from cryptography.fernet import Fernet

import logic
import voting


PLAYERS = pd.DataFrame([{"id_giocatore": i + 1, "nome_completo": name}
                        for i, name in enumerate(["Ada", "Beto", "Ciro", "Dina", "Enzo", "Fede", "Gino", "Hana", "Ivo", "Luca"])])
MATCH = {"id_partita": 1, "data": "2026-10-12", "squadra_a_giocatori": "Ada, Beto, Ciro, Dina, Enzo",
         "squadra_b_giocatori": "Fede, Gino, Hana, Ivo, Luca", "gol_squadra_a": 5, "gol_squadra_b": 4}


class VotingTests(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.join(os.path.dirname(__file__), "test-scratch", uuid.uuid4().hex)
        os.makedirs(self.test_dir, exist_ok=True)
        self.key = Fernet.generate_key().decode()
        self.state = {"authenticated": True, "user_role": "admin"}
        self.stub = SimpleNamespace(secrets={"auth": {"admin_pin": "2345", "voting_key": self.key}},
                                    session_state=self.state, context=SimpleNamespace(ip_address="test-client"))
        runtime = (threading.RLock(), {})
        self.patches = [patch.object(voting, "st", self.stub),
                        patch.object(voting, "LOCAL_LOG", os.path.join(self.test_dir, "private.jsonl")),
                        patch.object(voting, "_runtime", lambda: runtime),
                        patch.object(voting, "_backend", lambda: None),
                        patch.object(voting.storage, "DATA_DIR", self.test_dir)]
        for item in self.patches:
            item.start()
        self.state["admin_signature"] = voting.admin_signature()
        self.codes = voting.ensure_codes(PLAYERS)

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()

    def identity(self, player_id=1):
        return voting.authenticate(self.codes[str(player_id)]["code"], PLAYERS)

    def test_passwords_persist_unique_and_encrypted(self):
        self.assertEqual(len({row["code"] for row in self.codes.values()}), 10)
        self.assertTrue(all(len(row["code"]) == 5 and row["code"].isascii() for row in self.codes.values()))
        self.assertEqual({key: row["code"] for key, row in self.codes.items()},
                         {key: row["code"] for key, row in voting.ensure_codes(PLAYERS).items()})
        with open(voting.LOCAL_LOG) as handle:
            token = handle.readline().strip()
        self.assertNotIn('"code"', token)
        self.assertNotIn('"player_id"', token)
        self.assertIn(b'"code"', Fernet(self.key.encode()).decrypt(token.encode()))
        with patch.object(voting.secrets, "randbelow", return_value=0):
            self.assertEqual(voting._unique_code(set()), "00000")

    def test_edit_replaces_vote_and_validates_choices(self):
        identity = self.identity()
        for mvp, worst in [("Ada", "Beto"), ("Beto", "Beto"), ("Ghost", "Ciro"), (None, "Ciro")]:
            with self.assertRaises(voting.VotingError):
                voting.submit_ballot(identity, PLAYERS, MATCH, mvp, worst)
        voting.submit_ballot(identity, PLAYERS, MATCH, "Beto", "Ciro")
        voting.submit_ballot(identity, PLAYERS, MATCH, "Dina", "Ciro")
        votes = voting.ballots(voting.load_events(), 1)
        self.assertEqual(len(votes), 1)
        self.assertEqual(votes[0]["mvp"], "Dina")

    def test_only_participants_can_vote(self):
        shortened = dict(MATCH, squadra_a_giocatori="Beto, Ciro")
        with self.assertRaises(voting.VotingError):
            voting.submit_ballot(self.identity(), PLAYERS, shortened, "Beto", "Ciro")

    def test_manual_close_ties_privacy_reopen_and_freeze(self):
        voting.submit_ballot(self.identity(1), PLAYERS, MATCH, "Ciro", "Dina")
        voting.submit_ballot(self.identity(2), PLAYERS, MATCH, "Dina", "Ciro")
        public = voting.public_results_frame(pd.DataFrame([MATCH]), pd.DataFrame())
        self.assertTrue(public.empty)
        result = voting.close_election(PLAYERS, MATCH)
        self.assertEqual(result["mvp_names"], ["Ciro", "Dina"])
        self.assertEqual(result["worst_names"], ["Ciro", "Dina"])
        with self.assertRaises(voting.VotingError):
            voting.submit_ballot(self.identity(), PLAYERS, MATCH, "Enzo", "Ciro")
        public = voting.public_results_frame(pd.DataFrame([MATCH]), pd.DataFrame())
        self.assertNotIn("player_id", public.columns)
        self.assertNotIn("code", public.columns)
        self.assertNotIn("voter_name", public.columns)
        stats = logic.calculate_player_vote_stats(pd.DataFrame([MATCH]), public)
        self.assertEqual(stats["Ciro"]["titoli_mvp"], 1)
        self.assertEqual(stats["Dina"]["titoli_mvp"], 1)
        self.assertEqual(stats["Ciro"]["titoli_peggiore"], 1)
        self.assertIsNone(logic.calculate_match_ratings(public, 1)["mvp"]["media"])
        voting.reopen_election(1)
        self.assertTrue(voting.public_results_frame(pd.DataFrame([MATCH]), pd.DataFrame()).empty)

    def test_admin_guards_and_rotated_sessions(self):
        old_identity = self.identity()
        old_code = self.codes["1"]["code"]
        voting.rotate_code(PLAYERS, 1)
        with self.assertRaises(voting.VotingError):
            voting.authenticate(old_code, PLAYERS)
        with self.assertRaises(voting.VotingError):
            voting.submit_ballot(old_identity, PLAYERS, MATCH, "Beto", "Ciro")
        self.state["user_role"] = "viewer"
        for action in [lambda: voting.ensure_codes(PLAYERS), lambda: voting.rotate_code(PLAYERS, 1),
                       lambda: voting.close_election(PLAYERS, MATCH), lambda: voting.reopen_election(1)]:
            with self.assertRaises(voting.VotingError):
                action()

    def test_server_attempt_limit_and_pin_config(self):
        for _ in range(5):
            with self.assertRaises(voting.VotingError):
                voting.authenticate("bad", PLAYERS)
        with self.assertRaisesRegex(voting.VotingError, "Troppi tentativi"):
            self.identity()
        self.stub.secrets["auth"]["admin_pin"] = "8765"
        self.assertIsNone(voting.admin_pin())
        self.assertFalse(voting.is_private_admin())

    def test_concurrent_voters_do_not_overwrite(self):
        identities = [self.identity(1), self.identity(2)]
        with ThreadPoolExecutor(max_workers=2) as executor:
            list(executor.map(lambda identity: voting.submit_ballot(identity, PLAYERS, MATCH, "Ciro", "Dina"), identities))
        self.assertEqual(len(voting.ballots(voting.load_events(), 1)), 2)

    def test_cloud_failure_has_no_local_fallback(self):
        class FakeWorksheet:
            def append_rows(self, rows, **kwargs):
                raise OSError("Cloud unavailable")
        sheet = SimpleNamespace(worksheet=lambda title: FakeWorksheet())
        old_size = os.path.getsize(voting.LOCAL_LOG)
        with self.assertRaises(voting.VotingError):
            voting._append(sheet, [{"type": "open", "match_id": "1"}])
        self.assertEqual(os.path.getsize(voting.LOCAL_LOG), old_size)

    def test_legacy_results_are_preserved_until_new_ballots(self):
        legacy = pd.DataFrame([{"id_partita": 1, "votante": "Ada", "giocatore": "Beto", "voto": 8.0},
                               {"id_partita": 1, "votante": "Beto", "giocatore": "Ciro", "voto": 5.0}])
        result = voting.public_results_frame(pd.DataFrame([MATCH]), legacy)
        self.assertEqual(result.iloc[0]["mvp_names"], ["Beto"])
        voting.submit_ballot(self.identity(), PLAYERS, MATCH, "Dina", "Ciro")
        self.assertTrue(voting.public_results_frame(pd.DataFrame([MATCH]), legacy).empty)


if __name__ == "__main__":
    unittest.main()
