# -*- coding: utf-8 -*-

#实验效果：舵机控制
#接线：使用电脑连接一块UNIHIKER主控板，P10连接一个舵机
import time
from pinpong.board import Board,Pin,Servo

Board("UNIHIKER").begin()  #初始化，选择板型，不输入板型则进行自动识别

s0 = Servo(Pin(Pin.P0)) #将Pin传入Servo中初始化舵机引脚,支持P0 P2 P3 P8 P9 P10 P16  P21 P22 P23
s2 = Servo(Pin(Pin.P2)) #将Pin传入Servo中初始化舵机引脚,支持P0 P2 P3 P8 P9 P10 P16  P21 P22 P23
s3 = Servo(Pin(Pin.P3)) #将Pin传入Servo中初始化舵机引脚,支持P0 P2 P3 P8 P9 P10 P16  P21 P22 P23
#s8 = Servo(Pin(Pin.P8)) #将Pin传入Servo中初始化舵机引脚,支持P0 P2 P3 P8 P9 P10 P16  P21 P22 P23
#s9 = Servo(Pin(Pin.P9)) #将Pin传入Servo中初始化舵机引脚,支持P0 P2 P3 P8 P9 P10 P16  P21 P22 P23
s10 = Servo(Pin(Pin.P10)) #将Pin传入Servo中初始化舵机引脚,支持P0 P2 P3 P8 P9 P10 P16  P21 P22 P23

s16 = Servo(Pin(Pin.P16)) #将Pin传入Servo中初始化舵机引脚,支持P0 P2 P3 P8 P9 P10 P16  P21 P22 P23
s21 = Servo(Pin(Pin.P21)) #将Pin传入Servo中初始化舵机引脚,支持P0 P2 P3 P8 P9 P10 P16  P21 P22 P23
s22 = Servo(Pin(Pin.P22)) #将Pin传入Servo中初始化舵机引脚,支持P0 P2 P3 P8 P9 P10 P16  P21 P22 P23
s23 = Servo(Pin(Pin.P23)) #将Pin传入Servo中初始化舵机引脚,支持P0 P2 P3 P8 P9 P10 P16  P21 P22 P23
s26 = Servo(Pin(Pin.P26)) #将Pin传入Servo中初始化舵机引脚,支持P0 P2 P3 P8 P9 P10 P16  P21 P22 P23

while True:
  
  s26.angle(180) #控制舵机转到0度位置
  s2.angle(180) #控制舵机转到0度位置

  '''s0.angle(0) #控制舵机转到0度位置
  s2.angle(0) #控制舵机转到0度位置
  s3.angle(0) #控制舵机转到0度位置
  #s8.angle(0) #控制舵机转到0度位置
  #s9.angle(0) #控制舵机转到0度位置
  s10.angle(0) #控制舵机转到0度位置
  s16.angle(0) #控制舵机转到0度位置
  s21.angle(0) #控制舵机转到0度位置
  s22.angle(0) #控制舵机转到0度位置
  
  s23.angle(0) #控制舵机转到0度位置

  time.sleep(1)

  s0.angle(90) #控制舵机转到90度位置
  s2.angle(90) #控制舵机转到90度位置
  s3.angle(90) #控制舵机转到90度位置
  #s8.angle(90) #控制舵机转到90度位置
  #s9.angle(90) #控制舵机转到90度位置
  s10.angle(90) #控制舵机转到90度位置
  s16.angle(90) #控制舵机转到90度位置
  s21.angle(90) #控制舵机转到90度位置
  s22.angle(90) #控制舵机转到90度位置
  s23.angle(90) #控制舵机转到90度位置'''
  time.sleep(1)
