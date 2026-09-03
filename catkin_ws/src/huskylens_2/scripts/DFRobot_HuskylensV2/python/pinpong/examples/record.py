# -*- coding: utf-8 -*-

#实验效果：学习一次ID
#接线：使用windows或linux电脑连接一块树，树莓派主控板，哈士奇接到I2C口SCL SDA
import sys
import time
from pinpong.board import Board
import threading
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
        ret = self.husky.startRecording(MEDIA_TYPE_AUDIO, 0,"test0.mp3")
        logging.info(f"husky.startRecording(MEDIA_TYPE_AUDIO, 0,'test0.mp3')={ret}")
        time.sleep(10)
        ret = self.husky.stopRecording(MEDIA_TYPE_AUDIO)
        logging.info(f"husky.stopRecording(MEDIA_TYPE_AUDIO)={ret}")
        ret = self.husky.playMusic("test0.mp3",100)
        logging.info(f"husky.playMusic('test0.mp3',100)={ret}")
        time.sleep(12)

        ret = self.husky.startRecording(MEDIA_TYPE_AUDIO, 5,"test5.mp3")
        logging.info(f"husky.startRecording(MEDIA_TYPE_AUDIO, 0,'test5.mp3')={ret}")
        time.sleep(7)
        ret = self.husky.playMusic("test5.mp3",100)
        logging.info(f"husky.playMusic('test5.mp3',100)={ret}")
        time.sleep(7)



ProtocolThread().start()
while True:
    time.sleep(1)