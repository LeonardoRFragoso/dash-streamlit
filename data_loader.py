import pandas as pd

def load_data(file_path):
    """Load and preprocess the data."""
    # Carrega a planilha
    df = pd.read_excel(file_path, sheet_name='Multas')

    # Converte colunas de datas para o formato datetime
    df['Dia da Consulta'] = pd.to_datetime(df['Dia da Consulta'], errors='coerce', dayfirst=True)
    df['Data da Infração'] = pd.to_datetime(df['Data da Infração'], errors='coerce', dayfirst=True)

    # Preprocessa o campo 'Valor a Ser Pago (R$)'
    df['Valor a Ser Pago (R$)'] = df['Valor a Ser Pago (R$)'].astype(str)\
        .str.replace(r'[^\d,.-]', '', regex=True)\
        .str.replace(r'\.(?=\d{3,})', '', regex=True)\
        .str.replace(',', '.')\
        .apply(lambda x: float(x) if x.replace('.', '', 1).isdigit() else 0)

    return df

def clean_data(df):
    """Remove duplicates based on 'Auto de Infração'."""
    # Remove duplicados com base na coluna 'Auto de Infração'
    return df.drop_duplicates(subset=['Auto de Infração'])
