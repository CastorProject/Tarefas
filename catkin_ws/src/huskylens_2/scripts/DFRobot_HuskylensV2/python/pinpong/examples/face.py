# -*- coding: utf-8 -*-

#实验效果：学习一次ID
#接线：使用windows或linux电脑连接一块树，树莓派主控板，哈士奇接到I2C口SCL SDA

import sys
import time
import tkinter as tk
from pinpong.board import Board
from dfrobot_huskylensv2 import *
import threading
import logging

sys.path.append("..")
from dfrobot_huskylensv2 import *

Board("UNIHIKER").begin()  #初始化

# 创建主窗口
root = tk.Tk()
root.title("人脸特征绘制")
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
    
    # 遍历所有人脸进行绘制
    for _, result in enumerate(results):
        if not result:
            continue
        
        # 选择颜色（循环使用）
        color = colors[result.ID % len(colors)]
        
        # 绘制人脸框
        draw_rect(result.xCenter, result.yCenter, result.width, result.height, color)
              
        # ========== 左眼 ==========
        leye = (result.leye_x, result.leye_y)
        draw_point(*leye, color="blue", label="L-Eye")
        
        # ========== 右眼 ==========
        reye = (result.reye_x, result.reye_y)
        draw_point(*reye, color="blue", label="R-Eye")
        
        # ========== 鼻子 ==========
        nose = (result.nose_x, result.nose_y)
        draw_point(*nose, color="green", label="Nose")
               
        # ========== 嘴角 ==========
        lmouth = (result.lmouth_x, result.lmouth_y)
        rmouth = (result.rmouth_x, result.rmouth_y)
        draw_point(*lmouth, color="purple", label="L-Mouth")
        draw_point(*rmouth, color="purple", label="R-Mouth")
        
        # 连接嘴角
        draw_line(lmouth, rmouth, color="purple")
        
        
        # 显示ID和名称信息
        info_text = f"ID: {result.ID}"
        if result.name:
            info_text += f"\nName: {result.name}"
        canvas.create_text(result.xCenter, result.yCenter - result.height//2 - 20, 
                          text=info_text, fill=color, font=("Arial", 10, "bold"),
                          anchor="s")

class ProtocolThread(threading.Thread):
    def __init__(self):
        super().__init__()
        self.daemon = True

    def run(self):
        while True:
            husky = HuskylensV2_UART(tty_name="/dev/ttySP0", baudrate=115200, debug_level=logging.INFO)
            while not husky.knock():
                time.sleep(3)
            ret = husky.switchAlgorithm(ALGORITHM_FACE_RECOGNITION)
            logging.info(f"husky.switchAlgorithm(ALGORITHM_FACE_RECOGNITION)={ret}")
            time.sleep(5)
            while True:
                ret = husky.getResult(ALGORITHM_FACE_RECOGNITION)
                logging.info(f"husky.getResult(ALGORITHM_FACE_RECOGNITION)={ret}")
                maxID = husky.getCachedResultMaxID(ALGORITHM_FACE_RECOGNITION)
                logging.info(f"husky.getCachedResultMaxID(ALGORITHM_FACE_RECOGNITION)={maxID}")
                # 收集所有人脸结果
                results = []
                while husky.available(ALGORITHM_FACE_RECOGNITION):
                    result = husky.popCachedResult(ALGORITHM_FACE_RECOGNITION)
                    if result:
                        results.append(result)
                        print("result.ID=", result.ID)
                        print("result.name=", result.name)
                        print(f"result.Center={result.xCenter, result.yCenter}")
                        print(f"result.leye=({result.leye_x, result.leye_y})")
                
                # 一次性绘制所有人脸
                root.after(0, draw_results, results)
                time.sleep(0.1)  # 控制刷新频率

ProtocolThread().start()
root.mainloop()
