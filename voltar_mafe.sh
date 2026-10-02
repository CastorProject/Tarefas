#!/bin/bash
echo "Limpando IA Vitoria..."
sudo pkill -f start_ia_vitoria.sh
sudo pkill -f ros_microphone_vitoria.py
sudo pkill -f speaker_vitoria.py
sudo pkill -f ros_chat.py
sudo pkill -f ros_tts.py
sudo pkill -f llama-server
sudo pkill -f arecord
sudo pkill -f aplay
echo parado | sudo tee /tmp/castor_estado.txt > /dev/null
sleep 3
echo "Reiniciando sistema da Mafe..."
sudo systemctl restart castor_start.service
sleep 25
echo "Nos ativos:"
rosnode list
