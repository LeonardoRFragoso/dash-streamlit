from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from googleapiclient.http import MediaIoBaseDownload
from io import BytesIO
import streamlit as st

def get_service_account_credentials():
    """
    Obtém as credenciais de conta de serviço do Google Drive a partir do secrets.toml.
    Retorna um objeto Credentials autenticado.
    """
    credentials_info = st.secrets["CREDENTIALS"]
    scopes = ["https://www.googleapis.com/auth/drive.readonly"]
    credentials = Credentials.from_service_account_info(info=credentials_info, scopes=scopes)
    return credentials

def get_drive_service(credentials):
    """
    Cria e retorna um objeto de serviço do Google Drive autenticado.
    """
    return build("drive", "v3", credentials=credentials)

def get_file_id():
    """
    Obtém o ID do arquivo do Google Drive a partir do secrets.toml.
    Retorna o ID do arquivo como uma string.
    """
    return st.secrets["file_data"]["ultima_planilha_id"]

def download_file(service, file_id):
    """
    Faz o download do arquivo do Google Drive com o ID especificado.
    Retorna os dados do arquivo como um objeto BytesIO.
    """
    request = service.files().get_media(fileId=file_id)
    buffer = BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while done is False:
        _, done = downloader.next_chunk()
    buffer.seek(0)
    return buffer

def carregar_dados_google_drive():
    """
    Carrega os dados do arquivo do Google Drive.
    Retorna os dados como um objeto BytesIO.
    """
    try:
        # Verificar se o ID do arquivo está configurado
        if "file_data" not in st.secrets or "ultima_planilha_id" not in st.secrets["file_data"]:
            raise ValueError("ID do arquivo não configurado em secrets.toml")
        
        credentials = get_service_account_credentials()
        service = get_drive_service(credentials)
        file_id = get_file_id()
        file_data = download_file(service, file_id)
        return file_data
    except ValueError as e:
        st.error(f"Erro de configuração: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar os dados do Google Drive: {str(e)}")
        return None