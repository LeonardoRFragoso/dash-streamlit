import io
import pandas as pd
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import streamlit as st

def autenticar_google_drive():
    """
    Autentica no Google Drive usando credenciais de serviço armazenadas em `st.secrets`.
    """
    try:
        # Obter credenciais do Streamlit secrets
        credentials_info = st.secrets["CREDENTIALS"]
        
        # Criar as credenciais do Google OAuth
        credentials = Credentials.from_service_account_info(
            json.loads(credentials_info), 
            scopes=["https://www.googleapis.com/auth/drive"]
        )
        
        # Retorna o serviço autenticado do Google Drive
        return build("drive", "v3", credentials=credentials)
    except Exception as e:
        st.error(f"Erro ao autenticar no Google Drive: {e}")
        st.stop()

def carregar_dados_google_drive(sheet_name=None):
    """
    Faz o download da planilha do Google Drive e carrega como um DataFrame do pandas.
    """
    try:
        # Autenticar no Google Drive
        drive_service = autenticar_google_drive()
        
        # Obter o ID da planilha do Streamlit secrets
        file_id = st.secrets["file_data"]["ultima_planilha_id"]
        
        # Requisição para download do arquivo
        request = drive_service.files().get_media(fileId=file_id)
        file_buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(file_buffer, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        
        # Resetar o ponteiro do buffer para o início
        file_buffer.seek(0)
        
        # Carregar o conteúdo do buffer como um DataFrame
        return pd.read_excel(file_buffer, sheet_name=sheet_name)
    except Exception as e:
        st.error(f"Erro ao carregar os dados do Google Drive: {e}")
        st.stop()
