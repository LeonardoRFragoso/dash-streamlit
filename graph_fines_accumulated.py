import pandas as pd
import plotly.express as px

def create_fines_accumulated_chart(data, period='M'):
    """
    Create a line chart to display the accumulated fine values and count of fines by month or week.

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

    # Create line chart without a title
    fig = px.line(
        accumulated_fines,
        x='Período',
        y='Valor_Acumulado',
        labels={
            'Período': 'Período', 
            'Valor_Acumulado': 'Valor Acumulado (R$)',
            'Quantidade_de_Multas': 'Quantidade de Multas'
        },
        hover_data=['Quantidade_de_Multas']
    )

    # Update layout for better readability
    fig.update_layout(
        title="",  # Remover o título automático
        xaxis_title="",
        yaxis_title="Valor Acumulado (R$)",
        template="plotly_dark",  # Use a dark theme (optional)
        title_x=0.5,  # Center the title
        title_font_size=20,
        title_font=dict(family="Arial", weight="bold")
    )

    return fig

def create_location_ranking(data):
    """
    Create a DataFrame ranking locations by total fines value and count of fines.

    Parameters:
        data (DataFrame): The filtered data containing fines information.

    Returns:
        ranking_data (DataFrame): A DataFrame with the ranking of locations.
    """
    # Check if required columns exist
    required_columns = ['Local da Infração', 'Valor a ser pago R$']
    for col in required_columns:
        if col not in data.columns:
            raise KeyError(f"A coluna '{col}' não está presente no DataFrame.")

    # Aggregate data by location
    ranking_data = data.groupby('Local da Infração').agg(
        Valor_Total=('Valor a ser pago R$', 'sum'),
        Quantidade_Multas=('Valor a ser pago R$', 'size')
    ).reset_index()

    # Sort by total value of fines in descending order
    ranking_data = ranking_data.sort_values(by='Valor_Total', ascending=False)

    return ranking_data
