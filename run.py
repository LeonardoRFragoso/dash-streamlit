import streamlit as st
import pandas as pd
import folium
from folium.features import CustomIcon
from streamlit_folium import st_folium
from data_loader import clean_data  # Apenas a função de limpeza de dados é necessária aqui
from metrics import calculate_metrics
from graph_vehicles_fines import create_vehicle_fines_chart  # Importando a função de gráfico de veículos
from graph_common_infractions import create_common_infractions_chart  # Importando a função de gráfico de infrações comuns
from graph_fines_accumulated import create_fines_accumulated_chart  # Importando a função de gráfico de multas acumuladas
from graph_weekday_infractions import create_weekday_infractions_chart  # Importando a função de gráfico de infrações por dia
from geo_utils import load_cache, save_cache, get_cached_coordinates  # Funções para lidar com o cache geográfico
from google_drive import carregar_dados_google_drive  # Função para carregar dados do Google Drive

# Configuração inicial
st.set_page_config(page_title="Torre de Controle iTracker - Dashboard de Multas", layout="wide")

# Streamlit interface com a estilização fornecida
st.markdown(
    """
    <style>
        @keyframes fadeIn {
            0% { opacity: 0; transform: translateY(-20px); }
            100% { opacity: 1; transform: translateY(0); }
        }

        /* Container do título */
        .titulo-dashboard-container {
            display: flex;
            justify-content: center;
            align-items: center;
            margin: 40px auto;
            padding: 25px 20px;
            background: linear-gradient(to right, #F37529, rgba(255, 255, 255, 0.8));
            border-radius: 15px;
            box-shadow: 0 6px 10px rgba(0, 0, 0, 0.3);
            animation: fadeIn 1.2s ease-out;
        }

        /* Título principal */
        .titulo-dashboard {
            font-size: 50px;
            font-weight: bold;
            color: #333333;
            text-shadow: 2px 2px 6px rgba(0, 0, 0, 0.3);
            letter-spacing: 2px;
            text-transform: uppercase;
        }
    </style>

    <!-- Container do Título -->
    <div class="titulo-dashboard-container">
        <h1 class="titulo-dashboard">Torre de Controle iTracker - Dashboard de Multas</h1>
    </div>
    """,
    unsafe_allow_html=True
)

# Inserir o logo da Itracker no topo usando o link do secrets
logo_url = st.secrets["image"]["logo_url"]
st.image(logo_url, width=150, use_container_width=False)

# Carregar e limpar os dados utilizando a função do google_drive.py
data = carregar_dados_google_drive()
data_cleaned = clean_data(data)

# Verificar colunas essenciais antes de prosseguir
required_columns = ['Data da Infração', 'Valor a ser pago R$', 'Auto de Infração', 'Status de Pagamento']
if not all(col in data_cleaned.columns for col in required_columns):
    st.error(f"Faltam colunas essenciais: {', '.join([col for col in required_columns if col not in data_cleaned.columns])}")
    st.stop()

# Calcular métricas principais
total_multas, valor_total_a_pagar, multas_mes_atual = calculate_metrics(data_cleaned)

# Calcular a data da última consulta
ultima_data_consulta = pd.to_datetime(data_cleaned['Dia da Consulta'].max(), errors='coerce')

# Exibir os indicadores principais
st.markdown("<h2 style='text-align: center; color: #F37529; font-size: 36px; font-weight: bold;'>Indicadores Principais</h2>", unsafe_allow_html=True)

st.markdown(
    f"""
    <div style="display: flex; justify-content: center; gap: 40px; flex-wrap: wrap;">
        <div style="text-align: center; border: 2px solid #F37529; border-radius: 10px; padding: 20px; width: 200px;">
            <h3 style="color: #F37529;">Total de Multas</h3>
            <p style="font-size: 28px; font-weight: bold;">{total_multas}</p>
        </div>
        <div style="text-align: center; border: 2px solid #F37529; border-radius: 10px; padding: 20px; width: 200px;">
            <h3 style="color: #F37529;">Valor Total a Pagar</h3>
            <p style="font-size: 28px; font-weight: bold;">R$ {valor_total_a_pagar:,.2f}</p>
        </div>
        <div style="text-align: center; border: 2px solid #F37529; border-radius: 10px; padding: 20px; width: 200px;">
            <h3 style="color: #F37529;">Multas no Mês Atual</h3>
            <p style="font-size: 28px; font-weight: bold;">{multas_mes_atual}</p>
        </div>
        <div style="text-align: center; border: 2px solid #F37529; border-radius: 10px; padding: 20px; width: 200px;">
            <h3 style="color: #F37529;">Última Consulta</h3>
            <p style="font-size: 28px; font-weight: bold;">{ultima_data_consulta.strftime("%d/%m/%Y") if pd.notnull(ultima_data_consulta) else "Data não disponível"}</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Exibir gráfico de infrações mais comuns
st.divider()
common_infractions_chart = create_common_infractions_chart(data_cleaned)
st.plotly_chart(common_infractions_chart, use_container_width=True)

# Footer
st.markdown(""" 
    <style>
        .footer {
            position: fixed;
            bottom: 0;
            width: 100%;
            background-color: #f9f9f9;
            padding: 10px;
            text-align: center;
            font-size: 14px;
            color: #6c757d;
            box-shadow: 0 -1px 5px rgba(0,0,0,0.1);
        }
    </style>
    <div class="footer">
        Dashboard de Multas © 2024 | Desenvolvido pela Equipe de Qualidade
    </div>
""", unsafe_allow_html=True)
