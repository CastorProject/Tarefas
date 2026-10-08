"""Emotion game and token-scoped bridge to the camera's existing ROS node."""

from functools import wraps
import random
import threading
import time
from uuid import uuid4

from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for


EMOTIONS = {
    "happy": ("Feliz", "😊"), "sad": ("Triste", "😢"),
    "angry": ("Com raiva", "😠"), "surprise": ("Surpreso", "😮"),
}
INTRODUCTION = (
    "Olá, sou o robô CASTOR! Nesta atividade, vamos brincar de adivinhar emoções. "
    "A cada rodada, vamos sortear quem adivinha: às vezes você vai adivinhar a minha "
    "emoção, e às vezes eu vou adivinhar a sua! Quando for a minha vez, faça uma "
    "expressão e olhe para mim. Depois, me conte se eu acertei. Vamos brincar?"
)
PERSON_TURN_PROMPT = "Sua vez! Adivinhe qual é a minha emoção."
CASTOR_TURN_PHRASES = (
    "Agora é minha vez! Escolha uma emoção, faça a expressão e olhe para mim!",
    "Será que eu consigo descobrir? Escolha uma das emoções e mostre com seu rosto!",
    "Vamos trocar de papel! Faça uma expressão e eu vou tentar adivinhar!",
    "Minha vez de adivinhar! Olhe para mim e mostre a emoção que você escolheu!",
    "Prepare sua expressão! Quando estiver pronto, aperte o botão para eu adivinhar!",
    "Escolha alegria, tristeza, raiva ou surpresa. Mostre sua expressão e eu tento descobrir!",
    "Que emoção você vai escolher? Faça a expressão e deixe que eu tente adivinhar!",
    "Estou curioso! Escolha uma das emoções e mostre para mim!",
    "Vamos brincar com as expressões! Escolha uma emoção e olhe para mim!",
    "Agora o desafio é meu! Faça sua expressão e aperte o botão quando estiver pronto!",
)
SUCCESS_PHRASES = (
    "Muito bem! Você acertou!",
    "Parabéns! Você descobriu minha emoção!",
    "Isso mesmo! Uma estrela para você!",
    "Excelente! Você reconheceu minha expressão!",
    "Que legal! Você mandou muito bem!",
    "Boa! Vamos continuar brincando!",
)
ENCOURAGEMENT_PHRASES = (
    "Passou perto! Vamos tentar na próxima!",
    "Boa tentativa! Continue observando minhas expressões!",
    "Foi por pouco! Vamos continuar!",
    "Tudo bem! Cada rodada é uma nova chance!",
    "Não foi dessa vez, mas você está aprendendo!",
    "Continue tentando! Vamos descobrir mais emoções!",
)
RESULT_PHRASES = {
    "win": "Foi muito bom jogar com você! Você ganhou! Parabéns por reconhecer tantas emoções!",
    "draw": "Foi muito bom jogar com você! Nós empatamos! Parabéns, formamos uma ótima dupla!",
    "loss": "Foi muito bom jogar com você! Desta vez eu ganhei, mas você se esforçou muito! Parabéns pela participação!",
}


