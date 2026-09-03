'''!
  @file CenterFaceRecognition.py
  @brief Sample code for obtaining information about faces near the center
  @copyright  Copyright (c) 2025 DFRobot Co.Ltd (http://www.dfrobot.com)
  @license    The MIT License (MIT)
  @version    V1.0
  @date       2025-06-02
  @url https://github.com/DFRobot/DFRobot_HuskylensV2
'''
from pinpong.board import Board
import sys
import os
sys.path.append("../")
from dfrobot_huskylensv2 import *

Board("RASPBERRY").begin()  # Comment this line when using UNIHIKER M10
#Board().begin()

huskylens = HuskylensV2_I2C()  # Comment this line to disable I2C mode
# huskylens = HuskylensV2_UART(tty_name="/dev/ttySP0", baudrate=115200)  # Uncomment this line to use UART mode

huskylens.knock()
huskylens.switchAlgorithm(ALGORITHM_FACE_RECOGNITION)

while True:
    huskylens.getResult(ALGORITHM_FACE_RECOGNITION)
    if huskylens.available(ALGORITHM_FACE_RECOGNITION):
        result = huskylens.getCachedCenterResult(ALGORITHM_FACE_RECOGNITION)
        print(str("Face ID: ")     + str(result.ID))
        print(str("Face name: ")   + str(result.name))
        print(str("Face center coordinates: ") + str(result.xCenter) + str(", ") + str(result.yCenter))
        print(str("Face width: ")  + str(result.width))
        print(str("Face height: ") + str(result.height))
    time.sleep(0.5)
