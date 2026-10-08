#!/usr/bin/env python3

"""Nó ROS que mantém reconhecimento e cadastro facial ativos."""

import json
import subprocess
import sys
import time

import rospy
from std_msgs.msg import String

sys.path.append(
    "/home/pi/catkin_ws/src/huskylens_2/"
    "scripts/DFRobot_HuskylensV2/python/smbus2/"
)

from dfrobot_huskylensv2 import (
    ALGORITHM_EMOTION_RECOGNITION,
    ALGORITHM_FACE_RECOGNITION,
    HuskylensV2_I2C,
)

from face_registration import (
    FaceRegistrationManager,
    KNOWLEDGE_ID,
    normalize_name,
    read_center_result,
)
from piper_castor_tts import speak_greeting
from activity9_recognition import Activity9Recognition


LOOP_FREQUENCY_HZ = 10
GREETING_COOLDOWN_SECONDS = 10 * 60

REGISTRATION_REQUEST_TOPIC = "/face_registration/request"
REGISTRATION_STATUS_TOPIC = "/face_registration/status"

status_publisher = None

# Nome da pessoa reconhecida, para outros nos do robo saberem
# com quem estao falando. Nao altera nenhum comportamento existente.
PESSOA_TOPIC = "/pessoa_reconhecida"
pessoa_publisher = None
registration_manager = None
activity9 = None


def publish_registration_status(
    state,
    message,
    name="",
    face_id=None,
):
    status = {
        "state": state,
        "message": message,
        "name": name,
    }

    if face_id is not None:
        status["face_id"] = face_id

    status_publisher.publish(
        json.dumps(status, ensure_ascii=False)
    )

    if state in {"error", "registered_audio_error"}:
        rospy.logerr(message)
    elif state in {"timeout", "already_registered", "busy"}:
        rospy.logwarn(message)
    else:
        rospy.loginfo(message)


def registration_request_callback(message):
    if activity9 is not None and (activity9.dirty or activity9.request_token):
        publish_registration_status("busy", "Encerre a rodada de emoções antes de cadastrar.")
        return
    registration_manager.request(message.data)


def activity9_request_callback(message):
    try:
        command = json.loads(message.data)
        if isinstance(command, dict):
            activity9.request(command)
    except (TypeError, ValueError) as error:
        rospy.logwarn("Comando da atividade 9 inválido: %s", error)


def recognize_face(
    result,
    last_face_id,
    last_greeting_by_face_id,
):
    if result is None:
        return None

    face_id = getattr(result, "ID", 0)
    face_name = normalize_name(getattr(result, "name", ""))

    # ID 0 significa rosto detectado, mas ainda não aprendido.
    if face_id == 0:
        return None

    if (
        not face_name
        or face_name.casefold() in {"desconhecido", "unknown"}
    ):
        return None

    # Não repete enquanto o mesmo rosto permanece na câmera.
    if face_id == last_face_id:
        return last_face_id

    now = time.monotonic()
    last_greeting_at = last_greeting_by_face_id.get(face_id)

    # Cada ID facial tem seu próprio cooldown de dez minutos.
    if last_greeting_at is not None:
        remaining = GREETING_COOLDOWN_SECONDS - (
            now - last_greeting_at
        )

        if remaining > 0:
            rospy.loginfo(
                "Saudação de %s em espera. Restam %02d:%02d.",
                face_name,
                int(remaining) // 60,
                int(remaining) % 60,
            )
            return face_id

    rospy.loginfo(
        "Rosto reconhecido! ID: %s | Nome: %s",
        face_id,
        face_name,
    )

    if pessoa_publisher is not None:
        pessoa_publisher.publish(face_name)

    try:
        speak_greeting(face_name)
    except (
        OSError,
        RuntimeError,
        ValueError,
        subprocess.CalledProcessError,
    ) as error:
        rospy.logerr(
            "Erro ao reproduzir a saudação: %s",
            error,
        )
    else:
        last_greeting_by_face_id[face_id] = time.monotonic()

    return face_id


def initialize_huskylens():
    huskylens = HuskylensV2_I2C()

    if not huskylens.knock():
        raise RuntimeError("HuskyLens não encontrada.")

    if not huskylens.switchAlgorithm(ALGORITHM_FACE_RECOGNITION):
        raise RuntimeError("A HuskyLens não confirmou o modelo facial.")
    time.sleep(5)

    huskylens.loadKnowledges(
        ALGORITHM_FACE_RECOGNITION,
        KNOWLEDGE_ID,
    )
    time.sleep(0.5)

    return huskylens


def main():
    global status_publisher, pessoa_publisher
    global registration_manager
    global activity9

    rospy.init_node("face_recognition")

    huskylens = initialize_huskylens()

    pessoa_publisher = rospy.Publisher(
        PESSOA_TOPIC,
        String,
        queue_size=10,
    )

    status_publisher = rospy.Publisher(
        REGISTRATION_STATUS_TOPIC,
        String,
        queue_size=10,
        latch=True,
    )

    registration_manager = FaceRegistrationManager(
        publish_registration_status
    )

    emotion_status = rospy.Publisher(
        "/activity9/status", String, queue_size=1, latch=True,
    )
    activity9 = Activity9Recognition(
        huskylens, ALGORITHM_FACE_RECOGNITION, ALGORITHM_EMOTION_RECOGNITION,
        KNOWLEDGE_ID,
        lambda status: emotion_status.publish(json.dumps(status, ensure_ascii=False)),
    )
    rospy.Subscriber("/activity9/request", String,
                     activity9_request_callback, queue_size=10)

    rospy.Subscriber(
        REGISTRATION_REQUEST_TOPIC,
        String,
        registration_request_callback,
        queue_size=1,
    )

    publish_registration_status(
        "ready",
        "Reconhecimento facial ativo. Pronto para cadastrar.",
    )

    rate = rospy.Rate(LOOP_FREQUENCY_HZ)
    last_face_id = None
    last_greeting_by_face_id = {}

    try:
        while not rospy.is_shutdown():
            try:
                if activity9.tick(registration_manager.active):
                    last_face_id = None
                    rate.sleep()
                    continue
                result = read_center_result(huskylens)

                if registration_manager.active:
                    # O reconhecimento é pausado somente durante o cadastro.
                    if registration_manager.update(huskylens, result):
                        last_face_id = None
                        time.sleep(0.5)
                else:
                    last_face_id = recognize_face(
                        result,
                        last_face_id,
                        last_greeting_by_face_id,
                    )

            except Exception as error:
                rospy.logerr_throttle(
                    5,
                    "Erro na HuskyLens: {}".format(error),
                )

            rate.sleep()
    finally:
        try:
            activity9.restore()
        except Exception as error:
            rospy.logerr("Erro ao restaurar a câmera no encerramento: %s", error)


if __name__ == "__main__":
    try:
        main()
    except rospy.ROSInterruptException:
        pass
