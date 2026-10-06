# -*- coding: utf-8 -*-
import streamlit as st
import os
from config import CAMINHO_LOGO

# Importação das telas modularizadas
from visoes.tela_individual import renderizar_tela_individual
# AGORA ATIVADO: Importa a tela de evolução que acabamos de criar
from visoes.tela_evolucao import renderizar_tela_evolucao
# A importação abaixo continua comentada até criarmos o arquivo tela_grupo.py
# from visoes.tela_grupo import renderizar_tela_grupo

# 1. Configuração Global da Página
st.set_page_config(page_title="Castor - Dashboard Clínico", layout="wide")

def main():
    # 2. Configuração do Menu Lateral
    st.sidebar.title("Menu do Sistema")
    
    if os.path.exists(CAMINHO_LOGO):
        st.sidebar.image(CAMINHO_LOGO, width=150)
    else:
        st.sidebar.error("Logo não encontrada no caminho definido em config.py")

    # 3. Roteamento
    st.sidebar.subheader("Navegação")
    modo = st.sidebar.radio(
        "Selecione o módulo de análise:", 
        ["Relatório Individual", "Evolução do Usuário", "Sessão em Grupo"]
    )
    
    st.sidebar.divider()
    
    # Botão para atualizar dados do banco
    if st.sidebar.button("🔄 Atualizar Banco de Dados", use_container_width=True):
        st.cache_data.clear()
        st.sidebar.success("Cache limpo! Dados atualizados.")

    st.sidebar.info("Projeto Castor\nLaboratório de Tecnologia Assistiva - UFES")

    # 4. Controle de Exibição das Visões (Telas)
    if modo == "Relatório Individual":
        renderizar_tela_individual()
        
    elif modo == "Evolução do Usuário":
        # AGORA ATIVADO: Chama a função real que desenha os gráficos da evolução
        renderizar_tela_evolucao()
        
    elif modo == "Sessão em Grupo":
        st.title("👥 Análise de Sessão em Grupo")
        st.info("Módulo estruturado. Pronto para receber a análise multi-paciente utilizando a variável id_persona.")
        # renderizar_tela_grupo()

if __name__ == "__main__":
    main()