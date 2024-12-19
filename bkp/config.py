import streamlit as st
import json

# Configurações Globais para o Dashboard de Multas utilizando secrets

# Credenciais do Google carregadas a partir do secrets
CREDENTIALS_FILE = json.loads(st.secrets["CREDENTIALS"])

# ID da última planilha baixada do Google Drive
ULTIMA_PLANILHA_JSON = st.secrets["file_data"].get("ultima_planilha_id", None)

# Caminho para o arquivo de resultados organizados (não utilizado diretamente)
FILE_PATH = None  # O arquivo será baixado diretamente do Google Drive

# Chave da API para serviços externos (como geolocalização ou captcha, se necessário)
API_KEY = st.secrets["API_KEY"] if "API_KEY" in st.secrets else "CHAVE_PADRAO"

# Chave do site para reCAPTCHA
SITE_KEY = st.secrets["SITE_KEY"] if "SITE_KEY" in st.secrets else "CHAVE_PADRAO"

# ID da pasta no Google Drive onde a planilha de resultados está armazenada
GOOGLE_DRIVE_FOLDER_ID = st.secrets["file_data"].get("GOOGLE_DRIVE_FOLDER_ID", None)

# Outras configurações ou funções úteis para centralizar
def get_credentials():
    """Retorna as credenciais de serviço do Google"""
    return CREDENTIALS_FILE