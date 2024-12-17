import pandas as pd
from datetime import datetime

def calculate_metrics(data):
    """
    Calculate key metrics from the dataset.

    Parameters:
        data (DataFrame): The dataset containing fines information.

    Returns:
        tuple: Total fines, total unpaid amount, fines in the current month.
    """
    # Verificar se as colunas essenciais estão presentes
    required_columns = ['Data da Infração', 'Valor a ser pago R$', 'Auto de Infração', 'Status de Pagamento']
    if not all(col in data.columns for col in required_columns):
        raise ValueError(f"Faltam colunas essenciais: {', '.join([col for col in required_columns if col not in data.columns])}")

    # Fazer uma cópia dos dados para evitar modificações no original
    data = data.copy()

    # Garantir que 'Data da Infração' está no formato datetime
    data['Data da Infração'] = pd.to_datetime(data['Data da Infração'], format='%d/%m/%Y', errors='coerce')

    # Tratar a coluna 'Valor a ser pago R$'
    data['Valor a ser pago R$'] = (
        data['Valor a ser pago R$']
        .astype(str)
        .replace({r'[^\d,.-]': '', r'\.(?=\d{3,})': '', ',': '.'}, regex=True)
    )

    # Converter 'Valor a ser pago R$' para numérico, forçando NaN para valores não numéricos
    data['Valor a ser pago R$'] = pd.to_numeric(data['Valor a ser pago R$'], errors='coerce')

    # Tratar valores NaN na coluna 'Valor a ser pago R$', substituindo por 0
    data['Valor a ser pago R$'].fillna(0, inplace=True)

    # Calcular o total de multas (Auto de Infração únicos)
    total_multas = data['Auto de Infração'].nunique()

    # Calcular o valor total a pagar das multas não pagas
    valor_total_a_pagar = data.loc[data['Status de Pagamento'] == 'NÃO PAGO', 'Valor a ser pago R$'].sum()

    # Obter o mês e ano atual
    current_month = datetime.now().month
    current_year = datetime.now().year

    # Calcular o número de multas no mês e ano atual
    multas_mes_atual = data.loc[
        (data['Data da Infração'].dt.month == current_month) & 
        (data['Data da Infração'].dt.year == current_year),
        'Auto de Infração'
    ].nunique()

    return total_multas, valor_total_a_pagar, multas_mes_atual
