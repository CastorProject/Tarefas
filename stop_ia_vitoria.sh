#!/bin/bash
# ============================================================
#  Encerra a IA Vitoria.
#  NAO mexe no microfone nem no speaker: sao os mesmos nos
#  que o painel usa, e continuam de pe.
#  O llama-server fica vivo de proposito, para o proximo
#  Iniciar nao esperar o modelo carregar de novo.
# ============================================================
echo parado > /tmp/castor_estado.txt
pkill -f "scripts/ros_chat\.py" 2>/dev/null
( rostopic pub /mic std_msgs/String "Inactivo" --once > /dev/null 2>&1 & )
echo "IA Vitoria encerrada. Painel segue no ar."
