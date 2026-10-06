#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import pandas as pd
import json
import os
import glob
import shutil
import logging
from datetime import datetime

# Define a pasta raiz de varredura e o caminho do banco SQLite
PASTA_DATA = 'data'
os.makedirs(PASTA_DATA, exist_ok=True)
caminho_log = os.path.join(PASTA_DATA, 'importador.log')

# Configuração dupla de Log (Salva no arquivo físico importador.log e exibe no Terminal)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s',
    datefmt='%d/%m/%Y %H:%M:%S',
    handlers=[
        logging.FileHandler(caminho_log, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

CAMINHO_BANCO = os.path.join(PASTA_DATA, 'terapia.db')

def garantir_tabelas_e_indices(cursor) -> None:
    """ Prepara a modelagem relacional completa e otimiza a performance com índices """
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pacientes (
            id_paciente INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT UNIQUE
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessoes (
            id_sessao INTEGER PRIMARY KEY AUTOINCREMENT,
            id_paciente INTEGER,
            nivel_interacao TEXT, 
            data TEXT,
            duracao TEXT,
            arquivo_origem TEXT,
            FOREIGN KEY (id_paciente) REFERENCES pacientes (id_paciente)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sensor_laser (
            id_leitura_laser INTEGER PRIMARY KEY AUTOINCREMENT, 
            id_sessao INTEGER, 
            timestamp TEXT, 
            distancia_mm REAL,
            id_persona TEXT, 
            FOREIGN KEY (id_sessao) REFERENCES sessoes (id_sessao)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS acoes_robo (
            id_acao_executada INTEGER PRIMARY KEY AUTOINCREMENT, 
            id_sessao INTEGER, 
            timestamp TEXT, 
            categoria TEXT, 
            nome_comando TEXT, 
            FOREIGN KEY (id_sessao) REFERENCES sessoes (id_sessao)
        )
    ''')

    # Índices criados para que os gráficos do Streamlit carreguem instantaneamente
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_laser_sessao ON sensor_laser(id_sessao);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_acoes_sessao ON acoes_robo(id_sessao);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_paciente_nome ON pacientes(nome);")

def importar_dados_reais() -> None:
    logging.info("🚀 Varredura de novos arquivos iniciada.")
    
    conn = sqlite3.connect(CAMINHO_BANCO)
    cursor = conn.cursor()
    
    # ATIVAÇÃO CRÍTICA: Garante que o SQLite não insira eventos sem um paciente válido
    cursor.execute("PRAGMA foreign_keys = ON;")
    garantir_tabelas_e_indices(cursor)

    # Coleta todos os JSONs mestre gerados pelo Raspberry Pi
    padrao_busca = os.path.join(PASTA_DATA, "session_summary_*.json")
    ficheiros_json = glob.glob(padrao_busca)
    
    if not ficheiros_json:
        logging.info("ℹ️ Nenhum novo arquivo mestre localizado para integração.")
        conn.close()
        return

    # Subpasta estrutural para manter o ambiente de trabalho sempre organizado
    pasta_processados = os.path.join(PASTA_DATA, "processados")
    os.makedirs(pasta_processados, exist_ok=True)

    # Inicia a varredura atômica: processa e comita uma sessão de cada vez
    for caminho_json in ficheiros_json:
        nome_arquivo_json = os.path.basename(caminho_json)
        sufixo = nome_arquivo_json.replace("session_summary", "").replace(".json", "")
        caminho_eventos = os.path.join(PASTA_DATA, f"interaction_events{sufixo}.csv")
        caminho_metricas = os.path.join(PASTA_DATA, f"frames_metrics{sufixo}.csv")
        
        # Agrupa a tríade para facilitar o deslocamento à pasta 'processados'
        arquivos_vinculados = [caminho_json, caminho_eventos, caminho_metricas]

        try:
            # Trava anti-duplicados: Confere se a sessão já foi guardada no passado
            cursor.execute("SELECT id_sessao FROM sessoes WHERE arquivo_origem = ?", (nome_arquivo_json,))
            if cursor.fetchone():
                # Movimenta a tríade de arquivos para 'processados' mesmo se for cópia repetida, limpando a raiz
                for arq in arquivos_vinculados:
                    if os.path.exists(arq):
                        shutil.move(arq, os.path.join(pasta_processados, os.path.basename(arq)))
                continue

            logging.info(f"📁 Analisando pacote de dados: {nome_arquivo_json}")

            # 1. Leitura de Metadados e Ajuste Relacional do Paciente
            with open(caminho_json, 'r', encoding='utf-8') as f:
                resumo = json.load(f)

            meta = resumo.get('metadata', {})
            nome_paciente = meta.get('id_crianca') or resumo.get('session_label', 'Paciente_Sem_Nome')
            duracao_segundos = resumo.get('duration_sec', meta.get('tempo_total_s', 0))
            duracao_formatada = f"{duracao_segundos:.2f}s"
            data_sessao = meta.get('data', datetime.now().strftime("%d/%m/%Y"))

            # Associa ou cria um novo ID de Paciente na tabela raiz
            cursor.execute("SELECT id_paciente FROM pacientes WHERE nome = ?", (nome_paciente,))
            registro_paciente = cursor.fetchone()
            if registro_paciente:
                id_paciente_atual = registro_paciente[0]
            else:
                cursor.execute("INSERT INTO pacientes (nome) VALUES (?)", (nome_paciente,))
                id_paciente_atual = cursor.lastrowid

            # 2. Leitura dos Eventos (Necessário para classificar o nível de interação)
            lista_tuplas_eventos = []
            if os.path.exists(caminho_eventos):
                df_eventos = pd.read_csv(caminho_eventos)
                # itertuples() utilizado em vez de iterrows() para velocidade extrema de leitura no Pandas
                for row in df_eventos.itertuples(index=False):
                    lista_tuplas_eventos.append((str(row.start_time_sec), row.categoria, row.label))

            # Cálculo de Classificação Clínica (Eventos/Minuto)
            total_eventos = len(lista_tuplas_eventos)
            if total_eventos == 0:
                nivel_interacao = "nula"
            elif duracao_segundos > 0:
                eventos_por_minuto = total_eventos / (duracao_segundos / 60)
                if eventos_por_minuto <= 1.0: nivel_interacao = "baixa"
                elif eventos_por_minuto <= 5.0: nivel_interacao = "media"
                else: nivel_interacao = "alta"
            else:
                nivel_interacao = "baixa"

            # 3. Gravação Oficial e Encadeamento de IDs
            cursor.execute('''
                INSERT INTO sessoes (id_paciente, nivel_interacao, data, duracao, arquivo_origem)
                VALUES (?, ?, ?, ?, ?)
            ''', (id_paciente_atual, nivel_interacao, data_sessao, duracao_formatada, nome_arquivo_json))
            # Captura a Chave Estrangeira gerada que conectará o Laser e os Eventos a esta Sessão
            id_sessao_real = cursor.lastrowid

            # Persiste os Eventos com a chave vinculada
            if lista_tuplas_eventos:
                eventos_finais = [(id_sessao_real, ts, cat, lab) for (ts, cat, lab) in lista_tuplas_eventos]
                cursor.executemany('INSERT INTO acoes_robo (id_sessao, timestamp, categoria, nome_comando) VALUES (?,?,?,?)', eventos_finais)

            # Persiste a Telemetria Contínua (Laser)
            if os.path.exists(caminho_metricas):
                df_metrics = pd.read_csv(caminho_metricas)
                col_dist = 'body_to_castor_distance_cm' if 'body_to_castor_distance_cm' in df_metrics.columns else 'min_person_to_castor_px'
                col_time = 'timestamp_sec' if 'timestamp_sec' in df_metrics.columns else 'time_sec'
                
                # Prepara o nome da coluna para evitar falha no getattr()
                col_persona_real = 'id_persona' if 'id_persona' in df_metrics.columns else 'coluna_inexistente'

                laser_data = []
                for row in df_metrics.itertuples(index=False):
                    distancia = getattr(row, col_dist)
                    timestamp = str(getattr(row, col_time))
                    # MELHORIA: Fallback blindado. Traz "Desconhecido" caso a coluna não exista nos CSVs antigos
                    persona = getattr(row, col_persona_real, "Desconhecido")
                    laser_data.append((id_sessao_real, timestamp, distancia, persona))

                cursor.executemany('INSERT INTO sensor_laser (id_sessao, timestamp, distancia_mm, id_persona) VALUES (?,?,?,?)', laser_data)
                logging.info(f" 📊 Telemetria: {len(df_metrics)} frames indexados com índices de busca.")
            else:
                logging.warning(f" ⚠️ Arquivo de laser correspondente ausente. Pulando dados físicos.")

            # Salva o bloco da sessão no banco de forma independente
            conn.commit()
            logging.info(f"✅ Sessão salva no banco de dados com ID: {id_sessao_real}.")

            # 4. Limpeza da Zona de Transferência (Move a tríade importada)
            for arq in arquivos_vinculados:
                if os.path.exists(arq):
                    shutil.move(arq, os.path.join(pasta_processados, os.path.basename(arq)))
            logging.info(f"📦 Arquivos físicos movidos para a pasta 'processados'.")

        except Exception as e:
            # Reverte qualquer inserção se a tríade estiver corrompida, salvando a integridade do banco
            conn.rollback()
            logging.error(f"❌ Falha crítica ao processar pacote {nome_arquivo_json}: {e}. Pulando para o próximo.")

    # Fecha a comunicação do banco de dados na saída
    conn.close()
    logging.info("🔚 Ciclo de varredura finalizado de forma estável.")

if __name__ == "__main__":
    importar_dados_reais()