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
    # Group by 'Enquadramento da Infração' to calculate frequencies
    infraction_data = data.groupby(['Enquadramento da Infração', 'Descrição'])['Auto de Infração'].count().reset_index()
    infraction_data.rename(columns={'Auto de Infração': 'Frequência'}, inplace=True)

    # Sort by frequency
    infraction_data = infraction_data.sort_values(by='Frequência', ascending=False).head(10)

    # Criar texto combinando código da infração e número de ocorrências
    infraction_data['Texto'] = (
        "Código: " + infraction_data['Enquadramento da Infração'] + 
        "<br>" + infraction_data['Frequência'].astype(str) + " ocorrências"
    )

    # Create bar chart
    fig = px.bar(
        infraction_data,
        x='Frequência',
        y='Descrição',
        text='Texto',  # Texto personalizado com código e quantidade
        orientation='h',
        labels={'Descrição': 'Descrição da Infração', 'Frequência': 'Número de Ocorrências'},
        title="Infrações Mais Frequentes e suas Descrições"
    )

    # Personalizar o texto dentro das barras
    fig.update_traces(
        texttemplate='%{text}',  # Exibe o texto criado acima
        textposition='inside'  # Texto dentro da barra
    )

    # Atualiza o layout para melhor visualização
    fig.update_layout(
        yaxis=dict(autorange="reversed"),  # Inverte a ordem do eixo Y
        xaxis_title="",  # Remove título do eixo X
        template="plotly_white",  # Define um tema claro
        showlegend=False  # Remove legenda desnecessária
    )

    return fig
