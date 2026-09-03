import smbus

# 指定I2C总线，树莓派上通常为1
bus = smbus.SMBus(1)

# 要检查的设备地址
target_address = 0x50

def check_i2c_device(address):
    try:
        # 尝试向设备写入一个空操作（通常不会影响设备状态）
        bus.write_byte(address, 0)
        print(f"设备 0x{address:02x} 存在.")
        return True
    except Exception as e:
        # 如果发生异常（如IOError），通常表示设备无应答
        print(f"设备 0x{address:02x} 不存在或无应答: {e}")
        return False

if __name__ == "__main__":
    check_i2c_device(target_address)