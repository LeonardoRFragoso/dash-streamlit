import streamlit as st
import pandas as pd
import folium
from folium.features import CustomIcon
from streamlit_folium import st_folium
from data_loader import clean_data  # Apenas a função de limpeza de dados é necessária aqui
from metrics import calculate_metrics
from graph_vehicles_fines import create_vehicle_fines_chart  # Importando a função de gráfico de veículos
from graph_common_infractions import create_common_infractions_chart  # Importando a função de gráfico de infrações comuns
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

# Calcular a data da última consulta
ultima_data_consulta = pd.to_datetime(data_cleaned['Dia da Consulta'].max(), errors='coerce')

# Exibir os indicadores principais
st.markdown("<h2 style='text-align: center; color: #F37529; font-size: 36px; font-weight: bold;'>Indicadores Principais</h2>", unsafe_allow_html=True)

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

# Seleção das datas para o filtro
filter_col1, filter_col2 = st.columns(2)

# Garantir que a coluna de data está no formato datetime
data_cleaned['Dia da Consulta'] = pd.to_datetime(data_cleaned['Dia da Consulta'], errors='coerce')

# Definição de valores padrão para as datas
start_date_default = data_cleaned['Dia da Consulta'].min().date()
end_date_default = data_cleaned['Dia da Consulta'].max().date()

# Entrada para as datas
start_date = st.date_input("Data Inicial", value=start_date_default, min_value=start_date_default, max_value=end_date_default)
end_date = st.date_input("Data Final", value=end_date_default, min_value=start_date_default, max_value=end_date_default)

# Aplicar filtro conforme o período
filtered_data = data_cleaned[(data_cleaned['Dia da Consulta'] >= pd.Timestamp(start_date)) & (data_cleaned['Dia da Consulta'] <= pd.Timestamp(end_date))]

# Exibir gráfico dos veículos com mais multas
st.divider()
st.markdown("<h2 style='text-align: center; color: #FF7F00; font-weight: bold;'>Top 10 Veículos com Mais Multas e Valores Totais</h2>", unsafe_allow_html=True)
top_vehicles_chart = create_vehicle_fines_chart(filtered_data)
st.plotly_chart(top_vehicles_chart, use_container_width=True)

# Exibir mapa de distribuição geográfica das multas
st.divider()
st.markdown("<h2 style='text-align: center; color: #FF7F00; font-weight: bold;'>Distribuição Geográfica das Multas</h2>", unsafe_allow_html=True)
API_KEY = st.secrets["API_KEY"]
coordinates_cache = load_cache()

# Filtra dados para o mapa usando filtered_data
map_data = filtered_data.dropna(subset=['Local da Infração']).copy()
map_data[['Latitude', 'Longitude']] = map_data['Local da Infração'].apply(
    lambda x: pd.Series(get_cached_coordinates(x, API_KEY, coordinates_cache))
)

# Salvar cache atualizado
save_cache(coordinates_cache)

# Criar e exibir o mapa
map_center = [map_data['Latitude'].mean(), map_data['Longitude'].mean()] if not map_data.empty else [0, 0]
map_object = folium.Map(location=map_center, zoom_start=5, tiles="CartoDB dark_matter")

icon_url = "https://cdn-icons-png.flaticon.com/512/1828/1828843.png"  # URL de um triângulo de alerta

# Adicionar marcadores ao mapa
for _, row in map_data.iterrows():
    if pd.notnull(row['Latitude']) and pd.notnull(row['Longitude']):
        custom_icon = CustomIcon(icon_url, icon_size=(30, 30))
        # Garantir que a coluna 'Data da Infração' seja datetime
        map_data['Data da Infração'] = pd.to_datetime(map_data['Data da Infração'], errors='coerce')

        # Dentro do loop
        data_infracao = row['Data da Infração'].strftime('%d/%m/%Y') if pd.notnull(row['Data da Infração']) else "Data não disponível"

        
        # Garantir que 'Valor a ser pago R$' esteja como numérico antes de formatar
        row['Valor a ser pago R$'] = pd.to_numeric(row['Valor a ser pago R$'], errors='coerce')
        
        # Construir o conteúdo do popup com a formatação correta
        popup_content = f"<b>Local:</b> {row['Local da Infração']}<br><b>Valor:</b> R$ {row['Valor a ser pago R$']:.2f}<br><b>Data da Infração:</b> {data_infracao}"
        
        folium.Marker(
            location=[row['Latitude'], row['Longitude']],
            popup=folium.Popup(popup_content, max_width=300),
            icon=custom_icon
        ).add_to(map_object)


# Display map
st_folium(map_object, width=1800, height=600)

# Exibir gráfico de infrações mais comuns
st.divider()
st.markdown("<h2 style='text-align: center; color: #FF7F00; font-weight: bold;'>Infrações Mais Frequentes</h2>", unsafe_allow_html=True)
common_infractions_chart = create_common_infractions_chart(filtered_data)
st.plotly_chart(common_infractions_chart, use_container_width=True)

# Exibir gráfico de multas acumuladas por período
st.divider()
st.markdown("<h2 style='text-align: center; color: #FF7F00; font-weight: bold;'>Valores das Multas Acumulados por Período</h2>", unsafe_allow_html=True)
period_option = st.radio("Selecione o período para acumulação:", options=["Mensal", "Semanal"], index=0, horizontal=True)
period_code = 'M' if period_option == "Mensal" else 'W'
fines_accumulated_chart = create_fines_accumulated_chart(filtered_data, period=period_code)
st.plotly_chart(fines_accumulated_chart, use_container_width=True)

# Exibir gráfico de infrações por dia da semana
st.divider()
st.markdown("<h2 style='text-align: center; color: #FF7F00; font-weight: bold;'>Infrações Mais Frequentes por Dia da Semana</h2>", unsafe_allow_html=True)
weekday_infractions_chart = create_weekday_infractions_chart(filtered_data)
st.plotly_chart(weekday_infractions_chart, use_container_width=True)

# Footer
st.markdown(""" 
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
""", unsafe_allow_html=True)
