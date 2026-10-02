#!/bin/bash
# Protocolo de teste do Castor: bateria fixa, reprodutivel.
# Injeta texto no topico /microphone, isolando o PLN dos erros do Vosk.
source /home/pi/catkin_ws/devel/setup.bash
PAUSA=${1:-4}
LISTA=$(dirname "$0")/falas_teste.txt
TOTAL=$(wc -l < "$LISTA")
echo "Protocolo: $TOTAL falas, pausa de ${PAUSA}s"
echo "Inicio: $(date '+%H:%M:%S')"
echo ""
while IFS= read -r f; do
  [ -z "$f" ] && continue
  printf '  %-42s' "$f"
  rostopic pub /microphone std_msgs/String "$f" --once > /dev/null 2>&1
  sleep "$PAUSA"
  echo "ok"
done < "$LISTA"
echo ""
echo "Fim: $(date '+%H:%M:%S')"
