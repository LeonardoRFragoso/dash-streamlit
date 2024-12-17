import streamlit as st
import pandas as pd
import requests
import folium
import os
import io
import json
from folium.features import CustomIcon
from streamlit_folium import st_folium
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from data_loader import load_data, clean_data
from metrics import calculate_metrics
from graph_vehicles_fines import create_vehicle_fines_chart
from graph_common_infractions import create_common_infractions_chart
from graph_fines_accumulated import create_fines_accumulated_chart
from graph_weekday_infractions import create_weekday_infractions_chart

# Configuração inicial
st.set_page_config(page_title="Torre de Controle iTracker - Dashboard de Multas", layout="wide")

# Streamlit interface
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

        /* Subtítulo */
        .subtitulo-dashboard {
            font-size: 20px;
            color: #555555;
            margin-top: 10px;
            text-align: center;
            font-style: italic;
        }

        /* Seção dos indicadores principais */
        .indicadores-container {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 40px;
            flex-wrap: wrap;
            margin: 40px auto;
            padding: 30px 20px;
            background: linear-gradient(to right, #fff, #FDF1E8);
            border-radius: 15px;
            box-shadow: 0 10px 15px rgba(0, 0, 0, 0.2);
            animation: fadeIn 1.5s ease-out;
        }

        /* Indicador individual */
        .indicador {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            background-color: #FFFFFF;
            border: 4px solid #F37529; /* Laranja ITracker */
            border-radius: 15px;
            box-shadow: 0 8px 12px rgba(0, 0, 0, 0.3);
            width: 260px;
            height: 160px;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            animation: fadeIn 2s ease-out;
        }

        .indicador:hover {
            transform: translateY(-10px);
            box-shadow: 0 12px 18px rgba(0, 0, 0, 0.4);
            border-color: #F37529;
        }

        .indicador h3 {
            color: #F37529; /* Laranja ITracker */
            font-size: 22px;
            font-weight: bold;
            margin-bottom: 10px;
        }

        .indicador p {
            font-size: 38px;
            font-weight: bold;
            color: #F37529; /* Laranja ITracker */
            margin: 0;
        }
    </style>

    <!-- Container do Título -->
    <div class="titulo-dashboard-container">
        <div>
            <h1 class="titulo-dashboard">Torre de Controle iTracker - Dashboard de Multas</h1>
            <p class="subtitulo-dashboard">Monitore e analise suas multas em tempo real com gráficos e indicadores.</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Inserir o logo da Itracker no topo usando o link do secrets
logo_url = st.secrets["image"]["logo_url"]
st.image(logo_url, width=150, use_container_width=False)

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
    # Converte explicitamente o conteúdo de CREDENTIALS para string e depois para JSON
    credentials_str = str(st.secrets["CREDENTIALS"])  # Converte AttrDict para string
    credentials_dict = json.loads(credentials_str.replace("\n", "\\n"))  # Ajusta quebras de linha e carrega JSON
    
    # Cria as credenciais a partir do dicionário
    credentials = Credentials.from_service_account_info(
        credentials_dict, 
        scopes=["https://www.googleapis.com/auth/drive"]
    )
    
    # Retorna o serviço autenticado do Google Drive
    return build("drive", "v3", credentials=credentials)

def obter_id_ultima_planilha():
    """Obtém o ID da última planilha salva no JSON."""
    try:
        with open(st.secrets["ULTIMA_PLANILHA_JSON"], 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get("file_id")
    except Exception as e:
        st.error(f"Erro ao carregar o ID da última planilha: {e}")
        st.stop()

def carregar_dados_google_drive():
    """Carrega os dados da última planilha no Google Drive."""
    try:
        drive_service = autenticar_google_drive()
        file_id = st.secrets["file_data"]["ultima_planilha_id"]
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

# Calcular métricas principais
total_multas, valor_total_a_pagar, multas_mes_atual = calculate_metrics(data_cleaned)

# Calcular a data da última consulta
ultima_data_consulta = data_cleaned['Dia da Consulta'].max()

st.divider()

# Subtítulo para os indicadores principais
st.markdown("<h2 style='text-align: center; color: #F37529; font-size: 36px; font-weight: bold; text-shadow: 1px 1px 4px rgba(0,0,0,0.3);'>Indicadores Principais</h2>", unsafe_allow_html=True)

# Indicadores principais
st.markdown(
    f"""
    <style>
        /* Configurações globais */
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        /* Contêiner dos indicadores */
        .indicadores-container {{
            display: flex;
            justify-content: center; /* Centraliza horizontalmente */
            align-items: center; /* Alinha verticalmente */
            gap: 20px; /* Espaçamento uniforme entre caixas */
            flex-wrap: wrap;
            margin: 20px auto;
            max-width: 90%;
            padding: 20px 10px;
            background: linear-gradient(to right, #fff, #FDF1E8);
            border-radius: 15px;
            box-shadow: 0 10px 15px rgba(0, 0, 0, 0.2);
        }}

        /* Indicador individual */
        .indicador {{
            display: flex;
            flex-direction: column;
            justify-content: center; /* Alinha o conteúdo verticalmente */
            align-items: center; /* Alinha o conteúdo horizontalmente */
            text-align: center; /* Centraliza o texto */
            background-color: #FFFFFF;
            border: 4px solid #F37529;
            border-radius: 15px;
            box-shadow: 0 8px 12px rgba(0, 0, 0, 0.3);
            width: 230px; /* Largura fixa */
            height: 140px; /* Altura fixa */
            padding: 10px; /* Padding simétrico */
            box-sizing: border-box;
        }}

        /* Título do indicador - Usando span para mais controle */
        .indicador span {{
            font-size: 18px;
            font-weight: bold;
            color: #F37529;
            margin: 0; /* Remove margem */
            white-space: nowrap; /* Evita quebra de linha */
            flex: 1; /* Ocupa o espaço proporcional */
            display: flex;
            justify-content: center; /* Centraliza o título horizontalmente */
            align-items: center; /* Alinha o título verticalmente */
            text-align: center; /* Garante o alinhamento do texto */
        }}

        /* Valor do indicador */
        .indicador p {{
            font-size: 28px;
            font-weight: bold;
            color: #F37529;
            margin: 0; /* Remove margem */
            flex: 1; /* Ocupa o espaço proporcional */
            display: flex;
            justify-content: center; /* Centraliza o valor horizontalmente */
            align-items: center; /* Centraliza o valor verticalmente */
            text-align: center; /* Garante o alinhamento do valor */
        }}
    </style>

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
            <p>{ultima_data_consulta.strftime("%d/%m/%Y") if pd.notnull(ultima_data_consulta) else "Data não disponível"}</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.divider()

# Filtro por Período
st.divider()
st.markdown("<h2 style='text-align: center; color: #F37529; font-size: 32px; font-weight: bold;'>Filtro por Período</h2>", unsafe_allow_html=True)

# Criação das colunas para os campos de data
filter_col1, filter_col2 = st.columns(2)

# Definição de valores padrão para as datas
min_date = data_cleaned['Dia da Consulta'].min().date() if not data_cleaned['Dia da Consulta'].isnull().all() else None
max_date = data_cleaned['Dia da Consulta'].max().date() if not data_cleaned['Dia da Consulta'].isnull().all() else None

# Garante que as datas iniciais não estejam nulas
start_date_default = min_date or pd.to_datetime("today").date()
end_date_default = max_date or pd.to_datetime("today").date()

# Entrada de data inicial e final
with filter_col1:
    start_date = st.date_input(
        "Data Inicial",
        value=start_date_default,  # Valor padrão inicial
        min_value=min_date,  # Permite selecionar desde a data mínima
        max_value=max_date,  # Permite selecionar até a data máxima
        key="start_date"
    )

with filter_col2:
    end_date = st.date_input(
        "Data Final",
        value=end_date_default,  # Valor padrão inicial
        min_value=min_date,  # Permite selecionar desde a data mínima
        max_value=max_date,  # Permite selecionar até a data máxima
        key="end_date"
    )

# Inicializa filtered_data como data_cleaned para uso antes do botão ser clicado
filtered_data = data_cleaned.copy()

# Adiciona botão para confirmar o filtro
apply_filter = st.button("Aplicar Filtro")

# Validação das datas selecionadas e aplicação do filtro após o clique no botão
if apply_filter:
    if start_date > end_date:
        st.error("A Data Inicial não pode ser posterior à Data Final. Por favor, selecione um intervalo válido.")
    else:
        # Filtragem dos dados conforme as datas selecionadas
        filtered_data = data_cleaned[
            (data_cleaned['Dia da Consulta'] >= pd.Timestamp(start_date)) & 
            (data_cleaned['Dia da Consulta'] <= pd.Timestamp(end_date))
        ]

        # Exibir mensagem de sucesso
        st.success(f"Dados filtrados entre {start_date.strftime('%d/%m/%Y')} e {end_date.strftime('%d/%m/%Y')}")

# Veículos com mais multas
st.divider()
st.markdown("<h2 style='text-align: center; color: #FF7F00; font-weight: bold;'>Top 10 Veículos com Mais Multas e Valores Totais</h2>", unsafe_allow_html=True)
top_vehicles_chart = create_vehicle_fines_chart(filtered_data)
st.plotly_chart(top_vehicles_chart, use_container_width=True)

# Adicionar descrição abaixo do gráfico
st.markdown("<p style='text-align: center; font-size: 18px; color: black;'>"
    "10 veículos com mais multas e seus valores totais dentro do período selecionado."
    "</p>",
    unsafe_allow_html=True
)

st.divider()

# Distribuição geográfica das multas e ranking
st.markdown("<h2 style='text-align: center; color: #FF7F00; font-weight: bold;'>Distribuição Geográfica das Multas e Ranking</h2>", unsafe_allow_html=True)

# Prepare data for the map
API_KEY = st.secrets["API_KEY"]
coordinates_cache = load_cache()

# Filtra dados para o mapa usando filtered_data
map_data = filtered_data.dropna(subset=['Local da Infração']).copy()
map_data[['Latitude', 'Longitude']] = map_data['Local da Infração'].apply(
    lambda x: pd.Series(get_cached_coordinates(x, API_KEY, coordinates_cache))
)

# Save updated cache
save_cache(coordinates_cache)

# Criação do mapa
map_center = [map_data['Latitude'].mean(), map_data['Longitude'].mean()] if not map_data.empty else [0, 0]
map_object = folium.Map(location=map_center, zoom_start=5, tiles="CartoDB dark_matter")

icon_url = "https://cdn-icons-png.flaticon.com/512/1828/1828843.png"  # URL de um triângulo de alerta

# Adicionar marcadores ao mapa
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