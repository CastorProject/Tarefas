# -*- coding: utf-8 -*-

import serial,re
import serial.tools.list_ports
import platform
import os

PINPONG_MAJOR=0
PINPONG_MINOR=6
PINPONG_DELTA=2

FIRMATA_MAJOR = 2
FIRMATA_MINOR = 7


firmware_version = {
  "UNO":(2,8),
  "LEONARDO":(2,7),
  "MEGA2560":(2,8),
  "MICROBIT":(2,9),
  "HANDPY":(2,9),
  "UNIHIKER":(3,8)
}


def printlogo_big():
    print("""
  __________________________________________
 |    ____  _       ____                    |
 |   / __ \(_)___  / __ \____  ____  ____ _ |
 |  / /_/ / / __ \/ /_/ / __ \/ __ \/ __ `/ |
 | / ____/ / / / / ____/ /_/ / / / / /_/ /  |
 |/_/   /_/_/ /_/_/    \____/_/ /_/\__, /   |
 |   v%d.%d.%d  Designed by DFRobot  /____/    |
 |__________________________________________|
 """%(PINPONG_MAJOR,PINPONG_MINOR,PINPONG_DELTA))

def printlogo():
    print("""
  ___________________________
 |                           |
 |      PinPong v%d.%d.%d       |
 |    Designed by DFRobot    |
 |___________________________|
 """%(PINPONG_MAJOR,PINPONG_MINOR,PINPONG_DELTA))


 
class PinInformation:
  D0 = 0
  D1 = 1
  D2 = 2
  D3 = 3
  D4 = 4
  D5 = 5
  D6 = 6
  D7 = 7
  D8 = 8
  D9 = 9
  D10 = 10
  D11 = 11
  D12 = 12
  D13 = 13
  D14 = 14
  D15 = 15
  D16 = 16
  D17 = 17
  D18 = 18
  D19 = 19
  D20 = 20
  D21 = 21
  D22 = 22
  D23 = 23
  D24 = 24
  D25 = 25
  D26 = 26
  D27 = 27
  D28 = 28
  D29 = 29
  D30 = 30
  D31 = 31
  D32 = 32
  D33 = 33
  D34 = 34
  D35 = 35
  D36 = 36
  D37 = 37
  D38 = 38
  D39 = 39
  D40 = 40
  D41 = 41
  D42 = 42
  D43 = 43
  D44 = 44
  D45 = 45
  D46 = 46
  D47 = 47
  D48 = 48
  D49 = 49
  D50 = 50
  D51 = 51
  D52 = 52
  D53 = 53
  
  A0 = 100
  A1 = 101
  A2 = 102
  A3 = 103
  A4 = 104
  A5 = 105
  A6 = 106
  A7 = 107
  A8 = 108
  A9 = 109
  A10 = 110
  A11 = 111
  A12 = 112
  A13 = 113
  A14 = 114
  A15 = 115
  A16 = 116
  A17 = 117
  A18 = 118
  A19 = 119
  A20 = 120
  A21 = 121
  A22 = 122
  A23 = 123

  P0 = 0
  P1 = 1
  P2 = 2
  P3 = 3
  P4 = 4
  P5 = 5
  P6 = 6
  P7 = 7
  P8 = 8
  P9 = 9
  P10 = 10
  P11 = 11
  P12 = 12
  P13 = 13
  P14 = 14
  P15 = 15
  P16 = 16
  P17 = 17
  P18 = 18
  P19 = 19
  P20 = 20
  P21 = 21
  P22 = 22
  P23 = 23
  P24 = 24
  P25 = 25   #Pythonboard L锟斤拷
  P26 = 26   #Pythonboard 锟斤拷锟截凤拷锟斤拷锟斤拷
  P27 = 27   #Pythonboard key_a
  P28 = 28   #Pythonboard key_b
  P29 = 29
  P30 = 30
  P31 = 31
  P32 = 32
  
  OUT = 0
  IN = 1
  IRQ_FALLING = 2
  IRQ_RISING = 1
  IRQ_DRAIN = 7
  PULL_DOWN = 1
  PULL_UP = 2
  PWM     = 0x10
  ANALOG  = 0x11
  

