# -*- coding: utf-8 -*-
import time

from pinpong.base import pymata4
from pinpong.extension.globalvar import *
#from pinpong.extension.unihi import *
import ctypes
from ctypes import c_int, c_longlong
import os
import platform

if platform.system() == "Windows":
    # Windows 特定代码
    pass
else:
    # Unix/Linux 特定代码
    import fcntl
import array
import threading

WS2812_INIT = 0
WS2812_SET_PIXEL = 1
WS2812_SET_RANGE = 2
WS2812_SET_BRIGHT = 3
WS2812_SHOW = 4
WS2812_CLEAR = 5
WS2812_GRADUAL = 6
WS2812_SHIFT = 7
WS2812_ROTATE = 8
WS2812_DEINIT = 9
brightness = 255
DHT_INIT   = 1
DHT_MEASURE = 2
DHT_TEMP = 3
DHT_HUMIDITY = 4

DHT11_TYPE   = 11
DHT22_TYPE   = 22
MY_IOCTL_CMD = 0x12345678
IOCTL_IRSEND_CMD = 0x400a410a
IOCTL_IRRECV_CMD = 0xc00a410b

IOCTL_DS18B20_CMD =  0x40044400
IOCTL_GP2Y_CMD = 0x40044700
IOCTL_SR04_CMD = 0x40045301
IOCTL_DHT_CMD  = 0x40044403


STATE_GPIO = 1
STATE_PWM = 16
STATE_ADC = 32
STATE_2812    = 65
STATE_DHT11   = 66
STATE_18B20   = 67
STATE_SR04    = 70
STATE_IR_SEND = 71
STATE_IR_RECV = 72


# Define the parameters to be passed to the ioctl
class dhtIoctlParams(ctypes.Structure):
  _fields_ = [("data", ctypes.c_ubyte * 6)]

class IRIoctlParams(ctypes.Structure):
  _fields_ = [("data", ctypes.c_ubyte * 10)]

class genericIoctlPara(ctypes.Structure):
  _fields_ = [("data", ctypes.c_ubyte * 4)]



class IRRemoteExtension():
  def __init__(self, board=None, pin_obj=None, num=None):
    self.pin_obj  = pin_obj
    self.board = board
    index = self.board.res["pin"]["pinmap"][self.pin_obj.pin]
    board.res["pinReuse"](index, STATE_IR_SEND)
    self.__pin = index - 200
    self.__fd = os.open("/dev/ir_send", os.O_RDWR)
    
  def send(self, value):
    params = IRIoctlParams()
    params.data[0] = self.__pin    # 读取pin 对应的红外数据
    params.data[1] = value >> 24
    params.data[2] = value >> 16
    params.data[3] = value >> 8
    params.data[4] = value
    try:
      ret = fcntl.ioctl(self.__fd, IOCTL_IRSEND_CMD, params)
    except:
      ret = 0
      print("please irsend error!!! please try again!!!")
    return ret

class IRRecvExtension():
  def __init__(self, board=None, pin_obj=None, callback=None):
    self.pin_obj  = pin_obj
    self.board = board
    index = self.board.res["pin"]["pinmap"][self.pin_obj.pin]
    
    board.res["pinReuse"](index, STATE_IR_RECV)
    self.__pin = index - 200
    self.__fd = os.open("/dev/ir_recv", os.O_RDWR)

    # 初始化接收
    initRecv = IRIoctlParams()
    # initRecv.data[0] = 31   # P15
    initRecv.data[0] = self.__pin
    fcntl.ioctl(self.__fd, IOCTL_IRRECV_CMD, initRecv)
  
    self._callback = callback
    self.thread = threading.Thread(target=self.my_function)
    self.thread.daemon = True   # 守护线程
    self.thread.start()
  
  def read(self):
    params = IRIoctlParams()
    # params.data[0] = self.__pin    # 读取pin 对应的红外数据
    params.data[0] = 48   # 非正常引脚代表读取
    try:
      ret = fcntl.ioctl(self.__fd, IOCTL_IRRECV_CMD, params)
    except:
      print("ir recv set error!!!, please try again!!!")
    combined_value = 0
    for i in range(0, 4):
      combined_value |= params.data[i] << (8 * i)
    return combined_value
  
  # 线程执行的代码
  def my_function(self):
    while True:
      data = self.read()
      if data:
        self._callback(data)
      time.sleep(0.2)

