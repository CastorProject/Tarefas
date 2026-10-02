#!/bin/bash
# ============================================================
#  IA VITORIA - CASTOR
#  Sobe SO o que e da IA. O microfone e o speaker do painel
#  continuam de pe: depois da fusao eles atendem os dois.
# ============================================================
LOG_DIR=/home/pi/logs_ia
mkdir -p "$LOG_DIR"

echo "=============================================="
echo "  INICIANDO IA VITORIA"
echo "=============================================="

echo "[1/4] Limpando sobras da IA..."
pkill -f "scripts/ros_chat\.py" 2>/dev/null
sleep 1

echo "[2/4] llama-server..."
if pgrep -f "llama-server" > /dev/null; then
    echo "      ja estava rodando, reaproveitando"
else
    nohup /home/pi/llama.cpp/build/bin/llama-server \
          -m /home/pi/qwen2.5-0.5b-instruct-q4_k_m.gguf \
          --host 0.0.0.0 --port 11434 -c 2048 --threads 2 \
          > "$LOG_DIR/llama_server.log" 2>&1 &
    echo -n "      carregando modelo"
    for i in $(seq 1 120); do
        if grep -q "HTTP server listening" "$LOG_DIR/llama_server.log" 2>/dev/null; then
            echo " OK"; break
        fi
        echo -n "."; sleep 2
    done
fi

echo "[3/4] TTS (Piper)..."
if pgrep -f "scripts/ros_tts\.py" > /dev/null; then
    echo "      ja estava rodando"
else
    nohup python3 -u /home/pi/catkin_ws/src/text_to_speech/scripts/ros_tts.py \
          > "$LOG_DIR/ros_tts.log" 2>&1 &
    sleep 5
fi

echo "[4/4] chat (LLM)..."
nohup python3 -u /home/pi/catkin_ws/src/chat/scripts/ros_chat.py \
      > "$LOG_DIR/ros_chat.log" 2>&1 &
sleep 4

rostopic pub /mic std_msgs/String "Activo" --once > /dev/null 2>&1
echo ativo > /tmp/castor_estado.txt

echo ""
rosnode list | grep -E "chat|microphone|tts|speaker"
echo "IA Vitoria no ar."
