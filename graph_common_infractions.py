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
    # Agrupar por 'Enquadramento da Infração' para calcular frequências
    infraction_data = data.groupby(['Enquadramento da Infração', 'Descrição'])['Auto de Infração'].count().reset_index()
    infraction_data.rename(columns={'Auto de Infração': 'Frequência'}, inplace=True)

    # Ordenar pelos mais frequentes
    infraction_data = infraction_data.sort_values(by='Frequência', ascending=False).head(10)

    # Criar o texto formatado lado a lado
    infraction_data['Texto'] = (
        infraction_data['Enquadramento da Infração'] + " | " + 
        infraction_data['Frequência'].astype(str) + " ocorrências"
    )

    # Criar o gráfico de barras
    fig = px.bar(
        infraction_data,
        x='Frequência',
        y='Descrição',
        text='Texto',  # Texto com código e ocorrências lado a lado
        orientation='h',
        title="Infrações Mais Frequentes e suas Descrições",
        labels={'Descrição': 'Descrição da Infração', 'Frequência': 'Ocorrências'}
    )

    # Ajustar a legibilidade do texto
    fig.update_traces(
        texttemplate='%{text}',  # Formata o texto
        textposition='inside',   # Mantém texto dentro da barra
        insidetextanchor='middle',  # Centraliza o texto dentro da barra
        textfont=dict(size=16, color='white'),  # Aumenta tamanho e define cor branca
        marker_color='#007bff'  # Cor das barras em azul
    )

    # Ajustar layout
    fig.update_layout(
        xaxis_title="",  # Remove título do eixo X
        yaxis_title="",  # Remove título do eixo Y
        template="plotly_white",  # Tema claro
        title_x=0.5,  # Centraliza o título
        margin=dict(l=50, r=50, t=50, b=50)  # Ajusta margens
    )

    return fig
