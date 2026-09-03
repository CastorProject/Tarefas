#!/bin/bash
#enter_dfu.sh

echo "kill all process pleass wait !!!"

# 杀死使用 /dev/i2c-4 的进程
fuser -k /dev/i2c-4 > /dev/null 2>&1

# 杀死使用 /dev/ttySP0 的进程
fuser -k /dev/ttySP0 > /dev/null 2>&1

# 杀死使用 /dev/spidev3.0 的进程
fuser -k /dev/spidev3.0 > /dev/null 2>&1

# 杀死使用 /dev/spidev4.0 的进程
fuser -k /dev/spidev4.0 > /dev/null 2>&1

# 杀死使用 /dev/****
fuser -k /dev/icm20689 > /dev/null 2>&1
fuser -k /dev/gp2y1010au > /dev/null 2>&1
fuser -k /dev/pinpong_config > /dev/null 2>&1
fuser -k /dev/pinpong_count > /dev/null 2>&1
fuser -k /dev/ws_2812 > /dev/null 2>&1
fuser -k /dev/sr04 > /dev/null 2>&1
fuser -k /dev/ds18b20 > /dev/null 2>&1
fuser -k /dev/buzzer > /dev/null 2>&1
fuser -k /dev/dht > /dev/null 2>&1
fuser -k /dev/ir_send > /dev/null 2>&1
fuser -k /dev/ir_recv > /dev/null 2>&1


# GPIO 范围
START_GPIO=200
END_GPIO=232
# 遍历 GPIO
for ((gpio=$START_GPIO; gpio<=$END_GPIO; gpio++)); do
    # 检查 GPIO 是否已导出
    if [ -e "/sys/class/gpio/gpio$gpio" ]; then
        #echo "Unexporting GPIO $gpio"
        echo $gpio > /sys/class/gpio/unexport
    fi
done

# PWMCHIP 路径
PWMCHIP_PATH="/sys/class/pwm/pwmchip2"

# 遍历 PWM
for pwm in $PWMCHIP_PATH/pwm*; do
    # 获取 PWM 号码
    pwm_number=$(basename "$pwm" | sed 's/pwm//')
    # 检查 PWM 是否已导出
    if [ -e "$pwm" ]; then
        echo $pwm_number > "$PWMCHIP_PATH/unexport"
    fi
done
echo "kill all process completed !!!"
echo "start update gd32 firmware please wait !!!"
if [ ! -e /sys/class/gpio/gpio80 ]; then
    echo 80 > /sys/class/gpio/export #RST
fi

if [ ! -e /sys/class/gpio/gpio69 ]; then
    echo 69 > /sys/class/gpio/export #BOOT0
fi

echo out > /sys/class/gpio/gpio69/direction
echo out > /sys/class/gpio/gpio80/direction
echo 0 > /sys/class/gpio/gpio69/value #BOOT0 LOW
echo 1 > /sys/class/gpio/gpio80/value #RST HIGH
echo 1 > /sys/class/gpio/gpio69/value #BOOT0 HIGH
sleep 1                               
echo 0 > /sys/class/gpio/gpio80/value #RST LOW
sleep 1
echo 1 > /sys/class/gpio/gpio80/value #RST HIGH
sleep 1
echo 0 > /sys/class/gpio/gpio69/value #BOOT LOW

#stm32flash -w $pinpong_bin_path -v -g 0x08000000 /dev/ttyS3
sudo stm32flash -o /dev/ttyS3

echo 1 > /sys/class/gpio/gpio80/value #RST HIGH
