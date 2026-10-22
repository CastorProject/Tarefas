"""Falas de cadastro sem bloquear as leituras da câmera."""

import logging
import threading
import time

from piper_castor_tts import play_audio, prepare_registration_audio


PROCESSING_REMINDER_SECONDS = 8.0


class RegistrationVoice:
    def __init__(self):
        self.condition = threading.Condition()
        self.pending = None
        self.reminder_at = None
        self.stopped = False
        self.cancel_event = threading.Event()
        self.thread = threading.Thread(target=self.run, daemon=True)
        self.thread.start()

    def say(self, stage):
        with self.condition:
            if self.stopped:
                return
            # Só a instrução pendente mais recente continua na fila.
            self.pending = stage
            self.reminder_at = (
                time.monotonic() + PROCESSING_REMINDER_SECONDS
                if stage == "processamento" else None
            )
            self.condition.notify()

    def run(self):
        while True:
            with self.condition:
                while self.pending is None and not self.stopped:
                    if self.reminder_at is None:
                        self.condition.wait()
                    else:
                        remaining = self.reminder_at - time.monotonic()
                        if remaining > 0:
                            self.condition.wait(remaining)
                        else:
                            self.pending = "aguarde"
                            self.reminder_at = None
                if self.stopped:
                    return
                stage, self.pending = self.pending, None
            self.speak(stage, self.cancel_event)

    @staticmethod
    def speak(stage, cancel_event=None):
        try:
            if cancel_event is not None and cancel_event.is_set():
                return
            audio = prepare_registration_audio(stage)
            play_audio(audio, cancel_event=cancel_event)
        except Exception as error:
            # Falha no alto-falante não pode interromper o cadastro facial.
            logging.getLogger(__name__).warning("Erro na fala de cadastro %s: %s", stage, error)

    def close(self, terminal_stage=None):
        with self.condition:
            self.stopped = True
            self.pending = None
            self.reminder_at = None
            self.cancel_event.set()
            self.condition.notify()
        # Uma síntese que já começou pode terminar depois; o token impede a fala.
        self.thread.join(timeout=0.5)
        if terminal_stage:
            self.speak(terminal_stage)
