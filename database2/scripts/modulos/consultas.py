# -*- coding: utf-8 -*-
import sqlite3
import pandas as pd
import streamlit as st
# MELHORIA: Centralização de caminhos a partir do arquivo config.py global
from config import CAMINHO_BANCO

@st.cache_data
def carregar_lista_sessoes():
    """ Retorna a lista de sessões combinada com os nomes dos pacientes """
    # MELHORIA: O gerenciador de contexto 'with' fecha a conexão de forma limpa e automática
    with sqlite3.connect(CAMINHO_BANCO) as conn:
        query = """
            SELECT s.id_sessao, p.nome AS nome_paciente, s.nivel_interacao, s.data 
            FROM sessoes s
            JOIN pacientes p ON s.id_paciente = p.id_paciente
            ORDER BY s.id_sessao DESC
        """
        return pd.read_sql(query, conn)

@st.cache_data
def carregar_lista_pacientes():
    """ Retorna todos os pacientes cadastrados para o dropdown de evolução """
    with sqlite3.connect(CAMINHO_BANCO) as conn:
        query = "SELECT id_paciente, nome FROM pacientes ORDER BY nome ASC"
        return pd.read_sql(query, conn)

@st.cache_data
def buscar_historico_paciente(id_paciente):
    """ Traz o histórico longitudinal (várias sessões) de uma única criança """
    with sqlite3.connect(CAMINHO_BANCO) as conn:
        # MELHORIA: Uso de consultas parametrizadas (?) com tupla de parâmetros para total segurança
        query = """
            SELECT s.id_sessao, s.data, s.nivel_interacao,
                   (SELECT AVG(distancia_mm) FROM sensor_laser WHERE id_sessao = s.id_sessao) as distancia_media,
                   (SELECT COUNT(*) FROM acoes_robo WHERE id_sessao = s.id_sessao AND categoria != 'Pescoco') as total_eventos
            FROM sessoes s
            WHERE s.id_paciente = ?
            ORDER BY s.id_sessao ASC
        """
        return pd.read_sql(query, conn, params=(id_paciente,))

@st.cache_data
def buscar_dados_sessao(id_sessao):
    """ Traz a telemetria detalhada (Ações e Laser) de uma sessão específica """
    with sqlite3.connect(CAMINHO_BANCO) as conn:
        # MELHORIA: Aplicação de parametrização segura nas tabelas filhas da sessão individual
        query_laser = """
            SELECT timestamp, distancia_mm, id_persona 
            FROM sensor_laser 
            WHERE id_sessao = ?
        """
        df_laser = pd.read_sql(query_laser, conn, params=(id_sessao,))
        df_laser['timestamp'] = pd.to_numeric(df_laser['timestamp']).round(3)
        
        query_acoes = """
            SELECT timestamp, nome_comando, categoria 
            FROM acoes_robo 
            WHERE id_sessao = ?
        """
        df_acoes = pd.read_sql(query_acoes, conn, params=(id_sessao,))
        df_acoes['timestamp'] = pd.to_numeric(df_acoes['timestamp'])
        
        return df_laser, df_acoes

@st.cache_data
def buscar_dados_grupo(id_sessao):
    """ 
    Calcula o tempo de foco e aproximação por pessoa em sessões com múltiplas crianças.
    Essencial para a exigência clínica de análise de grupo utilizando o id_persona.
    """
    with sqlite3.connect(CAMINHO_BANCO) as conn:
        query = """
            SELECT id_persona, COUNT(*) as frames_capturados, AVG(distancia_mm) as distancia_media
            FROM sensor_laser
            WHERE id_sessao = ?
            GROUP BY id_persona
        """
        return pd.read_sql(query, conn, params=(id_sessao,))