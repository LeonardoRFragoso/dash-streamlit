import pandas as pd

def load_data(file_path, sheet_name='Multas'):
    """
    Carrega e faz o pré-processamento básico dos dados.
    """
    try:
        # Carrega a planilha
        df = pd.read_excel(file_path, sheet_name=sheet_name)

        # Converte colunas de datas para o formato datetime
        df['Dia da Consulta'] = pd.to_datetime(df['Dia da Consulta'], errors='coerce', dayfirst=True)
        df['Data da Infração'] = pd.to_datetime(df['Data da Infração'], errors='coerce', dayfirst=True)

        # Verificar se as colunas essenciais existem
        required_columns = ['Dia da Consulta', 'Data da Infração', 'Auto de Infração', 'Valor a Ser Pago (R$)']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"As colunas essenciais estão faltando: {', '.join(missing_columns)}")

        # Preprocessa o campo 'Valor a Ser Pago (R$)'
        df['Valor a Ser Pago (R$)'] = df['Valor a Ser Pago (R$)'].astype(str)\
            .str.replace(r'[^\d,.-]', '', regex=True)\
            .str.replace(r'\.(?=\d{3,})', '', regex=True)\
            .str.replace(',', '.')\
            .apply(lambda x: float(x) if x.replace('.', '', 1).isdigit() else 0)

        return df

    except Exception as e:
        print(f"Erro ao carregar os dados: {e}")
        raise

def clean_data(df):
    """
    Remove duplicados com base na coluna 'Auto de Infração'.
    """
    return df.drop_duplicates(subset=['Auto de Infração'])

def verify_columns(df, required_columns):
    """
    Verifica se as colunas essenciais estão presentes nos dados.
    """
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Colunas essenciais ausentes: {', '.join(missing_columns)}")

def preprocess_values(df):
    """
    Converte valores monetários e limpa dados de colunas numéricas específicas.
    """
    if 'Valor a Ser Pago (R$)' in df.columns:
        df['Valor a Ser Pago (R$)'] = df['Valor a Ser Pago (R$)'].astype(str)\
            .str.replace(r'[^\d,.-]', '', regex=True)\
            .str.replace(r'\.(?=\d{3,})', '', regex=True)\
            .str.replace(',', '.')\
            .apply(lambda x: float(x) if x.replace('.', '', 1).isdigit() else 0)
    return df
