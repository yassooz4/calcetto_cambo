import json
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

import rating_ui
import ui_components


class OVRUITests(unittest.TestCase):
    def app(self):
        return AppTest.from_file(str(Path(__file__).with_name("ovr_fixture.py")), default_timeout=30)

    def test_card_breakdown_and_scope_switch(self):
        app = self.app().run()
        self.assertFalse(app.exception)
        self.assertTrue(any("2 MVP su 3 partite votate" in text.value for text in app.markdown))
        self.assertTrue(any("moltiplicati per 1,5" in text.value for text in app.markdown))
        app.checkbox[0].check().run()
        self.assertFalse(app.exception)
        self.assertTrue(any("1 MVP su 2 partite votate" in text.value for text in app.markdown))

    def test_unplayed_member_has_no_numeric_rating_or_plots(self):
        app = self.app().run()
        app.selectbox[0].select("Dina").run()
        self.assertFalse(app.exception)
        self.assertTrue(any("Nessuna partita giocata" in item.value for item in app.info))
        self.assertTrue(any("Dati insufficienti" in item.value for item in app.info))
        self.assertEqual(len(app.get("plotly_chart")), 0)

    def test_card_escapes_names_and_shows_actual_stats_without_duplicate_weights(self):
        stats = {"ovr": 76, "pg": 7, "gol_totali": 12, "media_gol": 1.71, "win_rate": 71.4,
                 "mvp_partite": 3, "titoli_mvp": 2, "attributes": {"GOL": 78, "RIS": 81, "MVP": 62}, "ovr_delta": 1}
        with patch.object(rating_ui, "render_html") as render:
            rating_ui.render_card("<Ada>", stats, True)
        html = render.call_args.args[0]
        self.assertIn("&lt;Ada&gt;", html)
        self.assertIn("1,71 gol / partita", html)
        self.assertIn("71,4% vittorie", html)
        self.assertIn("2 MVP su 3 partite votate", html)
        self.assertNotIn("FRM", html)
        self.assertNotIn("45%", html)
        self.assertNotIn("None", html)

    def test_comparison_has_three_bars_and_history_matches_current_ovr(self):
        app = self.app().run()
        self.assertFalse(app.exception)
        plots = app.get("plotly_chart")
        self.assertEqual(len(plots), 2)
        comparison = json.loads(plots[0].proto.spec)
        history = json.loads(plots[1].proto.spec)
        self.assertEqual(comparison["data"][0]["type"], "bar")
        self.assertEqual(comparison["data"][0]["y"], ["Gol", "Risultati", "MVP"])
        self.assertEqual(history["data"][0]["type"], "scatter")
        self.assertEqual(len(history["data"][0]["y"]), 8)
        self.assertTrue(any("oggi pubblicati" in item.value for item in app.caption))

    def test_pitch_displays_the_same_supplied_card_rating(self):
        with patch.object(ui_components, "render_html") as render:
            ui_components.render_tactical_pitch(["Ada"], ["Dina"], {"Ada": 1900, "Dina": 1500},
                                                player_ovrs={"Ada": 68, "Dina": None})
        html = render.call_args.args[0]
        self.assertIn("68", html)
        self.assertIn("—", html)

    def test_actual_dashboard_and_cerchia_render_new_sheet(self):
        for page in ["dashboard", "cerchia"]:
            with self.subTest(page=page):
                app = self.app()
                app.session_state["full_page"] = page
                app.run()
                self.assertFalse(app.exception)
                self.assertTrue(any("Stima prudente" in item.value for item in app.caption))
                self.assertTrue(any("Andamento OVR" in item.value for item in app.markdown))


if __name__ == "__main__":
    unittest.main()
