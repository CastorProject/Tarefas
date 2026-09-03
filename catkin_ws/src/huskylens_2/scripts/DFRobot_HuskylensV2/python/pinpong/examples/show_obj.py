# -*- coding: utf-8 -*-

#实验效果：学习一次ID
#接线：使用windows或linux电脑连接一块树，树莓派主控板，哈士奇接到I2C口SCL SDA

import sys
import time
import tkinter as tk
from pinpong.board import Board
import threading
import logging

sys.path.append("..")
from dfrobot_huskylensv2 import *

Board("UNIHIKER").begin()  #初始化

# 创建主窗口
root = tk.Tk()
root.title("通用目标显示")
root.geometry("640x480")  # 设置窗口大小
# 创建画布
canvas = tk.Canvas(root, width=640, height=480, bg='white')
canvas.pack()

def draw_results(results):
    """绘制多个人脸结果"""
    # 工具函数：画点
    def draw_point(x, y, color="black", label=None):
        r = 4
        canvas.create_oval(x-r, y-r, x+r, y+r, fill=color, outline=color)
        if label:
            canvas.create_text(x, y-12, text=label, fill=color, font=("Arial", 8))
    
    # 工具函数：画线
    def draw_line(p1, p2, color="blue"):
        canvas.create_line(p1[0], p1[1], p2[0], p2[1], fill=color, width=2)
    
    # 工具函数：画矩形框
    def draw_rect(x, y, width, height, color="red"):
        canvas.create_rectangle(x-width//2, y-height//2, 
                               x+width//2, y+height//2, 
                               outline=color, width=2)
    
    # 先清空画布
    canvas.delete("all")
    
    if not results:
        return
    
    # 为每个人脸使用不同的颜色
    colors = ["red", "blue", "green", "orange", "purple", "brown"]
    
    # 遍历所有OBJ进行绘制
    for _, result in enumerate(results):
        if not result:
            continue
        
        # 选择颜色（循环使用）
        color = colors[result.ID % len(colors)]
        
        # 绘制OBJ框
        draw_rect(result.xCenter, result.yCenter, result.width, result.height, color)
        
        # 显示ID和名称信息
        info_text = f"ID: {result.ID}"
        if result.name:
            info_text += f"\nName: {result.name}"
        canvas.create_text(result.xCenter, result.yCenter - result.height//2 - 20, 
                          text=info_text, fill=color, font=("Arial", 10, "bold"),
                          anchor="s")
#ALGORITHM_FACE_RECOGNITION = 1
#ALGORITHM_OBJECT_RECOGNITION = 2
#ALGORITHM_OBJECT_TRACKING = 3
#ALGORITHM_COLOR_RECOGNITION = 4
#ALGORITHM_OBJECT_CLASSIFICATION = 5
#ALGORITHM_SELF_LEARNING_CLASSIFICATION = 6
#ALGORITHM_SEGMENT = 7
#ALGORITHM_HAND_RECOGNITION = 8
#ALGORITHM_POSE_RECOGNITION = 9
#ALGORITHM_LICENSE_RECOGNITION = 10
#ALGORITHM_OCR_RECOGNITION = 11
#ALGORITHM_LINE_TRACKING = 12
#ALGORITHM_EMOTION_RECOGNITION = 13
#ALGORITHM_GAZE_RECOGNITION = 14
#ALGORITHM_FACE_ORIENTATION = 15
#ALGORITHM_TAG_RECOGNITION = 16
#ALGORITHM_BARCODE_RECOGNITION = 17
#ALGORITHM_QRCODE_RECOGNITION = 18
#ALGORITHM_FALLDOWN_RECOGNITION = 19
ALGORITHM_ID = 128

class ProtocolThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True

    def run(self):
        while True:
            husky = HuskylensV2_UART(tty_name="/dev/ttySP0", baudrate=115200, debug_level=logging.INFO)
            while not husky.knock():
                time.sleep(3)
            ret = husky.switchAlgorithm(ALGORITHM_ID)
            logging.info(f"husky.switchAlgorithm{ALGORITHM_ID}={ret}")
            time.sleep(5)
            while True:
                ret = husky.getResult(ALGORITHM_ID)
                logging.info(f"husky.getResult{ALGORITHM_ID}={ret}")
                maxID = husky.getCachedResultMaxID(ALGORITHM_ID)
                logging.info(f"husky.getCachedResultMaxID{ALGORITHM_ID}={maxID}")
                # 收集所有OBJ
                results = []
                while husky.available(ALGORITHM_ID):
                    result = husky.popCachedResult(ALGORITHM_ID)
                    if result:
                        results.append(result)
                        print("result.ID=", result.ID)
                        print("result.name=", result.name)
                        print(f"result.Center={result.xCenter, result.yCenter}")
                
                # 一次性绘制所有人脸
                root.after(0, draw_results, results)
                time.sleep(0.1)  # 控制刷新频率

ProtocolThread().start()
root.mainloop()
