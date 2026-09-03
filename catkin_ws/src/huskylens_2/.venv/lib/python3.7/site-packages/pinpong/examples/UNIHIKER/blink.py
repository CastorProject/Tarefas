# -*- coding: utf-8 -*-

#实验效果：控制UNIHIKER板载LED灯一秒闪烁一次
#接线：使用电脑连接一块UNIHIKER主控板

import time
from pinpong.board import Board,Pin

Board("").begin()  #初始化，选择板型，不输入板型则进行自动识别

led0 = Pin(Pin.P0, Pin.OUT) #引脚初始化为电平输出
led1 = Pin(Pin.P1, Pin.OUT) #引脚初始化为电平输出
led2 = Pin(Pin.P2, Pin.OUT) #引脚初始化为电平输出
led3 = Pin(Pin.P3, Pin.OUT) #引脚初始化为电平输出
led4 = Pin(Pin.P4, Pin.OUT) #引脚初始化为电平输出
led5 = Pin(Pin.P5, Pin.OUT) #引脚初始化为电平输出
led6 = Pin(Pin.P6, Pin.OUT) #引脚初始化为电平输出
led7 = Pin(Pin.P7, Pin.OUT) #引脚初始化为电平输出
led8 = Pin(Pin.P8, Pin.OUT) #引脚初始化为电平输出
led9 = Pin(Pin.P9, Pin.OUT) #引脚初始化为电平输出
led10 = Pin(Pin.P10, Pin.OUT) #引脚初始化为电平输出
led11 = Pin(Pin.P11, Pin.OUT) #引脚初始化为电平输出
led12 = Pin(Pin.P12, Pin.OUT) #引脚初始化为电平输出
led13 = Pin(Pin.P13, Pin.OUT) #引脚初始化为电平输出
led14 = Pin(Pin.P14, Pin.OUT) #引脚初始化为电平输出
led15 = Pin(Pin.P15, Pin.OUT) #引脚初始化为电平输出
led16 = Pin(Pin.P16, Pin.OUT) #引脚初始化为电平输出
led25 = Pin(Pin.P25, Pin.OUT) #引脚初始化为电平输出
led26 = Pin(Pin.P26, Pin.OUT) #引脚初始化为电平输出

while True:
  #print(light.read())
  led0.value(1) #输出高电平
  led1.value(1) #输出高电平
  led2.value(1) #输出高电平
  led3.value(1) #输出高电平
  led4.value(1) #输出高电平
  led5.value(1) #输出高电平
  led6.value(1) #输出高电平
  led7.value(1) #输出高电平
  led8.value(1) #输出高电平
  led9.value(1) #输出高电平
  led10.value(1) #输出高电平
  led11.value(1) #输出高电平
  led12.value(1) #输出高电平
  led13.value(1) #输出高电平
  led14.value(1) #输出高电平
  led15.value(1) #输出高电平
  led16.value(1) #输出高电平
  led25.value(1) #输出高电平
  led26.value(1) #输出高电平
  print("1")
  time.sleep(1)
  led0.value(0) #输出低电平
  led1.value(0) #输出低电平
  led2.value(0) #输出低电平
  led3.value(0) #输出低电平
  led4.value(0) #输出低电平
  led5.value(0) #输出低电平
  led6.value(0) #输出低电平
  led7.value(0) #输出低电平
  led8.value(0) #输出低电平
  led9.value(0) #输出低电平
  led10.value(0) #输出低电平
  led11.value(0) #输出低电平
  led12.value(0) #输出低电平
  led13.value(0) #输出低电平
  led14.value(0) #输出低电平
  led15.value(0) #输出低电平
  led16.value(0) #输出低电平
  led25.value(0) #输出低电平
  led26.value(0) #输出低电平
  time.sleep(1)
  print("0")
