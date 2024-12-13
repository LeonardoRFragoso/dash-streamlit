import streamlit as st
import pandas as pd
import requests
import folium
import os
import json
from folium.features import CustomIcon
from streamlit_folium import st_folium
from config import FILE_PATH
from data_loader import load_data, clean_data
from metrics import calculate_metrics
from graph_vehicles_fines import create_vehicle_fines_chart
from graph_common_infractions import create_common_infractions_chart
from graph_plate_distribution import create_plate_distribution_chart
from graph_fines_accumulated import create_fines_accumulated_chart
from graph_weekday_infractions import create_weekday_infractions_chart

# Configuração inicial
st.set_page_config(page_title="Dashboard de Multas", layout="wide")

# Define cache file for coordinates
CACHE_FILE = "coordinates_cache.json"
API_KEY = '39758b43cb5649b0bc040bdd317ab3d9'

def load_cache():
    """Load the cache from a JSON file."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_cache(cache):
    """Save the cache to a JSON file."""
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f)

def get_cached_coordinates(local, api_key, cache):
    """Get coordinates from cache or API."""
    if local in cache:
        return cache[local]
    lat, lng = get_coordinates(local, api_key)
    if lat is not None and lng is not None:
        cache[local] = (lat, lng)
    return lat, lng

def get_coordinates(local, api_key):
    """Fetch coordinates for a given location using OpenCage API."""
    url = f'https://api.opencagedata.com/geocode/v1/json?q={local}&key={api_key}'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data['results']:
            geometry = data['results'][0]['geometry']
            return geometry['lat'], geometry['lng']
    return None, None

# Load and clean data
data = load_data(FILE_PATH)
data_cleaned = clean_data(data)

# Calculate metrics
total_multas, valor_total_a_pagar, multas_mes_atual = calculate_metrics(data_cleaned)

# Streamlit interface
st.markdown("<h1 style='text-align: center; color: #E74C3C;'>Dashboard de Multas</h1>", unsafe_allow_html=True)

# Highlight key metrics
st.markdown("<h2 style='text-align: center; color: #E74C3C; font-weight: bold;'>Indicadores Principais</h2>", unsafe_allow_html=True)
st.divider()
st.markdown(
    """
    <div style="display: flex; justify-content: center;">
        <div style="margin: 0 20px; text-align: center;">
            <h3 style="color: #E74C3C;">Total de Multas</h3>
            <p style="font-size: 34px; font-weight: bold; color: black;">{}</p>
        </div>
        <div style="margin: 0 20px; text-align: center;">
            <h3 style="color: #E74C3C;">Valor Total a Pagar (R$)</h3>
            <p style="font-size: 34px; font-weight: bold; color: black;">{}</p>
        </div>
        <div style="margin: 0 20px; text-align: center;">
            <h3 style="color: #E74C3C;">Multas no Mês Atual</h3>
            <p style="font-size: 34px; font-weight: bold; color: black;">{}</p>
        </div>
    </div>
    """.format(total_multas, f"R$ {valor_total_a_pagar:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), multas_mes_atual),
    unsafe_allow_html=True
)

st.divider()

# Date filter
st.markdown("<h2 style='text-align: center; color: #E74C3C; font-weight: bold;'>Filtro por Período</h2>", unsafe_allow_html=True)
filter_col1, filter_col2 = st.columns(2)
with filter_col1:
    start_date = st.date_input("Data inicial", value=data_cleaned['Dia da Consulta'].min().date())
with filter_col2:
    end_date = st.date_input("Data final", value=data_cleaned['Dia da Consulta'].max().date())

# Filter data by selected date range
filtered_data = data_cleaned[(data_cleaned['Dia da Consulta'] >= pd.Timestamp(start_date)) & 
                             (data_cleaned['Dia da Consulta'] <= pd.Timestamp(end_date))]

st.divider()

# Veículos com mais multas
st.markdown("<h2 style='text-align: center; color: #E74C3C; font-weight: bold;'>Top 10 Veículos com Mais Multas e Valores Totais</h2>", unsafe_allow_html=True)
top_vehicles_chart = create_vehicle_fines_chart(filtered_data)
st.plotly_chart(top_vehicles_chart, use_container_width=True)

# Add description below the chart
st.markdown(
    "<p style='text-align: center; font-size: 18px; color: black;'>"
    "Este gráfico mostra os 10 veículos com mais multas e seus valores totais dentro do período selecionado."
    "</p>",
    unsafe_allow_html=True
)

st.divider()

# Geographical distribution of fines and ranking
st.markdown("<h2 style='text-align: center; color: #E74C3C; font-weight: bold;'>Distribuição Geográfica das Multas e Ranking</h2>", unsafe_allow_html=True)

# Load cache
coordinates_cache = load_cache()

# Prepare data for the map
map_data = filtered_data.dropna(subset=['Local']).copy()
map_data[['Latitude', 'Longitude']] = map_data['Local'].apply(
    lambda x: pd.Series(get_cached_coordinates(x, API_KEY, coordinates_cache))
)

# Save updated cache
save_cache(coordinates_cache)

# Create map
map_center = [map_data['Latitude'].mean(), map_data['Longitude'].mean()] if not map_data.empty else [0, 0]
map_object = folium.Map(location=map_center, zoom_start=5, tiles="CartoDB dark_matter")

icon_url = "https://cdn-icons-png.flaticon.com/512/1828/1828843.png"  # URL de um triângulo de alerta

for _, row in map_data.iterrows():
    if pd.notnull(row['Latitude']) and pd.notnull(row['Longitude']):
        custom_icon = CustomIcon(icon_url, icon_size=(30, 30))
        popup_content = (
            f"<b>Local:</b> {row['Local']}<br>"
            f"<b>Valor:</b> R$ {row['Valor a Pagar (R$)']:,.2f}<br>"
            f"<b>Data da Infração:</b> {row['Data da Infração'].strftime('%d/%m/%Y')}<br>"
            f"<b>Detalhes:</b> {row.get('Descrição', 'Não especificado')}"
        )
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=folium.Popup(popup_content, max_width=300),
            icon=custom_icon
        ).add_to(map_object)

# Display map and ranking together
map_click_data = st_folium(map_object, width=1800, height=600)

# Detalhes das multas para a localização selecionada
if map_click_data and map_click_data.get("last_object_clicked"):
    lat = map_click_data["last_object_clicked"].get("lat")
    lng = map_click_data["last_object_clicked"].get("lng")

    # Ensure 'Descrição' column exists in map_data
    if 'Descrição' not in map_data.columns:
        map_data['Descrição'] = "Não especificado"

    # Filter fines for the selected location
    selected_fines = map_data[(map_data['Latitude'] == lat) & (map_data['Longitude'] == lng)]
    
    if not selected_fines.empty:
        st.markdown("<h2 style='text-align: center; color: #E74C3C; font-weight: bold;'>Detalhes das Multas para a Localização Selecionada</h2>", unsafe_allow_html=True)
        st.dataframe(
            selected_fines[['Local', 'Valor a Pagar (R$)', 'Data da Infração', 'Descrição']].reset_index(drop=True), 
            use_container_width=True, 
            hide_index=True
        )
    else:
        st.info("Nenhuma multa encontrada para a localização selecionada.")

st.divider()

# Ranking das Localidades com Maiores Valores de Multas
st.markdown("<h2 style='text-align: center; color: #E74C3C; font-weight: bold;'>Ranking das Localidades com Maiores Valores de Multas</h2>", unsafe_allow_html=True)
ranking_localidades = filtered_data.groupby('Local', as_index=False).agg(
    Valor_Total=('Valor a Pagar (R$)', 'sum'),
    Total_Multas=('Local', 'count')
).sort_values(by='Valor_Total', ascending=False).head(10)
st.dataframe(
    ranking_localidades.rename(columns={"Valor_Total": "Valor Total (R$)", "Total_Multas": "Total de Multas"}).reset_index(drop=True),
    use_container_width=True, 
    hide_index=True
)

st.divider()

# Infrações mais frequentes
st.markdown("<h2 style='text-align: center; color: #E74C3C; font-weight: bold;'>Infrações Mais Frequentes</h2>", unsafe_allow_html=True)
common_infractions_chart = create_common_infractions_chart(filtered_data)
st.plotly_chart(common_infractions_chart, use_container_width=True)

# Distribuição de Multas por Placas
st.markdown("<h2 style='text-align: center; color: #E74C3C; font-weight: bold;'>Distribuição de Multas por Placas</h2>", unsafe_allow_html=True)
plate_distribution_chart = create_plate_distribution_chart(filtered_data)
st.plotly_chart(plate_distribution_chart, use_container_width=True)

# Adicione uma descrição abaixo do gráfico
st.caption("Este gráfico mostra as placas com maior número de multas dentro do período selecionado.")

st.divider()

# Valores das Multas Acumulados por Período
st.markdown("<h2 style='text-align: center; color: #E74C3C; font-weight: bold;'>Valores das Multas Acumulados por Período</h2>", unsafe_allow_html=True)

# Permitir que o usuário selecione o período (Mensal ou Semanal)
period_option = st.radio(
    "Selecione o período para acumulação:",
    options=["Mensal", "Semanal"],
    index=0,
    horizontal=True
)

# Determinar o código do período com base na escolha do usuário
period_code = 'M' if period_option == "Mensal" else 'W'  # Corrigido de 'ME' para 'M'

# Criar o gráfico
fines_accumulated_chart = create_fines_accumulated_chart(filtered_data, period=period_code)

# Exibir o gráfico
st.plotly_chart(fines_accumulated_chart, use_container_width=True)

# Adicionar uma legenda explicando o gráfico
st.caption("Este gráfico mostra os valores acumulados das multas no período selecionado.")

st.divider()

# Infrações por Dia da Semana
st.markdown("<h2 style='text-align: center; color: #E74C3C; font-weight: bold;'>Infrações Mais Frequentes por Dia da Semana</h2>", unsafe_allow_html=True)

# Criar o gráfico de infrações por dia da semana
weekday_infractions_chart = create_weekday_infractions_chart(filtered_data)

# Exibir o gráfico
st.plotly_chart(weekday_infractions_chart, use_container_width=True)

# Adicionar uma legenda explicando o gráfico
st.caption("Este gráfico mostra a quantidade de multas distribuídas pelos dias da semana no período selecionado.")

# Footer
st.markdown(
    """
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
    """,
    unsafe_allow_html=True
)
