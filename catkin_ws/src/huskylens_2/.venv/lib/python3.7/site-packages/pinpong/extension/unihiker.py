# -*- coding: utf-8 -*-
import platform
import os
import time
import math
import numpy as np
from pinpong.extension.globalvar import *
from pinpong.board import Pin
from pinpong.extension.unihi import *


class GD32Sensor_mode:
    def __init__(self):
        if not os.path.exists('/opt/unihiker/Version'):
            print("This feature is only available for unihiker!!!")
            exit()
        pinpong_count_init()      
        get_pin_mode()
  
class GD32Sensor_buttonA:
    def __init__(self, board=None):
        self.pin = 219
        self._pin = 27 #Pin(Pin.P27)
        pin_default_state[19] = STATE_GPIO
        #pinReuse(self.pin, STATE_GPIO)
        self.export_path = "/sys/class/gpio/export"
        self.value_path = "/sys/class/gpio/gpio"+str(self.pin)+'/value'
        self.direction_path = "/sys/class/gpio/gpio"+str(self.pin)+'/direction'
        if not os.path.exists("/sys/class/gpio/gpio"+str(self.pin)):
            os.system('echo '+str(self.pin)+' > '+self.export_path)
            #print('echo '+str(self.pin)+' > '+self.export_path)
        os.system('echo in > ' + self.direction_path)
        
    def is_pressed(self):
        fd = os.open(self.value_path, os.O_RDONLY)
        data = os.read(fd, 2).decode('utf-8')
        os.close(fd)
        data = int(data)
        time.sleep(0.05)
        if data == 1:
            return 0
        else:
            return 1

    def irq(self, trigger=None, handler=None):
        self.old_value = self.value()
        self.trigger = trigger
        self.handler = handler
        thread = threading.Thread(target=self.my_function)
        thread.daemon = True   # 守护线程
        thread.start()

    def value(self):
        return 1 if self.is_pressed() else 0
    
    # 线程执行的代码
    def my_function(self):
      while True:
        a_value = self.value()
        #上升沿
        if self.trigger == Pin.IRQ_RISING:
          if self.old_value == 0 and a_value == 1:
            self.handler(self._pin)
            #print("rasing ")
        #下降沿
        elif self.trigger == Pin.IRQ_FALLING:
          if self.old_value == 1 and a_value == 0:
            self.handler(self._pin)
            #print("failing ")
        elif self.trigger == Pin.IRQ_FALLING+Pin.IRQ_RISING:
          if self.old_value == 1 and a_value == 0:
            self.handler(self._pin)
            #print("both failing ")
          if self.old_value == 0 and a_value == 1:
            self.handler(self._pin)
            #print("both rasing ")
        self.old_value = a_value
        time.sleep(0.1)


class GD32Sensor_buttonB:
    def __init__(self, board=None):
        self.pin = 200
        self._pin = 28
        pin_default_state[0] = STATE_GPIO
        #pinReuse(self.pin, STATE_GPIO)
        self.export_path = "/sys/class/gpio/export"
        self.value_path = "/sys/class/gpio/gpio"+str(self.pin)+'/value'
        self.direction_path = "/sys/class/gpio/gpio"+str(self.pin)+'/direction'
        if not os.path.exists("/sys/class/gpio/gpio"+str(self.pin)):
            os.system('echo '+str(self.pin)+' > '+self.export_path)
            #print('echo '+str(self.pin)+' > '+self.export_path)
        os.system('echo in > ' + self.direction_path)

    def is_pressed(self):
        fd = os.open(self.value_path, os.O_RDONLY)
        data = os.read(fd, 2).decode('utf-8')
        os.close(fd)
        data = int(data)
        time.sleep(0.05)
        if data == 1:
            return 0
        else:
            return 1

    def irq(self, trigger=None, handler=None):
        self.old_value = self.value()
        self.trigger = trigger
        self.handler = handler
        thread = threading.Thread(target=self.my_function)
        thread.daemon = True   # 守护线程
        thread.start()

    def value(self):
        return 1 if self.is_pressed() else 0
        
    def my_function(self):
      while True:
        b_value = self.value()
        #上升沿
        if self.trigger == Pin.IRQ_RISING:
          if self.old_value == 0 and b_value == 1:
            self.handler(self._pin)
            #print("rasing ")
        #下降沿
        elif self.trigger == Pin.IRQ_FALLING:
          if self.old_value == 1 and b_value == 0:
            self.handler(self._pin)
            #print("failing ")
        elif self.trigger == Pin.IRQ_FALLING+Pin.IRQ_RISING:
          if self.old_value == 1 and b_value == 0:
            self.handler(self._pin)
            #print("both failing ")
          if self.old_value == 0 and b_value == 1:
            self.handler(self._pin)
            #print("both rasing ")
        self.old_value = b_value
        time.sleep(0.1)


