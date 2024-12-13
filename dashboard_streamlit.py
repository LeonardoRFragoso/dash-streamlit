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
st.title("Dashboard de Multas")

# Highlight key metrics
st.markdown("### Indicadores principais")
col1, col2, col3 = st.columns(3)

col1.metric(label="Total de Multas", value=f"{total_multas}")
col2.metric(label="Valor Total a Pagar (R$)", value=f"{valor_total_a_pagar:,.2f}")
col3.metric(label="Multas no Mês Atual", value=f"{multas_mes_atual}")

# Date filter
st.markdown("#### Filtro por Período")
filter_col1, filter_col2 = st.columns(2)
with filter_col1:
    start_date = st.date_input("Data inicial", value=data_cleaned['Dia da Consulta'].min().date())
with filter_col2:
    end_date = st.date_input("Data final", value=data_cleaned['Dia da Consulta'].max().date())

# Filter data by selected date range
filtered_data = data_cleaned[(data_cleaned['Dia da Consulta'] >= pd.Timestamp(start_date)) & 
                             (data_cleaned['Dia da Consulta'] <= pd.Timestamp(end_date))]

# Veículos com mais multas
st.markdown("#### Top 10 Veículos com Mais Multas e Valores Totais")
top_vehicles_chart = create_vehicle_fines_chart(filtered_data)
st.plotly_chart(top_vehicles_chart, use_container_width=True)

# Add description below the chart
st.caption("Este gráfico mostra os 10 veículos com mais multas e seus valores totais dentro do período selecionado.")

# Geographical distribution of fines
st.markdown("#### Distribuição Geográfica das Multas")

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
map_object = folium.Map(location=map_center, zoom_start=5)

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

# Display map
map_click_data = st_folium(map_object, width=700, height=500)

# Display table of fines details based on map interaction
if map_click_data and map_click_data.get("last_object_clicked"):
    lat = map_click_data["last_object_clicked"].get("lat")
    lng = map_click_data["last_object_clicked"].get("lng")

    # Ensure 'Descrição' column exists in map_data
    if 'Descrição' not in map_data.columns:
        map_data['Descrição'] = "Não especificado"

    # Filter fines for the selected location
    selected_fines = map_data[(map_data['Latitude'] == lat) & (map_data['Longitude'] == lng)]
    
    if not selected_fines.empty:
        st.markdown("#### Detalhes das Multas para a Localização Selecionada")
        st.dataframe(selected_fines[['Local', 'Valor a Pagar (R$)', 'Data da Infração', 'Descrição']])
    else:
        st.info("Nenhuma multa encontrada para a localização selecionada.")