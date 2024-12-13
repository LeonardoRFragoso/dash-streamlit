import pandas as pd
import plotly.express as px

def get_vehicle_fines_data(df):
    """Process data to get vehicles with the most fines and their total amounts."""
    # Group data by 'Placa', summing the 'Valor a Pagar (R$)' and counting the fines
    fines_by_vehicle = df.groupby('Placa').agg(
        total_fines=('Valor a Pagar (R$)', 'sum'),
        num_fines=('Auto de Infração', 'count')
    ).reset_index()

    # Sort by the number of fines, descending
    fines_by_vehicle = fines_by_vehicle.sort_values(by='num_fines', ascending=False)

    return fines_by_vehicle

def create_vehicle_fines_chart(df):
    """Create a bar chart for vehicles with the most fines."""
    # Process data
    fines_by_vehicle = get_vehicle_fines_data(df)

    # Create the chart
    fig = px.bar(
        fines_by_vehicle.head(10),  # Limit to top 10 vehicles
        x='Placa',
        y='total_fines',
        color='num_fines',
        labels={'Placa': 'Veículo (Placa)', 'total_fines': 'Total das Multas (R$)', 'num_fines': 'Número de Multas'},
        title='Top 10 Veículos com Mais Multas e Valores Totais'
    )

    fig.update_layout(
        xaxis_title='Veículo (Placa)',
        yaxis_title='Total das Multas (R$)',
        coloraxis_colorbar=dict(title='Número de Multas')
    )

    return fig
