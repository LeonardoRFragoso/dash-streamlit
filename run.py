import streamlit as st
import pandas as pd
from datetime import datetime
from data_processing_loader import carregar_dados_google_drive, calcular_metricas

# Configuração inicial do Streamlit
st.set_page_config(page_title="Dashboard de Multas", layout="wide")

# Título do Dashboard
st.title("Dashboard de Multas")

# Carregar os dados
st.subheader("Carregando os Dados")
data_cleaned = carregar_dados_google_drive()

if data_cleaned is None:
    st.error("Não foi possível carregar os dados.")
    st.stop()

# Exibir as primeiras linhas para depuração
st.write("Primeiras linhas do DataFrame:", data_cleaned.head())

# Calcular métricas principais
total_multas, valor_total_a_pagar = calcular_metricas(data_cleaned)

# Exibir métricas principais
st.subheader("Métricas Principais")
col1, col2 = st.columns(2)
with col1:
    st.metric(label="Total de Multas", value=total_multas)
with col2:
    st.metric(label="Valor Total a Pagar (R$)", value=f"R$ {valor_total_a_pagar:,.2f}")

# Filtro de dados por período
data_inicial = st.date_input("Data Inicial", value=datetime(2024, 1, 1))
data_final = st.date_input("Data Final", value=datetime.now())

# Aplicar filtro
filtered_data = data_cleaned[(data_cleaned['Data da Infração'] >= pd.Timestamp(data_inicial)) &
                             (data_cleaned['Data da Infração'] <= pd.Timestamp(data_final))]

if filtered_data.empty:
    st.warning("Nenhum dado encontrado no período selecionado.")
else:
    st.write("Dados filtrados:", filtered_data)

# Exibir tabela final
st.subheader("Tabela Consolidada")
st.dataframe(filtered_data, use_container_width=True)
