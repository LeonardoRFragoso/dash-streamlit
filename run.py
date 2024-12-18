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
            margin: 40px auto;
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
        .footer {
            text-align: center;
            font-size: 14px;
            color: #F37529;
            margin-top: 40px;
            padding: 10px 0;
            border-top: 1px solid #ddd;
        }
        .indicadores-container {
            display: flex;
            justify-content: center;
            align-items: center;
            flex-wrap: wrap;
            gap: 40px;
            margin-top: 30px;
        }
        .indicador {
            display: flex;
            justify-content: center;
            align-items: center;
            flex-direction: column;
            text-align: center;
            background-color: #FFFFFF;
            border: 4px solid #F37529;
            border-radius: 15px;
            box-shadow: 0 8px 12px rgba(0, 0, 0, 0.3);
            width: 260px;
            height: 160px;
        }
        .indicador p {
            font-size: 38px;
            font-weight: bold;
            color: #F37529;
            margin: 0;
        }
        .indicador span {
            font-size: 18px;
            color: #F37529;
            margin-bottom: 8px;
        }
    </style>
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

# Configurar as datas padrão
data_inicial_default = datetime(2024, 1, 1)
data_final_default = datetime.now()

# Inputs de data no Streamlit
data_inicial = st.date_input("Data Inicial", value=data_inicial_default, key="start_date")
data_final = st.date_input("Data Final", value=data_final_default, key="end_date")

# Botão para aplicar filtro
if st.button("Aplicar Filtro"):
    filtered_data = filtrar_dados_por_periodo(data_cleaned, data_inicial, data_final)

    # Atualizar métricas e gráficos com os dados filtrados
    total_multas, valor_total_a_pagar, multas_mes_atual = calcular_metricas(filtered_data)
    ultima_consulta = filtered_data['Dia da Consulta'].max().strftime('%d/%m/%Y')

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
                <span>Multas no Mês Atual</span>
                <p>{multas_mes_atual}</p>
            </div>
            <div class="indicador">
                <span>Última Consulta</span>
                <p>{ultima_consulta}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Gráficos e Mapa
    st.plotly_chart(create_vehicle_fines_chart(filtered_data), use_container_width=True)
    st.plotly_chart(create_common_infractions_chart(filtered_data), use_container_width=True)
    st.plotly_chart(create_fines_accumulated_chart(filtered_data, 'M'), use_container_width=True)
    st.plotly_chart(create_weekday_infractions_chart(filtered_data), use_container_width=True)

    # Mapa de Distribuição Geográfica
    st.markdown("### Distribuição Geográfica das Multas")
    API_KEY = st.secrets["API_KEY"]
    coordinates_cache = load_cache()

    map_data = filtered_data.dropna(subset=['Local da Infração']).copy()
    map_data[['Latitude', 'Longitude']] = map_data['Local da Infração'].apply(
        lambda x: pd.Series(get_cached_coordinates(x, API_KEY, coordinates_cache))
    )
    save_cache(coordinates_cache)

    map_center = [map_data['Latitude'].mean(), map_data['Longitude'].mean()] if not map_data.empty else [0, 0]
    map_object = folium.Map(location=map_center, zoom_start=5, tiles="CartoDB dark_matter")
    for _, row in map_data.iterrows():
        popup_content = f"<b>Local:</b> {row['Local da Infração']}<br><b>Valor:</b> R$ {row['Valor a ser pago R$']:.2f}"
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=folium.Popup(popup_content, max_width=300),
            icon=CustomIcon("https://cdn-icons-png.flaticon.com/512/1828/1828843.png", icon_size=(30, 30)),
        ).add_to(map_object)

    st_folium(map_object, width=1800, height=600)

else:
    st.info("Aguardando aplicação do filtro.")

# Footer
st.markdown("<div class='footer'>Dashboard de Multas © 2024 | Desenvolvido pela Equipe de Qualidade</div>", unsafe_allow_html=True)