class NeoPixelExtension(object):
  def __init__(self, board=None, pin_obj=None, num=None):
    self.pin_obj  = pin_obj
    self.board = board
    self.num = num
    self.__data = [(0,0,0) for i in range(num)]
    #self.board.board.set_pin_mode_neo(self.pin_obj.pin)
    
    if "linux" in self.board.res:
      index = self.board.res["pin"]["pinmap"][self.pin_obj.pin]
      self.__pin = index - 200
      board.res["pinReuse"](index, STATE_2812)  #设置引脚复用模式
      self.__fd = os.open("/dev/ws_2812", os.O_RDWR)
      temp = [self.__pin, WS2812_INIT, self.num, brightness]
      self.__write(temp)
    else:
      time.sleep(0.1)
      self.board.board.neopixel_config(self.pin_obj.pin,self.num)

  def __repr__(self):
    return 'pixel data (%s)' % self.__data

  def __getitem__(self, i):
    return self.__data[i]  # 返回data绑定列表中的第i个元素

  def __setitem__(self, i, v):
    #print(i,v)
    self.__data[i]=v
    self.write(i,v)
    if self.board.boardname == "UNO":
      time.sleep(0.15)
    else:
      pass
      
  def __write(self, temp):
    try:
        os.write(self.__fd, bytearray(temp))
    except:
        print("ws2812 set error,Please try again")
    
  def write(self , index, r, g=None, b=None):
    if isinstance(r,tuple):
      b=r[2]
      g=r[1]
      r=r[0]
    else:
      b = (r>>0) &0xff
      g = (r>>8) &0xff
      r = (r>>16)&0xff
    color = (r<<16) + (g<<8) + b
    if "linux" in self.board.res:
      temp = [self.__pin, WS2812_SET_PIXEL, index, r, g, b, True]
      self.__write(temp)
    else:
      self.board.board.neopixel_write(self.pin_obj.pin, index, color)

  def brightness(self, brightness):
    if "linux" in self.board.res:
      temp = [self.__pin, WS2812_SET_BRIGHT, brightness]
      self.__write(temp)
    else:
      self.board.board.neopixel_set_brightness(self.pin_obj.pin, brightness)

  def rainbow(self , start, end, hsv_start, hsv_end):
    _start = hsv_start*182  # 0-360 remap 0-65535
    _end   = hsv_end*182
    _start_low = _start & 0xFF
    _start_high = (_start >> 8) & 0xFF
    _end_low = _end & 0xFF
    _end_high = (_end >> 8) & 0xFF
    
    if "linux" in self.board.res:
      #temp = [self.__pin, WS2812_GRADUAL, start, end, low_start, high_start, low_end, high_end]
      temp = [self.__pin, WS2812_GRADUAL, start, end, _start_low, _start_high, _end_low, _end_high]
      #temp = [self.__pin, WS2812_GRADUAL, start, end, 254, 255, 255, 255]
      self.__write(temp)
    else:
      self.board.board.neopixel_set_rainbow(self.pin_obj.pin, start, end, hsv_start, hsv_end)

  def shift(self , n):
    if "linux" in self.board.res:
      temp = [self.__pin, WS2812_SHIFT, n]
      self.__write(temp)
    else:
      self.board.board.neopixel_shift(self.pin_obj.pin, n)

  def rotate(self , n):
    if "linux" in self.board.res:
      temp = [self.__pin, WS2812_ROTATE, n]
      self.__write(temp)
    else:
      self.board.board.neopixel_rotate(self.pin_obj.pin, n)

  def range_color(self, start, end, color):
    if "linux" in self.board.res:
      if isinstance(color, int):
        red = (color >> 16) & 0xFF
        green = (color >> 8) & 0xFF
        blue = color & 0xFF
      elif isinstance(color, tuple):
        red = color[0]
        green = color[1]
        blue = color[2] 
      temp = [self.__pin, WS2812_SET_RANGE, start, end, red, green, blue]
      self.__write(temp)
    else:
      if isinstance(color, int):
        self.board.board.neopixel_set_range_color(self.pin_obj.pin, start, end, color)
      elif isinstance(color, tuple):
        self.board.board.neopixel_set_range_color(self.pin_obj.pin, start, end, (color[0]<<16 | color[1]<<8 | color[2]))
        
#  def bar_graph(self, start, end, numerator, denominator):
#    self.board.board.set_bar_graph(self.pin_obj.pin, start, end, numerator, denominator)

  def clear(self):
    if "linux" in self.board.res:
      temp = [self.__pin, WS2812_CLEAR]
      self.__write(temp)
    else:
      self.board.board.neopixel_set_range_color(self.pin_obj.pin, 0, self.num-1, 0)

