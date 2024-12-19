import pandas as pd
import io
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2.service_account import Credentials
import streamlit as st

# Função para autenticar no Google Drive
def autenticar_google_drive():
    """Autentica no Google Drive usando credenciais de serviço."""
    credentials = Credentials.from_service_account_info(
        st.secrets["CREDENTIALS"], 
        scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    return build("drive", "v3", credentials=credentials)

# Função para obter o ID da última planilha a partir do arquivo JSON
def obter_id_ultima_planilha():
    """Obtém o ID da última planilha salva no JSON."""
    try:
        # Lê o arquivo JSON para obter o ID da planilha
        file_id = st.secrets["file_data"]["ultima_planilha_id"]
        return file_id
    except Exception as e:
        st.error(f"Erro ao carregar o ID da última planilha: {e}")
        st.stop()

# Função para carregar os dados do Google Drive
def carregar_dados_google_drive():
    """Carrega os dados da última planilha no Google Drive."""
    try:
        drive_service = autenticar_google_drive()
        file_id = obter_id_ultima_planilha()
        request = drive_service.files().get_media(fileId=file_id)
        file_buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(file_buffer, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        file_buffer.seek(0)
        return pd.read_excel(file_buffer)
    except Exception as e:
        st.error(f"Erro ao carregar os dados do Google Drive: {e}")
        st.stop()

# Função para limpar e processar os dados
def clean_data(df):
    """Limpa os dados e trata valores ausentes ou inválidos."""
    try:
        if 'Valor a ser pago R$' in df.columns:
            # Remove caracteres não numéricos e converte para float
            df['Valor a ser pago R$'] = df['Valor a ser pago R$'].replace(
                {r'[^0-9,]': '', ',': '.'}, regex=True
            ).astype(float)
        else:
            st.error("A coluna 'Valor a ser pago R$' não foi encontrada nos dados carregados.")
            st.stop()

        if 'Local da Infração' in df.columns:
            df['Local da Infração'] = df['Local da Infração'].fillna('Desconhecido')
        else:
            st.error("A coluna 'Local da Infração' não foi encontrada nos dados carregados.")
            st.stop()

        # Ajuste das datas
        df['Dia da Consulta'] = pd.to_datetime(df['Dia da Consulta'], dayfirst=True, errors='coerce')
        df['Data da Infração'] = pd.to_datetime(df['Data da Infração'], dayfirst=True, errors='coerce')

        # Remover entradas com dados ausentes nas colunas principais
        df.dropna(subset=['Status de Pagamento', 'Auto de Infração', 'Dia da Consulta', 'Data da Infração'], inplace=True)
        return df
    except Exception as e:
        st.error(f"Erro ao limpar os dados: {e}")
        st.stop()

# Função para verificar e padronizar o DataFrame
def padronizar_dataframe(df):
    """
    Padroniza o DataFrame após o carregamento.
    """
    try:
        # Verifica se todas as colunas necessárias estão presentes
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
            df['Valor a ser pago R$'] = df['Valor a ser pago R$'].replace({r'[^\d,]': '', ',': '.'}, regex=True)
            df['Valor a ser pago R$'] = pd.to_numeric(df['Valor a ser pago R$'], errors='coerce').fillna(0)

        # Converter colunas de datas
        for date_col in ['Dia da Consulta', 'Data da Infração']:
            if date_col in df.columns:
                df[date_col] = pd.to_datetime(df[date_col], errors='coerce', dayfirst=True)
                if df[date_col].isna().all():
                    raise ValueError(f"Todas as entradas na coluna '{date_col}' são inválidas.")

        # Preencher valores nulos na coluna 'Local da Infração' com 'Desconhecido'
        if 'Local da Infração' in df.columns:
            df['Local da Infração'] = df['Local da Infração'].fillna('Desconhecido')

        return df

    except Exception as e:
        st.error(f"Erro ao padronizar DataFrame: {e}")
        st.stop()
