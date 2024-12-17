import pandas as pd
import plotly.express as px
from datetime import datetime

def create_fines_accumulated_chart(data, period='M'):
    """
    Create a line chart to display the accumulated fine values and count of fines by month or week.
    Ensure all months of the current year are displayed, even with no data.

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

    # Filter for the current year
    current_year = datetime.now().year
    data = data[data['Data da Infração'].dt.year == current_year]

    # Create a complete list of months for the current year
    all_months = pd.date_range(start=f"{current_year}-01-01", end=f"{current_year}-12-31", freq='MS')
    months_df = pd.DataFrame({'Período': all_months})

    # Aggregate data by month
    data['Período'] = data['Data da Infração'].dt.to_period('M').dt.to_timestamp()
    accumulated_fines = data.groupby('Período').agg(
        Valor_Acumulado=('Valor a ser pago R$', 'sum'),
        Quantidade_de_Multas=('Valor a ser pago R$', 'size')
    ).reset_index()

    # Merge the complete months list with the aggregated data
    accumulated_fines = pd.merge(months_df, accumulated_fines, on='Período', how='left')
    accumulated_fines['Valor_Acumulado'].fillna(0, inplace=True)  # Fill missing values with 0
    accumulated_fines['Quantidade_de_Multas'].fillna(0, inplace=True)

    # Create the line chart with markers
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

    # Adicionar marcadores e personalizar o estilo
    fig.update_traces(
        mode='lines+markers',  # Adiciona marcadores nos pontos da linha
        marker=dict(size=8, symbol='circle', color='blue', line=dict(width=2, color='DarkSlateGrey')),
        line=dict(color='royalblue', width=2)
    )

    # Update layout for better readability
    fig.update_layout(
        xaxis_title="",
        yaxis_title="Valor Acumulado (R$)",
        template="plotly_white",  # Light theme
        title_x=0.5,  # Center the title
        title_font_size=20,
        title_font=dict(family="Arial", weight="bold"),
        hovermode="x unified"  # Hover unificado na vertical
    )

    return fig
