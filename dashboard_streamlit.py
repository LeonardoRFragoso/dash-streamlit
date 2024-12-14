import streamlit as st
import pandas as pd
import requests
import folium
import os
import io
import json
from folium.features import CustomIcon
from streamlit_folium import st_folium
from config import CREDENTIALS_FILE, ULTIMA_PLANILHA_JSON, API_KEY, GOOGLE_DRIVE_FOLDER_ID
from data_loader import load_data, clean_data
from metrics import calculate_metrics
from graph_vehicles_fines import create_vehicle_fines_chart
from graph_common_infractions import create_common_infractions_chart
from graph_fines_accumulated import create_fines_accumulated_chart
from graph_weekday_infractions import create_weekday_infractions_chart
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# Configuração inicial
st.set_page_config(page_title="Torre de Controle - Dashboard de Multas", layout="wide")

# Inserir o logo da Itracker no topo
logo_path = r"C:\Users\leona\OneDrive\Documentos\Dash_streamlit\itracker logo.jpg"
st.image(logo_path, width=150, use_container_width=False)

# Define cache file for coordinates
CACHE_FILE = "coordinates_cache.json"

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

def autenticar_google_drive():
    """Autentica no Google Drive usando credenciais de serviço."""
    credentials = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=["https://www.googleapis.com/auth/drive"])
    return build("drive", "v3", credentials=credentials)

