import streamlit as st
import pandas as pd
import folium
from datetime import datetime
from folium.features import CustomIcon
from streamlit_folium import st_folium
from data_processing import (
    carregar_e_limpar_dados,
    calcular_metricas,
    filtrar_dados_por_periodo
)
from google_drive import carregar_dados_google_drive
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
        .titulo-secao {
            text-align: center;
            font-size: 36px;
            font-weight: bold;
            color: #0066B4;
            margin-top: 30px;
            margin-bottom: 20px;
        }
        .footer {
            text-align: center;
            font-size: 14px;
            color: #0066B4;
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
            justify-content: center;
            align-items: center;
            text-align: center;
            background-color: #FFFFFF;
            border: 4px solid #0066B4;
            border-radius: 15px;
            box-shadow: 0 8px 12px rgba(0, 0, 0, 0.3);
            width: 260px;
            height: 160px;
            padding: 10px;
        }
        .indicador span {
            font-size: 18px;
            color: #0066B4;
        }
        .indicador p {
            font-size: 38px;
            color: #0066B4;
            margin: 0;
            font-weight: bold;
        }
        .stDateInput input {
            box-shadow: none;
            border: 1px solid #ddd;
            padding: 5px 10px;
            width: 130px;
            font-size: 16px;
        }
        .stDateInput input:focus {
            border-color: #0066B4;
            outline: none;
        }
        .stDateInput {
            width: auto;
            margin: 0 10px;
        }
        .stButton {
            display: flex;
            justify-content: center;
            align-items: center;
            width: 100%;
            margin-top: 20px;
        }
        .logo-container {
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 20px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

try:
    # Exibir o logo da empresa
    logo_url = st.secrets["image"]["logo_url"]
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
    data_cleaned = carregar_e_limpar_dados(carregar_dados_google_drive)
    if data_cleaned is None:
        st.error("Não foi possível carregar os dados. Verifique a conexão com o Google Drive.")
        st.stop()

    # Filtro de dados por período
    st.markdown("<h2 class='titulo-secao'>Filtrar Dados por Período</h2>", unsafe_allow_html=True)
    data_inicial = st.date_input("Data Inicial", value=datetime(2024, 1, 1))
    data_final = st.date_input("Data Final", value=datetime.now())
    data_cleaned = filtrar_dados_por_periodo(data_cleaned, data_inicial, data_final)

    if data_cleaned.empty:
        st.error("Nenhum dado encontrado no período selecionado.")
        st.stop()

    # Calcular métricas principais
    total_multas, valor_total_a_pagar, ultima_consulta = calcular_metricas(data_cleaned)

    # Calcular multas do mês atual
    current_month = datetime.now().month
    current_year = datetime.now().year
    multas_mes_atual = data_cleaned[
        (data_cleaned['Data da Infração'].dt.month == current_month) &
        (data_cleaned['Data da Infração'].dt.year == current_year)
    ]
    valor_total_mes_atual = multas_mes_atual['Valor a ser pago R$'].sum()

    # Exibir métricas
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
                <p>R$ {valor_total_mes_atual:,.2f}</p>
            </div>
            <div class="indicador">
                <span>Última Consulta</span>
                <p>{ultima_consulta}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Mapa de Distribuição Geográfica
    st.markdown("<h2 class='titulo-secao' style='color: #0066B4;'>Distribuição Geográfica das Multas</h2>", unsafe_allow_html=True)
    
    # Carregar cache de coordenadas
    try:
        API_KEY = st.secrets["API_KEY"]["key"]
        coordinates_cache = load_cache()
    except KeyError:
        st.error("Chave de API não configurada corretamente no arquivo secrets.toml.")
        st.stop()

    # Preparar dados para o mapa
    map_data = data_cleaned.dropna(subset=['Local da Infração']).copy()
    
    # Obter coordenadas
    if 'Latitude' not in map_data.columns or 'Longitude' not in map_data.columns:
        try:
            map_data[['Latitude', 'Longitude']] = map_data['Local da Infração'].apply(
                lambda x: pd.Series(get_cached_coordinates(x, API_KEY, coordinates_cache))
                if pd.notnull(x) else pd.Series([None, None])
            )
            save_cache(coordinates_cache)
        except Exception as e:
            st.error(f"Erro ao obter as coordenadas geográficas: {str(e)}")
            st.stop()

    map_data = map_data.dropna(subset=['Latitude', 'Longitude'])

    # Criar mapa
    map_center = [map_data['Latitude'].mean(), map_data['Longitude'].mean()] if not map_data.empty else [-23.5505, -46.6333]
    map_object = folium.Map(location=map_center, zoom_start=5, tiles="CartoDB dark_matter")

    # Ícone personalizado
    icon_url = "https://cdn-icons-png.flaticon.com/512/1828/1828843.png"

    # Adicionar marcadores
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

    # Exibir mapa
    map_click_data = st_folium(map_object, width="100%", height=600)

    # Detalhes das multas para localização selecionada
    if map_click_data and map_click_data.get("last_object_clicked"):
        lat = map_click_data["last_object_clicked"].get("lat")
        lng = map_click_data["last_object_clicked"].get("lng")
        
        selected_fines = map_data[
            (map_data['Latitude'] == lat) & 
            (map_data['Longitude'] == lng)
        ]

        if not selected_fines.empty:
            st.markdown("<h2 class='titulo-secao' style='color: #0066B4;'>Detalhes das Multas para a Localização Selecionada</h2>", unsafe_allow_html=True)
            st.dataframe(
                selected_fines[['Local da Infração', 'Valor a ser pago R$', 'Data da Infração', 'Descrição']].reset_index(drop=True),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Nenhuma multa encontrada para a localização selecionada.")

    # Ranking das Localidades
    st.markdown("<h2 class='titulo-secao' style='color: #0066B4;'>Ranking das Localidades com Mais Multas</h2>", unsafe_allow_html=True)
    ranking_localidades = data_cleaned.groupby('Local da Infração', as_index=False).agg(
        Valor_Total=('Valor a ser pago R$', 'sum'),
        Total_Multas=('Local da Infração', 'count')
    ).sort_values(by='Valor_Total', ascending=False)

    st.dataframe(
        ranking_localidades.reset_index(drop=True),
        use_container_width=True,
        hide_index=True
    )

    # Gráficos
    st.markdown("<h2 class='titulo-secao' style='color: #0066B4;'>Top 10 Veículos com Mais Multas e Valores Totais</h2>", unsafe_allow_html=True)
    st.plotly_chart(create_vehicle_fines_chart(data_cleaned), use_container_width=True)

    st.markdown("<h2 class='titulo-secao' style='color: #0066B4;'>Infrações Mais Frequentes</h2>", unsafe_allow_html=True)
    st.plotly_chart(create_common_infractions_chart(data_cleaned), use_container_width=True)

    st.markdown("<h2 class='titulo-secao' style='color: #0066B4;'>Valores das Multas Acumulados por Período</h2>", unsafe_allow_html=True)
    period_option = st.radio("Selecione o período:", ["Mensal", "Semanal"], horizontal=True)
    st.plotly_chart(
        create_fines_accumulated_chart(data_cleaned, 'M' if period_option == "Mensal" else 'W'),
        use_container_width=True
    )

    st.markdown("<h2 class='titulo-secao' style='color: #0066B4;'>Infrações Mais Frequentes por Dia da Semana</h2>", unsafe_allow_html=True)
    st.plotly_chart(create_weekday_infractions_chart(data_cleaned), use_container_width=True)

    # Footer
    st.markdown(
        "<div class='footer'>Dashboard de Multas © 2024 | Desenvolvido pela Equipe de Qualidade</div>",
        unsafe_allow_html=True
    )

except Exception as e:
    st.error(f"Erro na execução do dashboard: {str(e)}")
