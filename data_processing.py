import pandas as pd

def carregar_e_limpar_dados(carregar_dados_func):
    """
    Carrega e faz o pré-processamento básico dos dados.
    """
    try:
        df = carregar_dados_func()
        df['Dia da Consulta'] = pd.to_datetime(df['Dia da Consulta'], errors='coerce', dayfirst=True)
        df['Data da Infração'] = pd.to_datetime(df['Data da Infração'], errors='coerce', dayfirst=True)

        # Preprocessar valores
        df['Valor a Ser Pago (R$)'] = df['Valor a Ser Pago (R$)'].astype(str)\
            .str.replace(r'[^\d,.-]', '', regex=True)\
            .str.replace(r'\.(?=\d{3,})', '', regex=True)\
            .str.replace(',', '.')\
            .apply(lambda x: float(x) if x.replace('.', '', 1).isdigit() else 0)
        return df
    except Exception as e:
        print(f"Erro ao carregar os dados: {e}")
        raise

def verificar_colunas_essenciais(df, required_columns):
    """
    Verifica se as colunas essenciais estão presentes nos dados.
    """
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Colunas essenciais ausentes: {', '.join(missing_columns)}")

def preprocessar_valores(df):
    """
    Preprocessa valores monetários no DataFrame.
    """
    if 'Valor a Ser Pago (R$)' in df.columns:
        df['Valor a Ser Pago (R$)'] = df['Valor a Ser Pago (R$)'].astype(str)\
            .str.replace(r'[^d,.-]', '', regex=True)\
            .str.replace(r'\.(?=\d{3,})', '', regex=True)\
            .str.replace(',', '.')\
            .apply(lambda x: float(x) if x.replace('.', '', 1).isdigit() else 0)
    return df
