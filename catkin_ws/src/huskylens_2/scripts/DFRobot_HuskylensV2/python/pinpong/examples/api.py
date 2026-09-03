# -*- coding: utf-8 -*-

#实验效果：学习一次ID
#接线：使用windows或linux电脑连接一块树，树莓派主控板，哈士奇接到I2C口SCL SDA
import sys
import time
import tkinter as tk
from pinpong.board import Board
import threading

sys.path.append("..")
from dfrobot_huskylensv2 import *

Board("RPI").begin()  #初始化

# 创建主窗口
root = tk.Tk()
root.title("面部特征绘制")
root.geometry("640x480")  # 设置窗口大小
# 创建画布
canvas = tk.Canvas(root, width=640, height=480, bg='white')
canvas.pack()


def draw_result(result):
    """在UI线程里绘制"""
    if result:
        # 绘制面部方框
        canvas.create_rectangle(
            result.xCenter - result.width / 2, result.yCenter - result.height / 2,
            result.xCenter + result.width / 2, result.yCenter + result.height / 2,
            outline='blue', width=2
        )

        # 左眼
        canvas.create_oval(
            result.leye_x - 5, result.leye_y - 5,
            result.leye_x + 5, result.leye_y + 5,
            fill='green', outline='green'
        )

        # 右眼
        canvas.create_oval(
            result.reye_x - 5, result.reye_y - 5,
            result.reye_x + 5, result.reye_y + 5,
            fill='green', outline='green'
        )

        # 鼻子
        canvas.create_oval(
            result.nose_x - 5, result.nose_y - 5,
            result.nose_x + 5, result.nose_y + 5,
            fill='red', outline='red'
        )

        # 嘴巴
        canvas.create_line(
            result.lmouth_x, result.lmouth_y,
            result.rmouth_x, result.rmouth_y,
            fill='red', width=2
        )

        # 标签
        canvas.create_text(result.leye_x, result.leye_y - 15, text="L-Eye", fill="black")
        canvas.create_text(result.reye_x, result.reye_y - 15, text="R-Eye", fill="black")
        canvas.create_text(result.nose_x, result.nose_y - 15, text="Nose", fill="black")
        canvas.create_text(
            (result.lmouth_x + result.rmouth_x) / 2,
            (result.lmouth_y + result.rmouth_y) / 2 - 15,
            text="Mouth", fill="black"
        )
    else:
        canvas.delete("all")
        #canvas.create_text(320, 240, text="No face detected", fill="gray")

class ProtocolThread(threading.Thread):
  def __init__(self):
    super().__init__()
    self.daemon = True

  def run(self):
    while True:
      husky = HuskylensV2_UART(tty_name="/dev/ttyUSB0")
      husky.knock()
      #husky.switchAlgorithm(ALGORITHM_FACE_RECOGNITION)
      #husky.takePhoto()
      #husky.takeScreenshot()
      #husky.learn(ALGORITHM_FACE_RECOGNITION)
      #husky.forgot(ALGORITHM_FACE_RECOGNITION)
      #husky.drawRect(ALGORITHM_FACE_RECOGNITION, 0xFF00FF, 100, 101, 200, 201)
      #husky.clearRect(ALGORITHM_FACE_RECOGNITION)
      #husky.drawText(ALGORITHM_FACE_RECOGNITION, 0xFF00FF, 100, 101, "shanghai成都")
      #husky.clearText(ALGORITHM_FACE_RECOGNITION)
      #husky.saveKnowledges(ALGORITHM_FACE_RECOGNITION,0)
      #husky.loadKnowledges(ALGORITHM_FACE_RECOGNITION,1)
      #husky.setNameByID(ALGORITHM_FACE_RECOGNITION , 1 , "成都hello")
      #husky.playMusic("开机123.mp3", 200)
      #husky.setMultiAlgorithm([ALGORITHM_FACE_RECOGNITION, ALGORITHM_POSE_RECOGNITION, ALGORITHM_HAND_RECOGNITION])
      #husky.setMultiAlgorithmRatio([2, 1, 0])
      
      #time.sleep(100)
      while True:
        husky.getResult(ALGORITHM_FACE_RECOGNITION)
        root.after(0, draw_result, None)
        result = None
        result = husky.getCachedCenterResult(ALGORITHM_FACE_RECOGNITION)
        #result = husky.getCachedResultByIndex(ALGORITHM_FACE_RECOGNITION, 0)
        #result = husky.getCachedResultByID(ALGORITHM_FACE_RECOGNITION,2)
        #result = husky.getCachedIndexResultByID(ALGORITHM_FACE_RECOGNITION, 1, 0)
        #n = husky.getCachedResultNum(ALGORITHM_FACE_RECOGNITION)
        #n = husky.getCachedResultLearnedNum(ALGORITHM_FACE_RECOGNITION)
        #n = husky.getCachedResultNumByID(ALGORITHM_FACE_RECOGNITION, 1)
        #n = husky.getCachedResultMaxID(ALGORITHM_FACE_RECOGNITION)
        #print(f"n   =   {n}")
        #husky.setLearningRectPosition(ALGORITHM_OBJECT_TRACKING, 100,101,200,201)
        if result:
            pass
        else:
            print(None)
        root.after(0, draw_result, result)

ProtocolThread().start()
root.mainloop()
