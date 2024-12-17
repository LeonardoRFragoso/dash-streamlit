import pandas as pd
import plotly.express as px
from datetime import datetime

def create_fines_accumulated_chart(data, period='M'):
    """
    Create a line chart to display the accumulated fine values and count of fines by month or week.
    Now restricted to display only the months of the current year.

    Parameters:
        data (DataFrame): The filtered data containing fines information.
        period (str): The period for grouping ('M' for monthly, 'W' for weekly).

    Returns:
        fig (plotly.graph_objects.Figure): A line chart showing accumulated fine values and fine counts.
    """
    # Check if required columns exist
    required_columns = ['Data da Infração', 'Valor a ser pago R$']
    for col in required_columns:
        if col not in data.columns:
            raise KeyError(f"A coluna '{col}' não está presente no DataFrame.")

    # Ensure 'Data da Infração' is a datetime object
    data['Data da Infração'] = pd.to_datetime(data['Data da Infração'], errors='coerce')

    # Filter out invalid dates
    data = data.dropna(subset=['Data da Infração'])

    # Filter data for the current year only
    current_year = datetime.now().year
    data = data[data['Data da Infração'].dt.year == current_year]

    # Group data by the selected period and calculate the accumulated value and count
    if period == 'M':
        data['Período'] = data['Data da Infração'].dt.to_period('M').dt.to_timestamp()
    elif period == 'W':
        data['Período'] = data['Data da Infração'].dt.to_period('W').dt.to_timestamp()
    else:
        raise ValueError("Período inválido. Use 'M' para mensal ou 'W' para semanal.")

    accumulated_fines = data.groupby('Período').agg(
        Valor_Acumulado=('Valor a ser pago R$', 'sum'),
        Quantidade_de_Multas=('Valor a ser pago R$', 'size')
    ).reset_index()

    # Create line chart
    fig = px.line(
        accumulated_fines,
        x='Período',
        y='Valor_Acumulado',
        labels={
            'Período': 'Período', 
            'Valor_Acumulado': 'Valor Acumulado (R$)',
            'Quantidade_de_Multas': 'Quantidade de Multas'
        },
        title="Valores das Multas Acumulados por Período",
        hover_data=['Quantidade_de_Multas']
    )

    # Update layout for better readability
    fig.update_layout(
        xaxis_title="",
        yaxis_title="Valor Acumulado (R$)",
        template="plotly_white",  # Tema claro
        title_x=0.5,  # Centraliza o título
        title_font_size=20,
        title_font=dict(family="Arial", weight="bold")
    )

    return fig
