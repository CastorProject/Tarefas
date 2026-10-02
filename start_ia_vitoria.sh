#!/bin/bash
# ============================================================
#  IA VITORIA - CASTOR 2
#  microfone (Vosk) -> chat (LLM) -> TTS (Piper) -> speaker
# ============================================================
LOG_DIR=/home/pi/logs_ia
mkdir -p "$LOG_DIR"

echo "=============================================="
echo "  INICIANDO IA VITORIA"
echo "=============================================="

echo "[1/6] Parando nos antigos..."
sudo pkill -f "scripts/ros_microphone\.py"  2>/dev/null   # mic padrao (Mafe)
sudo pkill -f "scripts/speaker\.py"         2>/dev/null   # speaker padrao (Mafe)
pkill -f "ros_microphone_vitoria.py"        2>/dev/null
pkill -f "speaker_vitoria.py"               2>/dev/null
pkill -f "ros_chat.py"                      2>/dev/null
pkill -f "ros_tts.py"                       2>/dev/null
pkill -f "llama-server"                     2>/dev/null
sleep 4

echo "[2/6] Subindo llama-server (2 threads)..."
nohup /home/pi/llama.cpp/build/bin/llama-server \
      -m /home/pi/qwen2.5-0.5b-instruct-q4_k_m.gguf \
      --host 0.0.0.0 --port 11434 -c 2048 --threads 2 \
      > "$LOG_DIR/llama_server.log" 2>&1 &
echo -n "      carregando modelo"
for i in $(seq 1 90); do
    if grep -q "HTTP server listening" "$LOG_DIR/llama_server.log" 2>/dev/null; then
        echo " OK"; break
    fi
    echo -n "."; sleep 2
done

echo "[3/6] Subindo speaker (aplay)..."
nohup python /home/pi/catkin_ws/src/speaker/scripts/speaker_vitoria.py \
      > "$LOG_DIR/speaker.log" 2>&1 &
sleep 5

echo "[4/6] Subindo microfone (Vosk)..."
nohup python3 -u /home/pi/catkin_ws/src/microphone/scripts/ros_microphone_vitoria.py \
      > "$LOG_DIR/ros_mic.log" 2>&1 &
sleep 5

echo "[5/6] Subindo TTS (Piper)..."
nohup python3 -u /home/pi/catkin_ws/src/text_to_speech/scripts/ros_tts.py \
      > "$LOG_DIR/ros_tts.log" 2>&1 &
sleep 6

echo "[6/6] Subindo chat (LLM)..."
nohup python3 -u /home/pi/catkin_ws/src/chat/scripts/ros_chat.py \
      > "$LOG_DIR/ros_chat.log" 2>&1 &
sleep 5

echo ""
echo "=============================================="
echo "  STATUS DOS NOS"
echo "=============================================="
rosnode list | grep -E "chat|microphone|tts|speaker"
echo ""
echo "Logs em: $LOG_DIR"
echo "Ativar microfone:"
echo "  rostopic pub /mic std_msgs/String \"Activo\" --once"
echo "=============================================="

# liga o microfone automaticamente
sleep 2
rostopic pub /mic std_msgs/String "Activo" --once > /dev/null 2>&1
echo "Microfone ativado."
