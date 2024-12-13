import pandas as pd
import plotly.express as px

def create_weekday_infractions_chart(data):
    """
    Create a bar chart to display the number of fines distributed by day of the week.

    Parameters:
        data (DataFrame): The filtered data containing fines information.

    Returns:
        fig (plotly.graph_objects.Figure): A bar chart showing the distribution of fines by day of the week.
    """
    # Check if required column exists
    if 'Data da Infração' not in data.columns:
        raise KeyError("A coluna 'Data da Infração' não está presente no DataFrame.")

    # Ensure 'Data da Infração' is a datetime object
    data['Data da Infração'] = pd.to_datetime(data['Data da Infração'], errors='coerce')

    # Filter out invalid dates
    data = data.dropna(subset=['Data da Infração'])

    # Extract day of the week
    data.loc[:, 'Dia da Semana'] = data['Data da Infração'].dt.day_name(locale='pt_BR') 

    # Count fines by day of the week
    weekday_counts = data['Dia da Semana'].value_counts().reindex(
        ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    ).reset_index()
    weekday_counts.columns = ['Dia da Semana', 'Quantidade de Multas']

    # Create bar chart
    fig = px.bar(
        weekday_counts,
        x='Dia da Semana',
        y='Quantidade de Multas',
        labels={
            'Dia da Semana': 'Dia da Semana',
            'Quantidade de Multas': 'Quantidade de Multas'
        },
        title="Distribuição de Multas por Dia da Semana",
        text='Quantidade de Multas'
    )

    # Update layout for better readability
    fig.update_traces(textposition='outside')
    fig.update_layout(
        xaxis_title="Dia da Semana",
        yaxis_title="Quantidade de Multas",
        template="plotly_dark"  # Use a dark theme (optional)
    )

    return fig
