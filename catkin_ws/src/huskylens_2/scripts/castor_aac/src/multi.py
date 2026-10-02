import sys
import time
import logging

sys.path.append(
    "/home/pi/catkin_ws/src/huskylens_2/scripts/"
    "DFRobot_HuskylensV2/python/smbus2/"
)
from dfrobot_huskylensv2 import *

logging.basicConfig(level=logging.DEBUG)

FACE = ALGORITHM_FACE_RECOGNITION
EMOTION = ALGORITHM_EMOTION_RECOGNITION

huskylens = HuskylensV2_I2C()

conectado = huskylens.knock()
print("Conexão I2C:", conectado)

if not conectado:
    raise RuntimeError("HUSKYLENS 2 não respondeu pelo I2C")

print("IDs dos modelos:", FACE, EMOTION)
print("Ativando Face Recognition + Emotion Recognition...")

ativou = huskylens.setMultiAlgorithm([FACE, EMOTION])
print("setMultiAlgorithm:", ativou)

# Mostra a última resposta recebida para diagnosticar uma falha.
resposta = list(
    huskylens.receive_buffer[:huskylens.receive_index + 1]
)
print("Resposta recebida:", resposta)

if not ativou:
    raise RuntimeError(
        "A combinação dos modelos não foi confirmada. "
        "Confira a resposta acima e a tela da HUSKYLENS 2."
    )

time.sleep(5)  # Aguarda os dois modelos carregarem.

proporcao = huskylens.setMultiAlgorithmRatio([1, 1])
print("setMultiAlgorithmRatio:", proporcao)

if not proporcao:
    raise RuntimeError(
        "Não foi possível atribuir processamento aos dois modelos"
    )

print("Reconhecimento iniciado. Pressione Ctrl+C para sair.")

try:
    while True:
        # Atualiza separadamente o resultado de cada modelo.
        leitura_face = huskylens.getResult(FACE)
        leitura_emotion = huskylens.getResult(EMOTION)

        if leitura_face is None or leitura_emotion is None:
            print("Falha na leitura; tentando novamente...")
            time.sleep(0.1)
            continue

        if huskylens.available(FACE):
            face = huskylens.getCachedCenterResult(FACE)

            if face is not None:
                nome = face.name or "desconhecido"
                print(f"Face detectada! ID: {face.ID}, nome: {nome}")

        if huskylens.available(EMOTION):
            emotion = huskylens.getCachedCenterResult(EMOTION)

            if emotion is not None:
                print(
                    f"Expressão detectada! "
                    f"ID: {emotion.ID}, nome: {emotion.name}"
                )

        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nPrograma encerrado.")
