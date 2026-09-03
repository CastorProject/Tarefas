# -*- coding: utf-8 -*-

#实验效果：学习一次ID
#接线：使用windows或linux电脑连接一块树，树莓派主控板，哈士奇接到I2C口SCL SDA

import sys
import time
import tkinter as tk
from pinpong.board import Board
import threading
import sys
sys.stdout.reconfigure(encoding='utf-8')

sys.path.append("..")
from dfrobot_huskylensv2 import *

Board("UNIHIKER").begin()  #初始化

class ProtocolThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.husky = HuskylensV2_UART(tty_name="/dev/ttySP0", baudrate=115200)
    def run(self):
        self.husky.knock()
        while True:
            self.husky.getResult(ALGORITHM_OBJECT_CLASSIFICATION)
            while self.husky.available(ALGORITHM_OBJECT_CLASSIFICATION):
                result = self.husky.popCachedResult(ALGORITHM_OBJECT_CLASSIFICATION)
                if result:
                    print("result.classID=",result.classID)
                    print("result.name=",result.name)
                else:
                    print(None)

ProtocolThread().start()
while True:
    time.sleep(1)