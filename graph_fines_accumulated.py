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
    # Garantir que 'Data da Infração' seja datetime
    data['Data da Infração'] = pd.to_datetime(data['Data da Infração'], errors='coerce')
    
    # Remover linhas com datas inválidas
    data = data.dropna(subset=['Data da Infração'])
    
    # Validar datas iniciais e finais
    if data_inicial is None or not pd.to_datetime(data_inicial, errors='coerce'):
        data_inicial = data['Data da Infração'].min()
    else:
        data_inicial = pd.to_datetime(data_inicial, errors='coerce')
    
    if data_final is None or not pd.to_datetime(data_final, errors='coerce'):
        data_final = data['Data da Infração'].max()
    else:
        data_final = pd.to_datetime(data_final, errors='coerce')

    # Filtrar os dados pelo período
    data = data[(data['Data da Infração'] >= data_inicial) & (data['Data da Infração'] <= data_final)]

    # Criar lista completa de períodos dentro do intervalo
    all_periods = pd.date_range(start=data_inicial, end=data_final, freq='MS' if period == 'M' else 'W')
    periods_df = pd.DataFrame({'Período': all_periods})

    # Agregar dados pelo período
    data['Período'] = data['Data da Infração'].dt.to_period(period).dt.to_timestamp()
    fines_by_period = data.groupby('Período').size().reset_index(name='Quantidade_de_Multas')

    # Mesclar lista de períodos completa com os dados agregados
    fines_by_period = pd.merge(periods_df, fines_by_period, on='Período', how='left')
    fines_by_period['Quantidade_de_Multas'].fillna(0, inplace=True)

    # Criar o gráfico
    fig = px.line(
        fines_by_period,
        x='Período',
        y='Quantidade_de_Multas',
        labels={'Período': 'Período', 'Quantidade_de_Multas': 'Quantidade de Multas'}
    )

    fig.update_traces(mode='lines+markers', marker=dict(size=8))
    fig.update_layout(xaxis_title="", yaxis_title="Quantidade de Multas", template="plotly_white")

    return fig
