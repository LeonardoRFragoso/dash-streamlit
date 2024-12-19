import pandas as pd
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from googleapiclient.http import MediaIoBaseDownload
from io import BytesIO
import streamlit as st

def get_service_account_credentials():
    """
    Obtém as credenciais de conta de serviço do Google Drive a partir do painel do Streamlit.
    Retorna um objeto Credentials autenticado.
    """
    try:
        # Obter credenciais do painel do Streamlit diretamente
        credentials_info = {
            "type": st.secrets["CREDENTIALS"]["type"],
            "project_id": st.secrets["CREDENTIALS"]["project_id"],
            "private_key_id": st.secrets["CREDENTIALS"]["private_key_id"],
            "private_key": st.secrets["CREDENTIALS"]["private_key"],
            "client_email": st.secrets["CREDENTIALS"]["client_email"],
            "client_id": st.secrets["CREDENTIALS"]["client_id"],
            "auth_uri": st.secrets["CREDENTIALS"]["auth_uri"],
            "token_uri": st.secrets["CREDENTIALS"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["CREDENTIALS"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["CREDENTIALS"]["client_x509_cert_url"],
        }

        # Define os escopos necessários
        scopes = ["https://www.googleapis.com/auth/drive.readonly"]

        # Cria o objeto Credentials
        credentials = Credentials.from_service_account_info(credentials_info, scopes=scopes)
        st.info("Credenciais de serviço obtidas com sucesso.")
        return credentials

    except KeyError as e:
        st.error(f"Chave ausente nas credenciais: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar as credenciais: {str(e)}")
        return None

def get_drive_service(credentials):
    """
    Cria e retorna um objeto de serviço do Google Drive autenticado.
    """
    try:
        service = build("drive", "v3", credentials=credentials)
        st.info("Serviço do Google Drive criado com sucesso.")
        return service
    except Exception as e:
        st.error(f"Erro ao criar o serviço do Google Drive: {str(e)}")
        return None

def get_file_id():
    """
    Obtém o ID do arquivo do Google Drive a partir do painel do Streamlit.
    Retorna o ID do arquivo como uma string.
    """
    try:
        file_id = st.secrets["file_data"]["ultima_planilha_id"]
        st.info(f"ID do arquivo obtido: {file_id}")
        return file_id
    except KeyError:
        st.error("ID do arquivo não encontrado no secrets. Verifique a configuração.")
        return None

def download_file(service, file_id):
    """
    Faz o download do arquivo do Google Drive com o ID especificado.
    Retorna os dados do arquivo como um objeto BytesIO.
    """
    try:
        request = service.files().get_media(fileId=file_id)
        buffer = BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        buffer.seek(0)
        st.info("Arquivo baixado com sucesso do Google Drive.")
        return buffer
    except Exception as e:
        st.error(f"Erro ao baixar o arquivo do Google Drive: {str(e)}")
        return None

def carregar_dados_google_drive(sheet_name=None):
    """
    Carrega os dados do arquivo do Google Drive.
    Retorna os dados como um DataFrame do Pandas.
    """
    try:
        # Obter credenciais e serviço
        credentials = get_service_account_credentials()
        if not credentials:
            raise ValueError("Credenciais inválidas.")

        service = get_drive_service(credentials)
        if not service:
            raise ValueError("Serviço do Google Drive não pôde ser criado.")

        file_id = get_file_id()
        if not file_id:
            raise ValueError("ID do arquivo não encontrado.")

        file_data = download_file(service, file_id)
        if not file_data:
            raise ValueError("Falha no download do arquivo.")

        # Carregar o conteúdo como DataFrame do Pandas
        df = pd.read_excel(file_data, sheet_name=sheet_name)
        if not isinstance(df, pd.DataFrame):
            raise ValueError("Os dados carregados não são um DataFrame válido.")

        st.info("Dados carregados e convertidos em DataFrame com sucesso.")
        return df

    except ValueError as e:
        st.error(f"Erro de configuração: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar os dados do Google Drive: {str(e)}")
        return None
