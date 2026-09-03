# -*- coding: utf-8 -*-
import time
from pinpong.board import Board, UART

Board("UNIHIKER").begin()  #初始化，选择板型，不输入板型则进行自动识别
#硬串口1 P0-RX P3-TX
#uart1 = UART()
uart1 = UART(None,"/dev/ttySP0")
#初始化串口 baud_rate 波特率, bits 数据位数(8/9) parity奇偶校验(0 无校验/1 奇校验/2 偶校验) stop 停止位(1/2)
uart1.init(baud_rate = 230400, bits=8, parity=0, stop = 1) 
#uart1.init() #默认波特率为9600
buf = [0x41, 0x42, 0x43, 0x44, 0x45, 0x46, 0x47]
#关闭硬串口1
#uart1.deinit() 
#返回可读取的字节数
#uart1.any() 
#串口写,buf为数列
#uart1.write(buf)
#读取串口字符,返回None或者数列
#uart1.read(n)
#读一行，以换行符结尾。读取行或 None 超时。(到换行键(0xa)结束，无则返回None)
#buf = uart1.readline()
#将字节读入buf。如果 nbytes 指定，则最多读取多个字节。否则，最多读取 len(buf) 字节数。
#uart1.readinto(buf, nbytes)
while True:
    uart1.write(buf)
 
    #读一行，以换行符结尾。读取行或 None 超时。(到换行键(0xa)结束，无则返回None)    
    '''line = uart1.readline()
    if line:
        print(f"Received line: {line.decode().strip()}")  # 使用 strip() 方法去除换行符和空白
    '''
    
    #返回可读取的字节数    
    '''bytes_waiting = uart1.any() 
    if bytes_waiting > 0:
        # 读取数据
        data = uart1.read(bytes_waiting)
        print(f"Received data: {data}")
    '''
    
    #将字节读入buf。如果 nbytes 指定，则最多读取多个字节。否则，最多读取 len(buf) 字节数。
    '''buf1 = [0]*10
    uart1.readinto(buf1)
    print(buf1)
    '''
    #读取一个
    #print(uart1.readchar())
    #读取所有
    #print(uart1.readall())
    time.sleep(1)
