# -*- coding: utf-8 -*-
import os

# --- DIRETÓRIOS ESTRUTURAIS ---
# Pastas principais do projeto Projeto Castor
PASTA_DATA = "data"
PASTA_ASSETS = "assets"

# Subpasta para organizar os arquivos brutos após importação
PASTA_PROCESSADOS = os.path.join(PASTA_DATA, "processados")

# --- CAMINHOS DE ARQUIVOS CRÍTICOS ---
# Caminho unificado para o banco de dados SQLite
CAMINHO_BANCO = os.path.join(PASTA_DATA, "terapia.db")

# Caminho para a identidade visual do dashboard
CAMINHO_LOGO = os.path.join(PASTA_ASSETS, "macaco.jpg")