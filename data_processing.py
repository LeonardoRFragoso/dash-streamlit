import pandas as pd
from data_loader import load_data, clean_data
import streamlit as st
from google_drive import carregar_dados_google_drive  # Adicione esta importação

def carregar_e_limpar_dados(file_path=None, sheet_name=None):
    """
    Carrega os dados usando `load_data` do `data_loader` e aplica limpeza adicional.
    Caso o caminho do arquivo não seja fornecido, ele será carregado a partir do Google Drive.
    """
    try:
        # Se file_path não for fornecido, carregar do Google Drive
        if not file_path:
            df = carregar_dados_google_drive()
        else:
            # Carregar os dados com `load_data` do data_loader
            df = load_data(file_path, sheet_name)

        if df is None:
            raise ValueError("Não foi possível carregar os dados")

        # Verificar colunas essenciais antes de qualquer operação
        required_columns = [
            'Status de Pagamento', 
            'Auto de Infração', 
            'Dia da Consulta', 
            'Data da Infração', 
            'Valor a ser pago R$'
        ]
        verificar_colunas_essenciais(df, required_columns)

        # Limpar dados com `clean_data`
        df_cleaned = clean_data(df)

        # Padronizar e filtrar apenas multas NÃO PAGAS
        df_cleaned['Status de Pagamento'] = (
            df_cleaned['Status de Pagamento']
            .astype(str)
            .str.strip()
            .str.upper()
        )
        df_cleaned = df_cleaned[df_cleaned['Status de Pagamento'] == 'NÃO PAGO']

        return df_cleaned
    except Exception as e:
        st.error(f"Erro ao carregar e limpar os dados: {str(e)}")
        return None

def verificar_colunas_essenciais(df, required_columns):
    """
    Verifica a existência e os tipos das colunas essenciais no DataFrame.
    """
    try:
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Faltam as seguintes colunas essenciais: {', '.join(missing_cols)}")

        # Validar tipos das colunas esperadas
        if 'Valor a ser pago R$' in df and not pd.api.types.is_numeric_dtype(df['Valor a ser pago R$']):
            raise TypeError("A coluna 'Valor a ser pago R$' deve ser numérica.")
        if 'Dia da Consulta' in df:
            df['Dia da Consulta'] = pd.to_datetime(df['Dia da Consulta'], errors='coerce')
    except Exception as e:
        raise RuntimeError(f"Erro na verificação de colunas essenciais: {e}")


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
            df['Valor a ser pago R$'] = pd.to_numeric(df['Valor a ser pago R$'], errors='coerce')

        # Total de multas com base em 'Auto de Infração' único
        total_multas = df['Auto de Infração'].nunique()

        # Valor total a pagar
        valor_total_a_pagar = df['Valor a ser pago R$'].sum()

        # Última data de consulta
        ultima_consulta = df['Dia da Consulta'].max()
        ultima_consulta = ultima_consulta.strftime('%d/%m/%Y') if pd.notnull(ultima_consulta) else "Data não disponível"

        return total_multas, valor_total_a_pagar, ultima_consulta
    except Exception as e:
        raise RuntimeError(f"Erro ao calcular métricas: {e}")


def filtrar_dados_por_periodo(df, data_inicial, data_final, coluna='Dia da Consulta'):
    """
    Filtra os dados pelo período especificado entre data_inicial e data_final.
    """
    try:
        if coluna not in df.columns:
            raise ValueError(f"A coluna '{coluna}' não existe no DataFrame.")

        # Garantir que a coluna de datas está no formato correto
        df[coluna] = pd.to_datetime(df[coluna], errors='coerce')

        return df[(df[coluna] >= pd.Timestamp(data_inicial)) & 
                  (df[coluna] <= pd.Timestamp(data_final))]
    except Exception as e:
        raise RuntimeError(f"Erro ao filtrar dados por período: {e}")
