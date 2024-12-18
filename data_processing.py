import streamlit as st
import pandas as pd
import folium
from datetime import datetime
from folium.features import CustomIcon
from streamlit_folium import st_folium
from google_drive import carregar_dados_google_drive
from data_processing import (
    carregar_e_limpar_dados,
    verificar_colunas_essenciais,
    calcular_metricas,
    filtrar_dados_por_periodo,
)
from graph_vehicles_fines import create_vehicle_fines_chart
from graph_common_infractions import create_common_infractions_chart
from graph_fines_accumulated import create_fines_accumulated_chart
from graph_weekday_infractions import create_weekday_infractions_chart
from geo_utils import load_cache, save_cache, get_cached_coordinates

# Configuração inicial do Streamlit
st.set_page_config(page_title="Torre de Controle iTracker - Dashboard de Multas", layout="wide")

# Estilização CSS e HTML
st.markdown(
    """
    <style>
        .titulo-dashboard-container {
            display: flex;
            justify-content: center;
            align-items: center;
            text-align: center;
            margin: 0 auto;
            padding: 25px 20px;
            background: linear-gradient(to right, #F37529, rgba(255, 255, 255, 0.8));
            border-radius: 15px;
            box-shadow: 0 6px 10px rgba(0, 0, 0, 0.3);
        }
        .titulo-dashboard {
            font-size: 50px;
            font-weight: bold;
            color: #F37529;
            text-transform: uppercase;
            margin: 0;
        }
        .titulo-secao {
            text-align: center;
            font-size: 36px;
            font-weight: bold;
            color: #0066B4;
            margin-top: 30px;
            margin-bottom: 20px;
        }
        .footer {
            text-align: center;
            font-size: 14px;
            color: #0066B4;
            margin-top: 40px;
            padding: 10px 0;
            border-top: 1px solid #ddd;
        }
        .indicadores-container {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 40px;
            margin-top: 30px;
        }
        .indicador {
            display: flex;
            flex-direction: column;
            justify-content: center;  /* Centraliza verticalmente */
            align-items: center;      /* Centraliza horizontalmente */
            text-align: center;
            background-color: #FFFFFF;
            border: 4px solid #0066B4;
            border-radius: 15px;
            box-shadow: 0 8px 12px rgba(0, 0, 0, 0.3);
            width: 260px;
            height: 160px;
            padding: 10px;            /* Adiciona espaçamento interno */
        }
        .indicador span {
            font-size: 18px;
            color: #0066B4;
        }
        .indicador p {
            font-size: 38px;
            color: #0066B4;
            margin: 0;
            font-weight: bold;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Exibir o logo da empresa acima do título
logo_url = st.secrets["image"]["logo_url"]  # URL do logo fornecido no secrets
st.markdown(
    f"""
    <div style='display: flex; justify-content: center; margin-bottom: 20px;'>
        <img src="{logo_url}" width="200" alt="Logo">
    </div>
    """,
    unsafe_allow_html=True
)

# Título do Dashboard
st.markdown(
    """
    <div class="titulo-dashboard-container">
        <h1 class="titulo-dashboard">Torre de Controle iTracker - Dashboard de Multas</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

# Carregar e processar dados
data_cleaned = carregar_e_limpar_dados(carregar_dados_google_drive)

# Verificar colunas essenciais
required_columns = ['Data da Infração', 'Valor a ser pago R$', 'Auto de Infração', 
                    'Status de Pagamento', 'Dia da Consulta', 'Local da Infração']
try:
    verificar_colunas_essenciais(data_cleaned, required_columns)
except ValueError as e:
    st.error(str(e))
    st.stop()

# Filtrar apenas registros com Status de Pagamento = 'NÃO PAGO' ao iniciar
data_inicial_default = data_cleaned[data_cleaned['Status de Pagamento'] == 'NÃO PAGO']

# Remover duplicatas baseadas em 'Auto de Infração'
data_inicial_default = data_inicial_default.drop_duplicates(subset=['Auto de Infração'])

# Converter valores monetários para float
data_inicial_default['Valor a ser pago R$'] = pd.to_numeric(
    data_inicial_default['Valor a ser pago R$'].astype(str)
    .str.replace(',', '.', regex=False)
    .str.replace('[^\d.]', '', regex=True), errors='coerce'
)

# Calcular métricas iniciais (antes da aplicação de filtros)
total_multas = data_inicial_default['Auto de Infração'].nunique()
valor_total_a_pagar = data_inicial_default['Valor a ser pago R$'].sum()
ultima_consulta = data_inicial_default['Dia da Consulta'].max().strftime('%d/%m/%Y')

# Indicadores Principais
st.markdown(
    f"""
    <div class="indicadores-container">
        <div class="indicador">
            <span>Total de Multas</span>
            <p>{total_multas}</p>
        </div>
        <div class="indicador">
            <span>Valor Total a Pagar</span>
            <p>R$ {valor_total_a_pagar:,.2f}</p>
        </div>
        <div class="indicador">
            <span>Última Consulta</span>
            <p>{ultima_consulta}</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Footer
st.markdown("<div class='footer'>Dashboard de Multas © 2024 | Desenvolvido pela Equipe de Qualidade</div>", unsafe_allow_html=True)
