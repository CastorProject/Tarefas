import subprocess
import os
import sys
import fcntl
import ctypes
import time
import shutil
from ctypes import c_int

# 定义一些常量
IOCTL_RESET    = 25345           # reset gd32V
IOCTL_MOUDLE   = 16642           # 加载linux 剩余的驱动
IOCTL_CONFIG   = 17162           # 给gd32v 写入当前的io口配置的模式

COUNT_PATH  = '/dev/pinpong_count'
CONFIG_PATH = '/dev/pinpong_config'

class IoctlParams(ctypes.Structure):
  _fields_ = [("mode", c_int) , ("num",  c_int)]  # 根据实际情况定义字段类型和名称


IOCTL_VERSION = 0x5201
class versionIoctlParams(ctypes.Structure):
  _fields_ = [("data", ctypes.c_ubyte * 2)]

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

'''
  检测dev_path 是否存在
  timerout 超时时间10s
  interval 间隔时间 1s
'''
def get_pinpong_state(device_path, timeout=10, interval=1):
  elapsed_time = 0
  while elapsed_time < timeout:
    if os.path.exists(device_path):
      return True
    #print("Please wait for pinpong to load !!!")
    time.sleep(interval)
    elapsed_time += interval
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
  

#  利用linux 自动close 解决计数问题
#  所有 调用pinpong库的时候必定初始化， 结束例程时，linux自动close
def pinpong_count_init():
  # 测试pinpong 是否准备好
  if False == get_pinpong_state(COUNT_PATH):
    #print("pinpong wasn't ready !!!")
    return -1
  #print("pinpong has been loaded !!!")
  rslt = [0] * 2
  # 使用新的version获取方式
  count = 0
  try:
    rslt = get_version()
  except Exception:
    while True:
      reset()
      count += 1
      if count > 5:
        #print("version no match，please reinstallation  ex: pip install pinpong")
        return -1
      #print("gd32v Failure to start ! reset gd32V!")
      time.sleep(2)
      rslt[0] = 0
      rslt[1] = 0
      rslt = get_version()
      # version v0.1.1
      if rslt[0] == 1 and rslt[1] == 1:
        #print("pinpong new version match")
        break
      else:
        print("version no match，please reinstallation  ex: pip install pinpong")
  
  if rslt[0] == 1 and rslt[1] == 1:
    #print("pinpong new version match")
    return 0
  else:
    #print("version no match，please reinstallation  ex: pip install pinpong")
    return -1  

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
        current_directory = os.path.dirname(__file__)
        gd32_script = current_directory+"bush.sh"
        print(gd32_script)
        os.chmod(gd32_script, 0o777)
        subprocess.run(["bash", gd32_script])
        time.sleep(1)
        rslt = get_version()
        break
    time.sleep(1)      
  if rslt[0] == 1 and rslt[1] == 1:
    print("pinpong update success")
    return 0
  else:
    print("version no match，please reinstallation  ex: pip install pinpong")
    exit()
    

  
 
def pinConfig():
  if -1 == pinpong_count_init():
    return -1
  fd = os.open("/dev/pinpong_config", os.O_RDWR)
  if fd == -1:
    #print("open error")
    return -1
  params = IoctlParams()
  params.mode = 0x1F
  params.num = 1
  ret = fcntl.ioctl(fd, IOCTL_CONFIG, params)
  
  os.close(fd)


# 全局变量，用于存储模式对应的数字
mode_mapping = {
    'STATE_NONE': 0,
    'STATE_GPIO': 1,
    'STATE_IIC': 2,
    'STATE_SPI': 4,
    'STATE_UART': 8,
    'STATE_PWM': 16,
    'STATE_ADC': 32,
    'STATE_SPECIAL': 64,
    'STATE_2812': 65,
    'STATE_DHT11': 66,
    'STATE_18B20': 67,
    'STATE_BUZZ': 68,
    'STATE_SR04': 69,
    'STATE_IR_SEND': 70,
    'STATE_IR_RECV': 71,
    'STATE_ICM20689': 72,
    'STATE_RESERVE': 255
}


def is_module_loaded(module_name):
    try:
        output = subprocess.check_output(['lsmod']).decode('utf-8')
        return module_name in output
    except subprocess.CalledProcessError:
        return False

