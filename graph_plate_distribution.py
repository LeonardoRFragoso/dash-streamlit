import pandas as pd
import plotly.express as px

def create_plate_distribution_chart(data):
    """
    Create a bar chart to display the distribution of fines by plate type.

    Parameters:
        data (DataFrame): The filtered data containing fines information.

    Returns:
        fig (plotly.graph_objects.Figure): A bar chart showing distribution by plate type.
    """
    # Check if column 'Placa' exists
    if 'Placa' not in data.columns:
        raise KeyError("A coluna 'Placa' não está presente no DataFrame.")

    # Group by 'Placa' and count occurrences
    plate_distribution = data['Placa'].value_counts().reset_index()
    plate_distribution.columns = ['Placa', 'Frequência']

    # Sort by frequency
    plate_distribution = plate_distribution.sort_values(by='Frequência', ascending=False).head(10)

    # Create bar chart
    fig = px.bar(
        plate_distribution,
        x='Frequência',
        y='Placa',
        orientation='h',
        labels={'Placa': 'Placa do Veículo', 'Frequência': 'Número de Multas'},
        title="Distribuição de Multas por Placas Mais Multadas"
    )

    # Update layout for better readability
    fig.update_layout(
        yaxis=dict(autorange="reversed"),  # Invert y-axis to show the most frequent at the top
        template="plotly_dark"  # Use a dark theme (optional)
    )

    return fig
