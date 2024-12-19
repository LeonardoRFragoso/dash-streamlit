from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import io
from googleapiclient.http import MediaIoBaseDownload
import pandas as pd
import streamlit as st

def carregar_dados_google_drive():
    try:
        # Carregar credenciais do secrets
        creds = Credentials.from_service_account_info(
            st.secrets["CREDENTIALS"], 
            scopes=["https://www.googleapis.com/auth/drive.readonly"]
        )

        # Construir o serviço da API Google Drive
        drive_service = build("drive", "v3", credentials=creds)

        # ID do arquivo armazenado no Google Drive (do secrets)
        file_id = st.secrets["file_data"]["ultima_planilha_id"]
        
        # Baixar o arquivo
        request = drive_service.files().get_media(fileId=file_id)
        fh = io.FileIO("/tmp/resultado_planilha.xlsx", "wb")
        downloader = MediaIoBaseDownload(fh, request)
        
        # Baixar o arquivo em partes
        done = False
        while done is False:
            status, done = downloader.next_chunk()
        
        # Carregar o arquivo em um DataFrame
        df = pd.read_excel("/tmp/resultado_planilha.xlsx")
        
        return df

    except Exception as e:
        st.error(f"Erro ao carregar os dados do Google Drive: {e}")
        return None
