from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import io
from googleapiclient.http import MediaIoBaseDownload
import pandas as pd
import streamlit as st
import os
from tempfile import NamedTemporaryFile

def carregar_dados_google_drive():
    """
    Carrega dados de uma planilha do Google Drive usando credenciais de serviço.
    Retorna um DataFrame pandas ou None em caso de erro.
    """
    try:
        # Verificar se o ID do arquivo está configurado
        if "file_data" not in st.secrets or "ultima_planilha_id" not in st.secrets["file_data"]:
            raise ValueError("ID do arquivo não configurado em secrets.toml")

        # Carregar credenciais do secrets
        creds = Credentials.from_service_account_info(
            st.secrets["CREDENTIALS"], 
            scopes=["https://www.googleapis.com/auth/drive.readonly"]
        )

        # Construir o serviço da API Google Drive
        drive_service = build("drive", "v3", credentials=creds)

        # ID do arquivo
        file_id = st.secrets["file_data"]["ultima_planilha_id"]
        
        # Usar arquivo temporário para evitar problemas de permissão
        with NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp_file:
            try:
                # Baixar o arquivo
                request = drive_service.files().get_media(fileId=file_id)
                downloader = MediaIoBaseDownload(tmp_file, request)
                
                # Download com feedback de progresso
                with st.spinner('Baixando arquivo do Google Drive...'):
                    done = False
                    while not done:
                        status, done = downloader.next_chunk()
                        if status:
                            st.progress(int(status.progress() * 100))
                
                # Carregar o arquivo em um DataFrame
                tmp_file.seek(0)
                df = pd.read_excel(tmp_file.name)
                
                return df

            finally:
                # Limpar o arquivo temporário
                try:
                    os.unlink(tmp_file.name)
                except:
                    pass

    except ValueError as e:
        st.error(f"Erro de configuração: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Erro ao carregar os dados do Google Drive: {str(e)}")
        return None