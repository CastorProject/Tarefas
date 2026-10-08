"""Speak activity prompts with CASTOR's existing Piper voice and audio cache."""

import importlib.util
from pathlib import Path
from queue import Empty, Full, Queue
import threading
import subprocess


class Activity9Voice:
    def __init__(self, log_error):
        self.log_error = log_error
        self.queue = Queue(maxsize=1)
        self.lock = threading.Lock()
        self.generation = 0
        self.playback = None
        threading.Thread(target=self.run, daemon=True).start()

    def say(self, text):
        self.cancel()
        # Keep only the latest waiting prompt; repeated clicks cannot pile up audio.
        try:
            self.queue.put_nowait((self.generation, text))
        except Full:
            pass

    def cancel(self):
        with self.lock:
            self.generation += 1
            if self.playback is not None and self.playback.poll() is None:
                self.playback.terminate()
        try:
            self.queue.get_nowait()
        except Empty:
            pass

    def run(self):
        path = (Path(__file__).resolve().parents[2] / "huskylens_2" / "scripts"
                / "castor_aac" / "src" / "piper_castor_tts.py")
        piper = None
        while True:
            generation, prompt = self.queue.get()
            try:
                if piper is None:
                    spec = importlib.util.spec_from_file_location("activity9_piper", path)
                    loaded = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(loaded)
                    piper = loaded
                texts = prompt if isinstance(prompt, (tuple, list)) else (prompt,)
                for text in texts:
                    with self.lock:
                        if generation != self.generation:
                            break
                    audio = piper.prepare_audio(text)
                    with self.lock:
                        if generation != self.generation:
                            break
                        playback = subprocess.Popen(["aplay", "-q", audio])
                        self.playback = playback
                    status = playback.wait()
                    with self.lock:
                        if self.playback is playback:
                            self.playback = None
                        if generation != self.generation:
                            break
                    if status:
                        self.log_error("Erro ao falar na atividade 9: aplay terminou com código %s", status)
            except Exception as error:
                self.log_error("Erro ao falar na atividade 9: %s", error)
