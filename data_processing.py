import pandas as pd
import streamlit as st
from data_loader import clean_data, process_currency_column

def carregar_e_limpar_dados(carregar_dados_func):
    """
    Carrega os dados do Google Drive e aplica limpeza e processamento.
    """
    try:
        # Carregar dados do Google Drive usando a função fornecida
        df = carregar_dados_func()

        if df is None or not isinstance(df, pd.DataFrame):
            st.error("Não foi possível carregar os dados ou os dados não são válidos")
            return None

        # Verificar e corrigir colunas essenciais
        required_columns = [
            'Status de Pagamento',
            'Auto de Infração',
            'Dia da Consulta',
            'Data da Infração',
            'Valor a ser pago R$'
        ]
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            st.error(f"Faltam as seguintes colunas: {', '.join(missing_cols)}")
            return None

        # Validar e processar colunas
        for col in ['Valor a ser pago R$', 'Dia da Consulta', 'Data da Infração']:
            if col in df.columns:
                if col == 'Valor a ser pago R$':
                    df[col] = process_currency_column(df[col])
                elif col in ['Dia da Consulta', 'Data da Infração']:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
                    if df[col].isna().all():
                        st.error(f"Falha ao converter a coluna '{col}' para formato de data")
                        return None

        # Limpar dados duplicados
        df_cleaned = clean_data(df)

        # Filtrar apenas multas não pagas
        df_cleaned = filtrar_multas_nao_pagas(df_cleaned)

        return df_cleaned

    except Exception as e:
        st.error(f"Erro ao carregar e limpar os dados: {str(e)}")
        return None


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
