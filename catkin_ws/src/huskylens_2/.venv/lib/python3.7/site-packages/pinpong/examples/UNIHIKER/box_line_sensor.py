# -*- coding:utf-8 -*-
"""!
  改i2c接口的巡线传感器的示例
"""
from __future__ import print_function

import time
import os
from pinpong.board import Board
from pinpong.libs.dfrobot_box_line_sensor import *


Board("UNIHIKER").begin()  # 初始化，选择板型和端口号，不输入端口号则进行自动识别

LS = Box_LineSensor(0x30)

def setup():
    while LS.begin() == False:
        print("Please check that the device is properly connected")
        time.sleep(3)
    print("line sensor begin successfully!!!")
    print("pid : 0x%x " %LS.get_pid())
    print("vid : 0x%x " %LS.get_vid())
    print("version : 0x%x " %LS.get_version())
    print("device addr : 0x%x " %LS.get_device_addr())

    # set iicaddr, Then reset, the iic communication address changes
    #LS.set_device_addr(0x20)
    
    # Set the detection threshold
    LS.set_threshod_number(0, 50)
    LS.set_threshod_number(1, 50)
    LS.set_threshod_number(2, 50)
    LS.set_threshod_number(3, 50)
    LS.set_threshod_number(4, 50)
    
def loop():
    # Get the probe to the black line state
    
    rslt = LS.get_adc_all()
    
    
    print(rslt)
    # The status of a single probe
    print("Second row right  = ", LS.get_adc(0))
    print("First row  right  = ", LS.get_adc(1))
    print("Second row middle = ", LS.get_adc(2))
    print("First row  left   = ", LS.get_adc(3))
    print("Second row left   = ", LS.get_adc(4))
    
    print("adc collect = ", LS.get_adc_value())
    print("threshold = ", LS.get_threshod_value())
    print("")
    #time.sleep(1)
if __name__ == "__main__":
    setup()
    while True:
        loop()
