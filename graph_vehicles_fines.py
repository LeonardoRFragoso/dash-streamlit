import pandas as pd
import plotly.express as px

def get_vehicle_fines_data(df):
    """
    Processa os dados para obter veículos com mais multas e seus valores totais.

    Parâmetros:
        df (DataFrame): O conjunto de dados contendo informações sobre multas.

    Retorna:
        DataFrame: Um DataFrame com os dados agregados por veículo.
    """
    # Nome correto da coluna de valor de multas
    value_column = 'Valor a ser pago R$'
    date_column = 'Data da Infração'

    # Verificar colunas essenciais
    required_columns = ['Placa Relacionada', value_column, 'Auto de Infração', date_column]
    for col in required_columns:
        if col not in df.columns:
            raise KeyError(f"A coluna '{col}' não está presente no DataFrame.")

    # Copiar o DataFrame
    df = df.copy()

    # Converter 'Data da Infração' para datetime e filtrar apenas o ano atual
    df[date_column] = pd.to_datetime(df[date_column], errors='coerce')
    df = df[df[date_column].dt.year == 2024]

    # Garantir que 'Valor a ser pago R$' esteja no formato numérico
    df[value_column] = (
        df[value_column]
        .astype(str)
        .str.replace(r'[^\d,.-]', '', regex=True)  # Remove caracteres não numéricos
        .str.replace(',', '.')
        .astype(float)
    )

    # Remover duplicatas baseadas no 'Auto de Infração' (registro único de multa)
    df = df.drop_duplicates(subset=['Auto de Infração'])

    # Agrupar os dados por 'Placa Relacionada'
    fines_by_vehicle = df.groupby('Placa Relacionada').agg(
        total_fines=(value_column, 'sum'),
        num_fines=('Auto de Infração', 'nunique')  # Contar apenas multas únicas
    ).reset_index()

    # Ordenar por número de multas em ordem decrescente
    fines_by_vehicle = fines_by_vehicle.sort_values(by='num_fines', ascending=False)

    return fines_by_vehicle

def create_vehicle_fines_chart(df):
    """
    Cria um gráfico de barras para os veículos com mais multas.

    Parâmetros:
        df (DataFrame): O conjunto de dados contendo informações sobre multas.

    Retorna:
        plotly.graph_objects.Figure: Um gráfico de barras mostrando os 10 veículos principais.
    """
    # Processar os dados
    fines_by_vehicle = get_vehicle_fines_data(df)

    # Verificar se há dados suficientes
    if fines_by_vehicle.empty:
        raise ValueError("Nenhum dado disponível para gerar o gráfico. Verifique os dados filtrados.")

    # Criar o gráfico
    fig = px.bar(
        fines_by_vehicle.head(10),  # Top 10 veículos
        x='Placa Relacionada',
        y='total_fines',
        color='num_fines',
        text='num_fines',
        labels={
            'Placa Relacionada': 'Veículo (Placa Relacionada)',
            'total_fines': 'Total das Multas (R$)',
            'num_fines': 'Número de Multas'
        }
    )

    # Ajustar o estilo do gráfico
    fig.update_traces(
        texttemplate='R$ %{y:,.2f}<br>%{text} multas',
        textposition='inside'
    )

    fig.update_layout(
        title="Top 10 Veículos com Mais Multas (Ano Atual)",
        xaxis_title='',
        yaxis_title='Total das Multas (R$)',
        coloraxis_colorbar=dict(title='Número de Multas'),
        template="plotly_white"
    )

    return fig
