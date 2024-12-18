import pandas as pd
from datetime import datetime

def carregar_e_limpar_dados(carregar_dados_func):
    """
    Carrega e faz o pré-processamento básico dos dados.
    """
    try:
        df = carregar_dados_func()

        # Padronizar nomes das colunas
        column_mapping = {
            "Valor a ser pago R$": "Valor a ser pago R$",
            "Data da Infração": "Data da Infração",
            "Dia da Consulta": "Dia da Consulta",
            "Auto de Infração": "Auto de Infração",
            "Status de Pagamento": "Status de Pagamento",
            "Local da Infração": "Local da Infração"
        }
        df.rename(columns=column_mapping, inplace=True)

        # Garantir que as colunas de data estão no formato correto
        df['Dia da Consulta'] = pd.to_datetime(df['Dia da Consulta'], errors='coerce', dayfirst=True)
        df['Data da Infração'] = pd.to_datetime(df['Data da Infração'], errors='coerce', dayfirst=True)

        # Remover linhas sem datas válidas
        df = df.dropna(subset=['Data da Infração', 'Dia da Consulta'])

        # Filtrar apenas o ano atual
        ano_atual = pd.Timestamp.now().year
        df = df[(df['Data da Infração'].dt.year == ano_atual) &
                (df['Status de Pagamento'] == 'NÃO PAGO')]

        # Preprocessar valores monetários
        df = preprocessar_valores(df)

        # Remover duplicatas com base no 'Auto de Infração'
        df = df.sort_values('Dia da Consulta').drop_duplicates(subset=['Auto de Infração'], keep='last')

        # Garantir que as colunas essenciais estejam presentes
        required_columns = ['Data da Infração', 'Valor a ser pago R$', 'Auto de Infração', 
                            'Status de Pagamento', 'Dia da Consulta', 'Local da Infração']
        verificar_colunas_essenciais(df, required_columns)

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
    if 'Valor a ser pago R$' in df.columns:
        # Limpar e converter os valores monetários
        df['Valor a ser pago R$'] = (
            df['Valor a ser pago R$']
            .astype(str)
            .str.replace(r'[^\d,.-]', '', regex=True)
            .str.replace(',', '.', regex=False)
            .astype(float)
        )
    return df

def calcular_metricas(df):
    """
    Calcula métricas principais:
    - Total de multas
    - Valor total a pagar
    - Multas do mês atual
    """
    # Calcular o total de multas considerando 'Auto de Infração' único
    total_multas = df['Auto de Infração'].nunique()

    # Calcular o valor total a pagar
    valor_total_a_pagar = df['Valor a ser pago R$'].sum()

    # Filtrar multas do mês atual
    mes_atual = pd.Timestamp.now().month
    multas_mes_atual = df[df['Data da Infração'].dt.month == mes_atual]['Auto de Infração'].nunique()

    return total_multas, valor_total_a_pagar, multas_mes_atual

def filtrar_dados_por_periodo(df, data_inicial, data_final, coluna='Dia da Consulta'):
    """
    Filtra os dados pelo período especificado entre data_inicial e data_final.

    Parameters:
        df (DataFrame): Dados a serem filtrados.
        data_inicial (str or datetime): Data inicial do filtro.
        data_final (str or datetime): Data final do filtro.
        coluna (str): Coluna de data usada para o filtro ('Dia da Consulta' ou 'Data da Infração').

    Returns:
        DataFrame: Dados filtrados.
    """
    if coluna not in df.columns:
        raise ValueError(f"A coluna '{coluna}' não existe no DataFrame.")

    # Garantir que a coluna de datas está no formato correto
    df[coluna] = pd.to_datetime(df[coluna], errors='coerce')

    return df[(df[coluna] >= pd.Timestamp(data_inicial)) & 
              (df[coluna] <= pd.Timestamp(data_final))]
