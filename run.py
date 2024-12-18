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
        .titulo-secao {
            text-align: center;
            font-size: 36px;
            font-weight: bold;
            color: #F37529;
            margin-top: 30px;
            margin-bottom: 20px;
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
            border: 4px solid #F37529;
            border-radius: 15px;
            box-shadow: 0 8px 12px rgba(0, 0, 0, 0.3);
            width: 260px;
            height: 160px;
            padding: 10px;            /* Adiciona espaçamento interno */
        }
        .indicador span {
            font-size: 18px;
            color: #F37529;
        }
        .indicador p {
            font-size: 38px;
            color: #F37529;
            margin: 0;
            font-weight: bold;
        }
    </style>
    <div class="titulo-dashboard-container">
        <h1 class="titulo-dashboard">Torre de Controle iTracker - Dashboard de Multas</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

# Exibir o logo da empresa abaixo do título
logo_url = st.secrets["image"]["logo_url"]  # URL do logo fornecido no secrets
st.image(logo_url, width=200, use_container_width=False)

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

# Cálculo do número de multas no mês atual
data_atual = pd.to_datetime(datetime.now()).date()  # Data de hoje
data_cleaned['Dia da Consulta'] = pd.to_datetime(data_cleaned['Dia da Consulta'], errors='coerce').dt.date

# Filtra apenas as multas do mês atual (dezembro de 2024)
multas_mes_atual = len(data_cleaned[
    (data_cleaned['Dia da Consulta'] == data_atual) & 
    (data_cleaned['Data da Infração'].dt.month == 12) & 
    (data_cleaned['Data da Infração'].dt.year == 2024)
])

# Calcular métricas
total_multas, valor_total_a_pagar, _ = calcular_metricas(data_cleaned)
ultima_consulta = data_cleaned['Dia da Consulta'].max().strftime('%d/%m/%Y')

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
        <div class="indicador">
            <span>Multas no Mês Atual</span>
            <p>{multas_mes_atual}</p>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Filtro por Período
st.markdown("<h2 class='titulo-secao' style='color: #F37529;'>Filtro por Período</h2>", unsafe_allow_html=True)
data_inicial = st.date_input("Data Inicial", value=datetime(2024, 1, 1), key="start_date")
data_final = st.date_input("Data Final", value=datetime.now(), key="end_date")

if st.button("Aplicar Filtro"):
    filtered_data = filtrar_dados_por_periodo(data_cleaned, data_inicial, data_final)
else:
    filtered_data = data_cleaned

# Gráfico de Top 10 Veículos
st.markdown("<h2 class='titulo-secao' style='color: #F37529;'>Top 10 Veículos com Mais Multas e Valores Totais</h2>", unsafe_allow_html=True)
st.plotly_chart(create_vehicle_fines_chart(filtered_data), use_container_width=True)

# Mapa de Distribuição Geográfica
st.markdown("<h2 class='titulo-secao' style='color: #F37529;'>Distribuição Geográfica das Multas</h2>", unsafe_allow_html=True)
API_KEY = st.secrets["API_KEY"]
coordinates_cache = load_cache()

# Filtrar dados e aplicar geolocalização
map_data = filtered_data.dropna(subset=['Local da Infração']).copy()
if 'Latitude' not in map_data.columns or 'Longitude' not in map_data.columns:
    map_data[['Latitude', 'Longitude']] = map_data['Local da Infração'].apply(
        lambda x: pd.Series(get_cached_coordinates(x, API_KEY, coordinates_cache))
    )
    save_cache(coordinates_cache)

# Garantir a existência da coluna 'Descrição'
if 'Descrição' not in map_data.columns:
    map_data['Descrição'] = "Não especificado"

# Criar o mapa com marcadores
map_center = [map_data['Latitude'].mean(), map_data['Longitude'].mean()] if not map_data.empty else [0, 0]
map_object = folium.Map(location=map_center, zoom_start=5, tiles="CartoDB dark_matter")
icon_url = "https://cdn-icons-png.flaticon.com/512/1828/1828843.png"

for _, row in map_data.iterrows():
    if pd.notnull(row['Latitude']) and pd.notnull(row['Longitude']):
        data_infracao = row['Data da Infração'].strftime('%d/%m/%Y') if pd.notnull(row['Data da Infração']) else "Não disponível"
        popup_content = f"""
        <b>Local:</b> {row['Local da Infração']}<br>
        <b>Valor:</b> R$ {row['Valor a ser pago R$']:.2f}<br>
        <b>Data da Infração:</b> {data_infracao}
        """
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=folium.Popup(popup_content, max_width=300),
            icon=CustomIcon(icon_url, icon_size=(30, 30)),
        ).add_to(map_object)

# Exibição do mapa
map_click_data = st_folium(map_object, width=1800, height=600)

# Detalhes das multas para a localização selecionada
if map_click_data and map_click_data.get("last_object_clicked"):
    lat = map_click_data["last_object_clicked"].get("lat")
    lng = map_click_data["last_object_clicked"].get("lng")

    # Filtrando as multas que correspondem ao local clicado
    selected_fines = map_data[(map_data['Latitude'] == lat) & (map_data['Longitude'] == lng)]

    if not selected_fines.empty:
        st.markdown("<h2 class='titulo-secao' style='color: #F37529;'>Detalhes das Multas para a Localização Selecionada</h2>", unsafe_allow_html=True)
        st.dataframe(
            selected_fines[['Local da Infração', 'Valor a ser pago R$', 'Data da Infração', 'Descrição']].reset_index(drop=True),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Nenhuma multa encontrada para a localização selecionada.")

# Ranking das Localidades
st.markdown("<h2 class='titulo-secao' style='color: #F37529;'>Ranking das Localidades com Mais Multas</h2>", unsafe_allow_html=True)
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
st.markdown("<h2 class='titulo-secao' style='color: #F37529;'>Infrações Mais Frequentes</h2>", unsafe_allow_html=True)
st.plotly_chart(create_common_infractions_chart(filtered_data), use_container_width=True)

st.markdown("<h2 class='titulo-secao' style='color: #F37529;'>Valores das Multas Acumulados por Período</h2>", unsafe_allow_html=True)
period_option = st.radio("Selecione o período:", ["Mensal", "Semanal"], horizontal=True)
st.plotly_chart(create_fines_accumulated_chart(filtered_data, 'M' if period_option == "Mensal" else 'W'), use_container_width=True)

st.markdown("<h2 class='titulo-secao' style='color: #F37529;'>Infrações Mais Frequentes por Dia da Semana</h2>", unsafe_allow_html=True)
st.plotly_chart(create_weekday_infractions_chart(filtered_data), use_container_width=True)

# Footer
st.markdown("<div class='footer'>Dashboard de Multas © 2024 | Desenvolvido pela Equipe de Qualidade</div>", unsafe_allow_html=True)
