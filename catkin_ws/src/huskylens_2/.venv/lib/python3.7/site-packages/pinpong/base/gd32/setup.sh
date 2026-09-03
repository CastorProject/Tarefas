#!/bin/bash

# 要插入的命令
new_command="cd /usr/local/lib/python3.7/dist-packages/pinpong/base/gd32/ && python3 anaysis.py"

# 检查rc.local是否包含指定的命令
if ! grep -qF "$new_command" /etc/rc.local; then
    # 获取原始的rc.local内容
    original_content=$(sudo cat /etc/rc.local)

    # 在倒数第二行插入命令
    new_content=$(echo "$original_content" | sed '$i\'"$new_command")

    # 将新内容写入rc.local文件
    echo "$new_content" | sudo tee /etc/rc.local > /dev/null
    echo "已将命令添加到 /etc/rc.local"
else
    echo "已存在相同的命令，无需修改 /etc/rc.local"
fi

# 重启系统
# sudo reboot

