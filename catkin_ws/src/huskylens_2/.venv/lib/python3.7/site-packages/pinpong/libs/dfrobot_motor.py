import time
from pinpong.board import gboard,I2C,Pin
import math

class MOTOR():
    M1                             = 0
    M2                             = 1
    ALL                            = 2
    CW                             = 0
    CCW                            = 1
    ERROR_COUNT = 0x05
    def __init__(self, board = None, i2c_addr = 0x10, bus_num=0):
        if isinstance(board, int):
            i2c_addr = board
            board = gboard
        elif board is None:
            board = gboard
        self._connect=0
        self.i2c_addr = i2c_addr
        self._i2c = I2C(bus_num)
    
    def motor_run(self, index, direction, speed):
        Speed = abs(speed)
        if Speed > 255:
            Speed = 255
        buf = [0, direction, Speed]
        if index > 3 or index < 0:
            return
        if index == self.M2:
            buf[0] = 0x00
            self.i2cWriteBuf(0x10, buf)
        elif index == self.M1:
            buf[0] = 0x02
            self.i2cWriteBuf(0x10, buf)
        elif index == self.ALL:
            buf[0] = 0x00
            self.i2cWriteBuf(0x10, buf)
            buf[0] = 0x02
            self.i2cWriteBuf(0x10, buf)
    
    def motor_stop(self, index):
        self.motor_run(index, self.CW, 0)
    
    def _error_handling(self, lens=0):
        result = [0] * lens
        self._connect += 1
        print("motor iic communication faild, please wait")
        time.sleep(1)  
        return result

    def read_to_addr(self, lens):
        self._connect = 0
        while True:
            try:
                result = self._i2c.readfrom(self.i2c_addr, lens)
                return result
            except:
                result = self._error_handling(lens)
            if self._connect > self.ERROR_COUNT:
                raise ValueError("Please check the motor connection or Reconnection sensor!!!")
    
    def i2cWriteBuf(self, addr, buf):
        self._connect = 0
        while True:
            try:
                self._i2c.writeto(addr, buf)
                return
            except:
                self._error_handling()
            if self._connect > self.ERROR_COUNT:
                raise ValueError("Please check the motor connection or Reconnection sensor!!!")