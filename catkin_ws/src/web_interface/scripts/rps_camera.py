import random
import time
import sys
import traceback
from datetime import datetime

huskylens = None
ALGORITHM_HAND_RECOGNITION = None

def init_husky():
    global huskylens
    global ALGORITHM_HAND_RECOGNITION
    if huskylens is not None:
        return True
    try:
        sys.path.append(
            "/home/pi/catkin_ws/src/huskylens_2/scripts/DFRobot_HuskylensV2/python/smbus2/"
        )
        import dfrobot_huskylensv2 as husky
        huskylens = husky.HuskylensV2_I2C()
        ALGORITHM_HAND_RECOGNITION = husky.ALGORITHM_HAND_RECOGNITION
        huskylens.knock()
        huskylens.switchAlgorithm(ALGORITHM_HAND_RECOGNITION)
        print("HuskyLens inicializada.")
        return True
    except Exception as e:
        print("Erro ao iniciar HuskyLens:", e)
        with open("/tmp/husky_error.log", "a") as f:
            f.write(f"\n--- {datetime.now()} ---\n")
            f.write(traceback.format_exc())
        huskylens = None
        return False

def jogar():
    global huskylens

    if not init_husky():
        return {"result": "CAMERA_OFFLINE"}

    opcoes = ["PEDRA", "PAPEL", "TESOURA"]
    inicio = time.time()

    while time.time() - inicio < 10:
        try:
            huskylens.getResult(ALGORITHM_HAND_RECOGNITION)

            if huskylens.available(ALGORITHM_HAND_RECOGNITION):

                result = huskylens.getCachedCenterResult(ALGORITHM_HAND_RECOGNITION)

                if result is None:
                    continue

                gesture_id = result.ID

                if gesture_id == 1:
                    jogador = "PEDRA"
                elif gesture_id == 2:
                    jogador = "TESOURA"
                elif gesture_id == 3:
                    jogador = "PAPEL"
                else:
                    continue

                castor = random.choice(opcoes)

                resultado = None

                if jogador == "PEDRA" and castor == "TESOURA":
                    resultado = "VENCEU"

                elif jogador == "PAPEL" and castor == "PEDRA":
                    resultado = "VENCEU"

                elif jogador == "TESOURA" and castor == "PAPEL":
                    resultado = "VENCEU"

                elif jogador == "PAPEL" and castor == "TESOURA":
                    resultado = "PERDEU"

                elif jogador == "TESOURA" and castor == "PEDRA":
                    resultado = "PERDEU"

                elif jogador == "PEDRA" and castor == "PAPEL":
                    resultado = "PERDEU"

                else:
                    resultado = "EMPATOU"

                return {
                    "player": jogador,
                    "computer": castor,
                    "result": resultado
                }

        except Exception as e:
            print("Erro durante o jogo:", e)

            with open("/tmp/husky_error.log", "a") as f:
                f.write(f"\n--- {datetime.now()} (jogar loop) ---\n")
                f.write(traceback.format_exc())

        time.sleep(0.2)

    return {"result": "TIMEOUT"}


if __name__ == "__main__":
    print(jogar())

#def reset_game():
   #global player_score
   # global computer_score

   # player_score = 0
    #computer_score = 0