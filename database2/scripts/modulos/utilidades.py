import pandas as pd

def aplicar_cores(val):
    """ Colore dinamicamente a tabela de eventos com base no nível de engajamento """
    if val == 'alta': return 'background-color: #d4edda; color: #155724'
    if val == 'media': return 'background-color: #fff3cd; color: #856404'
    if val == 'baixa': return 'background-color: #f8d7da; color: #721c24'
    return 'background-color: #e2e3e5; color: #383d41'

def calcular_duracao_engajamento(df, fim_sessao):
    """ Calcula o tempo exato (em segundos) que a criança passou em cada estado """
    if df.empty:
        return pd.DataFrame(columns=['nome_comando', 'duracao'])
    
    df = df.sort_values('timestamp').copy()
    # Puxa o timestamp do próximo evento para calcular a diferença (delta)
    df['proximo_ts'] = df['timestamp'].shift(-1).fillna(fim_sessao)
    df['duracao'] = df['proximo_ts'] - df['timestamp']
    
    return df.groupby('nome_comando')['duracao'].sum().reset_index()

def calcular_correlacao_emocao_distancia(df_laser, df_acoes):
    """
    Cruza os dados do laser com as emoções usando proximidade de tempo (merge_asof).
    Retorna a distância média do paciente para cada emoção expressada pelo robô.
    """
    if df_laser.empty or df_acoes.empty:
        return pd.DataFrame()

    # Filtra apenas as interações (rosto/voz), ignorando o pescoço
    df_emocoes = df_acoes[df_acoes['categoria'] != 'Pescoco'].copy()
    if df_emocoes.empty:
        return pd.DataFrame()

    # Para o merge_asof funcionar, os dataframes DEVEM estar ordenados pelo tempo
    df_laser_sorted = df_laser.sort_values('timestamp')
    
    # APLICAÇÃO DA REVISÃO: Isolando as colunas para evitar conflitos de nomes no merge
    df_emocoes_sorted = df_emocoes.sort_values('timestamp')[['timestamp', 'nome_comando']].copy()

    # A MÁGICA: Para cada leitura do laser, descobre qual era a emoção ATIVA (olhando para trás no tempo)
    df_merged = pd.merge_asof(df_laser_sorted, df_emocoes_sorted, on='timestamp', direction='backward')

    # Remove as leituras de laser que aconteceram antes do robô fazer a primeira expressão
    df_merged = df_merged.dropna(subset=['nome_comando'])

    # Agrupa por emoção e calcula a distância média (em centímetros para ficar amigável)
    df_resultado = df_merged.groupby('nome_comando')['distancia_mm'].mean().reset_index()
    df_resultado['distancia_media_cm'] = df_resultado['distancia_mm'] 
    
    return df_resultado