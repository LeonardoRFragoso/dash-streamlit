import pandas as pd
import plotly.express as px
from datetime import datetime

def create_fines_accumulated_chart(data, data_inicial=None, data_final=None, period='M'):
    """
    Cria um gráfico de linhas para exibir a contagem de multas acumuladas por período.

    Parâmetros:
        data (DataFrame): Os dados filtrados contendo informações sobre as multas.
        data_inicial (str ou datetime, opcional): Data inicial para o filtro do período.
        data_final (str ou datetime, opcional): Data final para o filtro do período.
        period (str): O período para agrupamento ('M' para mensal, 'W' para semanal).

    Retorna:
        fig (plotly.graph_objects.Figure): Um gráfico de linhas mostrando a quantidade de multas por período.
    """
    # Verificar se as colunas essenciais existem
    required_columns = ['Data da Infração', 'Valor a ser pago R$']
    for col in required_columns:
        if col not in data.columns:
            raise KeyError(f"A coluna '{col}' não está presente no DataFrame.")

    # Garantir que 'Data da Infração' seja um objeto datetime
    data['Data da Infração'] = pd.to_datetime(data['Data da Infração'], errors='coerce')

    # Filtrar valores inválidos
    invalid_dates = data['Data da Infração'].isna()
    if invalid_dates.any():
        print(f"Entradas inválidas em 'Data da Infração' removidas: {data[invalid_dates]}")

    data = data.dropna(subset=['Data da Infração'])

    # Filtrar os dados pelo período especificado
    if data_inicial is None:
        data_inicial = data['Data da Infração'].min()
    if data_final is None:
        data_final = data['Data da Infração'].max()

    data = data[(data['Data da Infração'] >= pd.to_datetime(data_inicial)) &
                (data['Data da Infração'] <= pd.to_datetime(data_final))]

    # Criar lista completa de períodos dentro do intervalo
    all_periods = pd.date_range(start=data_inicial, end=data_final, freq='MS' if period == 'M' else 'W')
    periods_df = pd.DataFrame({'Período': all_periods})

    # Agregar dados pelo período
    data['Período'] = data['Data da Infração'].dt.to_period(period).dt.to_timestamp()
    fines_by_period = data.groupby('Período').agg(
        Quantidade_de_Multas=('Valor a ser pago R$', 'size')
    ).reset_index()

    # Mesclar lista de períodos completa com os dados agregados
    fines_by_period = pd.merge(periods_df, fines_by_period, on='Período', how='left')
    fines_by_period['Quantidade_de_Multas'].fillna(0, inplace=True)  # Preencher valores ausentes com 0

    # Criar o gráfico de linhas com marcadores
    fig = px.line(
        fines_by_period,
        x='Período',
        y='Quantidade_de_Multas',
        labels={
            'Período': 'Período',
            'Quantidade_de_Multas': 'Quantidade de Multas'
        }
    )

    # Adicionar marcadores e personalizar estilo
    fig.update_traces(
        mode='lines+markers',  # Adicionar marcadores na linha
        marker=dict(size=8, color='blue', line=dict(width=2, color='DarkSlateGrey')),
        line=dict(color='royalblue', width=2)
    )

    # Atualizar layout para melhor legibilidade
    fig.update_layout(
        xaxis_title="",
        yaxis_title="Quantidade de Multas",
        template="plotly_white",  # Tema claro
        title="",  # Remover o título automático
        title_x=0.5,  # Centralizar o título
        hovermode="x unified"  # Hover unificado
    )

    return fig
