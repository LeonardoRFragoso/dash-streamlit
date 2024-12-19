import pandas as pd
import streamlit as st
from tempfile import NamedTemporaryFile
import os

def load_data(source, sheet_name=None):
    """
    Carrega dados de diferentes fontes (arquivo local ou ID do Google Drive).
    """
    try:
        # Se source for um ID do Google Drive, usar função específica
        if isinstance(source, str) and len(source) == 33:  # ID do Google Drive
            return load_from_google_drive(source, sheet_name)
        
        # Caso contrário, carregar como arquivo local
        return load_from_file(source, sheet_name)
    except Exception as e:
        raise RuntimeError(f"Erro ao carregar os dados: {e}")

def load_from_file(file_path, sheet_name=None):
    """
    Carrega dados de um arquivo Excel local.
    """
    try:
        # Detectar a aba automaticamente se não especificada
        sheet_name = sheet_name or 0

        # Carregar a planilha
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        return padronizar_dataframe(df)

    except Exception as e:
        raise RuntimeError(f"Erro ao carregar arquivo local: {e}")

def load_from_google_drive(file_id, sheet_name=None):
    """
    Carrega dados do Google Drive usando ID do arquivo.
    """
    try:
        from google_drive import carregar_dados_google_drive
        df = carregar_dados_google_drive(file_id)
        if df is None:
            raise ValueError("Falha ao carregar dados do Google Drive")
        return padronizar_dataframe(df)
    except Exception as e:
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
        raise RuntimeError(f"Erro ao processar coluna de valores: {e}")

def clean_data(df):
    """
    Remove duplicados com base na coluna 'Auto de Infração'.
    """
    try:
        if 'Auto de Infração' not in df.columns:
            raise KeyError("Coluna 'Auto de Infração' não encontrada")
        return df.drop_duplicates(subset=['Auto de Infração'], keep='last')
    except Exception as e:
        raise RuntimeError(f"Erro ao limpar dados: {e}")