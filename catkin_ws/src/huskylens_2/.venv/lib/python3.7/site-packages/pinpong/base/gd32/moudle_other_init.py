import os
import fcntl
import ctypes
import time
from ctypes import c_int

# 定义一些常量
IOCTL_RESET    = 25345           # reset gd32V
IOCTL_MOUDLE   = 16642           # 加载linux 剩余的驱动
IOCTL_CONFIG   = 17162           # 给gd32v 写入当前的io口配置的模式



class IoctlParams(ctypes.Structure):
  _fields_ = [("mode", c_int) , ("num",  c_int)]  # 根据实际情况定义字段类型和名称
              
def init_other_moudle():
  fd = os.open("/dev/pinpong_config", os.O_RDWR)
  if fd == -1:
    print("open error")
    return -1
    
  params = IoctlParams()
  params.mode = 0x1F
  params.num = 1

  ret = fcntl.ioctl(fd, IOCTL_MOUDLE, params)
  time.sleep(0.1);
  if ret == -1:
    print("other moudle init fail")
  else:
    print("other moudle init success")
  os.close(fd)


# 加载剩余的linux 驱动
init_other_moudle()

