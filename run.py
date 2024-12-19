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
from graph_vehicles_fines import create_vehicle_fines_chart
from graph_common_infractions import create_common_infractions_chart
from graph_fines_accumulated import create_fines_accumulated_chart
from graph_weekday_infractions import create_weekday_infractions_chart
from geo_utils import load_cache, save_cache, get_cached_coordinates

def setup_page():
    """Configura a página inicial do Streamlit"""
    st.set_page_config(
        page_title="Torre de Controle iTracker - Dashboard de Multas",
        layout="wide"
    )
    # Carregar CSS (mantido inline para garantir funcionamento)
    with open('styles.css', 'r') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def display_header():
    """Exibe o cabeçalho com logo e título"""
    try:
        logo_url = st.secrets["image"]["logo_url"]
        st.markdown(
            f"""
            <div class="logo-container">
                <img src="{logo_url}" width="200" alt="Logo">
            </div>
            <div class="titulo-dashboard-container">
                <h1 class="titulo-dashboard">Torre de Controle iTracker - Dashboard de Multas</h1>
            </div>
            """,
            unsafe_allow_html=True
        )
    except Exception as e:
        st.error(f"Erro ao carregar cabeçalho: {str(e)}")

def display_metrics(data):
    """Exibe os indicadores principais"""
    try:
        total_multas, valor_total_a_pagar, ultima_consulta = calcular_metricas(data)
        
        # Calcular multas do mês atual
        current_month = datetime.now().month
        current_year = datetime.now().year
        multas_mes_atual = data[
            (data['Data da Infração'].dt.month == current_month) &
            (data['Data da Infração'].dt.year == current_year)
        ]
        valor_total_mes_atual = multas_mes_atual['Valor a ser pago R$'].sum()

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
            unsafe_allow_html=True
        )
    except Exception as e:
        st.error(f"Erro ao exibir métricas: {str(e)}")

def create_map(data):
    """Cria e exibe o mapa de multas"""
    try:
        st.markdown(
            "<h2 class='titulo-secao' style='color: #0066B4;'>Distribuição Geográfica das Multas</h2>",
            unsafe_allow_html=True
        )
        
        API_KEY = st.secrets["API_KEY"]["key"]
        coordinates_cache = load_cache()
        
        map_data = data.dropna(subset=['Local da Infração']).copy()
        
        if 'Latitude' not in map_data.columns or 'Longitude' not in map_data.columns:
            map_data[['Latitude', 'Longitude']] = map_data['Local da Infração'].apply(
                lambda x: pd.Series(get_cached_coordinates(x, API_KEY, coordinates_cache))
                if pd.notnull(x) else pd.Series([None, None])
            )
            save_cache(coordinates_cache)

        map_data = map_data.dropna(subset=['Latitude', 'Longitude'])
        
        if map_data.empty:
            st.warning("Não há dados geográficos disponíveis para exibir no mapa")
            return None

        map_center = [map_data['Latitude'].mean(), map_data['Longitude'].mean()]
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

        return st_folium(map_object, width="100%", height=600)
    
    except Exception as e:
        st.error(f"Erro ao criar mapa: {str(e)}")
        return None

def display_location_details(map_data, map_click_data):
    """Exibe detalhes das multas para localização selecionada"""
    if map_click_data and map_click_data.get("last_object_clicked"):
        try:
            lat = map_click_data["last_object_clicked"].get("lat")
            lng = map_click_data["last_object_clicked"].get("lng")
            
            selected_fines = map_data[
                (map_data['Latitude'] == lat) & 
                (map_data['Longitude'] == lng)
            ]

            if not selected_fines.empty:
                st.markdown(
                    "<h2 class='titulo-secao' style='color: #0066B4;'>Detalhes das Multas para a Localização Selecionada</h2>",
                    unsafe_allow_html=True
                )
                st.dataframe(
                    selected_fines[['Local da Infração', 'Valor a ser pago R$', 'Data da Infração', 'Descrição']],
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("Nenhuma multa encontrada para a localização selecionada.")
        except Exception as e:
            st.error(f"Erro ao exibir detalhes da localização: {str(e)}")

def display_charts(data):
    """Exibe todos os gráficos do dashboard"""
    try:
        # Ranking das Localidades
        st.markdown(
            "<h2 class='titulo-secao' style='color: #0066B4;'>Ranking das Localidades com Mais Multas</h2>",
            unsafe_allow_html=True
        )
        ranking_localidades = data.groupby('Local da Infração', as_index=False).agg(
            Valor_Total=('Valor a ser pago R$', 'sum'),
            Total_Multas=('Local da Infração', 'count')
        ).sort_values(by='Valor_Total', ascending=False)

        st.dataframe(
            ranking_localidades.reset_index(drop=True),
            use_container_width=True,
            hide_index=True
        )

        # Demais gráficos
        charts = [
            ("Top 10 Veículos com Mais Multas e Valores Totais", create_vehicle_fines_chart),
            ("Infrações Mais Frequentes", create_common_infractions_chart),
            ("Valores das Multas Acumulados por Período", create_fines_accumulated_chart),
            ("Infrações Mais Frequentes por Dia da Semana", create_weekday_infractions_chart)
        ]

        for title, chart_func in charts:
            st.markdown(
                f"<h2 class='titulo-secao' style='color: #0066B4;'>{title}</h2>",
                unsafe_allow_html=True
            )
            
            if chart_func == create_fines_accumulated_chart:
                period_option = st.radio(
                    "Selecione o período:",
                    ["Mensal", "Semanal"],
                    horizontal=True
                )
                st.plotly_chart(
                    chart_func(data, 'M' if period_option == "Mensal" else 'W'),
                    use_container_width=True
                )
            else:
                st.plotly_chart(chart_func(data), use_container_width=True)

    except Exception as e:
        st.error(f"Erro ao exibir gráficos: {str(e)}")

def main():
    """Função principal do dashboard"""
    try:
        setup_page()
        display_header()
        
        data_cleaned = carregar_e_limpar_dados()
        if data_cleaned is None:
            st.error("Não foi possível carregar os dados. Verifique a conexão com o Google Drive.")
            st.stop()
            
        display_metrics(data_cleaned)
        
        map_click_data = create_map(data_cleaned)
        if map_click_data:
            display_location_details(data_cleaned, map_click_data)
            
        display_charts(data_cleaned)
        
        st.markdown(
            "<div class='footer'>Dashboard de Multas © 2024 | Desenvolvido pela Equipe de Qualidade</div>",
            unsafe_allow_html=True
        )
        
    except Exception as e:
        st.error(f"Erro na execução do dashboard: {str(e)}")

if __name__ == "__main__":
    main()