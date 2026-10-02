import sys
import os
import time

#sys.path.append("../")
# https://github.com/DFRobot/DFRobot_HuskylensV2/tree/master -> biblioteca
sys.path.append("/home/pi/catkin_ws/src/huskylens_2/scripts/DFRobot_HuskylensV2/python/smbus2/")
from dfrobot_huskylensv2 import *

huskylens = HuskylensV2_I2C()
huskylens.knock()
huskylens.switchAlgorithm(ALGORITHM_HAND_RECOGNITION)

print("Gesture recognition initializing...")

while True:
    huskylens.getResult(ALGORITHM_HAND_RECOGNITION)

    if huskylens.available(ALGORITHM_HAND_RECOGNITION):
        result = huskylens.getCachedCenterResult(ALGORITHM_HAND_RECOGNITION)
        gesture_id = result.ID

        print(f"Gesture detect! ID: {gesture_id}")

        # ID
        if gesture_id == 1:
            print("I love you too! <3")
        # elif gesture_id == 2:
        #     print("ID 2 FOUND")
        else:
            print(f"(ID {gesture_id})")

    time.sleep(0.1)