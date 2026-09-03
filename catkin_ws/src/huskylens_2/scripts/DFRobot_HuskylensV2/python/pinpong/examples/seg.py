# -*- coding: utf-8 -*-

#实验效果：学习一次ID
#接线：使用windows或linux电脑连接一块树，树莓派主控板，哈士奇接到I2C口SCL SDA
import os
import sys
import time
import tkinter as tk
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

# 创建主窗口
root = tk.Tk()
root.title("分割图像绘制")
root.geometry("640x480")  # 设置窗口大小
# 创建画布
canvas = tk.Canvas(root, width=640, height=480, bg='white')
canvas.pack()

class ProtocolThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True

    def run(self):
        while True:
            husky = HuskylensV2_UART(tty_name="/dev/ttySP0",baudrate=115200, debug_level=logging.INFO)
            while not husky.knock():
                time.sleep(3)
            husky.switchAlgorithm(ALGORITHM_SEGMENT)
            while True:
                ret = husky.getResult(ALGORITHM_SEGMENT)
                logging.info(f"husky.getResult(ALGORITHM_SEGMENT)={ret}");
                while husky.available(ALGORITHM_SEGMENT):
                    result = husky.popCachedResult(ALGORITHM_SEGMENT)
                    if result:
                        print("result.name=",result.name)
                        print(f"result.Center={result.xCenter,result.yCenter}")
                    else:
                        print(None)

ProtocolThread().start()
root.mainloop()
