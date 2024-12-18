import pandas as pd
import plotly.express as px
from datetime import datetime

def create_fines_accumulated_chart(data, period='M'):
    """
    Cria um gráfico de linhas para exibir a quantidade e o valor acumulado de multas por período (2024).

    Parâmetros:
        data (DataFrame): Os dados filtrados contendo informações sobre as multas.
        period (str): O período para agrupamento ('M' para mensal, 'W' para semanal).

    Retorna:
        fig (plotly.graph_objects.Figure): Um gráfico de linhas mostrando quantidade e valor acumulado de multas.
    """
    # Garantir que 'Data da Infração' seja datetime
    data['Data da Infração'] = pd.to_datetime(data['Data da Infração'], errors='coerce')

    # Remover linhas com datas inválidas
    data = data.dropna(subset=['Data da Infração'])
    
    # Filtrar apenas o ano atual (2024)
    data = data[data['Data da Infração'].dt.year == 2024]

    # Garantir que 'Valor a ser pago R$' esteja em formato numérico
    data['Valor a ser pago R$'] = (
        data['Valor a ser pago R$']
        .astype(str)
        .str.replace(r'[^\d,.-]', '', regex=True)
        .str.replace(',', '.')
        .astype(float)
    )

    # Criar um campo de período com base nos meses do ano
    data['Período'] = data['Data da Infração'].dt.to_period('M').dt.to_timestamp()

    # Agregar dados: contar multas e somar valores por período
    fines_by_period = data.groupby('Período').agg(
        Quantidade_de_Multas=('Auto de Infração', 'nunique'),
        Valor_Total=('Valor a ser pago R$', 'sum')
    ).reset_index()

    # Criar o gráfico com duas linhas: Quantidade de Multas e Valor Total
    fig = px.line(
        fines_by_period,
        x='Período',
        y=['Quantidade_de_Multas', 'Valor_Total'],
        labels={
            'value': 'Total de Multas',
            'Período': 'Período'
        },
        title=''
    )


    # Personalizar o layout
    fig.update_traces(mode='lines+markers', marker=dict(size=8))
    fig.update_layout(
        xaxis_title="",
        yaxis_title="Valores",
        template="plotly_white",
        legend=dict(title="Métricas")
    )

    return fig
