# -*- coding: utf-8 -*- 
import serial
import platform
import sys
import time
import os
import ctypes
from ctypes import c_int
import platform

if platform.system() == "Windows":
    # Windows 特定代码
    pass
else:
    # Unix/Linux 特定代码
    import fcntl
import threading
import subprocess
from pinpong.extension.globalvar import *
from pinpong.base.comm import *
#from pinpong.base.config import *

STATE_NONE = 0
STATE_GPIO = 1
STATE_IIC = 2
STATE_SPI = 4
STATE_UART = 8
STATE_PWM = 16
STATE_ADC = 32
STATE_SPECIAL = 64
STATE_2812    = 65
STATE_DHT11   = 66
STATE_18B20   = 67
STATE_BUZZ    = 68
STATE_SR04    = 69
STATE_IR_SEND = 70
STATE_IR_RECV = 71
STATE_20689= 72
STATE_RESERVE = 255


pin_default_state = [STATE_GPIO,    STATE_ADC,     STATE_GPIO,    STATE_GPIO,    STATE_GPIO,    STATE_GPIO,    STATE_GPIO,    STATE_GPIO,
                     STATE_BUZZ,    STATE_GPIO,    STATE_GPIO,    STATE_GPIO,    STATE_GPIO,    STATE_GPIO,    STATE_GPIO,    STATE_GPIO,
                     STATE_GPIO,    STATE_GPIO,    STATE_RESERVE, STATE_GPIO,    STATE_GPIO,    STATE_GPIO,    STATE_20689,   STATE_20689,
                     STATE_20689,   STATE_GPIO,    STATE_IIC,     STATE_IIC,     STATE_20689,   STATE_GPIO,    STATE_GPIO,    STATE_GPIO,
                     STATE_RESERVE, STATE_RESERVE, STATE_RESERVE, STATE_RESERVE, STATE_RESERVE, STATE_RESERVE, STATE_RESERVE, STATE_RESERVE,
                     STATE_RESERVE, STATE_RESERVE, STATE_RESERVE, STATE_RESERVE, STATE_RESERVE, STATE_GPIO,    STATE_GPIO,    STATE_GPIO]

pin_redundancy_state = [STATE_GPIO,    STATE_ADC,     STATE_GPIO,    STATE_GPIO,    STATE_GPIO,    STATE_GPIO,    STATE_GPIO,    STATE_GPIO,
                     STATE_BUZZ,    STATE_GPIO,    STATE_GPIO,    STATE_GPIO,    STATE_GPIO,    STATE_GPIO,    STATE_GPIO,    STATE_GPIO,
                     STATE_GPIO,    STATE_GPIO,    STATE_RESERVE, STATE_GPIO,    STATE_GPIO,    STATE_GPIO,    STATE_20689,   STATE_20689,
                     STATE_20689,   STATE_GPIO,    STATE_IIC,     STATE_IIC,     STATE_20689,   STATE_GPIO,    STATE_GPIO,    STATE_GPIO,
                     STATE_RESERVE, STATE_RESERVE, STATE_RESERVE, STATE_RESERVE, STATE_RESERVE, STATE_RESERVE, STATE_RESERVE, STATE_RESERVE,
                     STATE_RESERVE, STATE_RESERVE, STATE_RESERVE, STATE_RESERVE, STATE_RESERVE, STATE_GPIO,    STATE_GPIO,    STATE_GPIO]

