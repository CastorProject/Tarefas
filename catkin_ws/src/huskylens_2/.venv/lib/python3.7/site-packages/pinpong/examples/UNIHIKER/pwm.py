# -*- coding: utf-8 -*-

#实验效果：使用按钮控制LED呼吸灯
#接线：使用windows或linux电脑连接一块arduino主控板，主控板D6接一个LED灯模块
import time
from pinpong.board import Board,Pin,PWM #导入PWM类实现模拟输出

Board("UNIHIKER").begin()  #初始化，选择板型，不输入板型则进行自动识别
#P0 P2 P3 P8 P9 P10 P16 P21 P22 P23
pwm0 = PWM(Pin(Pin.P2)) #将Pin传入PWM中实现模拟输出
pwm26 = PWM(Pin(Pin.P26)) #将Pin传入PWM中实现模拟输
#PWM支持0-1023范围

while True:
    pwm0.duty(1024)  #设置模拟输出值
    time.sleep(1)
    pwm0.duty(512)  #设置模拟输出值
    pwm26.duty(512)  #设置模拟输出值
    #time.sleep(1)
    #pwm0.duty(512)  #设置模拟输出值
    time.sleep(1)
  #for i in range(1024): #从0到1023循环
    #pwm0.duty(i)  #设置模拟输出值
    #print(i)
