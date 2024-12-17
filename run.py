import streamlit as st
import pandas as pd
import folium
from folium.features import CustomIcon
from streamlit_folium import st_folium
from data_loader import clean_data  # Apenas a função de limpeza de dados é necessária aqui
from metrics import calculate_metrics
from graph_vehicles_fines import create_vehicle_fines_chart  # Importando a função de gráfico de veículos
common_infractions_chart = create_common_infractions_chart(filtered_data)
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

        /* Indicadores principais */
        .indicadores-container {
            display: flex;
            justify-content: center;
            gap: 40px;
            margin: 40px auto;
            flex-wrap: wrap;
        }

        .indicador {
            border: 4px solid #F37529;
            border-radius: 15px;
            box-shadow: 0 6px 10px rgba(0, 0, 0, 0.3);
            padding: 20px;
            text-align: center;
            width: 200px;
            font-size: 18px;
            color: #333;
            background-color: #FFF;
        }

        .indicador h3 {
            color: #F37529;
            font-size: 22px;
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
ultima_data_consulta = pd.to_datetime(data_cleaned['Dia da Consulta'].max(), errors='coerce')

# Exibir indicadores principais
st.markdown(
    f"""
    <div class="indicadores-container">
        <div class="indicador"><h3>Total de Multas</h3><p>{total_multas}</p></div>
        <div class="indicador"><h3>Valor Total a Pagar</h3><p>R$ {valor_total_a_pagar:,.2f}</p></div>
        <div class="indicador"><h3>Multas no Mês Atual</h3><p>{multas_mes_atual}</p></div>
        <div class="indicador"><h3>Última Consulta</h3><p>{ultima_data_consulta.strftime("%d/%m/%Y") if pd.notnull(ultima_data_consulta) else "Data não disponível"}</p></div>
    </div>
    """,
    unsafe_allow_html=True
)

# Gráficos sem o título do Plotly
st.divider()
st.markdown("<h2 style='text-align: center; color: #FF7F00;'>Top 10 Veículos com Mais Multas e Valores Totais</h2>", unsafe_allow_html=True)
st.plotly_chart(create_vehicle_fines_chart(data_cleaned), use_container_width=True)

st.divider()
st.markdown("<h2 style='text-align: center; color: #FF7F00;'>Distribuição Geográfica das Multas</h2>", unsafe_allow_html=True)
API_KEY = st.secrets["API_KEY"]
coordinates_cache = load_cache()
map_data = data_cleaned.dropna(subset=['Local da Infração']).copy()
map_data[['Latitude', 'Longitude']] = map_data['Local da Infração'].apply(
    lambda x: pd.Series(get_cached_coordinates(x, API_KEY, coordinates_cache))
)
save_cache(coordinates_cache)
map_center = [map_data['Latitude'].mean(), map_data['Longitude'].mean()] if not map_data.empty else [0, 0]
map_object = folium.Map(location=map_center, zoom_start=5)
st_folium(map_object, width=1200, height=600)

st.divider()
st.markdown("<h2 style='text-align: center; color: #FF7F00;'>Infrações Mais Frequentes</h2>", unsafe_allow_html=True)
st.plotly_chart(create_common_infractions_chart(data_cleaned), use_container_width=True)

st.divider()
st.markdown("<h2 style='text-align: center; color: #FF7F00;'>Valores das Multas Acumulados por Período</h2>", unsafe_allow_html=True)
st.plotly_chart(create_fines_accumulated_chart(data_cleaned, period='M'), use_container_width=True)

st.divider()
st.markdown("<h2 style='text-align: center; color: #FF7F00;'>Infrações Mais Frequentes por Dia da Semana</h2>", unsafe_allow_html=True)
st.plotly_chart(create_weekday_infractions_chart(data_cleaned), use_container_width=True)

# Footer
st.markdown("""
    <div style="text-align: center; margin-top: 50px; font-size: 14px; color: #777;">
        Dashboard de Multas © 2024 | Desenvolvido pela Equipe de Qualidade
    </div>
""", unsafe_allow_html=True)
