import time
from pinpong.board import gboard,I2C

class I2cMotor:
  I2C_ADDR = 0x10  
  _first = False

  def __init__(self, board = None, i2c_addr=I2C_ADDR, bus_num=0):
    if isinstance(board, int):
      i2c_addr = board
      board = gboard 

    self.board = board
    self.i2c_addr = i2c_addr
    self.i2c = I2C(bus_num)
    self.buf = []
    self._first = True
    #print("电机I2C通信初始化完成")



  def _send_command(self, head = None, data = None):
    if head == None:
      self.i2c.writeto(self.i2c_addr,data)
      #print("there's no head")
      #print(data)
    else:
      self.i2c.writeto(self.i2c_addr,head)
      self.i2c.writeto(self.i2c_addr,data)
      #print('there is a head:',head)
      #print(data)


  def _hardwareReset(self):
    if self._first == False:
        return
    #motor
    self._send_command(data=[0x00,0,0,0,0])
    #rgb
    self._send_command(data=[0x0B,8,8])
    self._first = False


  def motorStop(self,index):
    self._hardwareReset()
    self.motorRun(index=index,direction=1,speed=0)


  def motorRun(self,index=3, direction=1, speed=0):
    self._hardwareReset()
    speed=abs(speed)
    if speed >= 255 :
        speed = 255
    if index>3 and index<1:
        return
    if index == 1:
        self._send_command(data =[0x00, direction, speed])

    if index == 2:
        self._send_command(data =[0x02, direction, speed])

    if index == 3:
        self._send_command(data =[0x00, direction, speed, direction, speed])



  def setRGB(self,flag,color):
    self._hardwareReset()
    if flag == 1:
        self._send_command(data =[0x0B, color])
    if flag == 2:
        self._send_command(data =[0x0C, color])
    if flag == 3:
        self._send_command(data =[0x0B, color, color])

