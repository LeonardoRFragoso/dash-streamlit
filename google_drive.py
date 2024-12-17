import io
import json
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import streamlit as st

def autenticar_google_drive():
    """Autentica no Google Drive usando credenciais de serviço."""
    # Converte explicitamente o conteúdo de CREDENTIALS para string e depois para JSON
    credentials_str = str(st.secrets["CREDENTIALS"])  # Converte AttrDict para string
    credentials_dict = json.loads(credentials_str.replace("\n", "\\n"))  # Ajusta quebras de linha e carrega JSON
    
    # Cria as credenciais a partir do dicionário
    credentials = Credentials.from_service_account_info(
        credentials_dict, 
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    
    # Retorna o serviço autenticado do Google Drive
    return build("drive", "v3", credentials=credentials)

def carregar_dados_google_drive():
    """Carrega os dados da última planilha no Google Drive."""
    try:
        drive_service = autenticar_google_drive()
        file_id = st.secrets["file_data"]["ultima_planilha_id"]
        request = drive_service.files().get_media(fileId=file_id)
        file_buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(file_buffer, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        file_buffer.seek(0)
        return pd.read_excel(file_buffer)
    except Exception as e:
        st.error(f"Erro ao carregar os dados do Google Drive: {e}")
        st.stop()