import streamlit as st
import pandas as pd
import folium
from folium.features import CustomIcon
from streamlit_folium import st_folium
from data_loader import clean_data
from metrics import calculate_metrics
from graph_vehicles_fines import create_vehicle_fines_chart
from graph_common_infractions import create_common_infractions_chart
from graph_fines_accumulated import create_fines_accumulated_chart
from graph_weekday_infractions import create_weekday_infractions_chart
from geo_utils import load_cache, save_cache, get_cached_coordinates
from google_drive import carregar_dados_google_drive

# Configuração inicial
st.set_page_config(page_title="Torre de Controle iTracker - Dashboard de Multas", layout="wide")

# Estilização CSS e HTML
st.markdown(
    """
    <style>
        @keyframes fadeIn {
            0% { opacity: 0; transform: translateY(-20px); }
            100% { opacity: 1; transform: translateY(0); }
        }

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
            animation: fadeIn 1.2s ease-out;
        }

        .titulo-dashboard {
            font-size: 50px;
            font-weight: bold;
            color: #F37529;
            text-transform: uppercase;
            margin: 0;
        }

        .titulo-centralizado {
            text-align: center;
            font-size: 28px;
            font-weight: bold;
            color: #F37529;
            margin: 20px 0;
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

        .footer {
            text-align: center;
            font-size: 14px;
            color: #F37529;
            margin-top: 40px;
            padding: 10px 0;
            border-top: 1px solid #ddd;
        }
    </style>

    <div class="titulo-dashboard-container">
        <div>
            <h1 class="titulo-dashboard">Torre de Controle iTracker - Dashboard de Multas</h1>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# Logo
logo_url = st.secrets["image"]["logo_url"]
st.image(logo_url, width=150, use_container_width=False)

# Carregar e limpar dados
data = carregar_dados_google_drive()
data_cleaned = clean_data(data)

# Verificar colunas essenciais
required_columns = ['Data da Infração', 'Valor a ser pago R$', 'Auto de Infração', 'Status de Pagamento', 'Dia da Consulta']
if not all(col in data_cleaned.columns for col in required_columns):
    st.error(f"Faltam colunas essenciais: {', '.join([col for col in required_columns if col not in data_cleaned.columns])}")
    st.stop()

# Calcular métricas
total_multas, valor_total_a_pagar, multas_mes_atual = calculate_metrics(data_cleaned)
ultima_consulta = pd.to_datetime(data_cleaned['Dia da Consulta'].max(), errors='coerce').strftime('%d/%m/%Y')

# Indicadores Principais
st.markdown(
    """
    <div class="indicadores-container">
        <div class="indicador"><span>Total de Multas</span><p>{}</p></div>
        <div class="indicador"><span>Valor Total a Pagar</span><p>R$ {:,.2f}</p></div>
        <div class="indicador"><span>Multas no Mês Atual</span><p>{}</p></div>
        <div class="indicador"><span>Última Consulta</span><p>{}</p></div>
    </div>
    """.format(total_multas, valor_total_a_pagar, multas_mes_atual, ultima_consulta),
    unsafe_allow_html=True
)

# Filtro por Período
st.markdown(
    "<h2 class='titulo-centralizado' style='color: #F37529;'>Filtro por Período</h2>",
    unsafe_allow_html=True
)
data_cleaned['Dia da Consulta'] = pd.to_datetime(data_cleaned['Dia da Consulta'], errors='coerce')
start_date = st.date_input("Data Inicial", value=data_cleaned['Dia da Consulta'].min())
end_date = st.date_input("Data Final", value=data_cleaned['Dia da Consulta'].max())

filtered_data = data_cleaned[
    (data_cleaned['Dia da Consulta'] >= pd.Timestamp(start_date)) &
    (data_cleaned['Dia da Consulta'] <= pd.Timestamp(end_date))
]

# Função auxiliar para tratar valores monetários
def safe_float(value):
    try:
        return float(str(value).replace(",", ".").replace("R$", "").strip())
    except (ValueError, TypeError):
        return 0.00

# Gráficos
st.markdown(
    "<h2 class='titulo-centralizado' style='color: #F37529;'>Top 10 Veículos com Mais Multas e Valores Totais</h2>",
    unsafe_allow_html=True
)
st.plotly_chart(create_vehicle_fines_chart(filtered_data), use_container_width=True)

# Mapa e Tabela de Detalhes
st.markdown("<h2 style='color: #F37529;'>Distribuição Geográfica das Multas</h2>", unsafe_allow_html=True)
API_KEY = st.secrets["API_KEY"]
coordinates_cache = load_cache()

map_data = filtered_data.dropna(subset=['Local da Infração']).copy()
map_data[['Latitude', 'Longitude']] = map_data['Local da Infração'].apply(
    lambda x: pd.Series(get_cached_coordinates(x, API_KEY, coordinates_cache))
)
save_cache(coordinates_cache)

# Converter "Valor a ser pago R$" para float (corrige valores monetários)
if 'Valor a ser pago R$' in map_data.columns:
    map_data['Valor a ser pago R$'] = map_data['Valor a ser pago R$'].replace(
        {r'[^0-9,]': '', ',': '.'}, regex=True
    ).astype(float)
else:
    st.error("A coluna 'Valor a ser pago R$' não foi encontrada nos dados.")
    st.stop()

# Criação do mapa
map_center = [map_data['Latitude'].mean(), map_data['Longitude'].mean()] if not map_data.empty else [0, 0]
map_object = folium.Map(location=map_center, zoom_start=5, tiles="CartoDB dark_matter")

icon_url = "https://cdn-icons-png.flaticon.com/512/1828/1828843.png"
for _, row in map_data.iterrows():
    popup_content = f"<b>Local:</b> {row['Local da Infração']}<br><b>Valor:</b> R$ {row['Valor a ser pago R$']:.2f}"
    folium.Marker(
        location=[row['Latitude'], row['Longitude']],
        popup=folium.Popup(popup_content, max_width=300),
        icon=CustomIcon(icon_url, icon_size=(30, 30))
    ).add_to(map_object)

map_click_data = st_folium(map_object, width=1800, height=600)

# Tabela de Detalhes ao Clicar no Mapa
if map_click_data.get("last_object_clicked"):
    lat = map_click_data["last_object_clicked"].get("lat")
    lng = map_click_data["last_object_clicked"].get("lng")

    selected_fines = map_data[(map_data['Latitude'] == lat) & (map_data['Longitude'] == lng)]

    if not selected_fines.empty:
        st.markdown("<h3 style='color: #F37529;'>Detalhes das Multas na Localização</h3>", unsafe_allow_html=True)
        st.dataframe(
            selected_fines[['Local da Infração', 'Valor a ser pago R$', 'Data da Infração']],
            use_container_width=True
        )
    else:
        st.info("Nenhuma multa encontrada para a localização selecionada.")

# Ranking das Localidades
st.markdown("<h2 style='color: #F37529;'>Ranking das Localidades com Mais Multas</h2>", unsafe_allow_html=True)
ranking_localidades = filtered_data.groupby('Local da Infração', as_index=False).agg(
    Valor_Total=('Valor a ser pago R$', 'sum'),
    Total_Multas=('Local da Infração', 'count')
).sort_values(by='Valor_Total', ascending=False)

st.dataframe(
    ranking_localidades.rename(columns={"Valor_Total": "Valor Total (R$)", "Total_Multas": "Total de Multas"}),
    use_container_width=True,
    hide_index=True  # Esconde a coluna do índice
)

st.markdown(
    "<h2 class='titulo-centralizado' style='color: #F37529;'>Infrações Mais Frequentes</h2>",
    unsafe_allow_html=True
)
st.plotly_chart(create_common_infractions_chart(filtered_data), use_container_width=True)

st.markdown(
    "<h2 class='titulo-centralizado' style='color: #F37529;'>Valores das Multas Acumulados por Período</h2>",
    unsafe_allow_html=True
)
period_option = st.radio("Selecione o período:", ["Mensal", "Semanal"], horizontal=True)
st.plotly_chart(create_fines_accumulated_chart(filtered_data, 'M' if period_option == "Mensal" else 'W'), use_container_width=True)

st.markdown(
    "<h2 class='titulo-centralizado' style='color: #F37529;'>Infrações Mais Frequentes por Dia da Semana</h2>",
    unsafe_allow_html=True
)
st.plotly_chart(create_weekday_infractions_chart(filtered_data), use_container_width=True)

# Footer
st.markdown("<div class='footer'>Dashboard de Multas © 2024 | Desenvolvido pela Equipe de Qualidade</div>", unsafe_allow_html=True)
