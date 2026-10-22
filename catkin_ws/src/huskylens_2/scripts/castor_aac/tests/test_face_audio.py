"""Regression tests using fake hardware, synthesis and playback."""

from datetime import datetime
import importlib
import json
from pathlib import Path
import sys
import tempfile
import threading
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch
import wave


PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE / "src"))
import piper_castor_tts as audio
import registration_voice

hardware = ModuleType("dfrobot_huskylensv2")
hardware.ALGORITHM_FACE_RECOGNITION = 1
hardware.ALGORITHM_EMOTION_RECOGNITION = 2
hardware.HuskylensV2_I2C = Mock()
with patch.dict(sys.modules, {"dfrobot_huskylensv2": hardware}):
    registration = importlib.import_module("face_registration")


def fake_wav(text, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(22050)
        output.writeframes(b"\0\0" * 100)


class AudioTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.patchers = [
            patch.object(audio, "AUDIO_DIR", self.root / "audios"),
            patch.object(audio, "GREETING_DIR", self.root / "audios" / "saudacoes"),
            patch.object(audio, "REGISTRATION_DIR", self.root / "audios" / "cadastro_facial"),
            patch.object(audio, "CACHE_DIR", self.root / "cache"),
        ]
        for patcher in self.patchers:
            patcher.start()
            self.addCleanup(patcher.stop)
        self.generate = self.enterContext(patch.object(audio, "generate_audio", side_effect=fake_wav))
        self.play = self.enterContext(patch.object(audio, "play_audio", return_value=True))
        self.clock = self.enterContext(patch.object(audio, "datetime"))
        self.clock.now.return_value = datetime(2026, 10, 22, 9, 0)

    # TestCase.enterContext was added after the Raspberry's Python 3.7.
    def enterContext(self, context):
        value = context.__enter__()
        self.addCleanup(context.__exit__, None, None, None)
        return value

    def manifest(self, name="João", face_id=1):
        folder = audio.person_audio_dir(name, face_id)
        return json.loads((folder / "manifest.json").read_text(encoding="utf-8"))

    def test_prepare_all_eight_in_readable_folder_and_reuse(self):
        paths = audio.prepare_greetings("João da Silva", 12)
        self.assertEqual(len(paths), 8)
        self.assertTrue(all(Path(path).parent.name == "0012_joao_da_silva" for path in paths.values()))
        self.assertEqual(self.generate.call_count, 8)
        self.play.assert_not_called()
        self.assertIn("João da Silva", self.manifest("João da Silva", 12)["audios"]["03_felicidade_encontrar_voce"]["text"])
        audio.prepare_greetings("João da Silva", 12)
        self.assertEqual(self.generate.call_count, 8)

    def test_same_name_different_ids_and_unsafe_characters(self):
        first = audio.person_audio_dir("Ana", 1)
        second = audio.person_audio_dir("Ana", 2)
        self.assertNotEqual(first, second)
        folder = audio.person_audio_dir("../../João / : Silva", 3)
        self.assertEqual(folder.name, "0003_joao_silva")
        self.assertEqual(folder.parent, audio.GREETING_DIR)
        with self.assertRaises(ValueError):
            audio.person_audio_dir("Ana", 0)

    def test_first_recognition_prepares_all_eight_before_speaking(self):
        self.play.side_effect = lambda *args: self.assertEqual(self.generate.call_count, 8) or True
        audio.speak_greeting("João", 1)
        self.assertEqual(self.generate.call_count, 8)
        self.assertEqual(len(list(audio.person_audio_dir("João", 1).glob("*.wav"))), 8)

    def test_renaming_person_reuses_id_and_invalidates_text(self):
        audio.prepare_greetings("João", 1)
        audio.speak_greeting("João", 1)
        last = self.manifest()["last_greeting"]
        audio.prepare_greetings("João Silva", 1)
        self.assertFalse((audio.GREETING_DIR / "0001_joao").exists())
        self.assertEqual(self.manifest("João Silva")["last_greeting"], last)
        self.assertEqual(self.generate.call_count, 16)

    def test_changing_voice_regenerates_all_eight(self):
        audio.prepare_greetings("João", 1)
        with patch.object(audio, "VOICE_VERSION", "new-voice"):
            audio.prepare_greetings("João", 1)
        self.assertEqual(self.generate.call_count, 16)

    def test_partial_generation_is_resumable(self):
        calls = []

        def fail_once(text, path):
            calls.append(path)
            if len(calls) == 3:
                raise RuntimeError("Piper unavailable")
            fake_wav(text, path)

        self.generate.side_effect = fail_once
        with self.assertRaises(RuntimeError):
            audio.prepare_greetings("João", 1)
        self.generate.side_effect = fake_wav
        audio.prepare_greetings("João", 1)
        self.assertEqual(self.generate.call_count, 9)  # 2 saved + 1 failed + 6 remaining

    def test_no_repeats_within_cycle_or_across_cycles(self):
        chosen = [Path(audio.speak_greeting("João", 1)).stem for _ in range(18)]
        for start in (0, 6, 12):
            self.assertEqual(len(set(chosen[start:start + 6])), 6)
        self.assertTrue(all(left != right for left, right in zip(chosen, chosen[1:])))
        self.assertTrue(all(item not in {"06_boa_tarde", "07_boa_noite"} for item in chosen))
        self.assertEqual(self.manifest()["last_greeting"], chosen[-1])

    def test_time_boundaries(self):
        for hour, expected in ((0, "07_boa_noite"), (4, "07_boa_noite"), (5, "05_bom_dia"),
                               (11, "05_bom_dia"), (12, "06_boa_tarde"), (17, "06_boa_tarde"),
                               (18, "07_boa_noite"), (23, "07_boa_noite")):
            with self.subTest(hour=hour):
                choices = audio.eligible_greetings(hour)
                self.assertEqual(len(choices), 6)
                self.assertEqual(set(choices) & {"05_bom_dia", "06_boa_tarde", "07_boa_noite"}, {expected})

    def test_restart_and_period_change_respect_saved_last_greeting(self):
        audio.speak_greeting("João", 1)
        saved = self.manifest()
        # Force a cycle boundary as if the process had restarted.
        saved["remaining_greetings"] = []
        audio._write_manifest(audio.person_audio_dir("João", 1), saved)
        next_stem = Path(audio.speak_greeting("João", 1)).stem
        self.assertNotEqual(next_stem, saved["last_greeting"])
        self.clock.now.return_value = datetime(2026, 10, 22, 20, 0)
        for _ in range(8):
            stem = Path(audio.speak_greeting("João", 1)).stem
            self.assertNotIn(stem, {"05_bom_dia", "06_boa_tarde"})

    def test_playback_failure_does_not_consume_greeting(self):
        audio.speak_greeting("João", 1)
        before = self.manifest()
        self.play.side_effect = OSError("speaker unavailable")
        with self.assertRaises(OSError):
            audio.speak_greeting("João", 1)
        after = self.manifest()
        self.assertEqual(after["last_greeting"], before["last_greeting"])
        self.assertEqual(after["remaining_greetings"], before["remaining_greetings"])

    def test_existing_mp3_has_priority_without_synthesis(self):
        audio.REGISTRATION_DIR.mkdir(parents=True)
        mp3 = audio.REGISTRATION_DIR / "01_inicio.mp3"
        mp3.write_bytes(b"ID3" + b"\0" * 100)
        self.assertEqual(audio.prepare_registration_audio("inicio"), str(mp3))
        self.generate.assert_not_called()

    def test_missing_mp3_generates_named_wav_once(self):
        path = audio.prepare_registration_audio("inicio")
        self.assertEqual(Path(path).name, "01_inicio.wav")
        audio.prepare_registration_audio("inicio")
        self.generate.assert_called_once()

    def test_mp3_commands_and_missing_dependency(self):
        with patch.object(audio.shutil, "which", side_effect=lambda binary: binary if binary == "mpg123" else None):
            self.assertEqual(audio.playback_command("inicio.mp3")[:2], ["mpg123", "-q"])
        with patch.object(audio.shutil, "which", side_effect=lambda binary: binary if binary == "ffplay" else None):
            self.assertEqual(audio.playback_command("inicio.mp3")[0], "ffplay")
        with patch.object(audio.shutil, "which", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "sudo apt install mpg123"):
                audio.playback_command("inicio.mp3")
        self.assertEqual(audio.playback_command("inicio.wav")[0], "aplay")

    def test_docker_output_preserves_nested_directory(self):
        self.generate.side_effect = None
        original_generate = type(self).original_generate
        target = audio.GREETING_DIR / "0001_joao" / "01_que_bom_ver_voce.wav"
        commands = []

        def synthesize(command, **kwargs):
            commands.append(command)
            container_file = command[command.index("--output_file") + 1]
            self.assertTrue(container_file.startswith("/audios/saudacoes/0001_joao/"))
            fake_wav(kwargs["input"], audio.AUDIO_DIR / container_file[len("/audios/"):])

        with patch.object(audio.os, "getuid", return_value=1000, create=True), \
             patch.object(audio.os, "getgid", return_value=1000, create=True), \
             patch.object(audio.subprocess, "run", side_effect=synthesize):
            original_generate("Olá!", target)
        self.assertTrue(audio.is_valid_audio(target))
        self.assertEqual(len(commands), 1)
        self.assertFalse(list(target.parent.glob("*.tmp.wav")))

    def test_generic_cache_still_works(self):
        first = audio.prepare_audio("Fala de outra atividade")
        self.assertEqual(audio.prepare_audio("Fala de outra atividade"), first)
        self.assertEqual(Path(first).parent, audio.CACHE_DIR)
        self.generate.assert_called_once()


AudioTests.original_generate = staticmethod(audio.generate_audio)


class RecognitionCooldownTests(unittest.TestCase):
    def setUp(self):
        ros = ModuleType("rospy")
        ros.loginfo = Mock()
        ros.logerr = Mock()
        messages = ModuleType("std_msgs.msg")
        messages.String = Mock()
        with patch.dict(sys.modules, {"rospy": ros, "std_msgs.msg": messages,
                                     "dfrobot_huskylensv2": hardware}):
            self.recognition = importlib.import_module("face_recognition")
        self.now = 1000.0
        clock = patch.object(self.recognition.time, "monotonic", side_effect=lambda: self.now)
        clock.start()
        self.addCleanup(clock.stop)
        speech = patch.object(self.recognition, "speak_greeting")
        self.speak = speech.start()
        self.addCleanup(speech.stop)
        self.history = {}

    def see(self, face_id=1, last_face_id=None):
        return self.recognition.recognize_face(
            SimpleNamespace(ID=face_id, name="Pessoa {}".format(face_id)),
            last_face_id, self.history,
        )

    def test_ten_minutes_boundary_and_independent_person(self):
        self.assertEqual(self.recognition.GREETING_COOLDOWN_SECONDS, 600)
        self.see()
        self.now += 599.999
        self.see()
        self.assertEqual(self.speak.call_count, 1)
        self.see(face_id=2)
        self.assertEqual(self.speak.call_count, 2)
        self.now = 1600.0
        self.see()
        self.assertEqual(self.speak.call_count, 3)

    def test_continuous_face_does_not_repeat_after_cooldown(self):
        face_id = self.see()
        self.now += 601
        self.see(last_face_id=face_id)
        self.assertEqual(self.speak.call_count, 1)

    def test_failed_playback_does_not_start_cooldown(self):
        self.speak.side_effect = OSError("speaker unavailable")
        self.see()
        self.assertEqual(self.history, {})


class RegistrationTests(unittest.TestCase):
    def setUp(self):
        self.states = []
        self.voice = Mock()
        self.manager = registration.FaceRegistrationManager(lambda **status: self.states.append(status),
                                                              voice_factory=lambda: self.voice)
        self.now = 0
        clock = patch.object(registration.time, "monotonic", side_effect=lambda: self.now)
        clock.start()
        self.addCleanup(clock.stop)
        self.husky = Mock()
        self.husky.learn.return_value = 12
        self.husky.setNameByID.return_value = True
        self.husky.saveKnowledges.return_value = True
        self.result = SimpleNamespace(ID=0, name="")
        self.prepare = patch.object(registration, "prepare_greetings", return_value={str(i): "audio.wav" for i in range(8)})
        self.generate = self.prepare.start()
        self.addCleanup(self.prepare.stop)

    def capture(self):
        self.assertTrue(self.manager.request("João"))
        self.manager.update(self.husky, self.result)
        self.now = 3.1

    def test_complete_registration_speaks_only_after_save(self):
        self.capture()
        self.husky.saveKnowledges.side_effect = lambda *args: self.assertFalse(self.voice.close.called) or True
        self.assertTrue(self.manager.update(self.husky, self.result))
        self.generate.assert_called_once_with("João", 12)
        self.voice.close.assert_called_once_with("concluido")
        self.assertFalse(self.manager.active)
        self.assertEqual(self.states[-1]["state"], "registered")
        self.assertEqual([call[0][0] for call in self.voice.say.call_args_list], ["inicio", "captura", "processamento"])

    def test_failed_save_does_not_announce_success_or_generate(self):
        self.capture()
        self.husky.saveKnowledges.return_value = False
        self.manager.update(self.husky, self.result)
        self.generate.assert_not_called()
        self.voice.close.assert_called_once_with(None)
        self.assertEqual(self.states[-1]["state"], "error")
        self.assertFalse(self.manager.active)

    def test_failed_name_does_not_save_or_generate(self):
        self.capture()
        self.husky.setNameByID.return_value = False
        self.manager.update(self.husky, self.result)
        self.husky.saveKnowledges.assert_not_called()
        self.generate.assert_not_called()
        self.assertEqual(self.states[-1]["state"], "error")

    def test_audio_failure_preserves_registration(self):
        self.capture()
        self.generate.side_effect = RuntimeError("Piper unavailable")
        self.manager.update(self.husky, self.result)
        self.assertEqual(self.states[-1]["state"], "registered_audio_error")
        self.voice.close.assert_called_once_with("concluido")
        self.assertFalse(self.manager.active)

    def test_lost_face_restarts_stable_capture(self):
        self.capture()
        self.manager.update(self.husky, None)
        self.voice.say.assert_called_with("nova_tentativa")
        self.manager.update(self.husky, self.result)
        self.now = 4
        self.assertFalse(self.manager.update(self.husky, self.result))
        self.husky.learn.assert_not_called()

    def test_existing_face_timeout_invalid_request_and_busy(self):
        self.assertFalse(self.manager.request(" "))
        self.voice.say.assert_not_called()
        self.capture()
        self.assertFalse(self.manager.request("Ana"))
        self.now = 61
        self.manager.update(self.husky, None)
        self.assertEqual(self.states[-1]["state"], "timeout")
        self.husky.learn.assert_not_called()
        self.voice.close.assert_called_once_with(None)

    def test_existing_face_does_not_learn_again(self):
        self.result = SimpleNamespace(ID=2, name="Ana")
        self.capture()
        self.manager.update(self.husky, self.result)
        self.assertEqual(self.states[-1]["state"], "already_registered")
        self.husky.learn.assert_not_called()
        self.generate.assert_not_called()
        self.voice.close.assert_called_once_with(None)

    def test_failed_learning_requests_retry(self):
        self.capture()
        self.husky.learn.return_value = 0
        self.manager.update(self.husky, self.result)
        self.voice.close.assert_called_once_with("nova_tentativa")
        self.generate.assert_not_called()


class VoiceTests(unittest.TestCase):
    def test_processing_reminder_once_and_terminal_cancels_worker(self):
        spoken = []
        reminder = threading.Event()

        def play(path, cancel_event=None):
            spoken.append(path)
            if path == "aguarde":
                reminder.set()
            return True

        with patch.object(registration_voice, "PROCESSING_REMINDER_SECONDS", 0.02), \
             patch.object(registration_voice, "prepare_registration_audio", side_effect=lambda stage: stage), \
             patch.object(registration_voice, "play_audio", side_effect=play):
            voice = registration_voice.RegistrationVoice()
            try:
                voice.say("processamento")
                self.assertTrue(reminder.wait(2))
                voice.close("concluido")
                self.assertEqual(spoken, ["processamento", "aguarde", "concluido"])
                self.assertFalse(voice.thread.is_alive())
            finally:
                voice.close()

    def test_completion_discards_waiting_instruction_and_interrupts_audio(self):
        started = threading.Event()
        cancelled = threading.Event()
        spoken = []

        def play(path, cancel_event=None):
            spoken.append(path)
            if path == "inicio":
                started.set()
                if cancel_event.wait(2):
                    cancelled.set()
            return True

        with patch.object(registration_voice, "prepare_registration_audio", side_effect=lambda stage: stage), \
             patch.object(registration_voice, "play_audio", side_effect=play):
            voice = registration_voice.RegistrationVoice()
            try:
                voice.say("inicio")
                self.assertTrue(started.wait(2))
                voice.say("captura")
                voice.say("processamento")
                voice.close("concluido")
                self.assertTrue(cancelled.is_set())
                self.assertEqual(spoken, ["inicio", "concluido"])
            finally:
                voice.close()


if __name__ == "__main__":
    unittest.main()
