import pandas as pd
import streamlit as st
from data_loader import load_data, clean_data, process_currency_column
from google_drive import carregar_dados_google_drive

def carregar_e_limpar_dados():
    """
    Carrega os dados do Google Drive e aplica limpeza e processamento.
    """
    try:
        # Carregar dados do Google Drive
        df = carregar_dados_google_drive()  # Chamada direta

        if df is None:
            st.error("Não foi possível carregar os dados do Google Drive")
            return None

        # Verificar se é um DataFrame válido
        if not isinstance(df, pd.DataFrame):
            st.error("Os dados carregados não são um DataFrame válido")
            return None

        # Verificar colunas essenciais
        required_columns = [
            'Status de Pagamento', 
            'Auto de Infração', 
            'Dia da Consulta', 
            'Data da Infração', 
            'Valor a ser pago R$'
        ]
        
        try:
            verificar_colunas_essenciais(df, required_columns)
        except Exception as e:
            st.error(f"Erro na verificação de colunas: {str(e)}")
            return None

        # Limpar dados
        df_cleaned = clean_data(df)
        if df_cleaned is None:
            st.error("Erro na limpeza dos dados")
            return None

        # Filtrar multas não pagas
        try:
            df_cleaned = filtrar_multas_nao_pagas(df_cleaned)
        except Exception as e:
            st.error(f"Erro ao filtrar multas não pagas: {str(e)}")
            return None

        return df_cleaned

    except Exception as e:
        st.error(f"Erro ao carregar e limpar os dados: {str(e)}")
        return None

def verificar_colunas_essenciais(df, required_columns):
    """
    Verifica a existência e formatos das colunas necessárias.
    """
    try:
        # Verificar presença das colunas
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Faltam as seguintes colunas: {', '.join(missing_cols)}")

        # Validar formato e converter colunas
        for col in ['Valor a ser pago R$', 'Dia da Consulta', 'Data da Infração']:
            if col in df.columns:
                if col == 'Valor a ser pago R$':
                    df['Valor a ser pago R$'] = process_currency_column(df['Valor a ser pago R$'])
                elif col in ['Dia da Consulta', 'Data da Infração']:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    if df[col].isna().all():
                        raise ValueError(f"Falha ao converter a coluna '{col}' para formato de data")
        return df
    except Exception as e:
        raise RuntimeError(f"Erro na verificação de colunas: {e}")

def filtrar_multas_nao_pagas(df):
    """
    Filtra apenas as multas com status 'NÃO PAGO'.
    """
    try:
        df['Status de Pagamento'] = (
            df['Status de Pagamento']
            .astype(str)
            .str.strip()
            .str.upper()
        )
        return df[df['Status de Pagamento'] == 'NÃO PAGO']
    except Exception as e:
        raise RuntimeError(f"Erro ao filtrar multas não pagas: {e}")

def calcular_metricas(df):
    """
    Calcula métricas principais do dashboard.
    """
    try:
        if df is None or df.empty:
            return 0, 0.0, "Dados não disponíveis"

        total_multas = df['Auto de Infração'].nunique()
        valor_total = df['Valor a ser pago R$'].sum()
        
        ultima_consulta = df['Dia da Consulta'].max()
        ultima_consulta = (
            ultima_consulta.strftime('%d/%m/%Y') 
            if pd.notnull(ultima_consulta) 
            else "Data não disponível"
        )

        return total_multas, valor_total, ultima_consulta

    except Exception as e:
        st.error(f"Erro ao calcular métricas: {str(e)}")
        return 0, 0.0, "Erro no cálculo"

def filtrar_dados_por_periodo(df, data_inicial, data_final, coluna='Dia da Consulta'):
    """
    Filtra dados por período específico.
    """
    try:
        if df is None or df.empty:
            return df

        if coluna not in df.columns:
            raise ValueError(f"Coluna '{coluna}' não encontrada")

        # Garantir formato de data
        df[coluna] = pd.to_datetime(df[coluna], errors='coerce')
        
        # Converter datas de filtro
        data_inicial = pd.Timestamp(data_inicial)
        data_final = pd.Timestamp(data_final)

        # Aplicar filtro
        mask = (df[coluna] >= data_inicial) & (df[coluna] <= data_final)
        filtered_df = df[mask]

        if filtered_df.empty:
            st.warning(f"Nenhum dado encontrado para o período de {data_inicial.strftime('%d/%m/%Y')} a {data_final.strftime('%d/%m/%Y')}")

        return filtered_df

    except Exception as e:
        st.error(f"Erro ao filtrar por período: {str(e)}")
        return df
