#  -*- coding: UTF-8 -*-

import smbus
import time

def scan_i2c_addresses(bus_num, start_address, end_address):
    bus = smbus.SMBus(bus_num)
    found_devices = {}

    for address in range(start_address, end_address + 1):
        try:
            bus.write_quick(address)
            found_devices[address] = "Found"
        except OSError:
            found_devices[address] = "Not Found"
        time.sleep(0.01)
    return found_devices

if __name__ == "__main__":
    # 指定I2C总线编号（例如：在Raspberry Pi上通常是1）
    bus_number = 4

    # 需要扫描的I2C地址范围
    start_address = 0x03
    end_address = 0x7F

    while True:
        # 扫描I2C地址
        results = scan_i2c_addresses(bus_number, start_address, end_address)

        # 打印扫描结果
        for address, status in results.items():
            print(f"Address 0x{address:02X}: {status}")

        # 延迟一段时间后再次扫描