def obter_id_ultima_planilha():
    """Obtém o ID da última planilha salva no JSON."""
    try:
        with open(ULTIMA_PLANILHA_JSON, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("file_id")
    except Exception as e:
        st.error(f"Erro ao carregar o ID da última planilha: {e}")
        st.stop()

def carregar_dados_google_drive():
    """Carrega os dados da última planilha no Google Drive."""
    try:
        drive_service = autenticar_google_drive()
        file_id = obter_id_ultima_planilha()
        request = drive_service.files().get_media(fileId=file_id)
        file_buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(file_buffer, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        file_buffer.seek(0)
        return pd.read_excel(file_buffer)
    except Exception as e:
        st.error(f"Erro ao carregar os dados do Google Drive: {e}")
        st.stop()

# Carregar e limpar os dados
data = carregar_dados_google_drive()
data_cleaned = clean_data(data)

# Ajustar campos necessários
if 'Valor a ser pago R$' in data_cleaned.columns:
    data_cleaned.loc[:, 'Valor a ser pago R$'] = data_cleaned['Valor a ser pago R$'].replace(
        {r'[^0-9,]': '', ',': '.'}, regex=True
    ).astype(float)
else:
    st.error("A coluna 'Valor a ser pago R$' não foi encontrada nos dados carregados.")
    st.stop()

if 'Local da Infração' in data_cleaned.columns:
    data_cleaned.loc[:, 'Local da Infração'] = data_cleaned['Local da Infração'].fillna('Desconhecido')
else:
    st.error("A coluna 'Local da Infração' não foi encontrada nos dados carregados.")
    st.stop()

# Ajustar datas
data_cleaned.loc[:, 'Dia da Consulta'] = pd.to_datetime(data_cleaned['Dia da Consulta'], dayfirst=True, errors='coerce')
data_cleaned.loc[:, 'Data da Infração'] = pd.to_datetime(data_cleaned['Data da Infração'], dayfirst=True, errors='coerce')

# Calcular métricas
total_multas, valor_total_a_pagar, multas_mes_atual = calculate_metrics(data_cleaned)

# Streamlit interface
st.markdown("<h1 style='text-align: center; color: #0056b3;'>Torre de Controle - Dashboard de Multas</h1>", unsafe_allow_html=True)

st.divider()

# Highlight key metrics
st.markdown("<h2 style='text-align: center; color: #FF7F00; font-weight: bold;'>Indicadores Principais</h2>", unsafe_allow_html=True)

st.markdown(
    """
    <div style="display: flex; justify-content: space-around; margin: 20px 0; color: #333;">
        <div style="text-align: center;">
            <h3 style="color: #1E90FF;">Total de Multas</h3>
            <p style="font-size: 34px; font-weight: bold; color: black;">{}</p>
        </div>
        <div style="text-align: center;">
            <h3 style="color: #FFA500;">Valor Total a Pagar (R$)</h3>
            <p style="font-size: 34px; font-weight: bold; color: black;">{}</p>
        </div>
        <div style="text-align: center;">
            <h3 style="color: #1E90FF;">Multas no Mês Atual</h3>
            <p style="font-size: 34px; font-weight: bold; color: black;">{}</p>
        </div>
    </div>
    """.format(total_multas, f"R$ {valor_total_a_pagar:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'), multas_mes_atual),
    unsafe_allow_html=True
)

st.divider()

# Filtro de data com formato brasileiro (dd/mm/yyyy)
st.markdown("<h2 style='text-align: center; color: #FF7F00; font-weight: bold;'>Filtro por Período</h2>", unsafe_allow_html=True)

# Adicionar colunas para os campos de entrada
filter_col1, filter_col2 = st.columns(2)

with filter_col1:
    st.markdown("<p style='text-align: center; font-size: 18px; color: #333;'>Data Inicial:</p>", unsafe_allow_html=True)
    start_date = st.date_input("", value=data_cleaned['Dia da Consulta'].min().date(), key="start_date")
    st.markdown(f"<p style='text-align: center; font-size: 16px; color: #FF7F00;'>Selecionada: {start_date.strftime('%d/%m/%Y')}</p>", unsafe_allow_html=True)

with filter_col2:
    st.markdown("<p style='text-align: center; font-size: 18px; color: #333;'>Data Final:</p>", unsafe_allow_html=True)
    end_date = st.date_input("", value=data_cleaned['Dia da Consulta'].max().date(), key="end_date")
    st.markdown(f"<p style='text-align: center; font-size: 16px; color: #FF7F00;'>Selecionada: {end_date.strftime('%d/%m/%Y')}</p>", unsafe_allow_html=True)

# Filtrar dados pelo intervalo selecionado
filtered_data = data_cleaned[(data_cleaned['Dia da Consulta'] >= pd.Timestamp(start_date)) & 
                             (data_cleaned['Dia da Consulta'] <= pd.Timestamp(end_date))]

st.divider()

# Veículos com mais multas
st.markdown("<h2 style='text-align: center; color: #FF7F00; font-weight: bold;'>Top 10 Veículos com Mais Multas e Valores Totais</h2>", unsafe_allow_html=True)
top_vehicles_chart = create_vehicle_fines_chart(filtered_data)
st.plotly_chart(top_vehicles_chart, use_container_width=True)

# Adicionar descrição abaixo do gráfico com estilo consistente
st.markdown("<p style='text-align: center; font-size: 18px; color: black;'>"
    "10 veículos com mais multas e seus valores totais dentro do período selecionado."
    "</p>",
    unsafe_allow_html=True
)

st.divider()

# Distribuição geográfica das multas e ranking
st.markdown("<h2 style='text-align: center; color: #FF7F00; font-weight: bold;'>Distribuição Geográfica das Multas e Ranking</h2>", unsafe_allow_html=True)

# Load cache
coordinates_cache = load_cache()

# Prepare data for the map
map_data = filtered_data.dropna(subset=['Local da Infração']).copy()
map_data[['Latitude', 'Longitude']] = map_data['Local da Infração'].apply(
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
        data_infracao = (
            row['Data da Infração'].strftime('%d/%m/%Y') 
            if pd.notnull(row['Data da Infração']) else "Data não disponível"
        )
        popup_content = (
            f"<b>Local:</b> {row['Local da Infração']}<br>"
            f"<b>Valor:</b> R$ {row['Valor a ser pago R$']:,.2f}<br>"
            f"<b>Data da Infração:</b> {data_infracao}<br>"
            f"<b>Detalhes:</b> {row.get('Descrição', 'Não especificado')}"
        )
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=folium.Popup(popup_content, max_width=300),
            icon=custom_icon
        ).add_to(map_object)

# Display map
map_click_data = st_folium(map_object, width=1800, height=600)

# Detalhes das multas para a localização selecionada
if map_click_data and map_click_data.get("last_object_clicked"):
    lat = map_click_data["last_object_clicked"].get("lat")
    lng = map_click_data["last_object_clicked"].get("lng")

    if 'Descrição' not in map_data.columns:
        map_data['Descrição'] = "Não especificado"

    selected_fines = map_data[(map_data['Latitude'] == lat) & (map_data['Longitude'] == lng)]

    if not selected_fines.empty:
        st.markdown("<h2 style='text-align: center; color: #FF7F00; font-weight: bold;'>Detalhes das Multas para a Localização Selecionada</h2>", unsafe_allow_html=True)
        st.dataframe(
            selected_fines[['Local da Infração', 'Valor a ser pago R$', 'Data da Infração', 'Descrição']].reset_index(drop=True),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Nenhuma multa encontrada para a localização selecionada.")

st.divider()

# Ranking das Localidades com Maiores Valores de Multas
st.markdown("<h2 style='text-align: center; color: #FF7F00; font-weight: bold;'>Ranking das Localidades com Maiores Valores de Multas</h2>", unsafe_allow_html=True)

ranking_localidades = filtered_data.groupby('Local da Infração', as_index=False).agg(
    Valor_Total=('Valor a ser pago R$', 'sum'),
    Total_Multas=('Local da Infração', 'count')
).sort_values(by='Valor_Total', ascending=False).head(10)

st.dataframe(
    ranking_localidades.rename(columns={"Valor_Total": "Valor Total (R$)", "Total_Multas": "Total de Multas"}).reset_index(drop=True),
    use_container_width=True,
    hide_index=True
)

st.divider()

# Infrações mais frequentes
st.markdown("<h2 style='text-align: center; color: #FF7F00; font-weight: bold;'>Infrações Mais Frequentes</h2>", unsafe_allow_html=True)
common_infractions_chart = create_common_infractions_chart(filtered_data)
st.plotly_chart(common_infractions_chart, use_container_width=True)

# Valores das Multas Acumulados por Período
st.markdown("<h2 style='text-align: center; color: #FF7F00; font-weight: bold;'>Valores das Multas Acumulados por Período</h2>", unsafe_allow_html=True)
period_option = st.radio(
    "Selecione o período para acumulação:",
    options=["Mensal", "Semanal"],
    index=0,
    horizontal=True
)
period_code = 'M' if period_option == "Mensal" else 'W'
fines_accumulated_chart = create_fines_accumulated_chart(filtered_data, period=period_code)
st.plotly_chart(fines_accumulated_chart, use_container_width=True)
st.markdown("<p style='text-align: center; font-size: 18px; color: black;'>Valores acumulados das multas no período selecionado.</p>", unsafe_allow_html=True)

st.divider()

# Infrações por Dia da Semana
st.markdown("<h2 style='text-align: center; color: #FF7F00; font-weight: bold;'>Infrações Mais Frequentes por Dia da Semana</h2>", unsafe_allow_html=True)
weekday_infractions_chart = create_weekday_infractions_chart(filtered_data)
st.plotly_chart(weekday_infractions_chart, use_container_width=True)
st.markdown("<p style='text-align: center; font-size: 18px; color: black;'>Quantidade de multas distribuídas pelos dias da semana no período selecionado.</p>", unsafe_allow_html=True)

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
