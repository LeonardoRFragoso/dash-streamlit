import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from io import BytesIO

def load_data(sheet_name=None):
    """
    Carrega dados do Google Drive usando as credenciais do secrets.toml.
    """
    try:
        # Carregar credenciais do secrets.toml
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
        while done is False:
            _, done = downloader.next_chunk()
        
        # Carregar o arquivo em um DataFrame
        buffer.seek(0)
        df = pd.read_excel(buffer, sheet_name=sheet_name)
        
        return padronizar_dataframe(df)
    except Exception as e:
        st.error(f"Erro ao carregar do Google Drive: {e}")
        raise RuntimeError(f"Erro ao carregar do Google Drive: {e}")

def padronizar_dataframe(df):
    """
    Padroniza o DataFrame após o carregamento.
    """
    try:
        # Padronizar os nomes das colunas
        column_mapping = {
            "Valor a ser pago R$": "Valor a ser pago R$",
            "Data da Infração": "Data da Infração",
            "Dia da Consulta": "Dia da Consulta",
            "Auto de Infração": "Auto de Infração",
        }
        
        # Verificar se as colunas essenciais estão presentes
        missing_columns = [col for col in column_mapping.values() if col not in df.columns]
        if missing_columns:
            st.error(f"Faltam as colunas necessárias no DataFrame: {', '.join(missing_columns)}")
            raise ValueError(f"Faltam as colunas necessárias no DataFrame: {', '.join(missing_columns)}")

        df = df.rename(columns=column_mapping)

        # Converter colunas de datas
        for date_col in ['Dia da Consulta', 'Data da Infração']:
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce', dayfirst=True)

        # Processar coluna de valor
        if 'Valor a ser pago R$' in df.columns:
            df['Valor a ser pago R$'] = process_currency_column(df['Valor a ser pago R$'])

        return df
    except Exception as e:
        st.error(f"Erro ao padronizar DataFrame: {e}")
        raise RuntimeError(f"Erro ao padronizar DataFrame: {e}")

def process_currency_column(series):
    """
    Processa uma coluna de valores monetários.
    """
    try:
        return (series
                .astype(str)
                .str.replace(r'[^\d,.-]', '', regex=True)
                .str.replace(r'\.(?=\d{3,})', '', regex=True)
                .str.replace(',', '.', regex=False)
                .pipe(pd.to_numeric, errors='coerce')
                .fillna(0))
    except Exception as e:
        st.error(f"Erro ao processar coluna de valores: {e}")
        raise RuntimeError(f"Erro ao processar coluna de valores: {e}")

def clean_data(df):
    """
    Remove duplicados com base na coluna 'Auto de Infração'.
    """
    try:
        if 'Auto de Infração' not in df.columns:
            st.error("Coluna 'Auto de Infração' não encontrada")
            raise KeyError("Coluna 'Auto de Infração' não encontrada")
        return df.drop_duplicates(subset=['Auto de Infração'], keep='last')
    except Exception as e:
        st.error(f"Erro ao limpar dados: {e}")
        raise RuntimeError(f"Erro ao limpar dados: {e}")