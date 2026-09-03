# -*- coding: utf-8 -*-

#实验效果：学习一次ID
#接线：使用windows或linux电脑连接一块树，树莓派主控板，哈士奇接到I2C口SCL SDA
import os
import sys
import time
import tkinter as tk
from pinpong.board import Board
import threading
import sys
import logging

sys.path.append("..")
from dfrobot_huskylensv2 import *

sys.stdout.reconfigure(encoding='utf-8')
logging.basicConfig(
    level=logging.INFO,                # 日志级别：DEBUG/INFO/WARNING/ERROR
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
Board("UNIHIKER").begin()  #初始化



def main():
    husky = HuskylensV2_UART(tty_name="/dev/ttySP0",baudrate=115200, debug_level=logging.INFO)
    while not husky.knock():
        time.sleep(3)
    husky.switchAlgorithm(ALGORITHM_GAZE_RECOGNITION)
    time.sleep(5)
    
    while True:
        ret = husky.getResult(ALGORITHM_GAZE_RECOGNITION)
        logging.info(f"husky.getResult(ALGORITHM_GAZE_RECOGNITION)={ret}");

        while husky.available(ALGORITHM_GAZE_RECOGNITION):
            result = husky.popCachedResult(ALGORITHM_GAZE_RECOGNITION)
            if result:
                print("result.name=",result.name)
                print(f"result.pitch={result.pitch}")
                print(f"result.yaw={result.yaw}")
                print(f"result.azimuth={result.azimuth}")
            else:
                print(None)
            time.sleep(1)

if __name__ == "__main__":
    main()
