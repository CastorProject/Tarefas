import random
import time
import subprocess
import json

sys.path.append("/home/pi/catkin_ws/src/huskylens_2/scripts/DFRobot_HuskylensV2/python/smbus2/")
from dfrobot_huskylensv2 import *

huskylens = HuskylensV2_I2C() # inicializa a huskylens2

def eye_tracking():
    while True:
        try:
            section = 0
            block = huskylens.blocks()
            id_husky = block.ID
            x_husky, y_husky = block.x, block.y
            z = 1  # flag para colocar os olhos do robo em modo de seguir o objeto

            # Superior e Inferior
            if (140 <= x_husky <= 180):

                # Superior
                if (0 <= y_husky <= 100):
                    x = 0
                    y = 28  # 8 meio + 20 de abaixo
                    section = 2
                    return x, y, z, str(id_husky), section

                # Inferior
                if (140 <= y_husky <= 240):
                    x = 0
                    y = -20  # -20 abaixo
                    section = 8
                    return x, y, z, str(id_husky), section

            # Lateral Direita (superior, meio, inferior)
            if (180 <= x_husky <= 340):

                # Lateral Superior Direita
                if (0 <= y_husky <= 100):
                    x = 14
                    y = 28
                    section = 1
                    return x, y, z, str(id_husky), section

                # Lateral Inferior Direita
                if (140 <= y_husky <= 240):
                    x = 14
                    y = -20
                    section = 7
                    return x, y, z, str(id_husky), section

                # Lateral Meio Direita
                else:
                    x = 14
                    y = 8
                    section = 6
                    return x, y, z, str(id_husky), section

            # Lateral Esquerda (superior, meio, inferior)
            if (0 <= x_husky <= 140):

                # Lateral Superior Esquerda
                if (0 <= y_husky <= 100):
                    x = -28
                    y = 28
                    section = 3
                    return x, y, z, str(id_husky), section

                # Lateral Inferior Esquerda
                if (140 <= y_husky <= 240):
                    x = -28
                    y = -20
                    section = 9
                    return x, y, z, str(id_husky), section

                # Lateral Meio Esquerda
                else:
                    x = -28
                    y = 8
                    section = 4
                    return x, y, z, str(id_husky), section

            else:
                x = 0
                y = 8
                section = 5
                return x, y, z, str(id_husky), section

        except Exception as e:
            section = 0
            x = 0
            y = 0
            z = 0  # flag para colocar os olhos do robo em modo aleatorio
            id_husky = 0
            return x, y, z, str(id_husky), section

        except KeyboardInterrupt:
            print("\nQUITING")
            break
            quit()


def motor_tracking(angle):
    # Captura os blocos continuamente
    while True:
        try:
            block = huskylens.blocks()
            x_husky = block.x

            if (180 <= x_husky <= 340) and (angle > 380):
                angle = angle - 10

            elif (0 <= x_husky <= 140) and (angle < 900):
                angle = angle + 10

            return angle

        except Exception as e:
            return angle