class Activity9:
    TOTAL = 10
    IDLE_SECONDS = 300
    CAPTURE_SECONDS = 40

    def __init__(self, send_camera, show_emotion, speak, clock=time.monotonic, silence=lambda: None):
        self.send_camera = send_camera
        self.show_emotion = show_emotion
        self.speak = speak
        self.silence = silence
        self.clock = clock
        self.lock = threading.RLock()
        self.game = None
        self.camera_status = {}
        self.camera_status_at = 0
        self.blueprint = Blueprint("a9", __name__)
        for path, handler, methods in [
            ("", self.explicar, ["GET"]), ("/iniciar", self.iniciar, ["POST"]),
            ("/jogar", self.jogar, ["GET"]), ("/emocao/<emocao>", self.responder, ["POST"]),
            ("/observar", self.observar, ["POST"]), ("/status", self.status, ["GET"]),
            ("/confirmar/<resposta>", self.confirmar, ["POST"]),
            ("/proxima", self.proxima, ["POST"]), ("/resultado", self.resultado, ["GET"]),
            ("/liberar", self.liberar, ["POST"]), ("/sair", self.sair, ["POST"]),
        ]:
            self.blueprint.add_url_rule("/Activities/A9" + path, handler.__name__,
                                        self.serialized(handler), methods=methods)

    def serialized(self, handler):
        @wraps(handler)
        def wrapped(**kwargs):
            with self.lock:
                return handler(**kwargs)
        return wrapped

    def receive_status(self, status):
        if not isinstance(status, dict):
            return
        with self.lock:
            self.camera_status = status
            self.camera_status_at = self.clock()

    def command(self, mode):
        if self.game:
            self.send_camera({"mode": mode, "token": self.game["id"],
                              "capture_token": self.game["token"] if self.game["stage"] == "capturing" else None})

    def keep_camera(self):
        self.command("face" if self.game["stage"] == "finished" else "emotion")

    def current(self):
        if self.game and self.clock() - self.game["seen"] > self.IDLE_SECONDS:
            self.command("face")
            self.show_emotion("neutral")
            self.game = None
        if self.game and session.get("a9_id") == self.game["id"]:
            self.game["seen"] = self.clock()
            return self.game
        return None

    def correct_round(self):
        return self.game and request.form.get("token") == self.game["token"]

    def to_game(self):
        return redirect(url_for("a9.jogar"))

    def begin_round(self):
        self.game.update(token=uuid4().hex, stage="prepare", feedback="", guess=None, correct=None,
                         emotion=random.choice(tuple(EMOTIONS)))
        turn = self.game["turns"][self.game["round"] - 1]
        self.game["turn"] = turn
        self.show_emotion(self.game["emotion"] if turn == "person" else "neutral")
        self.keep_camera()
        if turn == "person":
            self.speak(PERSON_TURN_PROMPT)
        else:
            self.speak(self.choose_castor_prompt())

    def choose_castor_prompt(self):
        counts = self.game["castor_phrase_counts"]
        choices = [phrase for phrase in CASTOR_TURN_PHRASES
                   if phrase != self.game["last_castor_phrase"] and counts.get(phrase, 0) < 2]
        phrase = random.choice(choices)
        counts[phrase] = counts.get(phrase, 0) + 1
        self.game["last_castor_phrase"] = phrase
        return phrase

    def explicar(self):
        game = self.current()
        if game and game["stage"] != "intro":
            return self.to_game()
        if not game:
            if self.game and self.game["stage"] != "finished":
                return "O CASTOR já está jogando. Encerre a atividade na outra tela antes de começar.", 409
            self.game = {"id": uuid4().hex, "token": uuid4().hex, "stage": "intro", "seen": self.clock()}
            session["a9_id"] = self.game["id"]
        self.keep_camera()
        self.speak(INTRODUCTION)
        return render_template("Act9_1_emocoes.html", title="Atividade 9 - Emoções",
                               explanation=INTRODUCTION, game=self.game)

    def iniciar(self):
        game = self.current()
        if game and game["stage"] != "intro":
            return self.to_game()
        if not game and self.game and self.game["stage"] != "finished":
            return "O CASTOR já está jogando. Encerre a atividade na outra tela antes de começar.", 409
        turns = ["person"] * 5 + ["castor"] * 5
        random.shuffle(turns)
        self.game = {"id": game["id"] if game else uuid4().hex, "token": uuid4().hex, "round": 1,
                     "score": 0, "castor_score": 0, "turns": turns,
                     "seen": self.clock(), "phrase_counts": {}, "last_phrase": None,
                     "castor_phrase_counts": {}, "last_castor_phrase": None}
        self.silence()
        session.pop("a9_game", None)  # Remove cookies from the previous game version.
        session["a9_id"] = self.game["id"]
        self.begin_round()
        return self.to_game()

    def jogar(self):
        game = self.current()
        if not game:
            return redirect(url_for("a9.explicar"))
        if game["stage"] == "intro":
            return redirect(url_for("a9.explicar"))
        if game["stage"] == "finished":
            return redirect(url_for("a9.resultado"))
        return render_template("Act9_2_emocoes.html", title="Jogo das Emoções",
                               game=game, emotions=EMOTIONS, total=self.TOTAL)

    def choose_feedback(self, correct):
        phrases = SUCCESS_PHRASES if correct else ENCOURAGEMENT_PHRASES
        counts = self.game["phrase_counts"]
        choices = [phrase for phrase in phrases
                   if phrase != self.game["last_phrase"] and counts.get(phrase, 0) < 2]
        phrase = random.choice(choices)
        counts[phrase] = counts.get(phrase, 0) + 1
        self.game["last_phrase"] = phrase
        return phrase

    def finish_answer(self, feedback, spoken=None):
        self.silence()
        self.game.update(stage="answered", feedback=feedback)
        self.show_emotion("neutral")
        if self.game["round"] == self.TOTAL:
            self.game["stage"] = "finished"
            score, castor_score = self.game["score"], self.game["castor_score"]
            outcome = "win" if score > castor_score else "loss" if score < castor_score else "draw"
            self.game.update(outcome=outcome, result_message=RESULT_PHRASES[outcome])
            # One voice job preserves the last round's feedback before the goodbye.
            self.speak((spoken, self.game["result_message"]) if spoken else self.game["result_message"])
        elif spoken:
            self.speak(spoken)
        self.keep_camera()

    def responder(self, emocao):
        if emocao not in EMOTIONS:
            return "Emoção inválida", 404
        game = self.current()
        if (game and self.correct_round() and game["turn"] == "person"
                and game["stage"] == "prepare"):
            correct = emocao == game["emotion"]
            game["score"] += int(correct)
            game["correct"] = correct
            phrase = self.choose_feedback(correct)
            self.finish_answer(phrase, spoken=phrase)
        return self.to_game()

    def observar(self):
        game = self.current()
        if (game and self.correct_round() and game["turn"] == "castor"
                and game["stage"] in {"prepare", "error"}):
            self.silence()
            game.update(token=uuid4().hex, stage="capturing", guess=None,
                        capture_started=self.clock(), feedback="Estou preparando a câmera...")
            self.command("emotion")
        return self.to_game()

    def status(self):
        game = self.current()
        if not game:
            return jsonify(stage="gone")
        if game["stage"] == "capturing":
            status = self.camera_status
            matching = status.get("token") == game["id"] and status.get("capture_token") == game["token"]
            fresh = self.clock() - self.camera_status_at < 3
            if matching and fresh and status.get("state") == "detected" and status.get("emotion") in EMOTIONS:
                game.update(stage="guess", guess=status["emotion"])
                self.speak("Acho que sua expressão é: {}. Acertei?".format(EMOTIONS[game["guess"]][0]))
            elif matching and fresh and status.get("state") in {"error", "busy", "face"}:
                game.update(stage="error", feedback="Não consegui observar sua expressão. Vamos tentar novamente?")
            elif self.clock() - game["capture_started"] >= self.CAPTURE_SECONDS:
                game.update(stage="error", feedback="Não consegui reconhecer uma expressão a tempo. Olhe para mim e tente de novo!")
            else:
                if matching and fresh:
                    game["feedback"] = status.get("message", "Olhe para mim!")
        self.keep_camera()  # Renew throughout the game, including the person's turns.
        return jsonify(stage=game["stage"], token=game["token"], message=game.get("feedback", ""))

    def confirmar(self, resposta):
        if resposta not in {"sim", "nao"}:
            return "Resposta inválida", 404
        game = self.current()
        if game and self.correct_round() and game["turn"] == "castor" and game["stage"] == "guess":
            game["castor_score"] += int(resposta == "sim")
            self.finish_answer("Eu acertei! Uma estrela para o CASTOR!" if resposta == "sim" else
                               "Obrigado por me contar! Vou tentar de novo na próxima vez.")
        return self.to_game()

    def proxima(self):
        game = self.current()
        if game and self.correct_round() and game["stage"] == "answered" and game["round"] < self.TOTAL:
            game["round"] += 1
            self.begin_round()
        return self.to_game()

    def resultado(self):
        game = self.current()
        if not game or game["stage"] != "finished":
            return self.to_game()
        self.command("face")
        return render_template("Act9_3_emocoes.html", title="Resultado - Jogo das Emoções",
                               game=game, chances=self.TOTAL // 2)

    def liberar(self):
        game = self.current()
        if game and self.correct_round() and game["stage"] == "capturing":
            game["stage"] = "prepare"
            self.keep_camera()
        return "", 204

    def sair(self):
        if self.current():
            self.silence()
            self.command("face")
            self.show_emotion("neutral")
            self.game = None
        session.pop("a9_id", None)
        session.pop("a9_game", None)
        return redirect("/Activities")

    def navigation_cleanup(self):
        if (request.method != "GET" or request.path.startswith("/static/")
                or request.path.startswith("/Activities/A9") or request.path == "/favicon.ico"):
            return
        destination = request.headers.get("Sec-Fetch-Dest")
        if destination != "document" and not (destination is None and "text/html" in request.headers.get("Accept", "")):
            return
        with self.lock:
            if self.current():
                self.silence()
                self.command("face")
                self.show_emotion("neutral")
                self.game = None
                session.pop("a9_id", None)

    def shutdown(self):
        with self.lock:
            self.silence()
            self.command("face")