class GD32Sensor_light:
    def __init__(self, board=None):
        pin_default_state[1] = STATE_ADC
        #pinReuse(201, STATE_ADC)

    def read_and_average(self, num_reads=5):
      values = []
      for _ in range(num_reads):
        fd = os.open("/sys/bus/iio/devices/iio:device2/in_voltage0_raw", os.O_RDONLY)
        data = os.read(fd, 4).decode('utf-8')
        os.close(fd)
        value = int(data.strip())  # 假设数据为整数字符串，去除多余空白字符
        values.append(value)

      # 移除最大值和最小值
      values.remove(max(values))
      values.remove(min(values))
      average = int(np.mean(values))
      return average
    
    def read(self):   
        average_value = self.read_and_average()
        if average_value < 150:
          return 4095
        if average_value > 4080:
          return 0
        average_value = 4095 - average_value
        return int(average_value)
        
class GD32Sensor_acc:
    def __init__(self, board=None):
        self.__fd = os.open("/dev/icm20689", os.O_RDWR)
        self._ax = 0
        self._ay = 0
        self._az = 0
        
    def get_alldata(self):
        _axcounts = 0
        _aycounts = 0
        _azcounts = 0
        tX = [-1, 0, 0]
        tY = [0, -1, 0]
        tZ = [0, 0, -1]
        _accelScale = 9.8070 *16.0 / 32767.5
        _axb = 0
        _axs = 1.0
        _ayb = 0
        _ays = 1.0
        _azb = 0
        _azs = 1.0
        _buffer = os.read(self.__fd, 15)
        if _buffer[0] == 2:
          _axcounts = (int(_buffer[1] << 8)) | _buffer[2]
          if _axcounts & 0x8000:
            _axcounts = -((1 << 16) - _axcounts)
          _aycounts = (int(_buffer[3] << 8)) | _buffer[4]
          if _aycounts & 0x8000:
            _aycounts = -((1 << 16) - _aycounts)
          _azcounts = (int(_buffer[5] << 8)) | _buffer[6]
          if _azcounts & 0x8000:
            _azcounts = -((1 << 16) - _azcounts)
          self._ax = ((tX[0] * _axcounts + tX[1] * _aycounts + tX[2] * _azcounts) * _accelScale - _axb) * _axs / 10.0
          self._ay = ((tY[0] * _axcounts + tY[1] * _aycounts + tY[2] * _azcounts) * _accelScale - _ayb) * _ays / 10.0
          self._az = ((tZ[0] * _axcounts + tZ[1] * _aycounts + tZ[2] * _azcounts) * _accelScale - _azb) * _azs / 10.0
        else:
          if(_buffer[1]&0x80) == 0x80:
            self._ax = ((_buffer[1]&0x7f)*256 + _buffer[2]) / -2048.0
          else:
            self._ax = ((_buffer[1]&0x7f)*256 + _buffer[2]) / 2048.0
          if(_buffer[3]&0x80) == 0x80:
            self._ay = ((_buffer[3]&0x7f)*256 + _buffer[4]) / -2048.0
          else:
            self._ay = ((_buffer[3]&0x7f)*256 + _buffer[4]) / 2048.0
          if(_buffer[5]&0x80) == 0x80:
            self._az = ((_buffer[5]&0x7f)*256 + _buffer[6]) / 2048.0
          else:
            self._az = ((_buffer[5]&0x7f)*256 + _buffer[6]) / -2048.0
            
    def get_x(self):
      self.get_alldata()
      return round(self._ax, 2)

    def get_y(self):
      self.get_alldata()
      return round(self._ay, 2)

    def get_z(self):
      self.get_alldata()
      return round(self._az, 2)
      
    def get_strength(self):
      self.get_alldata()
      return round(math.sqrt(math.pow(self._ax ,2) + math.pow(self._ay ,2) + math.pow(self._az ,2)), 2 )

