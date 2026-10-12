import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest


class UITests(unittest.TestCase):
    def app(self):
        return AppTest.from_file(str(Path(__file__).with_name("ui_fixture.py")), default_timeout=20)

    def test_voter_login_self_exclusion_private_tabs_and_submit(self):
        app = self.app().run()
        self.assertFalse(app.exception)
        self.assertEqual([tab.label for tab in app.tabs], ["🗳️ Il tuo voto", "🏆 Risultati"])
        self.assertEqual(len(app.dataframe), 0)
        app.text_input[0].set_value("00000")
        app.button[0].click().run()
        self.assertFalse(app.exception)
        self.assertIn("Ada", app.success[0].value)
        for select in app.selectbox[1:]:
            self.assertNotIn("Ada", select.options)
        app.selectbox[1].select("Beto")
        app.selectbox[2].select("Ciro")
        next(button for button in app.button if button.label == "Invia il tuo voto").click().run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.dataframe), 0)
        self.assertIn("Voto salvato", app.success[0].value)

    def test_admin_closure_and_public_result(self):
        app = self.app()
        app.session_state["fixture_admin"] = True
        app.run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.tabs), 3)
        self.assertTrue(next(button for button in app.button if button.label.startswith("Chiudi")).disabled)
        events = app.session_state["fixture_events"]
        events.append(dict(type="ballot", player_id="1", match_id="1", voter_name="Ada", mvp="Beto", worst="Ciro", time="test", version=1))
        app.run()
        self.assertFalse(app.exception)
        self.assertEqual(app.dataframe[0].value.iloc[0]["Votante"], "Ada")
        next(button for button in app.button if button.label.startswith("Chiudi")).click().run()
        self.assertFalse(app.exception)
        app.session_state["fixture_admin"] = False
        app.run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.tabs), 2)
        self.assertEqual(len(app.text_input), 0)
        for table in app.dataframe:
            self.assertNotIn("Votante", table.value.columns)
            self.assertNotIn("Password", table.value.columns)

    def test_password_screen_admin_only(self):
        app = self.app()
        app.session_state["fixture_page"] = "passwords"
        app.run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.dataframe), 0)
        self.assertIn("riservato", app.error[0].value)
        app.session_state["fixture_admin"] = True
        app.run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.dataframe[0].value), 10)
        self.assertEqual(app.dataframe[0].value.columns.tolist(), ["Giocatore", "Password"])


if __name__ == "__main__":
    unittest.main()
