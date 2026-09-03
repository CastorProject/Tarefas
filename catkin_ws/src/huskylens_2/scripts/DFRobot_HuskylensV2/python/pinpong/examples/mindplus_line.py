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

xTarget1 = 0
yTarget1 = 0

def draw_result(result):
    global xTarget1, yTarget1
    """在UI线程里绘制"""
    w = int(canvas.cget("width"))
    h = int(canvas.cget("height"))

    if result:
        if result.level == 1:
            color = "red"
            xTarget1 = result.xTarget
            yTarget1 = result.yTarget
            ox = w / 2
            oy = h
            tx = ox + result.xTarget
            ty = oy - result.yTarget
        elif result.level == 2:
            color = "blue"
            ox = w / 2 + xTarget1
            oy = h - yTarget1
            tx = ox + result.xTarget
            ty = oy - result.yTarget
        else:
            print("--------------------------------------")
            return
        r = 4
        canvas.create_oval(ox-r, oy-r, ox+r, oy+r,
                           fill=color, outline=color,
                           tags="target_line")
        
        # 画从原点到目标点的线段（带箭头）
        canvas.create_line(ox, oy, tx, ty, fill=color, width=2,
                           arrow="last", arrowshape=(12,14,6), tags="target_line")
        
        # 可选：画目标点
        canvas.create_oval(tx-3, ty-3, tx+3, ty+3, fill=color, outline=color,
                           tags="target_line")
        show_label = True
        # 显示坐标标签
        if show_label:
            text = f"({result.xTarget:.1f}, {result.yTarget:.1f})"
            # 放在目标点的上方，避免超出画布
            label_x = tx
            label_y = ty - 12
            # 限制不跑出画布顶部
            label_y = max(6, label_y)
            canvas.create_text(label_x, label_y, text=text, fill=color,
                               font=("Arial", 10), tags="target_line")
    else:
        canvas.delete("all")

class ProtocolThread(threading.Thread):
  def __init__(self):
    super().__init__()
    self.daemon = True

  def run(self):
    while True:
      husky = HuskylensV2_UART(tty_name="/dev/ttyUSB0")
      husky.knock()

      while True:
        husky.getResult(ALGORITHM_LINE_TRACKING)
        root.after(0, draw_result, None)
        result = [husky.createResult()]
        #当前路径信息
        result[0].xTarget = husky.getCurrentBranch(ALGORITHM_LINE_TRACKING, "xTarget")
        result[0].yTarget = husky.getCurrentBranch(ALGORITHM_LINE_TRACKING, "yTarget")
        result[0].angle = husky.getCurrentBranch(ALGORITHM_LINE_TRACKING, "angle")
        result[0].length = husky.getCurrentBranch(ALGORITHM_LINE_TRACKING, "length")
        result[0].level = 1
        root.after(0, draw_result, result[0])
        
        #前方路口数目
        n = husky.getUpcomingBranchCount(ALGORITHM_LINE_TRACKING)
        print("n      =     ",n)

        #逆时针取出前方路口的每条分支
        for i in range(0,n):
            r = husky.createResult()
            r.xTarget = husky.getBranch(ALGORITHM_LINE_TRACKING, i, "xTarget")
            r.yTarget = husky.getBranch(ALGORITHM_LINE_TRACKING, i, "yTarget")
            r.angle = husky.getBranch(ALGORITHM_LINE_TRACKING, i, "angle")
            r.length = husky.getBranch(ALGORITHM_LINE_TRACKING, i, "length")
            r.level = 2
            result.append(r)
            root.after(0, draw_result, result[1+i])
ProtocolThread().start()
root.mainloop()
