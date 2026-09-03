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
root.title("手部特征绘制")
root.geometry("640x480")  # 设置窗口大小
# 创建画布
canvas = tk.Canvas(root, width=640, height=480, bg='white')
canvas.pack()

def draw_results(results):
    """绘制多个手部识别结果"""
    # 工具函数：画点
    def draw_point(x, y, color="black", label=None):
        r = 3
        if x == 0 and y == 0:
            return
        canvas.create_oval(x-r, y-r, x+r, y+r, fill=color, outline=color)
        if label:
            canvas.create_text(x, y-10, text=label, fill=color)

    # 工具函数：画骨架线
    def draw_line(p1, p2, color="blue"):
        if p1[0] == 0 and p1[1] == 0:
            return
        if p2[0] == 0 and p2[1] == 0:
            return
        canvas.create_line(p1[0], p1[1], p2[0], p2[1], fill=color, width=2)
    
    # 先清空画布
    canvas.delete("all")
    
    if not results:
        return
    
    # 为每只手使用不同的颜色
    colors = ["red", "blue", "green", "orange", "purple", "brown"]
    
    # 遍历所有手部进行绘制
    for _, result in enumerate(results):
        if not result:
            continue
        
        # 选择颜色（根据ID）
        color = colors[result.ID % len(colors)]
        
        # 绘制手部框（如果有的话）
        if hasattr(result, 'xCenter') and hasattr(result, 'yCenter') and hasattr(result, 'width') and hasattr(result, 'height'):
            canvas.create_rectangle(result.xCenter-result.width//2, result.yCenter-result.height//2, 
                                   result.xCenter+result.width//2, result.yCenter+result.height//2, 
                                   outline=color, width=2)
        
        # ========== 手腕 ==========
        wrist = (result.wrist_x, result.wrist_y)
        draw_point(*wrist, color=color, label="wrist")
        
        # ========== 拇指 ==========
        thumb_cmc = (result.thumb_cmc_x, result.thumb_cmc_y)
        thumb_mcp = (result.thumb_mcp_x, result.thumb_mcp_y)
        thumb_ip  = (result.thumb_ip_x, result.thumb_ip_y)
        thumb_tip = (result.thumb_tip_x, result.thumb_tip_y)
        
        # 点
        for pt, name in [(thumb_cmc, "thumb_cmc"), (thumb_mcp, "thumb_mcp"),
                         (thumb_ip, "thumb_ip"), (thumb_tip, "thumb_tip")]:
            draw_point(*pt, color="green", label=name)
        # 线
        draw_line(wrist, thumb_cmc)
        draw_line(thumb_cmc, thumb_mcp)
        draw_line(thumb_mcp, thumb_ip)
        draw_line(thumb_ip, thumb_tip)
        
        # ========== 食指 ==========
        index_mcp = (result.index_finger_mcp_x, result.index_finger_mcp_y)
        index_pip = (result.index_finger_pip_x, result.index_finger_pip_y)
        index_dip = (result.index_finger_dip_x, result.index_finger_dip_y)
        index_tip = (result.index_finger_tip_x, result.index_finger_tip_y)
        
        for pt, name in [(index_mcp, "index_mcp"), (index_pip, "index_pip"),
                         (index_dip, "index_dip"), (index_tip, "index_tip")]:
            draw_point(*pt, color="blue", label=name)
        draw_line(wrist, index_mcp)
        draw_line(index_mcp, index_pip)
        draw_line(index_pip, index_dip)
        draw_line(index_dip, index_tip)
        
        # ========== 中指 ==========
        middle_mcp = (result.middle_finger_mcp_x, result.middle_finger_mcp_y)
        middle_pip = (result.middle_finger_pip_x, result.middle_finger_pip_y)
        middle_dip = (result.middle_finger_dip_x, result.middle_finger_dip_y)
        middle_tip = (result.middle_finger_tip_x, result.middle_finger_tip_y)
        
        for pt, name in [(middle_mcp, "middle_mcp"), (middle_pip, "middle_pip"),
                         (middle_dip, "middle_dip"), (middle_tip, "middle_tip")]:
            draw_point(*pt, color="orange", label=name)
        draw_line(wrist, middle_mcp)
        draw_line(middle_mcp, middle_pip)
        draw_line(middle_pip, middle_dip)
        draw_line(middle_dip, middle_tip)
        
        # ========== 无名指 ==========
        ring_mcp = (result.ring_finger_mcp_x, result.ring_finger_mcp_y)
        ring_pip = (result.ring_finger_pip_x, result.ring_finger_pip_y)
        ring_dip = (result.ring_finger_dip_x, result.ring_finger_dip_y)
        ring_tip = (result.ring_finger_tip_x, result.ring_finger_tip_y)
        
        for pt, name in [(ring_mcp, "ring_mcp"), (ring_pip, "ring_pip"),
                         (ring_dip, "ring_dip"), (ring_tip, "ring_tip")]:
            draw_point(*pt, color="purple", label=name)
        draw_line(wrist, ring_mcp)
        draw_line(ring_mcp, ring_pip)
        draw_line(ring_pip, ring_dip)
        draw_line(ring_dip, ring_tip)
        
        # ========== 小拇指 ==========
        pinky_mcp = (result.pinky_finger_mcp_x, result.pinky_finger_mcp_y)
        pinky_pip = (result.pinky_finger_pip_x, result.pinky_finger_pip_y)
        pinky_dip = (result.pinky_finger_dip_x, result.pinky_finger_dip_y)
        pinky_tip = (result.pinky_finger_tip_x, result.pinky_finger_tip_y)
        
        for pt, name in [(pinky_mcp, "pinky_mcp"), (pinky_pip, "pinky_pip"),
                         (pinky_dip, "pinky_dip"), (pinky_tip, "pinky_tip")]:
            draw_point(*pt, color="brown", label=name)
        draw_line(wrist, pinky_mcp)
        draw_line(pinky_mcp, pinky_pip)
        draw_line(pinky_pip, pinky_dip)
        draw_line(pinky_dip, pinky_tip)
        
        # 显示ID和名称信息
        if hasattr(result, 'xCenter') and hasattr(result, 'yCenter'):
            info_text = f"ID: {result.ID}"
            if hasattr(result, 'name') and result.name:
                info_text += f"\nName: {result.name}"
            canvas.create_text(result.xCenter, result.yCenter - 20, 
                              text=info_text, fill=color, font=("Arial", 10, "bold"),
                              anchor="s")

class ProtocolThread(threading.Thread):
  def __init__(self):
    super().__init__()
    self.daemon = True

  def run(self):
    while True:
        husky = HuskylensV2_UART(tty_name="/dev/ttySP0",baudrate=115200, debug_level=logging.INFO)
        while not husky.knock():
            time.sleep(3)
        husky.switchAlgorithm(ALGORITHM_HAND_RECOGNITION)
        time.sleep(5)
        while True:
            husky.getResult(ALGORITHM_HAND_RECOGNITION)
            # 收集所有手部识别结果
            results = []
            while husky.available(ALGORITHM_HAND_RECOGNITION):
                result = husky.popCachedResult(ALGORITHM_HAND_RECOGNITION)
                if result:
                    results.append(result)
                    print("result.ID=", result.ID)
                    print("result.name=", result.name)
                    print(f"result.Center={result.xCenter, result.yCenter}")

            # 一次性绘制所有手部识别结果
            root.after(0, draw_results, results)
            time.sleep(0.1)  # 控制刷新频率

ProtocolThread().start()
root.mainloop()
