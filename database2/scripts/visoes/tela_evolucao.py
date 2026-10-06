# -*- coding: utf-8 -*-
import streamlit as st
import plotly.express as px
from modulos.consultas import carregar_lista_pacientes, buscar_historico_paciente

def renderizar_tela_evolucao():
    st.sidebar.header("Filtros de Evolução")
    
    # Mantemos a função original, mas tratamos os dados com a nova nomenclatura
    df_usuarios = carregar_lista_pacientes()
    
    if df_usuarios.empty:
        st.warning("Nenhum usuário cadastrado no banco de dados ainda.")
        st.stop()
        
    # Cria o mapeamento de nomes para IDs clínicos de forma limpa
    dict_usuarios = df_usuarios.set_index('nome')['id_paciente'].to_dict()
    nome_selecionado = st.sidebar.selectbox("Selecione o Usuário para análise histórica:", list(dict_usuarios.keys()))
    id_usuario_alvo = dict_usuarios[nome_selecionado]
    
    # Executa a busca longitudinal parametrizada no SQLite
    df_historico = buscar_historico_paciente(id_usuario_alvo)
    
    st.title(f"📈 Relatório de Evolução: {nome_selecionado}")
    st.markdown("Acompanhamento longitudinal das métricas de aproximação física e engajamento clínico.")
    
    if not df_historico.empty:
        # Prepara rótulo do eixo X combinando o ID da sessão e a resposta clínica obtida
        df_historico['Sessao_Label'] = "Sessão " + df_historico['id_sessao'].astype(str) + " \n(" + df_historico['nivel_interacao'] + ")"
        
        st.divider()
        col_ev1, col_ev2 = st.columns(2)
        
        with col_ev1:
            st.subheader("Evolução da Proximidade Média")
            fig_dist = px.line(
                df_historico, x='Sessao_Label', y='distancia_media', markers=True,
                title="Distância Média Corporal (Valores menores = maior aproximação)",
                labels={'distancia_media': 'Distância Média', 'Sessao_Label': 'Histórico'}
            )
            fig_dist.update_traces(line=dict(color='#636EFA', width=3))
            st.plotly_chart(fig_dist, use_container_width=True)
            
        with col_ev2:
            st.subheader("Frequência de Interações (Rosto e Voz)")
            fig_events = px.bar(
                df_historico, x='Sessao_Label', y='total_eventos', text_auto=True,
                title="Volume de Ações de Engajamento por Encontro",
                labels={'total_eventos': 'Quantidade de Interações', 'Sessao_Label': 'Histórico'},
                color='nivel_interacao',
                color_discrete_map={'baixa': '#dc3545', 'media': '#ffc107', 'alta': '#28a745'}
            )
            st.plotly_chart(fig_events, use_container_width=True)
            
        st.divider()
        
        st.subheader("Resumo Histórico de Encontros")
        df_tabela = df_historico[['id_sessao', 'data', 'nivel_interacao', 'distancia_media', 'total_eventos']].rename(
            columns={
                'id_sessao': 'ID da Sessão', 
                'data': 'Data', 
                'nivel_interacao': 'Avaliação', 
                'distancia_media': 'Distância Média', 
                'total_eventos': 'Total de Interações'
            }
        )
        st.dataframe(df_tabela, use_container_width=True)
    else:
        st.info(f"O usuário '{nome_selecionado}' ainda não possui histórico de sessões para exibição.")