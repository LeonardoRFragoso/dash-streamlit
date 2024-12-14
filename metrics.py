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
    # Ensure a copy of the DataFrame to avoid modifying the original data
    data = data.copy()

    # Ensure 'Data da Infração' is in datetime format
    data['Data da Infração'] = pd.to_datetime(data['Data da Infração'], format='%d/%m/%Y', errors='coerce')

    # Clean the 'Valor a ser pago R$' column by removing dots (thousands separator) and replacing commas (decimal separator)
    data['Valor a ser pago R$'] = (
        data['Valor a ser pago R$']
        .astype(str)
        .replace({r'[^\d,.-]': '', r'\.(?=\d{3,})': '', ',': '.'}, regex=True)
    )

    # Convert 'Valor a ser pago R$' to numeric, forcing errors to NaN for non-numeric values
    data['Valor a ser pago R$'] = pd.to_numeric(data['Valor a ser pago R$'], errors='coerce')

    # Calculate total number of fines
    total_multas = data['Auto de Infração'].nunique()

    # Calculate total amount to pay for fines that are not paid
    valor_total_a_pagar = data.loc[data['Status de Pagamento'] == 'NÃO PAGO', 'Valor a ser pago R$'].sum()

    # Get current month and year
    current_month = datetime.now().month
    current_year = datetime.now().year

    # Calculate the number of fines in the current month and year
    multas_mes_atual = data.loc[
        (data['Data da Infração'].dt.month == current_month) &
        (data['Data da Infração'].dt.year == current_year),
        'Auto de Infração'
    ].nunique()

    return total_multas, valor_total_a_pagar, multas_mes_atual