# 读取并解析 io_config.txt 文件
def parse_io_config(filename):
    gpio_modes = []  # 存储 GPIO 配置模式的列表
    
    with open(filename, 'r') as file:
        lines = file.readlines()
        for line in lines:
            if line.startswith('#') or not line.strip():
                continue  # 跳过注释和空行
            # 先用空格分割字符串
            parts1 = line.strip().split()
            # 再用等号分割字符串
            parts = parts1[0].strip().split('=')
            if len(parts) == 2:
                gpio_mode = parts[1]
                if gpio_mode in mode_mapping:
                    gpio_mode_value = mode_mapping[gpio_mode]
                    gpio_modes.append(gpio_mode_value)
    
    return gpio_modes

# 主程序

if __name__ == "__main__":
    # 目标路径
    old_config_filename = "/opt/.io_config.txt"
    destination_directory = "/opt/"
    # 获取当前工作目录
    
    script_path = sys.argv[0]
    
    current_directory = os.path.dirname(os.path.abspath(script_path))

    #print("当前路径:", current_directory)

    #current_directory = os.getcwd()
    #print('anaysis   path1:', current_directory)

    config_filename = os.path.join(current_directory,".io_config.txt")
    
    # 检查文件是否存在
    if os.path.exists(old_config_filename):
      #print(f"文件 '{old_config_filename}' 存在.")
      # 加载模式
      gpio_modes = parse_io_config(old_config_filename)
    else:
      #print(f"文件 '{old_config_filename}' 不存在.")
      # 加载模式
      gpio_modes = parse_io_config(config_filename)
      # 拷贝文件到目标目录
      shutil.copy(config_filename, destination_directory)
    
    if not gpio_modes or len(gpio_modes) != 48:
      raise ValueError("The gpio_modes list is empty. The file may be corrupt or incorrect")
    '''
    for gpio_num in range(48):
      print(gpio_modes[gpio_num])
    '''
    
    dev_iic1     = 0
    dev_spi0     = 0
    dev_spi1     = 0
    dev_uart     = 0
    dev_pwm      = 0
    dev_gpio     = 0
    dev_adc      = 0
    dev_ws2812   = 0
    dev_buzz     = 0
    dev_dht      = 0
    dev_icm20689 = 0
    dev_18b20    = 0
    dev_sr04     = 0
    dev_ir_send  = 0
    dev_ir_recv  = 0
    # 遍历从 0 到 32 的数字，并根据条件执行操作
    for gpio_num in range(48):
      mode = gpio_modes[gpio_num]
      if gpio_num == 0:
          if mode == mode_mapping['STATE_GPIO']:
              dev_gpio |= 1<<gpio_num
      elif gpio_num == 1:
          if mode == mode_mapping['STATE_ADC']:
              dev_adc |= 1<<gpio_num
      elif gpio_num == 2:
          if mode == mode_mapping['STATE_GPIO']:
              dev_gpio |= 1<<gpio_num
          elif mode == mode_mapping['STATE_PWM']:
              dev_pwm |= 1<<gpio_num
          elif mode == mode_mapping['STATE_ADC']:
              dev_adc |= 1<<gpio_num
          elif mode == mode_mapping['STATE_UART']:
              dev_uart |= 1<<gpio_num
          elif mode == mode_mapping['STATE_BUZZ']:
              dev_buzz |= 1<<gpio_num
          elif mode == mode_mapping['STATE_2812']:
              dev_ws2812 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_DHT11']:
              dev_dht |= 1<<gpio_num
          elif mode == mode_mapping['STATE_18B20']:
              dev_18b20 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_SR04']:
              dev_sr04 |= 1<<gpio_num
      elif gpio_num == 3:
          if mode == mode_mapping['STATE_GPIO']:
              dev_gpio |= 1<<gpio_num
          elif mode == mode_mapping['STATE_PWM']:
              dev_pwm |= 1<<gpio_num
          elif mode == mode_mapping['STATE_ADC']:
              dev_adc |= 1<<gpio_num
          elif mode == mode_mapping['STATE_UART']:
              dev_uart |= 1<<gpio_num
          elif mode == mode_mapping['STATE_BUZZ']:
              dev_buzz |= 1<<gpio_num
          elif mode == mode_mapping['STATE_2812']:
              dev_ws2812 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_DHT11']:
              dev_dht |= 1<<gpio_num
          elif mode == mode_mapping['STATE_18B20']:
              dev_18b20 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_SR04']:
              dev_sr04 |= 1<<gpio_num
      elif gpio_num == 4:
          if mode == mode_mapping['STATE_GPIO']:
              dev_gpio |= 1<<gpio_num
          elif mode == mode_mapping['STATE_ADC']:
              dev_adc |= 1<<gpio_num
          elif mode == mode_mapping['STATE_2812']:
              dev_ws2812 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_DHT11']:
              dev_dht |= 1<<gpio_num
          elif mode == mode_mapping['STATE_18B20']:
              dev_18b20 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_SR04']:
              dev_sr04 |= 1<<gpio_num
      elif gpio_num == 5:
          if mode == mode_mapping['STATE_GPIO']:
              dev_gpio |= 1<<gpio_num
          elif mode == mode_mapping['STATE_ADC']:
              dev_adc |= 1<<gpio_num
          elif mode == mode_mapping['STATE_SPI']:
              dev_spi0 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_2812']:
              dev_ws2812 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_DHT11']:
              dev_dht |= 1<<gpio_num
          elif mode == mode_mapping['STATE_18B20']:
              dev_18b20 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_SR04']:
              dev_sr04 |= 1<<gpio_num
      elif gpio_num == 6:
          if mode == mode_mapping['STATE_GPIO']:
              dev_gpio |= 1<<gpio_num
          elif mode == mode_mapping['STATE_PWM']:
              dev_pwm |= 1<<gpio_num
          elif mode == mode_mapping['STATE_ADC']:
              dev_adc |= 1<<gpio_num
          elif mode == mode_mapping['STATE_SPI']:
              dev_spi0 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_BUZZ']:
              dev_buzz |= 1<<gpio_num
          elif mode == mode_mapping['STATE_2812']:
              dev_ws2812 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_DHT11']:
              dev_dht |= 1<<gpio_num
          elif mode == mode_mapping['STATE_18B20']:
              dev_18b20 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_SR04']:
              dev_sr04 |= 1<<gpio_num
      elif gpio_num == 7:
          if mode == mode_mapping['STATE_GPIO']:
              dev_gpio |= 1<<gpio_num
          elif mode == mode_mapping['STATE_PWM']:
              dev_pwm |= 1<<gpio_num
          elif mode == mode_mapping['STATE_ADC']:
              dev_adc |= 1<<gpio_num
          elif mode == mode_mapping['STATE_SPI']:
              dev_spi0 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_BUZZ']:
              dev_buzz |= 1<<gpio_num
          elif mode == mode_mapping['STATE_2812']:
              dev_ws2812 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_DHT11']:
              dev_dht |= 1<<gpio_num
          elif mode == mode_mapping['STATE_18B20']:
              dev_18b20 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_SR04']:
              dev_sr04 |= 1<<gpio_num
      elif gpio_num == 8:
          if mode == mode_mapping['STATE_GPIO']:
              dev_gpio |= 1<<gpio_num
          elif mode == mode_mapping['STATE_PWM']:
              dev_pwm |= 1<<gpio_num
          elif mode == mode_mapping['STATE_BUZZ']:
              dev_buzz |= 1<<gpio_num
      elif gpio_num == 11:
          if mode == mode_mapping['STATE_GPIO']:
              dev_gpio |= 1<<gpio_num
          elif mode == mode_mapping['STATE_PWM']:
              dev_pwm |= 1<<gpio_num
          elif mode == mode_mapping['STATE_BUZZ']:
              dev_buzz |= 1<<gpio_num
          elif mode == mode_mapping['STATE_2812']:
              dev_ws2812 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_DHT11']:
              dev_dht |= 1<<gpio_num
          elif mode == mode_mapping['STATE_18B20']:
              dev_18b20 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_SR04']:
              dev_sr04 |= 1<<gpio_num
      elif gpio_num == 12:
          if mode == mode_mapping['STATE_GPIO']:
              dev_gpio |= 1<<gpio_num
          elif mode == mode_mapping['STATE_2812']:
              dev_ws2812 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_DHT11']:
              dev_dht |= 1<<gpio_num
          elif mode == mode_mapping['STATE_18B20']:
              dev_18b20 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_SR04']:
              dev_sr04 |= 1<<gpio_num
      elif gpio_num == 13:
          if mode == mode_mapping['STATE_GPIO']:
              dev_gpio |= 1<<gpio_num
          elif mode == mode_mapping['STATE_SPI']:
              dev_spi0 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_2812']:
              dev_ws2812 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_DHT11']:
              dev_dht |= 1<<gpio_num
          elif mode == mode_mapping['STATE_18B20']:
              dev_18b20 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_SR04']:
              dev_sr04 |= 1<<gpio_num
      elif gpio_num == 14:
          if mode == mode_mapping['STATE_GPIO']:
              dev_gpio |= 1<<gpio_num
          elif mode == mode_mapping['STATE_SPI']:
              dev_spi1 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_2812']:
              dev_ws2812 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_DHT11']:
              dev_dht |= 1<<gpio_num
          elif mode == mode_mapping['STATE_18B20']:
              dev_18b20 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_SR04']:
              dev_sr04 |= 1<<gpio_num
      elif gpio_num == 15:
          if mode == mode_mapping['STATE_GPIO']:
              dev_gpio |= 1<<gpio_num
      elif gpio_num == 16:
          if mode == mode_mapping['STATE_GPIO']:
              dev_gpio |= 1<<gpio_num
          elif mode == mode_mapping['STATE_ADC']:
              dev_adc |= 1<<gpio_num
          elif mode == mode_mapping['STATE_BUZZ']:
              dev_buzz |= 1<<gpio_num
          elif mode == mode_mapping['STATE_2812']:
              dev_ws2812 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_DHT11']:
              dev_dht |= 1<<gpio_num
          elif mode == mode_mapping['STATE_18B20']:
              dev_18b20 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_SR04']:
              dev_sr04 |= 1<<gpio_num
      elif gpio_num == 17:
          if mode == mode_mapping['STATE_GPIO']:
              dev_gpio |= 1<<gpio_num
          elif mode == mode_mapping['STATE_ADC']:
              dev_adc |= 1<<gpio_num
          elif mode == mode_mapping['STATE_BUZZ']:
              dev_buzz |= 1<<gpio_num
          elif mode == mode_mapping['STATE_2812']:
              dev_ws2812 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_DHT11']:
              dev_dht |= 1<<gpio_num
          elif mode == mode_mapping['STATE_18B20']:
              dev_18b20 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_SR04']:
              dev_sr04 |= 1<<gpio_num
      elif gpio_num == 19:
          if mode == mode_mapping['STATE_GPIO']:
              dev_gpio |= 1<<gpio_num
      elif gpio_num == 20:
          if mode == mode_mapping['STATE_GPIO']:
              dev_gpio |= 1<<gpio_num
          elif mode == mode_mapping['STATE_PWM']:
              dev_pwm |= 1<<gpio_num
          elif mode == mode_mapping['STATE_BUZZ']:
              dev_buzz |= 1<<gpio_num
          elif mode == mode_mapping['STATE_2812']:
              dev_ws2812 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_DHT11']:
              dev_dht |= 1<<gpio_num
          elif mode == mode_mapping['STATE_18B20']:
              dev_18b20 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_SR04']:
              dev_sr04 |= 1<<gpio_num
      elif gpio_num == 21:
          if mode == mode_mapping['STATE_GPIO']:
              dev_gpio |= 1<<gpio_num
          elif mode == mode_mapping['STATE_PWM']:
              dev_pwm |= 1<<gpio_num
          elif mode == mode_mapping['STATE_BUZZ']:
              dev_buzz |= 1<<gpio_num
          elif mode == mode_mapping['STATE_2812']:
              dev_ws2812 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_DHT11']:
              dev_dht |= 1<<gpio_num
          elif mode == mode_mapping['STATE_18B20']:
              dev_18b20 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_SR04']:
              dev_sr04 |= 1<<gpio_num
      elif gpio_num == 25:
          if mode == mode_mapping['STATE_GPIO']:
              dev_gpio |= 1<<gpio_num
          elif mode == mode_mapping['STATE_PWM']:
              dev_pwm |= 1<<gpio_num
          elif mode == mode_mapping['STATE_BUZZ']:
              dev_buzz |= 1<<gpio_num
          elif mode == mode_mapping['STATE_2812']:
              dev_ws2812 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_DHT11']:
              dev_dht |= 1<<gpio_num
          elif mode == mode_mapping['STATE_18B20']:
              dev_18b20 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_SR04']:
              dev_sr04 |= 1<<gpio_num
      elif gpio_num == 26:
          if mode == mode_mapping['STATE_IIC']:
              dev_iic1 |= 1<<gpio_num
      elif gpio_num == 27:
          if mode == mode_mapping['STATE_IIC']:
              dev_iic1 |= 1<<gpio_num
      elif gpio_num == 29:
          if mode == mode_mapping['STATE_GPIO']:
              dev_gpio |= 1<<gpio_num
          elif mode == mode_mapping['STATE_SPI']:
              dev_spi1 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_2812']:
              dev_ws2812 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_DHT11']:
              dev_dht |= 1<<gpio_num
          elif mode == mode_mapping['STATE_18B20']:
              dev_18b20 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_SR04']:
              dev_sr04 |= 1<<gpio_num
      elif gpio_num == 30:
          if mode == mode_mapping['STATE_GPIO']:
              dev_gpio |= 1<<gpio_num
          elif mode == mode_mapping['STATE_SPI']:
              dev_spi1 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_2812']:
              dev_ws2812 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_DHT11']:
              dev_dht |= 1<<gpio_num
          elif mode == mode_mapping['STATE_18B20']:
              dev_18b20 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_SR04']:
              dev_sr04 |= 1<<gpio_num
      elif gpio_num == 31:
          if mode == mode_mapping['STATE_GPIO']:
              dev_gpio |= 1<<gpio_num
          elif mode == mode_mapping['STATE_SPI']:
              dev_spi1 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_2812']:
              dev_ws2812 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_DHT11']:
              dev_dht |= 1<<gpio_num
          elif mode == mode_mapping['STATE_18B20']:
              dev_18b20 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_SR04']:
              dev_sr04 |= 1<<gpio_num
      elif gpio_num == 45:
          if mode == mode_mapping['STATE_GPIO']:
              dev_gpio |= 1<<gpio_num
          elif mode == mode_mapping['STATE_2812']:
              dev_ws2812 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_DHT11']:
              dev_dht |= 1<<gpio_num
          elif mode == mode_mapping['STATE_18B20']:
              dev_18b20 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_SR04']:
              dev_sr04 |= 1<<gpio_num
      elif gpio_num == 46:
          if mode == mode_mapping['STATE_GPIO']:
              dev_gpio |= 1<<gpio_num
          elif mode == mode_mapping['STATE_2812']:
              dev_ws2812 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_DHT11']:
              dev_dht |= 1<<gpio_num
          elif mode == mode_mapping['STATE_18B20']:
              dev_18b20 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_SR04']:
              dev_sr04 |= 1<<gpio_num
      elif gpio_num == 47:
          if mode == mode_mapping['STATE_GPIO']:
              dev_gpio |= 1<<gpio_num
          elif mode == mode_mapping['STATE_2812']:
              dev_ws2812 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_DHT11']:
              dev_dht |= 1<<gpio_num
          elif mode == mode_mapping['STATE_18B20']:
              dev_18b20 |= 1<<gpio_num
          elif mode == mode_mapping['STATE_SR04']:
              dev_sr04 |= 1<<gpio_num
    
    # 打印变量值（以十六进制方式）
    #print("dev_iic1:", hex(dev_iic1))
    #print("dev_spi0:", hex(dev_spi0))
    #print("dev_spi1:", hex(dev_spi1))
    #print("dev_uart:", hex(dev_uart))
    #print("dev_pwm:", hex(dev_pwm))
    #print("dev_gpio:", hex(dev_gpio))
    #print("dev_adc:", hex(dev_adc))
    #print("dev_ws2812:", hex(dev_ws2812))
    #print("dev_dht:", hex(dev_dht))
    #print("dev_18b20:", hex(dev_18b20))
    #print("dev_icm20689:", hex(dev_icm20689))
    #print("dev_sr04:", hex(dev_sr04))
    #print("dev_buzz:", hex(dev_buzz))
    #print("dev_ir_send:", hex(dev_ir_send))
    #print("dev_ir_recv:", hex(dev_ir_recv))
    
    # 构建新的文件路径
    module_name = os.path.join(current_directory,"pinpong_linux_module.ko")
    #print('module: ', module_name)
    # 参数字符串
    module_args = f"dev_iic1={hex(dev_iic1)} dev_spi0={hex(dev_spi0)} dev_spi1={hex(dev_spi1)} dev_uart={hex(dev_uart)} dev_pwm={hex(dev_pwm)} dev_gpio={hex(dev_gpio)} dev_adc={hex(dev_adc)} dev_ws2812={hex(dev_ws2812)} dev_buzz={hex(dev_buzz)} dev_dht={hex(dev_dht)} dev_icm20689={hex(dev_icm20689)} dev_18b20={hex(dev_18b20)} dev_sr04={hex(dev_sr04)} dev_ir_send={hex(dev_ir_send)} dev_ir_recv={hex(dev_ir_recv)}"

    # 构建命令
    cmd1 = ["rmmod", module_name]
    cmd = ["insmod", module_name, module_args]
    ko_name = "pinpong_linux_module"
    if is_module_loaded(ko_name):
        try:
            subprocess.run(cmd1, check=True)
            #print("Module rmmod successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to load module: {e}")
    # 加载 ko
    try:
        subprocess.run(cmd, check=True)
        #print("Module loaded successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to load module: {e}")
    time.sleep(1)
    # 运行io 配置
    pinConfig()
