# -*- coding: utf-8 -*-
import time
from pinpong.board import Board
from pinpong.libs.dfrobot_aht20 import AHT20

Board("UNIHIKER").begin()  # 初始化，选择板型和端口号，不输入端口号则进行自动识别

aht = AHT20()

while True:
    print("humidity = {} %RH".format(aht.humidity()))
    print("template = {} ℃".format(aht.temp_c()))
    print("")
    time.sleep(0.5)
