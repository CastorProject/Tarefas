# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
from modulos.consultas import carregar_lista_sessoes, buscar_dados_sessao
from modulos.utilidades import calcular_duracao_engajamento, aplicar_cores, calcular_correlacao_emocao_distancia
from modulos.graficos import plotar_pizza_engajamento, plotar_linha_proximidade, plotar_correlacao_emocao_distancia

def renderizar_tela_individual():
    st.sidebar.header("Filtros do Relatório")
    df_sessoes = carregar_lista_sessoes()

    if df_sessoes.empty:
        st.warning("Nenhuma sessão encontrada no banco de dados.")
        st.stop()

    # Mapeamento robusto por dicionário para evitar falhas de quebra de strings
    mapeamento_sessoes = {}
    for row in df_sessoes.itertuples(index=False):
        texto_exibicao = f"ID: {row.id_sessao} | Paciente: {row.nome_paciente} | Data: {row.data}"
        mapeamento_sessoes[texto_exibicao] = {
            "id": row.id_sessao,
            "nome": row.nome_paciente,
            "nivel": row.nivel_interacao
        }

    escolha = st.sidebar.selectbox("Selecione a Sessão Clínica:", list(mapeamento_sessoes.keys()))

    # Extração segura das variáveis associadas à escolha do usuário
    id_selecionado = mapeamento_sessoes[escolha]["id"]
    nome_paciente  = mapeamento_sessoes[escolha]["nome"]
    classificacao_clinica = mapeamento_sessoes[escolha]["nivel"]

    # Busca os dados de telemetria e ações associados ao ID da sessão
    df_laser, df_acoes = buscar_dados_sessao(id_selecionado)

    st.title(f"📊 Relatório Individual: {nome_paciente}")
    st.markdown(f"**Avaliação de Engajamento:** `{classificacao_clinica.upper()}`")

    # ── PAINEL DE KPIs FIXOS (4 colunas) ─────────────────────────────────────
    # FIX: substituído o st.columns(len(mapa_tempos_geral)+1) que explodia em
    # dezenas de colunas minúsculas quando a sessão tinha muitos comandos.
    st.subheader("⏱️ Indicadores de Performance")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total de Eventos", len(df_acoes))

    with col2:
        total_emocoes = (
            len(df_acoes[df_acoes['categoria'] == 'Emocao'])
            if not df_acoes.empty else 0
        )
        st.metric("Emoções Registradas", total_emocoes)

    with col3:
        total_audio = (
            len(df_acoes[df_acoes['categoria'] == 'Atividade_Audio'])
            if not df_acoes.empty else 0
        )
        st.metric("Áudios Reproduzidos", total_audio)

    with col4:
        if not df_laser.empty:
            media_distancia = df_laser['distancia_mm'].mean()
            unidade_medida  = "cm" if media_distancia < 500 else "px"
            st.metric("Proximidade Média", f"{media_distancia:.2f} {unidade_medida}")
        else:
            st.metric("Proximidade Média", "Sem dados")

    st.divider()

    # ── CÁLCULO DO FIM DA SESSÃO (com fallback robusto) ──────────────────────
    if not df_laser.empty:
        fim_da_sessao_ts = df_laser['timestamp'].max()
    elif not df_acoes.empty:
        fim_da_sessao_ts = df_acoes['timestamp'].max()
    else:
        fim_da_sessao_ts = 0

    # ── SEPARAÇÃO: PESCOÇO vs INTERAÇÕES REAIS ────────────────────────────────
    if not df_acoes.empty:
        df_acoes_pescoco    = df_acoes[df_acoes['categoria'] == 'Pescoco']
        df_acoes_interacoes = df_acoes[df_acoes['categoria'] != 'Pescoco']
    else:
        df_acoes_pescoco    = pd.DataFrame(columns=['nome_comando', 'timestamp', 'categoria'])
        df_acoes_interacoes = pd.DataFrame(columns=['nome_comando', 'timestamp', 'categoria'])

    df_tempos_pescoco    = calcular_duracao_engajamento(df_acoes_pescoco,    fim_da_sessao_ts)
    df_tempos_interacoes = calcular_duracao_engajamento(df_acoes_interacoes, fim_da_sessao_ts)

    # ── GRÁFICOS PRINCIPAIS ───────────────────────────────────────────────────
    col_grafico, col_pizza = st.columns([2, 1])

    with col_grafico:
        st.subheader("Proximidade ao Castor (Tendência)")
        plotar_linha_proximidade(df_laser)

    with col_pizza:
        st.write("#### 🎭 Emoções e Interações")
        plotar_pizza_engajamento(df_tempos_interacoes)

        st.write("#### 🤖 Movimentos do Pescoço")
        plotar_pizza_engajamento(df_tempos_pescoco)

    st.divider()

    # ── CORRELAÇÃO CLÍNICA: EMOÇÃO x PROXIMIDADE ─────────────────────────────
    st.subheader("🧠 Análise Comportamental: Emoção x Proximidade")
    df_correlacao = calcular_correlacao_emocao_distancia(df_laser, df_acoes)

    if not df_correlacao.empty:
        st.markdown(
            "Este gráfico cruza a telemetria do laser com as expressões do robô "
            "para descobrir **qual estímulo causa a maior aproximação física**."
        )
        plotar_correlacao_emocao_distancia(df_correlacao)
    else:
        st.info("Não foi possível gerar a correlação: faltam dados de laser ou de expressões nesta sessão.")

    st.divider()

    # ── LOG DE EVENTOS ────────────────────────────────────────────────────────
    st.subheader("📝 Log de Eventos")
    if not df_acoes.empty:
        st.dataframe(
            df_acoes.style
                .map(aplicar_cores, subset=['nome_comando'])
                .format({"timestamp": "{:.3f}"}),
            use_container_width=True
        )
    else:
        st.info("Nenhum evento registrado nesta sessão.")