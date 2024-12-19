import pandas as pd
from data_loader import load_data, clean_data


def carregar_e_limpar_dados(file_path, sheet_name=None):
    """
    Carrega os dados usando `load_data` do `data_loader` e aplica limpeza adicional.
    """
    try:
        # Carregar e preprocessar os dados com `load_data`
        df = load_data(file_path, sheet_name)

        # Verificar colunas essenciais antes de qualquer operação
        required_columns = ['Status de Pagamento', 'Auto de Infração', 'Dia da Consulta', 'Data da Infração', 'Valor a ser pago R$']
        verificar_colunas_essenciais(df, required_columns)

        # Limpar duplicatas usando `clean_data`
        df_cleaned = clean_data(df)

        # Filtrar apenas multas NÃO PAGAS (garantindo padronização)
        df_cleaned['Status de Pagamento'] = df_cleaned['Status de Pagamento'].str.strip().str.upper()
        df_cleaned = df_cleaned[df_cleaned['Status de Pagamento'] == 'NÃO PAGO']

        return df_cleaned
    except Exception as e:
        print(f"Erro ao carregar e limpar os dados: {e}")
        raise


def verificar_colunas_essenciais(df, required_columns):
    """
    Verifica a existência das colunas essenciais no DataFrame.
    """
    try:
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Faltam as seguintes colunas essenciais: {', '.join(missing_cols)}")
    except Exception as e:
        print(f"Erro na verificação de colunas essenciais: {e}")
        raise


def calcular_metricas(df):
    """
    Calcula métricas principais:
    - Total de multas únicas
    - Valor total a pagar
    - Última data de consulta
    """
    try:
        # Garantir que a coluna de valor está em formato numérico
        if not pd.api.types.is_numeric_dtype(df['Valor a ser pago R$']):
            raise ValueError("A coluna 'Valor a ser pago R$' não está em formato numérico.")

        # Total de multas com base em 'Auto de Infração' único
        total_multas = df['Auto de Infração'].nunique()

        # Valor total a pagar
        valor_total_a_pagar = df['Valor a ser pago R$'].sum()

        # Última data de consulta
        ultima_consulta = df['Dia da Consulta'].max()
        ultima_consulta = ultima_consulta.strftime('%d/%m/%Y') if pd.notnull(ultima_consulta) else "Data não disponível"

        return total_multas, valor_total_a_pagar, ultima_consulta
    except Exception as e:
        print(f"Erro ao calcular métricas: {e}")
        raise


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
    try:
        if coluna not in df.columns:
            raise ValueError(f"A coluna '{coluna}' não existe no DataFrame.")

        # Garantir que a coluna de datas está no formato correto
        df[coluna] = pd.to_datetime(df[coluna], errors='coerce')

        return df[(df[coluna] >= pd.Timestamp(data_inicial)) & 
                  (df[coluna] <= pd.Timestamp(data_final))]
    except Exception as e:
        print(f"Erro ao filtrar dados por período: {e}")
        raise
