import sqlite3
from datetime import datetime

# Caminho completo para não ter erro de "tabela não encontrada"
db_path = '/home/pi/catkin_ws/src/database/scripts/data/terapia.db'

def conferir_banco():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("\n--- RELATÓRIO FORMATADO PARA TO (Últimas 10 Ações) ---")
    
    # Buscamos os dados brutos
    cursor.execute("SELECT id_sessao, timestamp, categoria, nome_comando FROM acoes_robo ORDER BY id_acao_executada DESC LIMIT 10")
    linhas = cursor.fetchall()

    for linha in linhas:
        id_s, ts_bruto, cat, cmd = linha
        
        try:
            valor_ts = float(ts_bruto)
            # Se o número for gigante, é data real (Unix)
            if valor_ts > 1000000:
                data_hora = datetime.fromtimestamp(valor_ts).strftime('%d/%m/%Y %H:%M:%S')
            # Se for pequeno, é o tempo do vídeo (ex: 1914 segundos)
            else:
                minutos = int(valor_ts // 60)
                segundos = int(valor_ts % 60)
                data_hora = f"Vídeo: {minutos:02d}:{segundos:02d}"
        except:
            data_hora = ts_bruto

        print(f"Sessão: {id_s} | Hora: {data_hora} | {cat}: {cmd}")

    conn.close()

if __name__ == "__main__":
    conferir_banco()
