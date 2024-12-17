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

# Função para carregar os dados do Google Drive
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

# Filtro por Período
st.markdown("<h2 style='text-align: center; color: #F37529; font-size: 32px; font-weight: bold;'>Filtro por Período</h2>", unsafe_allow_html=True)

filter_col1, filter_col2 = st.columns(2)

min_date = data_cleaned['Dia da Consulta'].dropna().min().date()
max_date = data_cleaned['Dia da Consulta'].dropna().max().date()

# Captura das datas com valores padrão
with filter_col1:
    start_date = st.date_input("Data Inicial", value=min_date, min_value=min_date, max_value=max_date, key="start_date")

with filter_col2:
    end_date = st.date_input("Data Final", value=max_date, min_value=min_date, max_value=max_date, key="end_date")

# Botão para aplicar o filtro
if st.button("Aplicar Filtro"):
    if start_date > end_date:
        st.error("A Data Inicial não pode ser posterior à Data Final.")
    else:
        # Aplicar o filtro com base nas datas selecionadas
        filtered_data = data_cleaned[
            (data_cleaned['Dia da Consulta'].dt.date >= start_date) &
            (data_cleaned['Dia da Consulta'].dt.date <= end_date)
        ]

        if filtered_data.empty:
            st.warning("Nenhum dado encontrado para o intervalo selecionado.")
        else:
            st.success("Filtro aplicado com sucesso!")
            # Gráfico Top 10 Veículos
            try:
                top_vehicles_chart = create_vehicle_fines_chart(filtered_data)
                st.plotly_chart(top_vehicles_chart, use_container_width=True)
            except Exception as e:
                st.error(f"Erro ao gerar o gráfico: {e}")

            
            # Verificar se a coluna 'Placa Relacionada' tem dados
            if 'Placa Relacionada' not in filtered_data.columns or filtered_data['Placa Relacionada'].isnull().all():
                st.error("Os dados filtrados não possuem informações suficientes sobre 'Placa Relacionada'.")
            else:
                try:
                    top_vehicles_chart = create_vehicle_fines_chart(filtered_data)
                    st.plotly_chart(top_vehicles_chart, use_container_width=True)

                    common_infractions_chart = create_common_infractions_chart(filtered_data)
                    st.plotly_chart(common_infractions_chart, use_container_width=True)

                    period_option = st.radio("Selecione o período para acumulação:", options=["Mensal", "Semanal"], index=0, horizontal=True)
                    period_code = 'M' if period_option == "Mensal" else 'W'
                    fines_accumulated_chart = create_fines_accumulated_chart(filtered_data, period=period_code)
                    st.plotly_chart(fines_accumulated_chart, use_container_width=True)

                    weekday_infractions_chart = create_weekday_infractions_chart(filtered_data)
                    st.plotly_chart(weekday_infractions_chart, use_container_width=True)

                except Exception as e:
                    st.error(f"Erro ao gerar os gráficos: {e}")

st.divider()

# Veículos com mais multas
st.markdown("<h2 style='text-align: center; color: #FF7F00; font-weight: bold;'>Top 10 Veículos com Mais Multas e Valores Totais</h2>", unsafe_allow_html=True)
top_vehicles_chart = create_vehicle_fines_chart(filtered_data)
top_vehicles_chart.update_layout(template="plotly_dark")  # Forçar o template escuro
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

# Prepare data for the map
API_KEY = st.secrets["API_KEY"]  # Adicione esta linha
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