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

def calcular_metricas(df):
    """
    Calcula métricas principais:
    - Total de multas
    - Valor total a pagar
    - Multas do mês atual
    """
    total_multas = len(df)
    valor_total_a_pagar = df['Valor a Ser Pago (R$)'].sum()

    # Filtra multas do mês atual
    mes_atual = pd.Timestamp.now().month
    multas_mes_atual = df[df['Data da Infração'].dt.month == mes_atual].shape[0]

    return total_multas, valor_total_a_pagar, multas_mes_atual
