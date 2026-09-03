# -*- coding: utf-8 -*-
from pinpong.board import gboard,I2C
import time

class MLX90614:
  MLX90614_IIC_ADDR   = (0x5A)
  MLX90614_TA         = (0x06)
  MLX90614_TOBJ1      = (0x07)
  ERROR_COUNT = 0x05
  def __init__(self, board=None, i2c_addr=MLX90614_IIC_ADDR,bus_num=0):
    if isinstance(board, int):
      i2c_addr = board
      board = gboard
    elif board is None:
      board = gboard
    self._connect=0
    self.board = board
    self.i2c_addr = i2c_addr
    self.i2c = I2C(bus_num)

  def obj_temp_c(self):
    return round(self.__temperature(self.MLX90614_TOBJ1),2)    #Get celsius temperature of the object 

  def env_temp_c(self):
    return round(self.__temperature(self.MLX90614_TA),2)    #Get celsius temperature of the ambient

  def obj_temp_f(self):
    return round((self.__temperature(self.MLX90614_TOBJ1) * 9 / 5) + 32,2)  #Get fahrenheit temperature of the object

  def env_temp_f(self):
    return round((self.__temperature(self.MLX90614_TA) * 9 / 5) + 32, 2) #Get fahrenheit temperature of the ambient

  def __temperature(self,reg):
    temp = self.__get_reg(reg)*0.02-273.15             #Temperature conversion
    return temp

  def _error_handling(self, lens=0):
    result = [0] * lens
    self._connect += 1
    print("mlx90614 iic communication faild, please wait")
    time.sleep(0.5)
    return result

  def __get_reg(self,reg):
    self._connect = 0
    while True:
      try:
        data = self.i2c.readfrom_mem_restart_transmission(self.i2c_addr, reg, 3)
        result = (data[1]<<8) | data[0]
        return result  
      except:
        data = self._error_handling(3)
      if self._connect > self.ERROR_COUNT:
        raise ValueError("Please check the mlx90614 connection or Reconnection sensor!!!")
    