uni_res = {
    "i2c" : {
        "busnum" : [4],
        "class" : "LinuxI2C",
        },
    "spi" : {
        "busnum" : [(3,0), (4,0)],
        "class" : "LinuxSPI"
        },
    "uart" : {
        "busnum" : ["/dev/ttySP0"],
        "class" : "TTYUART", 
        "pinnum" : [202,203]
        },
    "pin" : {
        "pinnum" : [0  ,1  ,2  ,3  ,4  ,5  ,6  ,7  ,8  ,9  ,10 ,11 ,12 ,13 ,14 ,15 ,16 ,17, 18 ,19 ,20 ,21 ,22 ,23 ,24 ,25 ,26 ,27 ,28 ,29],
        "pinmap" : [203,205,207,202,204,246,245,247,221,220,206,214,213,229,230,231,225,240,240,226,227,217,216,211,212,215,208,219,200,201],
        "class" : "SYSFSPin",
        "export_path" : "/sys/class/gpio/export",
        "value_path" : "/sys/class/gpio/gpio"
        }, 
    "adc" : {
        "pinadc" : [0  ,1  ,2  ,3  ,4  ,10 ,21 ,22 ,29],
        "pinnum" : [203,205,207,202,204,206,217,216,201],
        "pinmap" : [4  ,6  ,8  ,3  ,5  ,7  ,10 ,9  ,2],
        "class" : "LinuxADC",
        "value_path" : "/sys/bus/iio/devices/iio:device",
        },
    "pwm" : {
        "pinpwm" : [0,2,3,8,9,10,16,20,21,22,23,26],
        #"pinmap" : [203,207,202,204,221,220,225,227,217,216,211],
        "pinmap" : [203,207,202,221,220,206,225,227,217,216,211,208],
        "class" : "SYSFSPWM",
        "pwmconfig" : {203:{"channel":"3"},  202:{"channel":2},    207:{"channel":"7"}, 
        227:{"channel":"27"}, 217:{"channel":"17"}, 216:{"channel":"16"} , 
        211:{"channel":"11"}, 220:{"channel":"20"}, 221:{"channel":"21"} , 
        225:{"channel":"25"}, 206:{"channel":"6"} , 208:{"channel":"8"}},
        "export_path" : "/sys/class/pwm/pwmchip2/export",
        "comm_path" : "/sys/class/pwm/pwmchip2/pwm"
        },
    "dht11" : {
       
        },
    "dht22" : {
       
        },
    "servo" : {
        "type" : "firmata",
        "class" : "SYSFSServo",
        "pininvalid" : []
        },
    "irrecv" : {
       
        },
    "irremote" : {
        
        },        
    "tone" : {
        "class" : "LinuxTone" ,
        "pininvalid" : []
        },
    "linux" : {
        "type" : "linux"
        },
  }


COUNT_PATH  = '/dev/pinpong_count'
CONFIG_PATH = '/dev/pinpong_config'

#  利用linux 自动close 解决计数问题
#  所有 调用pinpong库的时候必定初始化， 结束例程时，linux自动close
def pinpong_count_init():
  count = 0
  # 测试pinpong 是否准备好
  if False == get_pinpong_state(COUNT_PATH):
    print("pinpong wasn't ready !!!")
    return -1
  print("pinpong has been loaded !!!")
  rslt = [0] * 2
  # 使用新的version获取方式
  count = 0
  while True:
    try:        
      rslt = get_version()
      break
    except Exception:
      print("gd32v Failure to start ! reset gd32V!")
      reset()
      count += 1
      if count > 10:
        print("version no match，please reinstallation, Reload firmware!!!")
        # gd32v 不能启动
        # exit()
        gd32_script = "/usr/local/lib/python3.7/dist-packages/pinpong/base/gd32/burn.sh"
        os.chmod(gd32_script, 0o777)
        subprocess.run(["bash", gd32_script])
        time.sleep(1)
        rslt = get_version()
        break
    time.sleep(1)      
  if rslt[0] == 1 and rslt[1] == 1:
    print("pinpong new version match")
  else:
    print("version no match，please reinstallation  ex: pip install pinpong")
    exit()
    
  fd = os.open(COUNT_PATH, os.O_RDWR)       # 利用linux 自动close 解决计数问题
  if fd == -1:
    return -1
  temp = bytearray(4)
  temp[3] = 1

  flag = os.read(fd, 4)
  if(flag[3] == 0):
    os.write(fd, temp)        # 初始化所有模块的标志
    init_other_moudle()
  return 0


IOCTL_VERSION = 0x5201
class versionIoctlParams(ctypes.Structure):
  _fields_ = [("data", ctypes.c_ubyte * 2)]


