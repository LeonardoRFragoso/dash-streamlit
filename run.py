import streamlit as st
import pandas as pd
import folium
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
        .footer {
            text-align: center;
            font-size: 14px;
            color: #0066B4;
            margin-top: 40px;
            padding: 10px 0;
            border-top: 1px solid #ddd;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Exibir o logo da empresa acima do título
logo_url = st.secrets["image"]["logo_url"]  # URL do logo fornecido no secrets

st.markdown(
    f"""
    <div class="logo-container">
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
try:
    # Carregar dados do Google Drive
    raw_data = carregar_dados_google_drive()
    # Limpar e processar dados
    data_cleaned = carregar_e_limpar_dados(raw_data)
except Exception as e:
    st.error(f"Erro ao carregar ou processar os dados: {e}")
    st.stop()

# Verificar colunas essenciais
required_columns = ['Dia da Consulta', 'Data da Infração', 'Valor a ser pago R$', 'Auto de Infração', 'Status de Pagamento']
try:
    verificar_colunas_essenciais(data_cleaned, required_columns)
except ValueError as e:
    st.error(f"Erro: {e}")
    st.stop()

# Calcular métricas principais
total_multas, valor_total_a_pagar, ultima_consulta = calcular_metricas(data_cleaned)

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

# Filtro por Período
st.markdown("<h2 class='titulo-secao'>Filtro por Período</h2>", unsafe_allow_html=True)
start_date = st.date_input("Data Inicial", value=data_cleaned['Dia da Consulta'].min())
end_date = st.date_input("Data Final", value=data_cleaned['Dia da Consulta'].max())

filtered_data = filtrar_dados_por_periodo(data_cleaned, start_date, end_date)

# Gráficos e Mapas
st.markdown("<h2 class='titulo-secao'>Top 10 Veículos com Mais Multas</h2>", unsafe_allow_html=True)
st.plotly_chart(create_vehicle_fines_chart(filtered_data), use_container_width=True)

st.markdown("<h2 class='titulo-secao'>Distribuição Geográfica</h2>", unsafe_allow_html=True)
map_data = filtered_data.dropna(subset=['Local da Infração']).copy()
coordinates_cache = load_cache()
map_data[['Latitude', 'Longitude']] = map_data['Local da Infração'].apply(
    lambda x: pd.Series(get_cached_coordinates(x, st.secrets["API_KEY"], coordinates_cache))
)
save_cache(coordinates_cache)

map_center = [map_data['Latitude'].mean(), map_data['Longitude'].mean()] if not map_data.empty else [0, 0]
map_object = folium.Map(location=map_center, zoom_start=5, tiles="CartoDB dark_matter")

for _, row in map_data.iterrows():
    folium.Marker(
        location=[row['Latitude'], row['Longitude']],
        popup=f"{row['Local da Infração']} - R$ {row['Valor a ser pago R$']:.2f}",
        icon=CustomIcon("https://cdn-icons-png.flaticon.com/512/1828/1828843.png", icon_size=(30, 30))
    ).add_to(map_object)
st_folium(map_object, width="100%", height=600)

# Detalhes das multas para a localização selecionada
map_click_data = st_folium(map_object, width="100%", height=600)
if map_click_data and map_click_data.get("last_object_clicked"):
    lat = map_click_data["last_object_clicked"].get("lat")
    lng = map_click_data["last_object_clicked"].get("lng")

    # Filtrando as multas que correspondem ao local clicado
    selected_fines = map_data[(map_data['Latitude'] == lat) & (map_data['Longitude'] == lng)]

    if not selected_fines.empty:
        st.markdown("<h2 class='titulo-secao' style='color: #0066B4;'>Detalhes das Multas para a Localização Selecionada</h2>", unsafe_allow_html=True)
        st.dataframe(
            selected_fines[['Local da Infração', 'Valor a ser pago R$', 'Data da Infração', 'Descrição']].reset_index(drop=True),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Nenhuma multa encontrada para a localização selecionada.")

# Gráfico de Top 10 Veículos
st.markdown("<h2 class='titulo-secao' style='color: #0066B4;'>Top 10 Veículos com Mais Multas e Valores Totais</h2>", unsafe_allow_html=True)
st.plotly_chart(create_vehicle_fines_chart(filtered_data), use_container_width=True)

# Ranking das Localidades
st.markdown("<h2 class='titulo-secao' style='color: #0066B4;'>Ranking das Localidades com Mais Multas</h2>", unsafe_allow_html=True)
ranking_localidades = filtered_data.groupby('Local da Infração', as_index=False).agg(
    Valor_Total=('Valor a ser pago R$', 'sum'),
    Total_Multas=('Local da Infração', 'count')
).sort_values(by='Valor_Total', ascending=False)

st.dataframe(
    ranking_localidades.reset_index(drop=True),  # Remove o índice original
    use_container_width=True,
    hide_index=True  # Oculta o índice no Streamlit
)

# Gráficos adicionais
st.markdown("<h2 class='titulo-secao' style='color: #0066B4;'>Infrações Mais Frequentes</h2>", unsafe_allow_html=True)
st.plotly_chart(create_common_infractions_chart(filtered_data), use_container_width=True)

st.markdown("<h2 class='titulo-secao' style='color: #0066B4;'>Valores das Multas Acumulados por Período</h2>", unsafe_allow_html=True)
period_option = st.radio("Selecione o período:", ["Mensal", "Semanal"], horizontal=True)
st.plotly_chart(create_fines_accumulated_chart(filtered_data, 'M' if period_option == "Mensal" else 'W'), use_container_width=True)

st.markdown("<h2 class='titulo-secao' style='color: #0066B4;'>Infrações Mais Frequentes por Dia da Semana</h2>", unsafe_allow_html=True)
st.plotly_chart(create_weekday_infractions_chart(filtered_data), use_container_width=True)

# Footer
st.markdown("<div class='footer'>Dashboard de Multas © 2024 | Desenvolvido pela Equipe de Qualidade</div>", unsafe_allow_html=True)
