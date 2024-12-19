import pandas as pd
from datetime import datetime

def preprocess_data(data):
    """
    Ensure data is preprocessed to align with required structure and formats.

    Parameters:
        data (DataFrame): The raw dataset containing fines information.

    Returns:
        DataFrame: Cleaned and standardized dataset.
    """
    # Rename columns to standardize
    column_mapping = {
        "Valor original R$": "Valor Original R$",
        "Valor a ser pago R$": "Valor a ser pago R$",
        "Data da Infração": "Data da Infração",
        "Status de Pagamento": "Status de Pagamento",
        "Auto de Infração": "Auto de Infração",
    }
    data.rename(columns=column_mapping, inplace=True)

    # Ensure 'Data da Infração' is a datetime object
    data['Data da Infração'] = pd.to_datetime(data['Data da Infração'], format='%d/%m/%Y', errors='coerce')

    # Standardize monetary values
    data['Valor a ser pago R$'] = (
        data['Valor a ser pago R$']
        .astype(str)
        .replace({r'[^\d,.-]': '', r'\.(?=\d{3,})': '', ',': '.'}, regex=True)
    )
    data['Valor a ser pago R$'] = pd.to_numeric(data['Valor a ser pago R$'], errors='coerce').fillna(0)

    # Drop rows with essential missing data
    required_columns = ['Data da Infração', 'Valor a ser pago R$', 'Auto de Infração', 'Status de Pagamento']
    data.dropna(subset=required_columns, inplace=True)

    return data

def calculate_metrics(data):
    """
    Calculate key metrics from the dataset.

    Parameters:
        data (DataFrame): The dataset containing fines information.

    Returns:
        tuple: Total fines, total unpaid amount, fines in the current month.
    """
    # Verify required columns
    required_columns = ['Data da Infração', 'Valor a ser pago R$', 'Auto de Infração', 'Status de Pagamento']
    if not all(col in data.columns for col in required_columns):
        raise ValueError(f"Faltam colunas essenciais: {', '.join([col for col in required_columns if col not in data.columns])}")

    # Copy data to avoid modifications
    data = data.copy()

    # Calculate total fines (unique 'Auto de Infração')
    total_multas = data['Auto de Infração'].nunique()

    # Calculate total unpaid amount
    valor_total_a_pagar = data.loc[data['Status de Pagamento'] == 'NÃO PAGO', 'Valor a ser pago R$'].sum()

    # Current month and year
    current_month = datetime.now().month
    current_year = datetime.now().year

    # Calculate fines in the current month
    multas_mes_atual = data.loc[
        (data['Data da Infração'].dt.month == current_month) & 
        (data['Data da Infração'].dt.year == current_year),
        'Auto de Infração'
    ].nunique()

    return total_multas, valor_total_a_pagar, multas_mes_atual

# Example usage
if __name__ == "__main__":
    # Load your dataset here
    file_path = "ResultadosOrganizados.xlsx"
    raw_data = pd.read_excel(file_path)

    # Preprocess the data
    clean_data = preprocess_data(raw_data)

    # Calculate metrics
    total_fines, total_unpaid, current_month_fines = calculate_metrics(clean_data)

    print(f"Total Fines: {total_fines}")
    print(f"Total Unpaid Amount: R$ {total_unpaid:,.2f}")
    print(f"Fines in Current Month: {current_month_fines}")
