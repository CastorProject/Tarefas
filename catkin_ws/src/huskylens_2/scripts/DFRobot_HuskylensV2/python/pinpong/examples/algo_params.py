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
        ret = self.husky.switchAlgorithm(ALGORITHM_TAG_RECOGNITION)
        logging.info(f"husky.switchAlgorithm(ALGORITHM_TAG_RECOGNITION)={ret}")
        time.sleep(5)
        while True:
            ret = self.husky.setAlgorithmParams(ALGORITHM_TAG_RECOGNITION,{"show_name":False, "dict_type":"36h11"})
            logging.info(f"husky.setAlgorithmParams(ALGORITHM_TAG_RECOGNITION)={ret}")
            ret = self.husky.updateAlgoParams(ALGORITHM_TAG_RECOGNITION)
            logging.info(f"update1 ret={ret}")
            time.sleep(10)
            params = self.husky.getAlgorithmParams(ALGORITHM_TAG_RECOGNITION,["show_name", "dict_type"])
            logging.info(f"get params={params}")
            time.sleep(10)
            ret = self.husky.setAlgorithmParams(ALGORITHM_TAG_RECOGNITION,{"show_name":True, "dict_type":"36h10"})
            logging.info(f"set ret={ret}")
            ret = self.husky.updateAlgoParams(ALGORITHM_TAG_RECOGNITION)
            logging.info(f"update2 ret={ret}")
            time.sleep(10)
            params = self.husky.getAlgorithmParams(ALGORITHM_TAG_RECOGNITION,["show_name", "dict_type"])
            logging.info(f"get params={params}")
            time.sleep(10)

ProtocolThread().start()
while True:
    time.sleep(1)