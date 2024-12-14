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
    # Check if required columns exist
    required_columns = ['Placa Relacionada', 'Valor a ser pago R$']
    for col in required_columns:
        if col not in data.columns:
            raise KeyError(f"A coluna '{col}' não está presente no DataFrame.")

    # Ensure 'Valor a ser pago R$' is numeric
    data['Valor a ser pago R$'] = pd.to_numeric(
        data['Valor a ser pago R$'], errors='coerce'
    )

    # Group by 'Placa Relacionada' and count occurrences
    plate_distribution = data['Placa Relacionada'].value_counts().reset_index()
    plate_distribution.columns = ['Placa Relacionada', 'Frequência']

    # Sort by frequency
    plate_distribution = plate_distribution.sort_values(by='Frequência', ascending=False).head(10)

    # Create bar chart
    fig = px.bar(
        plate_distribution,
        x='Frequência',
        y='Placa Relacionada',
        orientation='h',
        labels={'Placa Relacionada': 'Placa do Veículo', 'Frequência': 'Número de Multas'},
        title="Distribuição de Multas por Placas Mais Multadas"
    )

    # Update layout for better readability
    fig.update_layout(
        yaxis=dict(autorange="reversed"),  # Invert y-axis to show the most frequent at the top
        template="plotly_dark"  # Use a dark theme (optional)
    )

    return fig