def find_board(board):
  vidpid={
    "UNO":"3343:0043",
    "UNO":"2341:0043",
    "LEONARDO":"3343:8036",
    "LEONARDO":"2341:8036",
    "MEGA2560":"2341:0042",
    "MEGA2560":"3343:0042",
    "MICROBIT":"0D28:0204",
    "HANDPY":"10C4:EA60",
    "HANDPY":"1A86:55D4"
    }
  findboard={
    "VID:PID=3343:0043":"UNO",
    "VID:PID=2341:0043":"UNO",
    "VID:PID=3343:8036":"LEONARDO",
    "VID:PID=2341:8036":"LEONARDO",
    "VID:PID=2341:0042":"MEGA2560",
    "VID:PID=3343:0042":"MEGA2560",
    "VID:PID=0D28:0204":"MICROBIT",
    "VID:PID=10C4:EA60":"HANDPY",
    "VID:PID=1A86:55D4":"HANDPY"
    }
  _vidpid = '''
    VID:PID=3343:0043
    VID:PID=2341:0043
    VID:PID=3343:8036
    VID:PID=2341:8036
    VID:PID=3343:0042
    VID:PID=2341:0042
    VID:PID=0D28:0204
    VID:PID=10C4:EA60
    VID:PID=1A86:55D4
    '''
  # 如果板子名字和 端口都为空
  if board.boardname == "" and board.port == None:
    if platform.node() == "milkv-duo":
        board.boardname = "MILKV-DUO"
        return
    if os.path.exists('/opt/unihiker/Version'):
        board.boardname = "UNIHIKER"
        board.port = "/dev/ttyS3"
        return
    if platform.node() == "raspberrypi":
        board.boardname = "RPI"
        board.port = "/dev/test"
        return
  
  portlist=[]
  localportlist=[]
  if board.boardname in ["RPI","NEZHA","UNIHIKER"]:
      board.port = "nothing"
      testnode = None
      # linux 结点不匹配的问题
      if board.boardname != "":
        if platform.node() == "milkv-duo":
          testnode = "MILKV-DUO"
        if os.path.exists('/opt/unihiker/Version'):
          testnode = "UNIHIKER"
        if platform.node() == "raspberrypi":
          testnode = "RPI"
        if board.boardname != testnode: 
          print("")
          print(f"The selected development board is {board.boardname}")
          print(f"The development board found is {testnode}")
          print("The development board does not match !!!")
          print("")
          exit()
        if board.boardname == "UNIHIKER":
          board.port = "/dev/ttyS3"
      return

  if board.boardname != "" and board.port == None:
    #2024 7 -24 优化多开发板的问题
    # 通过 board name 找pid vid
    pid_vid = get_vid_pids_by_boardname(board.boardname, findboard)
    if pid_vid == None:
      print("The development board is currently not supported!!!")
      exit()
    pidvid_len = len(pid_vid)
    # 通过 pid vid 找端口
    plist = list(serial.tools.list_ports.comports())
    for port in plist:
      msg = list(port)
      # 通pidvid  找comxxx
      if msg[0] == "/dev/ttySP0" or msg[2]=='n/a':
        continue  # 行空版 串口异常问题,mac
      try:
        list_vidpid = msg[2].split(" ")[1]
        # 找列表中的第一个优先匹配
        for i in range(len(pid_vid)):
          if list_vidpid == pid_vid[i]:
            board.port = msg[0]
            break
      except:
        pass
  elif board.boardname == "" and board.port != None:
    plist = list(serial.tools.list_ports.comports())
    for port in plist:
      msg = list(port)
      if msg[0] == "/dev/ttySP0" or msg[2]=='n/a':
        continue  # 行空版 串口异常问题,mac未知usb问题
      if msg[0] == board.port:
        vidpid = msg[2].split(" ")
        if len(vidpid) > 2 and vidpid[1] in _vidpid:
          board.boardname = findboard[vidpid[1]]
          board.port = msg[0]
          break
  elif board.boardname == "" and board.port == None:
    plist = list(serial.tools.list_ports.comports())
    for port in plist:
      msg = list(port)
      if msg[0] == "/dev/ttySP0" or msg[2]=='n/a':
        continue  # 行空版 串口异常问题,mac
      msg = list(port)
      vidpid = msg[2].split(" ")
      if len(vidpid) > 2 and vidpid[1] in _vidpid:
        board.boardname = findboard[vidpid[1]]
        board.port = msg[0]
    return      # 不传任何board名字和 端口 自动寻找，找到自动结束
  else:
    pass

# 获取 名字对应的pid vid 列表
def get_vid_pids_by_boardname(boardname, findboard):
  vid_pids = []
  for vid_pid, name in findboard.items():
    if name == boardname:
      vid_pids.append(vid_pid)
  if vid_pids:
    return vid_pids
  else:
    return None