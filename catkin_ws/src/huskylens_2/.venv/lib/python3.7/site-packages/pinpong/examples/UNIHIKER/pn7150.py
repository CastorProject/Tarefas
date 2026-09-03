# -*- coding: utf-8 -*
""" 
  @file  pn7150.py
  @brief  Read the basic information of the card and read and write the card memory
  @copyright  Copyright (c) 2010 DFRobot Co.Ltd (http://www.dfrobot.com)
  @licence  The MIT License (MIT)
  @author  [qsjhyy](yihuan.huang@dfrobot.com)
  @version  V1.0
  @date  2024-03-14
  @url https://github.com/DFRobot/DFRobot_PN7150
"""
from __future__ import print_function

from time import sleep

from pinpong.board import Board
from pinpong.libs.dfrobot_pn7150 import *


Board("UNIHIKER").begin()  # 初始化，选择板型和端口号，不输入端口号则进行自动识别

"""
  @brief Module I2C communication init
  @param i2c_addr - I2C communication address
  @param bus - I2C bus
"""
PN7150 = DFRobot_PN7150(i2c_addr=PN7150_I2C_ADDR, bus_num=4)


def setup():
    assert PN7150.connect()
    print("Connected.")

    assert PN7150.mode_rw()
    print("Switched to read/write mode.")


def loop():
    
    protocol = PN7150.read_protocol() 
    if protocol == "T2T":
      print("T2T")
      PN7150.t2t_write_index_data(5, 1, 200)
      print(PN7150.t2t_read(5))
      print(PN7150.t2t_read(5, 1))
    elif protocol == "mifare":
      print("mifare")
      PN7150.write_index_data(1, 1, 200)
      print(PN7150.read_data(1))
      print(PN7150.read_data(1, 1))
    print(PN7150.read_uid())
    #print(PN7150.scan("acee50e3"))
    print(PN7150.scan())
    print("---------------------")


if __name__ == "__main__":
    setup()
    while True:
        loop()
