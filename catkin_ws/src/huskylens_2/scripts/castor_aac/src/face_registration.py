#!/usr/bin/env python3

"""Fluxo de cadastro facial compartilhado pelo nó e pelo modo manual."""

import subprocess
import sys
import threading
import time

sys.path.append(
    "/home/pi/catkin_ws/src/huskylens_2/"
    "scripts/DFRobot_HuskylensV2/python/smbus2/"
)

from dfrobot_huskylensv2 import ALGORITHM_FACE_RECOGNITION

from piper_castor_tts import prepare_greetings
from registration_voice import RegistrationVoice


KNOWLEDGE_ID = 1
REGISTRATION_STABLE_SECONDS = 3.0
REGISTRATION_TIMEOUT_SECONDS = 60.0


def normalize_name(name):
    if isinstance(name, bytes):
        name = name.decode("utf-8", errors="replace")

    return str(name).strip()


def read_center_result(huskylens):
    huskylens.getResult(ALGORITHM_FACE_RECOGNITION)

    if not huskylens.available(ALGORITHM_FACE_RECOGNITION):
        return None

    return huskylens.getCachedCenterResult(
        ALGORITHM_FACE_RECOGNITION
    )


class FaceRegistrationManager:
    """Controla uma solicitação de cadastro por vez."""

    def __init__(self, status_callback, voice_factory=RegistrationVoice):
        self.status_callback = status_callback
        self.voice_factory = voice_factory
        self.voice = None
        self.name = None
        self.requested_at = None
        self.face_started_at = None
        self.lock = threading.Lock()

    @property
    def active(self):
        return self.name is not None

    def publish(self, state, message, face_id=None):
        self.status_callback(
            state=state,
            message=message,
            name=self.name or "",
            face_id=face_id,
        )

    def request(self, name):
        requested_name = normalize_name(name)

        if not requested_name:
            self.status_callback(
                state="error",
                message="Digite o nome da pessoa.",
                name="",
                face_id=None,
            )
            return False

        if len(requested_name) > 40:
            self.status_callback(
                state="error",
                message="O nome deve ter no máximo 40 caracteres.",
                name=requested_name,
                face_id=None,
            )
            return False

        with self.lock:
            if self.active:
                self.publish(
                    "busy",
                    "Já existe um cadastro em andamento para {}.".format(
                        self.name
                    ),
                )
                return False

            self.requested_at = time.monotonic()
            self.face_started_at = None
            self.voice = self.voice_factory()
            self.voice.say("inicio")
            self.name = requested_name

        self.publish(
            "waiting_face",
            "Cadastro de {} solicitado. Aproxime a pessoa da câmera.".format(
                requested_name
            ),
        )
        return True

    def finish(self, terminal_stage=None):
        if self.voice is not None:
            self.voice.close(terminal_stage)
        with self.lock:
            self.voice = None
            self.name = None
            self.requested_at = None
            self.face_started_at = None

    def update(self, huskylens, result):
        try:
            return self._update(huskylens, result)
        except Exception as error:
            self.publish("error", "Cadastro interrompido: {}".format(error))
            self.finish()
            return True

    def _update(self, huskylens, result):
        """Avança o cadastro e retorna True quando ele termina."""

        if not self.active:
            return False

        now = time.monotonic()

        if now - self.requested_at >= REGISTRATION_TIMEOUT_SECONDS:
            self.publish(
                "timeout",
                "Cadastro cancelado: tempo esgotado. Tente novamente.",
            )
            self.finish()
            return True

        if result is None:
            if self.face_started_at is not None:
                self.face_started_at = None
                self.voice.say("nova_tentativa")
                self.publish(
                    "waiting_face",
                    "Rosto perdido. Aproxime a pessoa novamente.",
                )
            return False

        if self.face_started_at is None:
            self.face_started_at = now
            self.voice.say("captura")
            self.publish(
                "face_detected",
                "Rosto detectado. Mantenha {} parado por 3 segundos.".format(
                    self.name
                ),
            )
            return False

        if now - self.face_started_at < REGISTRATION_STABLE_SECONDS:
            return False

        person_name = self.name
        face_id = getattr(result, "ID", 0)

        # ID 0 representa um rosto detectado, mas ainda não aprendido.
        if face_id > 0:
            existing_name = normalize_name(
                getattr(result, "name", "")
            ) or "sem nome"

            self.publish(
                "already_registered",
                "Cadastro não realizado: este rosto já está cadastrado "
                "como {} (ID {}).".format(existing_name, face_id),
                face_id,
            )
            self.finish()
            return True

        self.publish(
            "learning",
            "Cadastrando {}, aguarde...".format(person_name),
        )
        self.voice.say("processamento")

        learned_id = huskylens.learn(ALGORITHM_FACE_RECOGNITION)

        if not learned_id:
            self.publish(
                "error",
                "Cadastro não concluído: a HuskyLens não conseguiu "
                "aprender o rosto.",
            )
            self.finish("nova_tentativa")
            return True

        named = huskylens.setNameByID(
            ALGORITHM_FACE_RECOGNITION,
            learned_id,
            person_name,
        )
        if not named:
            raise RuntimeError("A HuskyLens não confirmou o nome do cadastro.")

        saved = huskylens.saveKnowledges(
            ALGORITHM_FACE_RECOGNITION,
            KNOWLEDGE_ID,
        )
        if not saved:
            raise RuntimeError("A HuskyLens não confirmou o salvamento do cadastro.")

        self.publish(
            "preparing_audio",
            "Rosto salvo. Preparando as oito saudações de {}...".format(person_name),
            learned_id,
        )

        try:
            audio_files = prepare_greetings(person_name, learned_id)
        except (
            OSError,
            RuntimeError,
            ValueError,
            subprocess.SubprocessError,
        ) as error:
            self.publish(
                "registered_audio_error",
                "Cadastro concluído! {} foi cadastrado, mas o áudio "
                "não pôde ser preparado: {}".format(person_name, error),
                learned_id,
            )
        else:
            self.publish(
                "registered",
                "Cadastro concluído! {} foi cadastrado com sucesso.".format(
                    person_name
                ),
                learned_id,
            )
            print("Saudações preparadas: {}".format(len(audio_files)))

        # O rosto já foi salvo, mesmo se a geração de alguma saudação falhar.
        self.finish("concluido")
        return True
