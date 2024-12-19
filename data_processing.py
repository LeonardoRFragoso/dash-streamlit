import pandas as pd
from datetime import datetime

def carregar_e_limpar_dados(carregar_dados_func):
    """
    Carrega e faz o pré-processamento básico dos dados.
    """
    try:
        # Carregar os dados
        df = carregar_dados_func()

        # Verificar se as colunas essenciais estão presentes
        required_columns = ['Auto de Infração', 'Status de Pagamento', 'Valor a ser pago R$', 'Dia da Consulta']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Colunas faltantes: {', '.join(missing_columns)}")

        # Filtrar multas não pagas
        df_nao_pago = df[df['Status de Pagamento'].str.strip().str.upper() == 'NÃO PAGO']

        # Remover duplicatas por 'Auto de Infração'
        df_unicos = df_nao_pago.drop_duplicates(subset=['Auto de Infração'], keep='last')

        # Preprocessar valores monetários
        df_unicos['Valor a ser pago R$'] = (
            df_unicos['Valor a ser pago R$']
            .astype(str)
            .str.replace(r'[^\d,.-]', '', regex=True)  # Remove caracteres não numéricos
            .str.replace(r'\.(?=\d{3})', '', regex=True)  # Remove separadores de milhares
            .str.replace(',', '.', regex=False)       # Substitui vírgula por ponto decimal
        )
        df_unicos['Valor a ser pago R$'] = pd.to_numeric(df_unicos['Valor a ser pago R$'], errors='coerce').fillna(0)

        # Garantir que as datas estão no formato datetime
        df_unicos['Dia da Consulta'] = pd.to_datetime(df_unicos['Dia da Consulta'], errors='coerce', dayfirst=True)
        df_unicos['Data da Infração'] = pd.to_datetime(df_unicos['Data da Infração'], errors='coerce', dayfirst=True)

        return df_unicos
    except Exception as e:
        print(f"Erro ao carregar e limpar os dados: {e}")
        raise

def calcular_metricas(df):
    """
    Calcula métricas principais:
    - Total de multas
    - Valor total a pagar
    - Última consulta
    """
    # Calcular o total de multas considerando 'Auto de Infração' único
    total_multas = df['Auto de Infração'].nunique()

    # Calcular o valor total a pagar
    valor_total_a_pagar = df['Valor a ser pago R$'].sum()

    # Garantir que 'Dia da Consulta' está no formato datetime
    ultima_consulta = df['Dia da Consulta'].max()
    if pd.notnull(ultima_consulta):
        ultima_consulta = ultima_consulta.strftime('%d/%m/%Y')
    else:
        ultima_consulta = "Data não disponível"

    return total_multas, valor_total_a_pagar, ultima_consulta


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
        # Substituir valores vazios, nulos ou inválidos por '0'
        df['Valor a ser pago R$'] = df['Valor a ser pago R$'].fillna('0').replace(['', None], '0')

        # Remover caracteres inválidos e converter para float
        df['Valor a ser pago R$'] = (
            df['Valor a ser pago R$']
            .astype(str)
            .str.replace(r'[^\d,.-]', '', regex=True)  # Remove caracteres não numéricos
            .str.replace(r'\.(?=\d{3})', '', regex=True)  # Remove separadores de milhares
            .str.replace(',', '.', regex=False)       # Converte vírgula para ponto
        )

        # Garantir conversão segura para float
        df['Valor a ser pago R$'] = pd.to_numeric(df['Valor a ser pago R$'], errors='coerce').fillna(0)

    return df

def calcular_metricas(df):
    """
    Calcula métricas principais:
    - Total de multas
    - Valor total a pagar
    - Última consulta
    """
    # Calcular o total de multas considerando 'Auto de Infração' único
    total_multas = df['Auto de Infração'].nunique()

    # Calcular o valor total a pagar
    valor_total_a_pagar = df['Valor a ser pago R$'].sum()

    # Garantir que 'Dia da Consulta' está no formato datetime
    ultima_consulta = df['Dia da Consulta'].max()
    if pd.notnull(ultima_consulta):
        ultima_consulta = ultima_consulta.strftime('%d/%m/%Y')
    else:
        ultima_consulta = "Data não disponível"

    return total_multas, valor_total_a_pagar, ultima_consulta


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
