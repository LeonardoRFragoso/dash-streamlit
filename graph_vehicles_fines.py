import pandas as pd
import plotly.express as px

def get_vehicle_fines_data(df):
    """
    Process data to get vehicles with the most fines and their total amounts.

    Parameters:
        df (DataFrame): The dataset containing fines information.

    Returns:
        DataFrame: A DataFrame with aggregated data for fines by vehicle.
    """
    # Nome correto da coluna de valor de multas
    value_column = 'Valor a ser pago R$'

    # Verificar se as colunas necessárias existem
    required_columns = ['Placa Relacionada', value_column, 'Auto de Infração']
    for col in required_columns:
        if col not in df.columns:
            raise KeyError(f"A coluna '{col}' não está presente no DataFrame.")

    # Fazer uma cópia do DataFrame para evitar modificar o original
    df = df.copy()

    # Garantir que a coluna de valores está no formato numérico
    df[value_column] = (
        df[value_column]
        .astype(str)
        .replace({r'[^\d,.-]': '', r'\.(?=\d{3,})': '', ',': '.'}, regex=True)
    )
    df[value_column] = pd.to_numeric(df[value_column], errors='coerce')

    # Agrupar os dados por 'Placa Relacionada'
    fines_by_vehicle = df.groupby('Placa Relacionada').agg(
        total_fines=(value_column, 'sum'),
        num_fines=('Auto de Infração', 'count')
    ).reset_index()

    # Ordenar por número de multas em ordem decrescente
    fines_by_vehicle = fines_by_vehicle.sort_values(by='num_fines', ascending=False)

    return fines_by_vehicle

def create_vehicle_fines_chart(df):
    """
    Create a bar chart for vehicles with the most fines.

    Parameters:
        df (DataFrame): The dataset containing fines information.

    Returns:
        plotly.graph_objects.Figure: A bar chart showing the top 10 vehicles with the most fines.
    """
    # Processar os dados
    fines_by_vehicle = get_vehicle_fines_data(df)

    # Criar o gráfico
    fig = px.bar(
        fines_by_vehicle.head(10),  # Limitar aos 10 veículos principais
        x='Placa Relacionada',
        y='total_fines',
        color='num_fines',
        labels={
            'Placa Relacionada': 'Veículo (Placa Relacionada)',
            'total_fines': 'Total das Multas (R$)',
            'num_fines': 'Número de Multas'
        },
        title='Top 10 Veículos com Mais Multas e Valores Totais'
    )

    fig.update_layout(
        xaxis_title='Veículo (Placa Relacionada)',
        yaxis_title='Total das Multas (R$)',
        coloraxis_colorbar=dict(title='Número de Multas'),
        template="plotly_dark"  # Tema opcional escuro
    )

    return fig
