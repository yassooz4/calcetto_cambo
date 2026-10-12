import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

import ui_components


class OVRUITests(unittest.TestCase):
    def app(self):
        return AppTest.from_file(str(Path(__file__).with_name("ovr_fixture.py")), default_timeout=20)

    def test_card_breakdown_and_scope_switch(self):
        app = self.app().run()
        self.assertFalse(app.exception)
        self.assertTrue(any("45% gol" in caption.value for caption in app.caption))
        self.assertTrue(any("2 titoli in 3" in text.value for text in app.markdown))
        app.checkbox[0].check().run()
        self.assertFalse(app.exception)
        self.assertTrue(any("1 titoli in 2" in text.value for text in app.markdown))

    def test_unplayed_member_has_empty_radar_and_no_numeric_rating(self):
        app = self.app().run()
        app.selectbox[0].select("Dina").run()
        self.assertFalse(app.exception)
        self.assertTrue(any("Nessuna partita giocata" in item.value for item in app.info))
        self.assertTrue(any("Dati insufficienti" in item.value for item in app.info))

    def test_card_does_not_expose_old_elo_ovr_or_fabricated_attributes(self):
        stats = {"ovr": None, "pg": 0, "elo": 2000, "attributes": {}}
        with patch.object(ui_components, "render_html") as render:
            ui_components.render_fut_card("<Dina>", stats)
        html = render.call_args.args[0]
        self.assertIn("Non ancora valutato", html)
        self.assertIn("&lt;Dina&gt;", html)
        self.assertNotIn("ELO (Indice)", html)
        self.assertNotIn("AFF (Pres.)", html)
        self.assertNotIn("None", html)

    def test_pitch_displays_supplied_card_ratings_and_unrated_players(self):
        with patch.object(ui_components, "render_html") as render:
            ui_components.render_tactical_pitch(["Ada"], ["Dina"], {"Ada": 1900, "Dina": 1500},
                                                player_ovrs={"Ada": 68, "Dina": None})
        html = render.call_args.args[0]
        self.assertIn("68", html)
        self.assertIn("—", html)

    def test_actual_dashboard_and_cerchia_pages_render_new_cards(self):
        for page in ["dashboard", "cerchia"]:
            with self.subTest(page=page):
                app = self.app()
                app.session_state["full_page"] = page
                app.run()
                self.assertFalse(app.exception)
                self.assertTrue(any("OVR: 45% gol" in caption.value for caption in app.caption))


if __name__ == "__main__":
    unittest.main()