class GD32Sensor_gyro:
    def __init__(self, board=None):
        self.__fd = os.open("/dev/icm20689", os.O_RDWR)
        self._gx = 0
        self._gy = 0
        self._gz = 0

    def get_alldata(self):
        _gxcounts = 0
        _gycounts = 0
        _gzcounts = 0
        tX = [1, 0, 0]
        tY = [0, 1, 0]
        tZ = [0, 0, 1]
        _gyroScale = 2000.0 / 32767.5 * (3.14159265359 / 180.0)
        _qmi_gyroScale = (3.14159265359 / 180.0)
        _gxb = 0
        _gyb = 0
        _gzb = 0
        _buffer = os.read(self.__fd, 15)
        
        if _buffer[0] == 2:
          _gxcounts = (_buffer[9] << 8) | _buffer[10]
          if _gxcounts & 0x8000:
              _gxcounts = -((1 << 16) - _gxcounts)
          _gycounts = (_buffer[11] << 8) | _buffer[12]
          if _gycounts & 0x8000:
              _gycounts = -((1 << 16) - _gycounts)
          _gzcounts = (_buffer[13] << 8) | _buffer[14]
          if _gzcounts & 0x8000:
              _gzcounts = -((1 << 16) - _gzcounts)
          self._gx = (tX[0] * _gxcounts + tX[1] * _gycounts + tX[2] * _gzcounts) * _gyroScale - _gxb
          self._gy = (tY[0] * _gxcounts + tY[1] * _gycounts + tY[2] * _gzcounts) * _gyroScale - _gyb
          self._gz = (tZ[0] * _gxcounts + tZ[1] * _gycounts + tZ[2] * _gzcounts) * _gyroScale - _gzb
        else:
          if(_buffer[7]&0x80) == 0x80:
            self._gx = ((_buffer[7]&0x7f)*256 + _buffer[8]) / -32.0 * _qmi_gyroScale
          else:
            self._gx = ((_buffer[7]&0x7f)*256 + _buffer[8]) / 32.0 * _qmi_gyroScale
          if(_buffer[9]&0x80) == 0x80:
            self._gy = ((_buffer[9]&0x7f)*256 + _buffer[10]) / -32.0 * _qmi_gyroScale
          else:
            self._gy = ((_buffer[9]&0x7f)*256 + _buffer[10]) / 32.0 * _qmi_gyroScale
          if(_buffer[11]&0x80) == 0x80:
            self._gz = ((_buffer[11]&0x7f)*256 + _buffer[12]) / -32.0 * _qmi_gyroScale
          else:
            self._gz = ((_buffer[11]&0x7f)*256 + _buffer[12]) / 32.0 * _qmi_gyroScale
          
    def get_x(self):
      self.get_alldata()        
      return round(self._gx, 2)

    def get_y(self):
      self.get_alldata()        
      return round(self._gy, 2)

    def get_z(self):
      self.get_alldata()        
      return round(self._gz, 2)


