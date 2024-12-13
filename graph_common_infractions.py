import pandas as pd
import plotly.express as px

def create_common_infractions_chart(data):
    """
    Create a bar chart to display the most common infractions and their descriptions.

    Parameters:
        data (DataFrame): The filtered data containing fines information.

    Returns:
        fig (plotly.graph_objects.Figure): A bar chart of the most common infractions.
    """
    # Group by 'Enquadramento' to calculate frequencies
    infraction_data = data.groupby(['Enquadramento', 'Descrição'])['Auto de Infração'].count().reset_index()
    infraction_data.rename(columns={'Auto de Infração': 'Frequência'}, inplace=True)

    # Sort by frequency
    infraction_data = infraction_data.sort_values(by='Frequência', ascending=False).head(10)

    # Create bar chart
    fig = px.bar(
        infraction_data,
        x='Frequência',
        y='Descrição',
        text='Enquadramento',
        orientation='h',
        labels={'Descrição': 'Descrição da Infração', 'Frequência': 'Número de Ocorrências'},
        title="Infrações Mais Frequentes e suas Descrições"
    )

    # Update layout for better readability
    fig.update_layout(
        yaxis=dict(autorange="reversed"),  # Invert y-axis to show the most frequent at the top
        template="plotly_dark"  # Use a dark theme (optional)
    )

    return fig
