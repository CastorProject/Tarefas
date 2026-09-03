# -*- coding: utf-8 -*-

#实验效果：学习一次ID
#接线：使用windows或linux电脑连接一块树，树莓派主控板，哈士奇接到I2C口SCL SDA
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

class ProtocolThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.husky = HuskylensV2_UART(tty_name="/dev/ttySP0", baudrate=115200)
    def run(self):
        while not self.husky.knock():
            time.sleep(0.5)

        ret = self.husky.setMultiAlgorithm([ALGORITHM_FACE_RECOGNITION,
            ALGORITHM_OBJECT_RECOGNITION,ALGORITHM_POSE_RECOGNITION])
        logging.info(f"setMultiAlgorithms ret={ret}")
        time.sleep(5)

        while True:           
            ret = self.husky.setMultiAlgorithmRatio([1,1,1])
            logging.info(f"setMultiAlgorithmRatios111 ret={ret}")
            time.sleep(5)
            
            ret = self.husky.setMultiAlgorithmRatio([0,1,1])
            logging.info(f"setMultiAlgorithmRatios011 ret={ret}")
            time.sleep(5)

            ret = self.husky.setMultiAlgorithmRatio([1,1,0])
            logging.info(f"setMultiAlgorithmRatios110 ret={ret}")
            time.sleep(5)
            
            ret = self.husky.setMultiAlgorithmRatio([1,0,0])
            logging.info(f"setMultiAlgorithmRatios100 ret={ret}")
            time.sleep(5)

            ret = self.husky.setMultiAlgorithmRatio([0,1,0])
            logging.info(f"setMultiAlgorithmRatios010 ret={ret}")
            time.sleep(5)

            ret = self.husky.setMultiAlgorithmRatio([0,0,1])
            logging.info(f"setMultiAlgorithmRatios001 ret={ret}")
            time.sleep(10)

ProtocolThread().start()
while True:
    time.sleep(1)