'''
  检测dev_path 是否存在
  timerout 超时时间60s
  interval 间隔时间 2s
'''
def get_pinpong_state(device_path, timeout=60, interval=2):
  elapsed_time = 0
  while elapsed_time < timeout:
    if os.path.exists(device_path):
      time.sleep(0.1)
      return True
    print("Please wait for pinpong to load !!!")
    time.sleep(interval)
    elapsed_time += interval
  print("pingpong takes too long to load, please try again !!!")
  exit()
  return False

def get_version():
  rslt = [0]*2
  fd = os.open(CONFIG_PATH, os.O_RDWR)  # 根据实际情况修改设备路径
  params = versionIoctlParams()
  params.data[0] = 0x1E
  params.data[1] = 0x02
  try:
    ret = fcntl.ioctl(fd, IOCTL_VERSION, params)
  except:
    # 不能读取时会出错
    os.close(fd) 
  os.close(fd)
  rslt[:] = params.data
  return rslt
  

# 定义一些常量
IOCTL_MOUDLE   = 16642           # 加载linux 剩余的驱动
class IoctlParams(ctypes.Structure):
  _fields_ = [("mode", c_int) , ("num",  c_int)]  # 根据实际情况定义字段类型和名称

def init_other_moudle():
  fd = os.open(CONFIG_PATH, os.O_RDWR)
  if fd == -1:
    return -1
  params = IoctlParams()
  params.mode = 0x1F
  params.num = 1
  ret = fcntl.ioctl(fd, IOCTL_MOUDLE, params)
  if ret == -1:
    print("other moudle init fail")
  else:
    print("other moudle init success")
  os.close(fd)


# 全局变量，用于存储模式对应的数字

STATE_NONE     = 0
STATE_GPIO     = 1
STATE_IIC      = 2
STATE_SPI      = 4
STATE_UART     = 8
STATE_PWM      = 16
STATE_ADC      = 32
STATE_SPECIAL  = 64
STATE_2812     = 65
STATE_DHT11    = 66
STATE_18B20    = 67
STATE_BZZER    = 68
STATE_20689    = 69
STATE_URM09    = 70
STATE_RESERVE  = 255


config_filename = "/opt/.io_config.txt"
def get_pin_mode():
  fd = os.open(CONFIG_PATH, os.O_RDWR)       # 利用linux 自动close 解决计数问题
  if fd == -1:
    os.close(fd)
    return -1
  temp = os.read(fd, 48)
  if temp[0] == 0 and temp[1] == 0:
    # 数据不正常
    print("gpio mode error please reinit ")
  else:
    for gpio_num in range(48):
      pin_default_state[gpio_num] = temp[gpio_num]
  os.close(fd)

def init(board):
  # 因为要强制刷新，所以这里不能做操作
  pass
  
  #board.connected = True
  
def begin(board):
  ret = pinpong_count_init()
  if(ret == -1):
    return -1
  get_pin_mode()
  printlogo()
  board.port = "/dev/ttyS3"

def pinReuse(pin, mode):
  pin_default_state[pin-200] = mode
  fd = os.open(CONFIG_PATH, os.O_RDWR)
  if fd == -1:
    os.close(fd)  
    return -1
  temp = bytearray(200)
  # Configuring all IO ports
  temp[0] = 0
  temp[1:49] = bytearray(pin_default_state)
  ret = 0
  try:
    ret = os.write(fd, temp[:49])
  except:
    print("io ramap error please reinit")
    ret = -1
  if ret == -1:
    print("Please start running pinpong again ")
    os.close(fd)
    exit()
  os.close(fd)

def reset():
  if not os.path.exists("/sys/class/gpio/gpio80"):
    os.system("echo 80 > /sys/class/gpio/export")#RST
  if not os.path.exists("/sys/class/gpio/gpio69"):
    os.system("echo 69 > /sys/class/gpio/export")#BOOT0      
  os.system("echo out > /sys/class/gpio/gpio69/direction")
  os.system("echo out > /sys/class/gpio/gpio80/direction")
  os.system("echo 0 > /sys/class/gpio/gpio69/value")
  os.system("echo 1 > /sys/class/gpio/gpio80/value")
  os.system("echo 0 > /sys/class/gpio/gpio80/value")
  os.system("echo 1 > /sys/class/gpio/gpio80/value")

