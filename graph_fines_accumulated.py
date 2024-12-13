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
    if 'Data da Infração' not in data.columns or 'Valor a Pagar (R$)' not in data.columns:
        raise KeyError("As colunas 'Data da Infração' e 'Valor a Pagar (R$)' não estão presentes no DataFrame.")

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
        Valor_Acumulado=('Valor a Pagar (R$)', 'sum'),
        Quantidade_de_Multas=('Valor a Pagar (R$)', 'size')
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
        xaxis_title="Período",
        yaxis_title="Valor Acumulado (R$)",
        template="plotly_dark"  # Use a dark theme (optional)
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
    if 'Local' not in data.columns or 'Valor a Pagar (R$)' not in data.columns:
        raise KeyError("As colunas 'Local' e 'Valor a Pagar (R$)' não estão presentes no DataFrame.")

    # Aggregate data by location
    ranking_data = data.groupby('Local').agg(
        Valor_Total=('Valor a Pagar (R$)', 'sum'),
        Quantidade_Multas=('Valor a Pagar (R$)', 'size')
    ).reset_index()

    # Sort by total value of fines in descending order
    ranking_data = ranking_data.sort_values(by='Valor_Total', ascending=False)

    return ranking_data
