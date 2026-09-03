# -*- coding: utf-8 -*-

#实验效果：巡线绘制
#接线：使用windows或linux电脑连接一块树，树莓派主控板，哈士奇接到I2C口SCL SDA
import sys
import time
import tkinter as tk
import math
from pinpong.board import Board
import threading
import logging

sys.path.append("..")
from dfrobot_huskylensv2 import *

Board("UNIHIKER").begin()  #初始化

# 创建主窗口
root = tk.Tk()
root.title("巡线效果绘制")
root.geometry("640x480")  # 设置窗口大小
# 创建画布
canvas = tk.Canvas(root, width=640, height=480, bg='white')
canvas.pack()

# Level 1 的原点坐标
LEVEL1_ORIGIN_X = 320
LEVEL1_ORIGIN_Y = 480

def calculate_endpoint(start_x, start_y, xTarget, yTarget):
    end_x = start_x + xTarget
    end_y = start_y - yTarget
    return end_x, end_y

def draw_results(results):
    """绘制巡线结果"""
    # 工具函数：画点
    def draw_point(x, y, color="black", label=None, size=4):
        r = size
        canvas.create_oval(x-r, y-r, x+r, y+r, fill=color, outline=color)
        if label:
            canvas.create_text(x, y-12, text=label, fill=color, font=("Arial", 8))
    
    # 工具函数：画线
    def draw_line(p1, p2, color="blue", width=3):
        canvas.create_line(p1[0], p1[1], p2[0], p2[1], fill=color, width=width)
    
    # 先清空画布
    canvas.delete("all")
    
    if not results:
        return
    
    # 绘制原点（Level 1的起点）
    draw_point(LEVEL1_ORIGIN_X, LEVEL1_ORIGIN_Y, color="red", label="Origin", size=6)
    
    # 分离 level 1 和 level 2 的结果
    level1_results = []
    level2_results = []
    
    for result in results:
        if not result:
            continue
        if result.level == 1:
            level1_results.append(result)
        elif result.level == 2:
            level2_results.append(result)
    
    # 绘制 Level 1 的线路
    level1_endpoints = {}  # 存储每个ID的level1终点，供level2使用
    
    for result in level1_results:
        # Level 1 从原点开始
        start_x = LEVEL1_ORIGIN_X
        start_y = LEVEL1_ORIGIN_Y
        
        # 计算终点
        end_x, end_y = calculate_endpoint(start_x, start_y, result.xTarget, result.yTarget)
        
        # 绘制线段（Level 1 用蓝色）
        draw_line((start_x, start_y), (end_x, end_y), color="blue", width=3)
        
        # 绘制起点和终点
        draw_point(start_x, start_y, color="blue", label=f"L1-Start", size=5)
        draw_point(end_x, end_y, color="blue", label=f"L1-End(ID:{result.ID})", size=5)
        
        # 保存终点供 Level 2 使用
        level1_endpoints[result.ID] = (end_x, end_y)
        
        # 显示信息
        info_text = f"L1: ID={result.ID}\nAngle={result.angle}°\nLen={result.length}"
        canvas.create_text((start_x + end_x) / 2, (start_y + end_y) / 2 - 15, 
                          text=info_text, fill="blue", font=("Arial", 8),
                          anchor="s")
    
    # 绘制 Level 2 的线路
    for result in level2_results:
        # Level 2 从对应的 Level 1 终点开始
        if result.ID in level1_endpoints:
            start_x, start_y = level1_endpoints[result.ID]
        else:
            # 如果没有对应的 Level 1，使用原点
            start_x = LEVEL1_ORIGIN_X
            start_y = LEVEL1_ORIGIN_Y
        
        # 计算终点
        end_x, end_y = calculate_endpoint(start_x, start_y, result.xTarget, result.yTarget)
        
        # 绘制线段（Level 2 用绿色）
        draw_line((start_x, start_y), (end_x, end_y), color="green", width=3)
        
        # 绘制起点和终点
        draw_point(start_x, start_y, color="green", label=f"L2-Start", size=5)
        draw_point(end_x, end_y, color="green", label=f"L2-End(ID:{result.ID})", size=5)
        
        # 显示信息
        info_text = f"L2: ID={result.ID}\nAngle={result.angle}°\nLen={result.length}"
        canvas.create_text((start_x + end_x) / 2, (start_y + end_y) / 2 - 15, 
                          text=info_text, fill="green", font=("Arial", 8),
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
            ret = husky.switchAlgorithm(ALGORITHM_LINE_TRACKING)
            logging.info(f"husky.switchAlgorithm(ALGORITHM_LINE_TRACKING)={ret}")
            time.sleep(5)
            while True:
                ret = husky.getResult(ALGORITHM_LINE_TRACKING)
                logging.info(f"husky.getResult(ALGORITHM_LINE_TRACKING)={ret}")
                maxID = husky.getCachedResultMaxID(ALGORITHM_LINE_TRACKING)
                logging.info(f"husky.getCachedResultMaxID(ALGORITHM_LINE_TRACKING)={maxID}")
                # 收集所有巡线结果
                results = []
                while husky.available(ALGORITHM_LINE_TRACKING):
                    result = husky.popCachedResult(ALGORITHM_LINE_TRACKING)
                    if result:
                        results.append(result)
                        print("result.level=", result.level)
                        print("result.ID=", result.ID)
                        print("result.angle=", result.angle)
                        print("result.length=", result.length)
                        print("result.xTarget=", result.xTarget)
                        print("result.yTarget=", result.yTarget)
                
                # 一次性绘制所有巡线结果
                root.after(0, draw_results, results)
                time.sleep(0.1)  # 控制刷新频率

ProtocolThread().start()
root.mainloop()
