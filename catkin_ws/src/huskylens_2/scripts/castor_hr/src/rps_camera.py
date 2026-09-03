import random
import time

huskylens = None

def init_husky():
    global huskylens

    if huskylens is not None:
        return

    try:
        from dfrobot_huskylensv2 import HuskylensV2_I2C, ALGORITHM_HAND_RECOGNITION

        huskylens = HuskylensV2_I2C()
        huskylens.knock()
        huskylens.switchAlgorithm(ALGORITHM_HAND_RECOGNITION)

    except Exception as e:
        print("Erro ao iniciar HuskyLens:", e)
        huskylens = None


def jogar():
    global huskylens

    if huskylens is None:
        init_husky()

    if huskylens is None:
        return {"result": "CAMERA_OFFLINE"}

    opcoes = ["PEDRA", "PAPEL", "TESOURA"]

    start = time.time()

    while time.time() - start < 10:
        huskylens.getResult(ALGORITHM_HAND_RECOGNITION)

        if huskylens.available(ALGORITHM_HAND_RECOGNITION):
            Castor = random.choice(opcoes)
            result = huskylens.getCachedCenterResult(ALGORITHM_HAND_RECOGNITION)

            gesture_id = result.ID

            if gesture_id == 1:
                jogador = "PEDRA"
            elif gesture_id == 2:
                jogador = "TESOURA"
            elif gesture_id == 3:
                jogador = "PAPEL"
            else:
                continue

            return {
                "player": jogador,
                "computer": Castor,
                "result": "OK"
            }

        time.sleep(0.2)

    return {"result": "TIMEOUT"}