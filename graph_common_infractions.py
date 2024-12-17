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
        infraction_data['Enquadramento da Infração'] + 
        "<br><b>" + infraction_data['Frequência'].astype(str) + " ocorrências</b>"
    )

    # Create bar chart
    fig = px.bar(
        infraction_data,
        x='Frequência',
        y='Descrição',
        text='Texto',  # Exibe o texto personalizado dentro das barras
        orientation='h',
        labels={'Descrição': 'Descrição da Infração', 'Frequência': ''},  # Remove título desnecessário do eixo X
        title="Infrações Mais Frequentes e suas Descrições"
    )

    # Personalizar o texto dentro das barras
    fig.update_traces(
        texttemplate='%{text}',  # Exibe texto com código e ocorrências
        textposition='inside',  # Texto dentro da barra
        insidetextanchor='start',  # Alinha o texto à esquerda para legibilidade
        textfont=dict(size=12, color='white'),  # Ajusta o tamanho e cor do texto
    )

    # Remover o eixo X
    fig.update_layout(
        xaxis=dict(visible=False),  # Remove o eixo inferior
        yaxis=dict(autorange="reversed"),  # Inverte a ordem do eixo Y
        template="plotly_white",  # Define um tema claro
        title_x=0.5,  # Centraliza o título
    )

    return fig
