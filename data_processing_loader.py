import pandas as pd
import streamlit as st

def carregar_dados_google_drive():
    """
    Carrega e processa os dados financeiros de uma planilha do Google Drive.
    """
    try:
        # Simula o carregamento da planilha (substitua pelo real carregamento do Google Drive)
        df = pd.read_excel("ResultadosOrganizados.xlsx")

        # Padronizar a coluna de valores monetários
        for col in ['Valor a ser pago R$', 'Valor original R$']:
            if col in df.columns:
                df[col] = (
                    df[col]
                    .astype(str)
                    .str.replace('.', '', regex=False)  # Remove pontos (separadores de milhares)
                    .str.replace(',', '.', regex=False)  # Substitui vírgulas por pontos (decimais)
                    .astype(float)  # Converte para float
                )

        return df

    except Exception as e:
        st.error(f"Erro ao carregar os dados: {e}")
        return None


# data_processing.py

def calcular_metricas(df):
    """
    Calcula as métricas principais do dashboard.
    """
    try:
        if df is None or df.empty:
            return 0, 0.0

        # Contar registros únicos de multas
        total_multas = df['Auto de Infração'].nunique()

        # Somar os valores das multas únicas
        valor_total = df.drop_duplicates(subset='Auto de Infração')['Valor a ser pago R$'].sum()

        return total_multas, valor_total

    except Exception as e:
        st.error(f"Erro ao calcular métricas: {e}")
        return 0, 0.0
