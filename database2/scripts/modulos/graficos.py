import plotly.express as px
import streamlit as st

def plotar_pizza_engajamento(df_tempos):
    """ Renderiza o gráfico de pizza interativo usando Plotly """
    if df_tempos.empty:
        st.info("Nenhum evento registrado nesta sessão para gerar análise de pizza.")
        return
    
    fig_pizza = px.pie(
        df_tempos, values='duracao', names='nome_comando', color='nome_comando',
        color_discrete_map={'alta': '#28a745', 'media': '#ffc107', 'baixa': '#dc3545'}
    )
    # Tira as margens para o gráfico encaixar perfeitamente na coluna
    fig_pizza.update_layout(margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig_pizza, use_container_width=True)

def plotar_linha_proximidade(df_laser):
    """ Renderiza a evolução da distância física usando a janela de suavização """
    if df_laser.empty:
        st.warning("Sem dados de telemetria laser localizados para esta sessão.")
        return
    
    # Lógica adaptativa para não travar o navegador caso existam milhares de leituras
    total_linhas = len(df_laser)
    tamanho_janela = 50 if total_linhas > 1000 else 5
    passo_amostragem = 10 if total_linhas > 5000 else 1
    
    df_laser['distancia_suave'] = df_laser['distancia_mm'].rolling(window=tamanho_janela, min_periods=1).mean()
    st.line_chart(df_laser.iloc[::passo_amostragem, :].set_index('timestamp')['distancia_suave'])

def plotar_correlacao_emocao_distancia(df_correlacao):
    if df_correlacao.empty:
        st.info("Sem dados sobrepostos suficientes para gerar a correlação nesta sessão.")
        return

    fig = px.bar(
        df_correlacao,
        x='nome_comando',
        y='distancia_media_cm',
        text='distancia_media_cm',
        title="Qual emoção gera mais aproximação?",
        labels={'nome_comando': 'Estímulo do Robô', 'distancia_media_cm': 'Distância Média (cm)'},
        color='nome_comando'
    )
    # Formata o texto em cima das barras para mostrar o valor em cm
    fig.update_traces(texttemplate='%{text:.1f} cm', textposition='auto')
    
    # Inverte o eixo Y para que barras "maiores" signifiquem que a criança chegou mais perto (distância menor)
    fig.update_layout(yaxis=dict(autorange="reversed"))
    
    st.plotly_chart(fig, use_container_width=True)