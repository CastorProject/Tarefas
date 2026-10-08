"""Temporary emotion mode, operated only by the face node's I2C loop."""

import threading
import time
import unicodedata


def normalize_emotion(name):
    if isinstance(name, bytes):
        name = name.decode("utf-8", errors="replace")
    name = "".join(c for c in unicodedata.normalize("NFD", str(name).casefold())
                   if unicodedata.category(c) != "Mn").strip()
    return {
        "happy": "happy", "happiness": "happy", "feliz": "happy", "alegria": "happy",
        "sad": "sad", "sadness": "sad", "triste": "sad", "tristeza": "sad",
        "angry": "angry", "anger": "angry", "raiva": "angry",
        "surprise": "surprise", "surprised": "surprise", "surpresa": "surprise",
        "surpreso": "surprise",
    }.get(name)


class Activity9Recognition:
    LEASE_SECONDS = 15
    STABLE_SECONDS = 1

    def __init__(self, camera, face_algorithm, emotion_algorithm, knowledge_id,
                 publish, clock=time.monotonic, sleep=time.sleep):
        self.camera = camera
        self.face = face_algorithm
        self.emotion = emotion_algorithm
        self.knowledge_id = knowledge_id
        self.publish = publish
        self.clock = clock
        self.sleep = sleep
        self.lock = threading.Lock()
        self.request_token = None
        self.request_capture = None
        self.deadline = 0
        self.token = None
        self.capture_token = None
        self.dirty = False
        self.multi_ready = False
        self.face_selected = False
        self.candidate = None
        self.candidate_since = 0
        self.guess = None

    def request(self, command):
        """ROS callbacks never touch the camera."""
        token = command.get("token")
        if not isinstance(token, str) or not token or len(token) > 100:
            return
        with self.lock:
            if command.get("mode") == "emotion":
                capture = command.get("capture_token")
                if capture is not None and (not isinstance(capture, str) or not capture or len(capture) > 100):
                    return
                self.request_token = token
                self.request_capture = capture
                self.deadline = self.clock() + self.LEASE_SECONDS
            elif command.get("mode") == "face" and token == self.request_token:
                self.request_token = None

    def status(self, state, message, emotion=None):
        self.publish({"token": self.token, "state": state,
                      "capture_token": self.capture_token, "message": message, "emotion": emotion})

    def restore(self):
        """Keep dirty=True on failure so the next loop retries restoration."""
        if not self.dirty:
            return
        if not self.face_selected:
            if not self.camera.switchAlgorithm(self.face):
                raise RuntimeError("Não foi possível restaurar o reconhecimento facial.")
            self.face_selected = True
            # Loading a model after multi-algorithm mode takes several seconds.
            self.sleep(10)
        if not self.camera.loadKnowledges(self.face, self.knowledge_id):
            raise RuntimeError("Não foi possível recarregar os rostos cadastrados.")
        self.sleep(0.5)
        self.dirty = False
        self.multi_ready = False
        self.face_selected = False
        self.status("face", "Reconhecimento facial padrão restaurado.")
        self.token = None
        self.capture_token = None
        self.candidate = self.guess = None

    def tick(self, registration_active=False):
        with self.lock:
            if self.clock() >= self.deadline:
                self.request_token = None
            requested = self.request_token
            capture = self.request_capture

        if requested is None:
            self.restore()
            return False

        if not self.multi_ready:
            self.restore()  # Finish any failed restoration before reusing the camera.
            self.token = requested
            self.capture_token = capture
            if registration_active:
                self.status("busy", "Aguarde o cadastro facial terminar.")
                self.token = None
                return False
            self.status("starting", "Estou preparando a câmera...")
            self.dirty = True  # Even partial activation must be undone.
            self.face_selected = False
            try:
                if not self.camera.setMultiAlgorithm([self.face, self.emotion]):
                    raise RuntimeError("A câmera não confirmou o modo de emoções.")
                self.sleep(5)
                if not self.camera.setMultiAlgorithmRatio([1, 1]):
                    raise RuntimeError("A câmera não confirmou os dois modelos.")
                self.multi_ready = True
            except Exception as error:
                self.status("error", str(error))
                with self.lock:
                    if self.request_token == requested:
                        self.request_token = None
                self.restore()
                return False

        # A stop received during model loading takes effect before any reading.
        with self.lock:
            cancelled = self.request_token is None or self.clock() >= self.deadline
            requested, capture = self.request_token, self.request_capture
        if cancelled:
            self.restore()
            return False
        if requested != self.token or capture != self.capture_token:
            self.token, self.capture_token = requested, capture
            self.candidate = self.guess = None
        if self.capture_token is None:
            self.status("idle", "Câmera pronta para a próxima expressão.")
            return True
        if self.guess:
            self.status("detected", "Já escolhi meu palpite!", self.guess)
            return True

        try:
            face_read = self.camera.getResult(self.face)
            emotion_read = self.camera.getResult(self.emotion)
            result = None
            if (face_read is not None and emotion_read is not None
                    and self.camera.available(self.face) and self.camera.available(self.emotion)):
                result = self.camera.getCachedCenterResult(self.emotion)
            emotion = normalize_emotion(getattr(result, "name", ""))
            if emotion is None:
                self.candidate = None
                self.status("waiting", "Olhe para mim e faça uma expressão de alegria, tristeza, raiva ou surpresa.")
            elif emotion != self.candidate:
                self.candidate = emotion
                self.candidate_since = self.clock()
                self.status("waiting", "Segure essa expressão por um instante!")
            elif self.clock() - self.candidate_since >= self.STABLE_SECONDS:
                self.guess = emotion
                self.status("detected", "Já escolhi meu palpite!", emotion)
        except Exception as error:
            self.candidate = None
            self.status("error", "Falha ao ler a câmera: {}".format(error))
        return True