class DS18B20Extension:
  def __init__(self, board=None, pin_obj=None):
    self.board = board
    self.pin_obj = pin_obj
    if "linux" in self.board.res:
      index = self.board.res["pin"]["pinmap"][self.pin_obj.pin]
      self.__pin = index - 200
      #board.res["pinReuse"](index, STATE_18B20)  #设置引脚复用模式
      board.res["pinReuse"](index, STATE_GPIO)
      self.__fd = os.open("/dev/ds18b20", os.O_RDWR)
    else:
      self.board.board.set_pin_mode_DS18B20(self.pin_obj.pin)
    
  def temp_c(self):
    if "linux" in self.board.res:
      readlen = 4
      params = genericIoctlPara()
      params.data[0] = self.__pin    # 读取pin 对应的红外数据
      params.data[1] = readlen
      try:
        ret = fcntl.ioctl(self.__fd, IOCTL_DS18B20_CMD, params)
      except:
        print("ds18b20 set error!!! please try again!!!")
      temp_decimal = 0.0
      temp_int =  params.data[1] << 8  | params.data[0]
      if temp_int == 65535 or temp_int == 85:
        return 0.0
      if (temp_int & (1 << 15)) != 0:
        temp_decimal = temp_int | ~((1 << 16) - 1)
      else:
        temp_decimal = temp_int
      temp_decimal /= 16.0

      return round(temp_decimal, 2)
    else:
      return self.board.board.ds18b20_read(self.pin_obj.pin)

class DHTExtension:
  def __init__(self,board=None, pin_obj=None, num=0):
    self.flag = False
    self.board = board
    self.pin_obj = pin_obj
    self.key = "dht%d"%num
    self.temp = 0.0
    self._humidity = 0.0
    if "linux" in self.board.res:
      index = self.board.res["pin"]["pinmap"][self.pin_obj.pin]
      self.__pin = index - 200
      board.res["pinReuse"](index, STATE_DHT11)  #设置引脚复用模式
      self.__fd = os.open("/dev/dht", os.O_RDWR)
      if self.key == "dht11":
        self._type = DHT11_TYPE
      else:
        self._type = DHT22_TYPE
      temp = [self.__pin, self._type, DHT_INIT]
      os.write(self.__fd, bytearray(temp))
    else:
      if pin_obj.pin in board.res[self.key]["pininvalid"]:
        raise ValueError(self.key+"is not supported %d pin"%pin_obj.pin, "Pin lists are not supported",board.res[self.key]["pininvalid"])
      self.type = num
      self.board.board.set_pin_mode_dht(self.pin_obj.pin, self.type, differential=.01)
      time.sleep(1.2) #防止用户层读出数据为0
    
  def measure(self):
    if "linux" in self.board.res:
      params = genericIoctlPara()
      params.data[0] = self.__pin
      try:
        ret = fcntl.ioctl(self.__fd, IOCTL_DHT_CMD, params)
      except:
        print("dht set error!!! please try again!!!")
        
      if params.data[0] == 0xff:
        self.__temp = -1
        self.__humidity = -1
        return
      if params.data[0] > 0x80:
        params.data[0] &= 0x7F
        self.__humidity = -1 * (params.data[0] + params.data[1]/100.0)
      else:
        self.__humidity = params.data[0] + params.data[1]/100.0
      
      if params.data[2] > 0x80:
        params.data[2] &= 0x7F
        self.__temp = -1 * (params.data[2] + params.data[3]/100.0)  
      else:
        self.__temp = params.data[2] + params.data[3]/100.0
    else:
      if self.board.res[self.key]["type"] == "dfrobot_firmata":
        self.board.board.dfrobot_dht_read(self.pin_obj.pin, self.type)
      self.value = self.board.board.dht_read(self.pin_obj.pin)

  def temp_c(self):
    if "linux" in self.board.res:
      self.measure()
      return self.__temp
    else:
      if self.board.res[self.key]["type"] == "dfrobot_firmata":
        self.board.board.dfrobot_dht_read(self.pin_obj.pin, self.type)
      return self.board.board.dht_read(self.pin_obj.pin)[1]

  def humidity(self):
    if "linux" in self.board.res:
      self.measure()
      return self.__humidity
    else:
      if self.board.res[self.key]["type"] == "dfrobot_firmata":
        self.board.board.dfrobot_dht_read(self.pin_obj.pin, self.type)
      return self.board.board.dht_read(self.pin_obj.pin)[0]

