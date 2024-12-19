import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from io import BytesIO
import re

def load_data(sheet_name=None):
    """
    Carrega dados do Google Drive utilizando credenciais de serviço e retorna um DataFrame limpo.
    """
    try:
        # Carregar credenciais do secrets.toml
        if "CREDENTIALS" not in st.secrets or "file_data" not in st.secrets or "ultima_planilha_id" not in st.secrets["file_data"]:
            st.error("As credenciais ou configurações do arquivo estão ausentes no secrets.toml.")
            raise KeyError("As credenciais ou configurações do arquivo estão ausentes no secrets.toml.")
        
        creds = Credentials.from_service_account_info(
            st.secrets["CREDENTIALS"], 
            scopes=["https://www.googleapis.com/auth/drive.readonly"]
        )
        
        # Construir o serviço da API Google Drive
        drive_service = build("drive", "v3", credentials=creds)

        # ID do arquivo
        file_id = st.secrets["file_data"]["ultima_planilha_id"]
        
        # Baixar o arquivo
        request = drive_service.files().get_media(fileId=file_id)
        buffer = BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        
        # Carregar o arquivo em um DataFrame
        buffer.seek(0)
        df = pd.read_excel(buffer, sheet_name=sheet_name)

        # Verificar se o DataFrame está vazio ou não
        if df is None or df.empty:
            st.error("O arquivo carregado está vazio ou não foi possível carregar os dados.")
            raise ValueError("O arquivo carregado está vazio ou não contém dados utilizáveis.")

        # Padronizar e limpar os dados
        return padronizar_dataframe(df)

    except Exception as e:
        st.error(f"Erro ao carregar dados do Google Drive: {e}")
        raise RuntimeError(f"Erro ao carregar dados do Google Drive: {e}")

def padronizar_dataframe(df):
    """
    Padroniza o DataFrame após o carregamento.
    """
    try:
        # Verificar e corrigir colunas essenciais
        required_columns = ['Status de Pagamento', 'Auto de Infração', 'Dia da Consulta', 'Data da Infração', 'Valor a ser pago R$']
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            st.error(f"Faltam as seguintes colunas: {', '.join(missing_cols)}")
            raise ValueError(f"Faltam as colunas: {', '.join(missing_cols)}")

        # Renomear as colunas para o padrão esperado
        column_mapping = {
            "Valor a Ser Pago": "Valor a ser pago R$",
            "Data da Infração": "Data da Infração",
            "Dia da Consulta": "Dia da Consulta",
            "Auto de Infração": "Auto de Infração",
            "Status de Pagamento": "Status de Pagamento",
            "Local da Infração": "Local da Infração"
        }
        df = df.rename(columns=column_mapping)

        # Processar valores monetários (Valor a ser pago R$)
        if 'Valor a ser pago R$' in df.columns:
            df['Valor a ser pago R$'] = process_currency_column(df['Valor a ser pago R$'])

        # Converter colunas de datas
        for date_col in ['Dia da Consulta', 'Data da Infração']:
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce', dayfirst=True)
                if df[date_col].isna().all():
                    raise ValueError(f"Todas as entradas na coluna '{date_col}' são inválidas.")

        # Preencher valores nulos na coluna 'Local da Infração' com 'Desconhecido'
        if 'Local da Infração' in df.columns:
            df['Local da Infração'] = df['Local da Infração'].fillna('Desconhecido')

        # Retornar o DataFrame limpo e padronizado
        return df

    except Exception as e:
        st.error(f"Erro ao padronizar DataFrame: {e}")
        raise RuntimeError(f"Erro ao padronizar DataFrame: {e}")

def process_currency_column(series):
    """
    Processa uma coluna de valores monetários, removendo caracteres não numéricos e convertendo para float.
    """
    try:
        return (series
                .astype(str)
                .str.replace(r'[^\d,.-]', '', regex=True)  # Remove caracteres não numéricos
                .str.replace(r'\.(?=\d{3,})', '', regex=True)  # Remove ponto de milhar
                .str.replace(',', '.', regex=False)  # Troca vírgula por ponto decimal
                .pipe(pd.to_numeric, errors='coerce')  # Converte para numérico, com erro tratado
                .fillna(0))  # Substitui valores inválidos (NaN) por 0
    except Exception as e:
        st.error(f"Erro ao processar coluna de valores: {e}")
        raise RuntimeError(f"Erro ao processar coluna de valores: {e}")

def clean_data(df):
    """
    Remove duplicados com base na coluna 'Auto de Infração' para garantir que não haja registros duplicados.
    """
    try:
        if 'Auto de Infração' not in df.columns:
            st.error("Coluna 'Auto de Infração' não encontrada")
            raise KeyError("Coluna 'Auto de Infração' não encontrada")
        return df.drop_duplicates(subset=['Auto de Infração'], keep='last')
    except Exception as e:
        st.error(f"Erro ao limpar dados: {e}")
        raise RuntimeError(f"Erro ao limpar dados: {e}")
