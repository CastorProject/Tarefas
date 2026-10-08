"""Run with: python -m unittest discover -s catkin_ws/src/web_interface/tests"""

from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SRC = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(SRC / "web_interface" / "scripts"))
sys.path.insert(0, str(SRC / "huskylens_2" / "scripts" / "castor_aac" / "src"))

from flask import Flask
from activity9 import Activity9, INTRODUCTION, PERSON_TURN_PROMPT
from activity9_recognition import Activity9Recognition, normalize_emotion


class Clock:
    now = 0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += seconds


class GameTests(unittest.TestCase):
    def setUp(self):
        self.clock = Clock()
        self.commands, self.emotions, self.spoken = [], [], []
        self.activity = Activity9(self.commands.append, self.emotions.append,
                                 self.spoken.append, self.clock)
        self.app = Flask(__name__, template_folder=str(SRC / "web_interface" / "scripts" / "templates"),
                         static_folder=str(SRC / "web_interface" / "scripts" / "static"))
        self.app.config.update(TESTING=True, SECRET_KEY="test")
        self.app.register_blueprint(self.activity.blueprint)
        self.app.before_request(self.activity.navigation_cleanup)
        self.app.add_url_rule("/Activities", view_func=lambda: "Activities")
        self.client = self.app.test_client()

    def start(self, turn="person"):
        with patch("activity9.random.shuffle", lambda turns: None):
            self.client.post("/Activities/A9/iniciar")
        self.activity.game["turn"] = turn
        self.activity.game["turns"][0] = turn

    def post(self, path, token=None):
        return self.client.post("/Activities/A9/" + path,
                                data={"token": token or self.activity.game["token"]})

    def capture(self):
        self.post("observar")
        self.activity.receive_status({"token": self.activity.game["id"],
                                      "capture_token": self.activity.game["token"],
                                      "state": "detected", "emotion": "happy"})
        return self.client.get("/Activities/A9/status")

    def test_introduction_and_complete_balanced_game(self):
        page = self.client.get("/Activities/A9")
        self.assertIn(INTRODUCTION, page.get_data(as_text=True))
        self.assertEqual(self.spoken, [INTRODUCTION])
        self.start()
        self.assertEqual(self.activity.game["turns"].count("person"), 5)
        self.assertEqual(self.activity.game["turns"].count("castor"), 5)
        for number in range(1, 11):
            game = self.activity.game
            self.assertEqual(game["round"], number)
            if game["turn"] == "person":
                page = self.client.get("/Activities/A9/jogar").get_data(as_text=True)
                self.assertEqual(page.count('class="emoji-button'), 4)
                self.post("emocao/" + game["emotion"])
            else:
                self.assertEqual(self.capture().json["stage"], "guess")
                self.assertIn("Acertei?", self.client.get("/Activities/A9/jogar").get_data(as_text=True))
                self.post("confirmar/sim")
            if number < 10:
                self.assertTrue(all(command["mode"] == "emotion" for command in self.commands))
                self.post("proxima")
        self.assertEqual((game["score"], game["castor_score"]), (5, 5))
        self.assertEqual(game["stage"], "finished")
        self.assertEqual(self.commands[-1]["mode"], "face")
        self.assertIn("CONCLUÍDA", self.client.get("/Activities/A9/resultado").get_data(as_text=True))

    def test_duplicate_and_stale_submissions_do_not_score_or_skip_rounds(self):
        self.start()
        old_token = self.activity.game["token"]
        correct = self.activity.game["emotion"]
        self.post("emocao/" + correct)
        self.post("emocao/" + correct)
        self.assertEqual(self.activity.game["score"], 1)
        self.post("proxima")
        self.post("proxima", old_token)
        self.post("emocao/" + self.activity.game["emotion"], old_token)
        self.assertEqual(self.activity.game["round"], 2)
        self.assertEqual(self.activity.game["score"], 1)

    def test_castor_cannot_score_before_guess_and_no_does_not_score(self):
        self.start("castor")
        self.post("confirmar/sim")
        self.assertEqual(self.activity.game["stage"], "prepare")
        self.capture()
        self.post("confirmar/nao")
        self.assertEqual(self.activity.game["castor_score"], 0)
        self.assertEqual(self.activity.game["stage"], "answered")

    def test_old_camera_results_are_ignored_and_timeout_can_retry(self):
        self.start("castor")
        self.post("observar")
        self.activity.receive_status({"token": "old-round", "state": "detected", "emotion": "happy"})
        self.assertEqual(self.client.get("/Activities/A9/status").json["stage"], "capturing")
        self.clock.advance(41)
        self.assertEqual(self.client.get("/Activities/A9/status").json["stage"], "error")
        self.assertEqual(self.commands[-1]["mode"], "emotion")
        old_token = self.activity.game["token"]
        self.post("observar")
        self.assertNotEqual(self.activity.game["token"], old_token)
        self.assertEqual(self.activity.game["round"], 1)

    def test_stale_release_does_not_cancel_retry(self):
        self.start("castor")
        self.post("observar")
        old_token = self.activity.game["token"]
        self.post("liberar")
        self.post("observar")
        self.post("liberar", old_token)
        self.assertEqual(self.activity.game["stage"], "capturing")

    def test_navigation_exit_shutdown_and_idle_restore_camera(self):
        for exit_kind in ["navigation", "exit", "shutdown", "idle"]:
            with self.subTest(exit_kind=exit_kind):
                self.activity.game = None
                self.start("castor")
                self.post("observar")
                if exit_kind == "navigation":
                    self.client.get("/Activities", headers={"Accept": "text/html"})
                elif exit_kind == "exit":
                    self.post("sair")
                elif exit_kind == "shutdown":
                    self.activity.shutdown()
                else:
                    self.clock.advance(301)
                    self.client.get("/Activities/A9/status")
                self.assertEqual(self.commands[-1]["mode"], "face")

    def test_other_client_cannot_replace_or_stop_active_game(self):
        self.start("castor")
        self.post("observar")
        other = self.app.test_client()
        self.assertEqual(other.post("/Activities/A9/iniciar").status_code, 409)
        other.post("/Activities/A9/sair")
        self.assertEqual(self.activity.game["stage"], "capturing")

    def test_background_requests_and_favicon_do_not_end_game(self):
        self.start("castor")
        self.post("observar")
        self.client.get("/favicon.ico", headers={"Sec-Fetch-Dest": "image"})
        self.client.get("/face_registration/status", headers={"Accept": "application/json"})
        self.assertEqual(self.activity.game["stage"], "capturing")

    def test_person_prompt_once_per_round_and_heartbeat_on_every_screen(self):
        self.start()
        self.assertEqual(self.spoken, [PERSON_TURN_PROMPT])
        page = self.client.get("/Activities/A9/jogar").get_data(as_text=True)
        self.client.get("/Activities/A9/jogar")
        self.assertEqual(self.spoken, [PERSON_TURN_PROMPT])
        self.assertIn('data-stage="prepare"', page)
        self.client.get("/Activities/A9/status")
        game_id = self.activity.game["id"]
        self.assertEqual(self.commands[-1], {"mode": "emotion", "token": game_id, "capture_token": None})
        self.post("emocao/" + self.activity.game["emotion"])
        self.assertIn('data-stage="answered"', self.client.get("/Activities/A9/jogar").get_data(as_text=True))
        self.client.get("/Activities/A9/status")
        self.assertEqual(self.commands[-1]["mode"], "emotion")
        self.post("proxima")
        self.assertEqual(self.spoken, [PERSON_TURN_PROMPT, PERSON_TURN_PROMPT])
        self.assertTrue(all(command["token"] == game_id for command in self.commands))

    def test_previous_capture_from_same_game_cannot_answer_next_attempt(self):
        self.start("castor")
        self.post("observar")
        old_capture = self.activity.game["token"]
        self.post("liberar")
        self.post("observar")
        self.activity.receive_status({"token": self.activity.game["id"], "capture_token": old_capture,
                                      "state": "detected", "emotion": "happy"})
        self.assertEqual(self.client.get("/Activities/A9/status").json["stage"], "capturing")