class SR04_URM10Extension:
  def __init__(self,board=None, trigger_pin_obj=None, echo_pin_obj=None):
    self.board  = board
    self.trigger_pin_obj = trigger_pin_obj
    self.echo_pin_obj = echo_pin_obj
    if "linux" in self.board.res:
      index_t = self.board.res["pin"]["pinmap"][self.trigger_pin_obj.pin]
      index_e = self.board.res["pin"]["pinmap"][self.echo_pin_obj.pin]
      self.__pin_t = index_t - 200
      self.__pin_e = index_e - 200
      board.res["pinReuse"](index_t, STATE_SR04)  #设置引脚复用模式
      board.res["pinReuse"](index_t, STATE_SR04)  #设置引脚复用模式
      self.__fd = os.open("/dev/sr04", os.O_RDWR)
    else:
      if self.board.res["sr04"]["type"] == "dfrobot_firmata":
        self.board.board.dfrobot_set_pin_mode_sonar(self.trigger_pin_obj.pin, self.echo_pin_obj.pin)
      else:
        self.board.board.set_pin_mode_sonar(self.trigger_pin_obj.pin, self.echo_pin_obj.pin)

  def distance_cm(self):
    if "linux" in self.board.res:
      params = genericIoctlPara()
      params.data[0] = self.__pin_t
      params.data[1] = self.__pin_e
      try:
        ret = fcntl.ioctl(self.__fd, IOCTL_SR04_CMD, params)
      except:
        print("sr04 set error!!! please try again!!!")
      distance = params.data[1] *256 + params.data[0]
      if distance >= 500:
        distance = -1
      return distance
    else:
      if self.board.res["sr04"]["type"] == "dfrobot_firmata":
        self.board.board.dfrobot_sonar_read(self.trigger_pin_obj.pin, self.echo_pin_obj.pin)
        time.sleep(0.01)
      return self.board.board.sonar_read(self.trigger_pin_obj.pin)[0]

class GP2Y1010AU0FExtension: #空气质量粉尘传感器 仅unihiker
  def __init__(self, board=None, anapin=None, digpin=None):
    self.board = board
    self.anapin = anapin
    self.digpin = digpin
    self.dust_value = 0
    if "linux" in self.board.res:
      index_g = self.board.res["pin"]["pinmap"][self.digpin]
      index_a = self.board.res["pin"]["pinmap"][self.anapin]
      self.__pin_g = index_g - 200
      self.__pin_a = index_a - 200
      board.res["pinReuse"](index_g, STATE_GPIO)
      board.res["pinReuse"](index_a, STATE_ADC)
      self.__fd = os.open("/dev/gp2y1010au", os.O_RDWR)
      #fd = os.open("/dev/pinpong_config", os.O_RDWR)       # 利用linux 自动close 解决计数问题
      #temp = os.read(fd, 48)
      
  def dust_density(self):
    self.__calc_value()
    return round(self.dust_value,2)
  
  def __calc_value(self):
    if "linux" in self.board.res:
      params = genericIoctlPara()
      params.data[0] = self.__pin_g
      params.data[1] = self.__pin_a
      try:
        ret = fcntl.ioctl(self.__fd, IOCTL_GP2Y_CMD, params)
      except:
        print("gp2y set error!!! please try again!!!")
        self.dust_value = 0.0
        return
      raw_value = params.data[1] *256 + params.data[0]
      calc_value = raw_value * (3.3 / 4095.0)
      if calc_value >= 0.6:
        self.dust_value = 0.17 * calc_value - 0.1
      else:
        self.dust_value = 0.0
    else:
      raw_value = self.board.board.gp2y1010au0f_read(self.anapin, self.digpin)
      calc_value = raw_value * (6.0 / 4095.0)
      self.dust_value = 0.17 * calc_value - 0.1
      
class AudioAnalyzerExtension:
  def __init__(self, board=None, strobe_pin=None, RST_pin=None, DC_pin=None):
    
    self.board = board
    self.strobe_pin = strobe_pin
    self.RST_pin = RST_pin
    self.DC_pin = DC_pin
    
    self.DC_pin,self.DC_apin = board.res["get_pin"](board,DC_pin)
    self.RST_pin,self.RST_apin = board.res["get_pin"](board,RST_pin)
    self.strobe_pin,self.strobe_apin = board.res["get_pin"](board,strobe_pin)
    
    self.board.board.set_audio_init(self.strobe_pin, self.RST_pin, self.DC_pin)
    
  def read_freq(self):
    return self.board.board.audio_analyzer_read_freq()

class HX711Extension:
  def __init__(self, board, dout_pin, sck_pin, scale = None):
    
    self.board = board
    self.dout_pin = dout_pin
    self.sck_pin = sck_pin
    self.dout_pin,self.dout_apin = board.res["get_pin"](board,dout_pin)
    self.sck_pin,self.sck_apin = board.res["get_pin"](board,sck_pin)
    self.scale = scale
    
    if "linux" in self.board.res:
      print("The linux board does not support this sensor!!!")
      exit()
    else:
      self.board.board.set_hx711_init(self.dout_pin, self.sck_pin, self.scale)
    
  def read_weight(self):
    return self.board.board.hx711_read_weight(self.dout_pin)
    

