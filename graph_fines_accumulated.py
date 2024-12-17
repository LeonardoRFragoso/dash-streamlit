import pandas as pd
import plotly.express as px
from datetime import datetime

def create_fines_accumulated_chart(data, period='M'):
    """
    Create a line chart to display the count of fines per month with better relevance.

    Parameters:
        data (DataFrame): The filtered data containing fines information.
        period (str): The period for grouping ('M' for monthly, 'W' for weekly).

    Returns:
        fig (plotly.graph_objects.Figure): A line chart showing the number of fines by period.
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
    monthly_fines = data.groupby('Período').agg(
        Quantidade_de_Multas=('Valor a ser pago R$', 'size')
    ).reset_index()

    # Merge the complete months list with the aggregated data
    monthly_fines = pd.merge(months_df, monthly_fines, on='Período', how='left')
    monthly_fines['Quantidade_de_Multas'].fillna(0, inplace=True)  # Fill missing values with 0

    # Create the line chart with markers
    fig = px.line(
        monthly_fines,
        x='Período',
        y='Quantidade_de_Multas',
        labels={
            'Período': 'Período',
            'Quantidade_de_Multas': 'Quantidade de Multas'
        },
        title="Quantidade de Multas por Mês em 2024"
    )

    # Add markers and customize style
    fig.update_traces(
        mode='lines+markers',  # Add markers on the line
        marker=dict(size=8, color='blue', line=dict(width=2, color='DarkSlateGrey')),
        line=dict(color='royalblue', width=2)
    )

    # Update layout for better readability
    fig.update_layout(
        xaxis_title="",
        yaxis_title="Quantidade de Multas",
        template="plotly_white",  # Light theme
        title_x=0.5,  # Center the title
        title_font_size=20,
        title_font=dict(family="Arial", weight="bold"),
        hovermode="x unified"  # Unified hover
    )

    return fig