class Camera:
    def __init__(self):
        self.calls = []
        self.name = "Happy"
        self.read_ok = True
        self.face_visible = True
        self.multi_ok = True
        self.ratio_ok = True
        self.restore_ok = True
        self.load_ok = True

    def setMultiAlgorithm(self, algorithms):
        self.calls.append(("multi", algorithms))
        return self.multi_ok

    def setMultiAlgorithmRatio(self, ratios):
        self.calls.append(("ratio", ratios))
        return self.ratio_ok

    def switchAlgorithm(self, algorithm):
        self.calls.append(("face", algorithm))
        return self.restore_ok

    def loadKnowledges(self, algorithm, knowledge_id):
        self.calls.append(("load", algorithm, knowledge_id))
        return self.load_ok

    def getResult(self, algorithm):
        return True if self.read_ok else None

    def available(self, algorithm):
        return self.face_visible

    def getCachedCenterResult(self, algorithm):
        return SimpleNamespace(name=self.name, ID=99)


class RecognitionTests(unittest.TestCase):
    def setUp(self):
        self.clock, self.camera, self.statuses = Clock(), Camera(), []
        self.manager = Activity9Recognition(self.camera, 1, 13, 1,
                                           self.statuses.append, self.clock, lambda seconds: None)

    def start(self):
        self.manager.request({"mode": "emotion", "token": "round-1", "capture_token": "capture-1"})
        self.assertTrue(self.manager.tick())

    def test_stable_expression_then_default_mode_with_saved_faces(self):
        self.start()
        self.clock.advance(1.1)
        self.manager.tick()
        self.assertEqual(self.statuses[-1]["emotion"], "happy")
        self.manager.request({"mode": "face", "token": "round-1"})
        self.assertFalse(self.manager.tick())
        self.assertEqual(self.camera.calls[-2:], [("face", 1), ("load", 1, 1)])
        self.assertFalse(self.manager.dirty)

    def test_lease_expiry_restores_without_browser_or_web_server(self):
        self.start()
        self.clock.advance(16)
        self.assertFalse(self.manager.tick())
        self.assertEqual(self.camera.calls[-1], ("load", 1, 1))

    def test_no_face_unsupported_name_and_failed_read_do_not_guess(self):
        self.start()
        self.clock.advance(1.1)
        self.camera.read_ok = False
        self.manager.tick()
        self.assertIsNone(self.manager.guess)
        self.camera.read_ok = True
        self.camera.name = "unknown-id-99"
        self.manager.tick()
        self.assertIsNone(self.manager.guess)
        self.camera.name = "Happy"
        self.camera.face_visible = False
        self.manager.tick()
        self.assertIsNone(self.manager.guess)

    def test_partial_activation_and_ratio_failure_both_restore(self):
        for failure in ["multi_ok", "ratio_ok"]:
            with self.subTest(failure=failure):
                self.setUp()
                setattr(self.camera, failure, False)
                self.manager.request({"mode": "emotion", "token": "round-1"})
                self.assertFalse(self.manager.tick())
                self.assertFalse(self.manager.dirty)
                self.assertEqual(self.camera.calls[-1], ("load", 1, 1))

    def test_restore_failure_is_retried(self):
        self.start()
        self.manager.request({"mode": "face", "token": "round-1"})
        self.camera.restore_ok = False
        with self.assertRaises(RuntimeError):
            self.manager.tick()
        self.assertTrue(self.manager.dirty)
        self.camera.restore_ok = True
        self.assertFalse(self.manager.tick())
        self.assertFalse(self.manager.dirty)

    def test_registration_blocks_activation_and_stale_stop_is_ignored(self):
        self.manager.request({"mode": "emotion", "token": "round-1"})
        self.assertFalse(self.manager.tick(registration_active=True))
        self.assertEqual(self.statuses[-1]["state"], "busy")
        self.assertEqual(self.camera.calls, [])
        self.start()
        self.manager.request({"mode": "face", "token": "old-round"})
        self.assertTrue(self.manager.tick())

    def test_reload_retry_does_not_restart_model_loading(self):
        self.start()
        self.manager.request({"mode": "face", "token": "round-1"})
        self.camera.load_ok = False
        with self.assertRaises(RuntimeError):
            self.manager.tick()
        self.camera.load_ok = True
        self.assertFalse(self.manager.tick())
        self.assertEqual(self.camera.calls.count(("face", 1)), 1)

    def test_cancellation_during_model_loading(self):
        self.manager.sleep = lambda seconds: self.manager.request({"mode": "face", "token": "round-1"})
        self.manager.request({"mode": "emotion", "token": "round-1"})
        self.assertFalse(self.manager.tick())
        self.assertFalse(self.manager.dirty)

    def test_names_are_normalized_without_inventing_id_mapping(self):
        self.assertEqual(normalize_emotion("SURPRESA"), "surprise")
        self.assertEqual(normalize_emotion(b"Happy"), "happy")
        self.assertIsNone(normalize_emotion("Fear"))

    def test_multi_stays_loaded_between_captures_and_guesses_reset(self):
        self.start()
        self.clock.advance(1.1)
        self.manager.tick()
        self.assertEqual(self.manager.guess, "happy")
        self.manager.request({"mode": "emotion", "token": "round-1", "capture_token": None})
        self.assertTrue(self.manager.tick())
        self.assertIsNone(self.manager.guess)
        self.assertEqual(self.statuses[-1]["state"], "idle")
        self.camera.name = "Sad"
        self.manager.request({"mode": "emotion", "token": "round-1", "capture_token": "capture-2"})
        self.manager.tick()
        self.clock.advance(1.1)
        self.manager.tick()
        self.assertEqual(self.statuses[-1]["emotion"], "sad")
        self.assertEqual(self.statuses[-1]["capture_token"], "capture-2")
        self.assertEqual(self.camera.calls, [("multi", [1, 13]), ("ratio", [1, 1])])
        self.manager.request({"mode": "face", "token": "round-1"})
        self.assertFalse(self.manager.tick())

    def test_standby_lease_is_renewed_but_restores_when_browser_stops(self):
        command = {"mode": "emotion", "token": "game-1", "capture_token": None}
        self.manager.request(command)
        self.assertTrue(self.manager.tick())
        for _ in range(3):
            self.clock.advance(10)
            self.manager.request(command)
            self.assertTrue(self.manager.tick())
        self.assertEqual(self.camera.calls, [("multi", [1, 13]), ("ratio", [1, 1])])
        self.clock.advance(16)
        self.assertFalse(self.manager.tick())
        self.assertEqual(self.statuses[-1]["state"], "face")


if __name__ == "__main__":
    unittest.main()
