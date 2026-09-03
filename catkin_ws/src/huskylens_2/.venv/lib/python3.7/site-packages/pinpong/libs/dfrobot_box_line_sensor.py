# -*- coding:utf-8 -*-
"""!
  改i2c接口的巡线传感器的库
"""
from __future__ import print_function

import time
import os
from pinpong.board import gboard, I2C


        
class Box_LineSensor():
    ## Default I2C address of AHT20 sensor
    LS_I2C_ADDR = 0x30
    ## Init command
    CMD_INIT = 0xBE
    ## The first parameter of init command: 0x08
    CMD_INIT_PARAMS_1ST = 0x08
    ## The second parameter of init command: 0x00

    I2C_PID_H    		= 0x00
    I2C_PID_l    		= 0x01
    I2C_VID_H    		= 0x02
    I2C_VID_L    		= 0x03
    I2C_DEV_ADDR_H 	= 0x04
    I2C_DEV_ADDR_L 	= 0x05
    I2C_VERSION_H   = 0x06
    I2C_VERSION_L   = 0x07
    I2C_B_VAL  			= 0x08   # adc 是否采集到黑线
    I2C_L2_ADC 			= 0x09	 # L2  Value
    I2C_L1_ADC 			= 0x0A	 # L1  Value
    I2C_M_ADC  			= 0x0B	 # M   Value
    I2C_R1_ADC 			= 0x0C	 # R1  Value
    I2C_R2_ADC 			= 0x0D	 # R2  Value
    I2C_L2_BLACK 		= 0x0E	 # L2  Value
    I2C_L1_BLACK  	= 0x0F	 # L1  Value
    I2C_M_BLACK 		= 0x10	 # M  Value
    I2C_R1_BLACK 		= 0x11	 # R1  Value
    I2C_R2_BLACK 		= 0x12	 # R2  Value
    ERROR_COUNT     = 0X05
    def __init__(self, board=None, i2c_addr=LS_I2C_ADDR, bus_num=0):
        if isinstance(board, int):
            i2c_addr = board
            board = gboard
        elif board is None:
            board = gboard
        self._i2c_addr = i2c_addr
        self._i2c = I2C(bus_num)
        self._connect = 0
        
    def begin(self):
        pid = self.get_pid()
        if pid == 0x2ff:
            return True
        else:
            return False

    def get_pid(self):
        rslt = self._read_regs(self.I2C_PID_H, 2)
        return rslt[0]<<8 | rslt[1]
        
    def get_vid(self):
        rslt = self._read_regs(self.I2C_VID_H, 2)
        return rslt[0]<<8 | rslt[1]
    
    def get_version(self):
        rslt = self._read_regs(self.I2C_VERSION_H, 2)
        return rslt[0]<<8 | rslt[1]
    
    def get_device_addr(self):
        rslt = self._read_regs(self.I2C_DEV_ADDR_L, 1)
        return rslt[0]
    
    def set_device_addr(self, addr):
        rslt = [0]*1
        rslt[0] = addr
        self._write_regs(self.I2C_DEV_ADDR_L, rslt)
        time.sleep(0.1)
        return True
    
    def get_adc(self, number):
        rslt = self._read_regs(self.I2C_B_VAL, 1)
        return (rslt[0] >> number)&0x01
        
    def get_adc_all(self):
        rslt = self._read_regs(self.I2C_B_VAL, 1)
        binary_str = bin(rslt[0])[2:].zfill(5)
        reversed_binary_str = binary_str[::-1]
        return reversed_binary_str
        
    def get_adc_value(self):
        rslt = self._read_regs(self.I2C_L2_ADC, 5)
        return rslt
        
    def get_threshod_value(self):
        rslt = self._read_regs(self.I2C_L2_BLACK, 5)
        return rslt
    
    def set_threshod_number(self, number, value):
        rslt = [0]*1
        rslt[0] = value
        if number < 0 or number > 5 or value > 255 or value < 0:
          return False
        self._write_regs(self.I2C_L2_BLACK+number, rslt)
        time.sleep(0.1)
        return True
        
    def _error_handling(self, lens=0):
        result = [0] * lens
        self._connect += 1    
        print("box line Sensor iic communication faild, please wait")
        time.sleep(0.5)
        return result
    
    def _read_regs(self, reg_addr, lens):
        self._connect = 0
        while True:
            try:
                result = self._i2c.readfrom_mem(self._i2c_addr, reg_addr, lens)
                return result
            except:
                result = self._error_handling(lens)
            if self._connect > self.ERROR_COUNT:
                raise ValueError("Please check the box_line connection or Reconnection sensor!!!")  

    def _write_regs(self, reg_addr, value):
        self._connect = 0
        while True:
            try:
                self._i2c.writeto_mem(self._i2c_addr, reg_addr, value)
                break
            except:
                self._error_handling()
            if self._connect > self.ERROR_COUNT:
                raise ValueError("Please check the box_line connection or Reconnection sensor!!!")
