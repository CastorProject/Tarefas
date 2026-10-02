#!/bin/bash
source /opt/ros/melodic/setup.bash
source /home/pi/catkin_ws/devel/setup.bash
rostopic pub /mic std_msgs/String "Inactivo" --once > /dev/null 2>&1
sleep 1
pkill -f start_ia_vitoria.sh
pkill -f ros_microphone_vitoria.py
pkill -f speaker_vitoria.py
pkill -f ros_tts.py
pkill -f llama-server
pkill -f arecord
sleep 2
pkill -f ros_chat.py
sleep 3
pkill -f "scripts/ros_microphone.py"
pkill -f "scripts/speaker.py"
sleep 1
setsid nohup python /home/pi/catkin_ws/src/microphone/scripts/ros_microphone.py > /home/pi/logs_ia/mic_mafe.log 2>&1 &
setsid nohup python /home/pi/catkin_ws/src/speaker/scripts/speaker.py > /home/pi/logs_ia/speaker_mafe.log 2>&1 &
echo parado > /tmp/castor_estado.txt
sleep 4
rosnode list