class GD32_buzz:
    DADADADUM = 0
    ENTERTAINER = 1
    PRELUDE = 2
    ODE = 3
    NYAN = 4
    RINGTONE = 5
    FUNK = 6
    BLUES = 7
    BIRTHDAY = 8
    WEDDING = 9
    FUNERAL = 10
    PUNCHLINE = 11
    BADDY = 12
    CHASE = 13
    BA_DING = 14
    WAWAWAWAA = 15
    JUMP_UP = 16
    JUMP_DOWN = 17
    POWER_UP = 18
    POWER_DOWN = 19

    Once = 1
    Forever = 2
    OnceInBackground = 4
    ForeverInBackground = 8

    BEAT_1 = 4
    BEAT_1_2 = 2
    BEAT_1_4 = 1
    BEAT_3_4 = 3
    BEAT_3_2 = 6
    BEAT_2 = 8
    BEAT_3 = 12
    BEAT_4 = 16
    
    TYPE_MUSIC = 1
    TYPE_NOTE = 2
    TYPE_SET_MODE = 3
    TYPE_SET_PIN = 4
    TYPE_STOP = 5
    
    music_map = {
      "C3": 131,
      "D3": 147,
      "E3": 165,
      "F3": 175,
      "G3": 196,
      "A3": 220,
      "B3": 247,
      "C4": 262,
      "D4": 294,
      "E4": 330,
      "F4": 349,
      "G4": 392,
      "A4": 440,
      "B4": 494,
      "C5": 523,
      "D5": 587,
      "E5": 659,
      "F5": 698,
      "G5": 784,
      "A5": 880,
      "B5": 988,
      "C#3": 139,
      "D#3": 156,
      "F#3": 185,
      "G#3": 208,
      "A#3": 233,
      "C#4": 277,
      "D#4": 311,
      "F#4": 370,
      "G#4": 415,
      "A#4": 466,
      "C#5": 554,
      "D#5": 622,
      "F#5": 740,
      "G#5": 831,
      "A#5": 932
       }

    def __init__(self, board=None):
        pinReuse(208, STATE_BZZER)
        self.__fd = os.open("/dev/buzzer", os.O_RDWR)
        self.first_flag = True
        self._stop = False

    def play(self, index, options):
        temp = [self.TYPE_MUSIC, index, options]
        os.write(self.__fd, bytearray(temp))
        if options == self.Once or options == self.Forever:
            while True:
              try:
                flag = os.read(self.__fd, 1)
                if flag[0] == 0:
                  break
              except:
                pass
              time.sleep(0.5)
        
    def pitch(self, freq, beat=None):
        _freq_low = freq & 0xFF
        _freq_high = (freq >> 8) & 0xFF
        
        if beat == None:
          _beat_low = 4
          _beat_high = 0
          self.mode = self.OnceInBackground
        else:
          _beat_low = beat & 0xFF
          _beat_high = (beat >> 8) & 0xFF
          self.mode = self.Once
        
        temp = [self.TYPE_NOTE, _freq_high, _freq_low, _beat_high, _beat_low, self.mode]
        os.write(self.__fd, bytearray(temp))
        
        if self.mode == self.Once:
          while True:
            flag = os.read(self.__fd, 1)
            if flag[0] == 0:
              break
            time.sleep(0.5)
        
    def set_tempo(self, ticks, bpm):
        _ticks_low = ticks & 0xFF
        _ticks_high = (ticks >> 8) & 0xFF
        _bpm_low = bpm & 0xFF
        _bpm_high = (bpm >> 8) & 0xFF
        
        temp = [self.TYPE_SET_MODE, _ticks_high, _ticks_low, _bpm_high, _bpm_low]
        os.write(self.__fd, bytearray(temp))

    def stop(self):
        temp = [self.TYPE_STOP]
        os.write(self.__fd, bytearray(temp))

    def redirect(self, pin):
        self.__pin = uni_res["pin"]["pinmap"][pin] - 200
        temp = [self.TYPE_SET_PIN, self.__pin]
        os.write(self.__fd, bytearray(temp))
        
    def __del__(self):
        self.stop()
      

mode     = GD32Sensor_mode()
button_a = GD32Sensor_buttonA()  # 兼容micropython方法
button_b = GD32Sensor_buttonB()
light = GD32Sensor_light()
accelerometer = GD32Sensor_acc()
gyroscope = GD32Sensor_gyro()
buzzer = GD32_buzz()
