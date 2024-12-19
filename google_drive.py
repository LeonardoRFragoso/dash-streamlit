import pandas as pd
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from googleapiclient.http import MediaIoBaseDownload
from io import BytesIO
import streamlit as st
import json

def get_service_account_credentials():
    """
    Obtém as credenciais de conta de serviço do Google Drive a partir do painel do Streamlit.
    Retorna um objeto Credentials autenticado.
    """
    try:
        # Obter credenciais como string do painel do Streamlit
        credentials_info = st.secrets["CREDENTIALS"]

        # Se for string, converte para dicionário
        if isinstance(credentials_info, str):
            credentials_info = json.loads(credentials_info)

        # Define os escopos necessários
        scopes = ["https://www.googleapis.com/auth/drive.readonly"]

        # Cria o objeto Credentials
        credentials = Credentials.from_service_account_info(info=credentials_info, scopes=scopes)
        st.info("Credenciais de serviço obtidas com sucesso.")
        return credentials

    except json.JSONDecodeError:
        st.error("Erro ao interpretar as credenciais como JSON. Verifique o formato no painel do Streamlit.")
        return None
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
    except KeyError as e:
        st.error(f"Chave ausente ao obter o ID do arquivo: {str(e)}")
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
        # Verificar se o ID do arquivo está configurado
        if "file_data" not in st.secrets or "ultima_planilha_id" not in st.secrets["file_data"]:
            raise ValueError("ID do arquivo não configurado em secrets do painel do Streamlit.")
        
        credentials = get_service_account_credentials()
        if not credentials:
            st.error("Credenciais inválidas. Verifique o painel do Streamlit.")
            return None

        service = get_drive_service(credentials)
        if not service:
            st.error("Não foi possível criar o serviço do Google Drive.")
            return None

        file_id = get_file_id()
        if not file_id:
            st.error("ID do arquivo não encontrado.")
            return None

        file_data = download_file(service, file_id)
        if not file_data:
            st.error("Erro ao baixar o arquivo. Verifique o ID e as permissões do arquivo.")
            return None

        # Carregar o conteúdo como DataFrame do Pandas
        df = pd.read_excel(file_data, sheet_name=sheet_name)
        if df.empty:
            st.error("O arquivo baixado está vazio ou não contém dados.")
            return None

        st.info("Dados carregados com sucesso como DataFrame.")
        return df

    except ValueError as e:
        st.error(f"Erro de configuração: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar os dados do Google Drive: {str(e)}")
        return None
