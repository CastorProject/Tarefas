# -*- coding: utf-8 -*-

#实验效果：控制WS2812单线RGB LED灯
#接线：使用windows或linux电脑连接一块arduino主控板，ws2812灯接到D9口
import time
from pinpong.board import Board,Pin,NeoPixel

NEOPIXEL_PIN = Pin.P2
PIXELS_NUM = 7 #灯数

Board().begin()  #初始化，选择板型和端口号，不输入端口号则进行自动识别
#Board("uno","COM36").begin()  #windows下指定端口初始化
#Board("uno","/dev/ttyACM0").begin()   #linux下指定端口初始化
#Board("uno","/dev/cu.usbmodem14101").begin()   #mac下指定端口初始化

np = NeoPixel(Pin(NEOPIXEL_PIN), PIXELS_NUM)

while True:
  
  np.brightness(105)
  
  np[0] = 0xff00ff#(255, 0, 0) #设置第一个灯RGB颜色
  np[1] = (0, 255, 0) #设置第二个灯RGB颜色
  np[2] = (0, 0, 255) #设置第三个灯RGB颜色
  np[3] = (255, 255, 0) #设置第四个灯RGB颜色
  np[4] = (255, 0, 255) #设置第五个灯RGB颜色
  np[5] = (0, 255, 255) #设置第六个灯RGB颜色
  np[6] = (255, 255, 255) #设置第六个灯RGB颜色
  
  time.sleep(1)

  # 循环跳动
  for i in range(PIXELS_NUM):
    np.rotate(1)
    time.sleep(0.1)
  
  
  np.clear()
  time.sleep(1)
  
  np[0] = (255, 0, 0) #设置第一个灯RGB颜色
  np[1] = (0, 255, 0) #设置第二个灯RGB颜色
  np[2] = (0, 0, 255) #设置第三个灯RGB颜色
  np[3] = (255, 255, 0) #设置第四个灯RGB颜色
  np[4] = (255, 0, 255) #设置第五个灯RGB颜色
  np[5] = (0, 255, 255) #设置第六个灯RGB颜色
  np[6] = (255, 255, 255) #设置第六个灯RGB颜色
  
  time.sleep(1)
  # 单次跳动 逐跳消失
  for i in range(PIXELS_NUM):
    np.shift(1)
    time.sleep(0.1)
  np.clear()
  
  
  
  np.range_color(0,PIXELS_NUM,0xFF0000)
  time.sleep(0.5)
  np.range_color(0,PIXELS_NUM,0x00FF00)
  time.sleep(0.5)  
  np.range_color(0,PIXELS_NUM,0x0000FF)
  time.sleep(0.5)
  
  np.clear()
  time.sleep(1)
  
  
  np.rainbow(0,PIXELS_NUM,0,360)    # 彩虹灯
  
  
  # 渐变颜色
  for i in range(0, 360):
    np.rainbow(0,7,0,i)
    time.sleep(0.01)  # 根据需求调整延迟时间
  
  #np.rainbow(0,7,0,360)
  time.sleep(2)
  np.clear()
  
  
