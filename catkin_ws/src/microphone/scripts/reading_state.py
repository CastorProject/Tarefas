# -*- coding: utf-8 -*-
"""Estado da leitura separado do ROS/Flask para permitir testes locais."""
import threading
import uuid
import time


class ReadingState:
    def __init__(self, clock=time.monotonic):
        self.lock = threading.RLock()
        self.clock = clock
        self.session = ""
        self.page = 0
        self.segments = []
        self.partial = ""
        self.final = False
        self.final_at = None
        self.restart_on_speech = False

    def start(self, page):
        with self.lock:
            self.session = uuid.uuid4().hex
            self.page = page
            self.segments = []
            self.partial = ""
            self.final = False
            self.final_at = None
            self.restart_on_speech = False
            return self.session

    def update(self, event):
        with self.lock:
            if event.get("session") != self.session or not self.session:
                return
            text = event.get("text")
            if not isinstance(text, str) or not isinstance(event.get("final"), bool):
                return
            text = text.strip()
            if event["final"] and not text:
                return
            if text and self.restart_on_speech:
                self.segments = []
                self.restart_on_speech = False
            self.final = event["final"]
            if self.final:
                if text:
                    self.segments.append(text)
                self.final_at = self.clock()
                self.partial = ""
            else:
                # Parcial é uma hipótese revisável, nunca um novo trecho final.
                self.partial = text
                self.final_at = None

    def finish_failed_attempt(self, session, heard):
        with self.lock:
            if (session == self.session and heard == " ".join(self.segments)
                    and self.final and self.final_at is not None
                    and self.clock() - self.final_at >= 0.35):
                self.restart_on_speech = True

    def snapshot(self):
        with self.lock:
            # A tela recebe somente trechos confirmados, nunca hipóteses parciais.
            heard = " ".join(self.segments)
            # Curta confirmação após o resultado final. Uma nova parcial cancela.
            ready = (self.final and self.final_at is not None
                     and self.clock() - self.final_at >= 0.35)
            return self.session, self.page, heard, ready