def open_serial(board):
  board.serial = serial.Serial(board.port, 115200, timeout=board.duration[board.boardname])

def find_port(board):
  pass

def PWM(board):
  board.fixed_value = 1000000
  if os.path.exists("/sys/class/pwm/pwmchip2/pwm"+board.channel):
    os.system('echo '+board.channel+ ' > /sys/class/pwm/pwmchip2/unexport')
    #print('echo '+board.channel+ ' > /sys/class/pwm/pwmchip2/unexport')
  os.system('echo '+board.channel+' > '+board.export_path)
  #print('echo '+board.channel+' > '+board.export_path)
  board.isStart = False

def ADC(board):
  adcname = "in_voltage0_raw"
  index = uni_res["adc"]["pinmap"].index(board.pin_obj.apin)
  pinReuse(uni_res["adc"]["pinnum"][index], STATE_ADC)
  board.value_path = uni_res["adc"]["value_path"]+str(board.pin_obj.apin)+"/"+adcname
  #print(board.value_path)

def UART(tty_name):
  pin_default_state[2]  = STATE_UART
  pin_default_state[3]  = STATE_UART
  pinReuse(202, STATE_UART)
  '''
  for i in uni_res["uart"]["pinnum"]:
    pinReuse(i, STATE_UART)
    print("uart  ")
    print(i)
  '''

def SPI(bus_num, dev_num):
  if((bus_num,dev_num) == (3,0)):
    pin_default_state[5]  = STATE_SPI
    pin_default_state[7]  = STATE_SPI
    pin_default_state[6]  = STATE_SPI
    pin_default_state[13] = STATE_SPI
    pinReuse(205, STATE_SPI)
  if((bus_num,dev_num) == (4,0)):
    pin_default_state[29] = STATE_SPI
    pin_default_state[30] = STATE_SPI
    pin_default_state[31] = STATE_SPI
    pin_default_state[14] = STATE_SPI
    pinReuse(229, STATE_SPI)

def irq(self, trigger, handler):
  IRQ_FALLING = 2
  IRQ_RISING = 1
  board = self
  index = uni_res["pin"]["pinmap"].index(board.pin) 
  pin = uni_res["pin"]["pinnum"][index]
  time.sleep(1)
  if self.thread_flag == 0:
    self.handler = handler
    self.thread_flag = 1
    self.trigger = trigger
    self.read_digital() # 记录此次引脚状态
    thread = threading.Thread(target=self.my_function)
    thread.daemon = True   # 守护线程
    thread.start()



def getPinmap(pin, mode):
  if(mode == 1):
    index = uni_res["pin"]["pinnum"].index(pin) 
    dpin = uni_res["pin"]["pinmap"][index]
  elif(mode == 2):
    index = uni_res["pwm"]["pinpwm"].index(pin)
    dpin = uni_res["pwm"]["pinmap"][index]  
  else:
    index = uni_res["adc"]["pinadc"].index(pin)
    dpin = uni_res["adc"]["pinmap"][index]
  return dpin

def get_pin(board,vpin):
  apin = 0
  if(vpin >= 100):
    vpin = vpin - 100
    apin = vpin
  else:
    apin = vpin
  if vpin not in uni_res["pin"]["pinnum"]:
    raise ValueError("%d pin is not supported"%vpin, "Support pin", uni_res["pin"]["pinnum"])
  dpin = vpin
  return dpin,apin

def soft_reset(board):
  pass
  

uni_res["init"] = init
uni_res["begin"] = begin
uni_res["reset"] = reset
uni_res["open_serial"] = open_serial 
uni_res["find_port"] = find_port 
uni_res["get_pin"] = get_pin
uni_res["soft_reset"] = soft_reset 
uni_res["PWM"] = PWM
uni_res["pinReuse"] = pinReuse
uni_res["getPinmap"] = getPinmap
uni_res["irq"] = irq
uni_res["ADC"] = ADC
uni_res["UART"] = UART
uni_res["SPI"] = SPI
uni_res["version"] = get_version
set_globalvar_value("UNIHIKER", uni_res)