# -*- coding: utf-8 -*-

#实验效果：人体姿态识别
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
root.title("人体姿态识别")
root.geometry("640x480")  # 设置窗口大小
# 创建画布
canvas = tk.Canvas(root, width=640, height=480, bg='white')
canvas.pack()

def draw_results(results):
    """绘制多个人体姿态结果"""
    # 工具函数：画点
    def draw_point(x, y, color="black", label=None):
        r = 4
        if x == 0 and y == 0:
            return
        canvas.create_oval(x-r, y-r, x+r, y+r, fill=color, outline=color)
        if label:
            canvas.create_text(x, y-12, text=label, fill=color, font=("Arial", 7))

    # 工具函数：画骨架线
    def draw_line(p1, p2, color="blue", width=2):
        if p1[0] == 0 and p1[1] == 0:
            return
        if p2[0] == 0 and p2[1] == 0:
            return
        canvas.create_line(p1[0], p1[1], p2[0], p2[1], fill=color, width=width)
    
    # 工具函数：画矩形框
    def draw_rect(x, y, width, height, color="red"):
        canvas.create_rectangle(x-width//2, y-height//2, 
                               x+width//2, y+height//2, 
                               outline=color, width=2)
    
    # 先清空画布
    canvas.delete("all")
    
    if not results:
        return
    
    # 为每个人体使用不同的颜色
    colors = ["red", "blue", "green", "orange", "purple", "brown"]
    
    # 遍历所有人体进行绘制
    for _, result in enumerate(results):
        if not result:
            continue
        
        # 选择颜色（根据ID）
        color = colors[result.ID % len(colors)]
        
        # 绘制人体框
        draw_rect(result.xCenter, result.yCenter, result.width, result.height, color)
        
        # ======== 关键点 =========
        keypoints = {
            "nose": (result.nose_x, result.nose_y),
            "leye": (result.leye_x, result.leye_y),
            "reye": (result.reye_x, result.reye_y),
            "lear": (result.lear_x, result.lear_y),
            "rear": (result.rear_x, result.rear_y),
            "lshoulder": (result.lshoulder_x, result.lshoulder_y),
            "rshoulder": (result.rshoulder_x, result.rshoulder_y),
            "lelbow": (result.lelbow_x, result.lelbow_y),
            "relbow": (result.relbow_x, result.relbow_y),
            "lwrist": (result.lwrist_x, result.lwrist_y),
            "rwrist": (result.rwrist_x, result.rwrist_y),
            "lhip": (result.lhip_x, result.lhip_y),
            "rhip": (result.rhip_x, result.rhip_y),
            "lknee": (result.lknee_x, result.lknee_y),
            "rknee": (result.rknee_x, result.rknee_y),
            "lankle": (result.lankle_x, result.lankle_y),
            "rankle": (result.rankle_x, result.rankle_y),
        }

        # 绘制关键点（头部用不同颜色）
        for name, (x, y) in keypoints.items():
            if name in ["nose", "leye", "reye", "lear", "rear"]:
                draw_point(x, y, color="cyan", label=name)
            else:
                draw_point(x, y, color=color, label=name)

        # ======== 骨架连线 =========
        skeleton = [
            # 头部连线
            ("nose", "leye"), ("nose", "reye"),
            ("leye", "lear"), ("reye", "rear"),
            # 上身连线
            ("lshoulder", "rshoulder"),
            ("lshoulder", "lelbow"), ("lelbow", "lwrist"),
            ("rshoulder", "relbow"), ("relbow", "rwrist"),
            # 躯干连线
            ("lshoulder", "lhip"), ("rshoulder", "rhip"),
            ("lhip", "rhip"),
            # 下身连线
            ("lhip", "lknee"), ("lknee", "lankle"),
            ("rhip", "rknee"), ("rknee", "rankle"),
        ]

        for p1, p2 in skeleton:
            draw_line(keypoints[p1], keypoints[p2], color=color, width=2)
        
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
            husky.switchAlgorithm(ALGORITHM_POSE_RECOGNITION)
            time.sleep(5)
            while True:
                husky.getResult(ALGORITHM_POSE_RECOGNITION)
                # 收集所有人体姿态结果
                results = []
                while husky.available(ALGORITHM_POSE_RECOGNITION):
                    result = husky.popCachedResult(ALGORITHM_POSE_RECOGNITION)
                    if result:
                        results.append(result)
                        print("result.ID=", result.ID)
                        print("result.name=", result.name)
                        print(f"result.Center={result.xCenter, result.yCenter}")
                        print(f"result.nose=({result.nose_x, result.nose_y})")
                
                # 一次性绘制所有人体姿态
                root.after(0, draw_results, results)
                time.sleep(0.1)  # 控制刷新频率

ProtocolThread().start()
root.mainloop()
