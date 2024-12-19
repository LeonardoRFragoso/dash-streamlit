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

def setup_page_config():
    """Configuração inicial da página Streamlit"""
    st.set_page_config(
        page_title="Torre de Controle iTracker - Dashboard de Multas",
        layout="wide",
        initial_sidebar_state="expanded"
    )

def load_styles():
    """Carrega os estilos CSS"""
    with open('styles/main.css', 'r') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

def display_header():
    """Exibe o cabeçalho do dashboard com logo e título"""
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

def display_metrics(data_cleaned):
    """Exibe os indicadores principais do dashboard"""
    try:
        total_multas, valor_total_a_pagar, ultima_consulta = calcular_metricas(data_cleaned)
        
        # Calcular multas do mês atual
        current_month = datetime.now().month
        current_year = datetime.now().year
        multas_mes_atual = data_cleaned[
            (data_cleaned['Data da Infração'].dt.month == current_month) &
            (data_cleaned['Data da Infração'].dt.year == current_year)
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

def create_map(data_cleaned):
    """Cria e exibe o mapa de distribuição geográfica das multas"""
    try:
        st.markdown("<h2 class='titulo-secao'>Distribuição Geográfica das Multas</h2>", unsafe_allow_html=True)
        
        # Carregar configurações e cache
        API_KEY = st.secrets["API_KEY"]["key"]
        coordinates_cache = load_cache()
        
        # Preparar dados para o mapa
        map_data = data_cleaned.dropna(subset=['Local da Infração']).copy()
        
        # Obter coordenadas
        if 'Latitude' not in map_data.columns or 'Longitude' not in map_data.columns:
            map_data[['Latitude', 'Longitude']] = map_data['Local da Infração'].apply(
                lambda x: pd.Series(get_cached_coordinates(x, API_KEY, coordinates_cache))
                if pd.notnull(x) else pd.Series([None, None])
            )
            save_cache(coordinates_cache)
        
        # Limpar dados inválidos
        map_data = map_data.dropna(subset=['Latitude', 'Longitude'])
        
        # Criar mapa
        map_center = [map_data['Latitude'].mean(), map_data['Longitude'].mean()] if not map_data.empty else [-23.5505, -46.6333]
        map_object = folium.Map(location=map_center, zoom_start=5, tiles="CartoDB dark_matter")
        
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
                    icon=folium.Icon(color='red', icon='info-sign')
                ).add_to(map_object)
        
        # Exibir mapa
        map_data = st_folium(map_object, width="100%", height=600)
        return map_data

    except Exception as e:
        st.error(f"Erro ao criar mapa: {str(e)}")
        return None

def display_charts(data_cleaned):
    """Exibe todos os gráficos do dashboard"""
    try:
        # Top 10 Veículos
        st.markdown("<h2 class='titulo-secao'>Top 10 Veículos com Mais Multas</h2>", unsafe_allow_html=True)
        st.plotly_chart(create_vehicle_fines_chart(data_cleaned), use_container_width=True)
        
        # Infrações Mais Frequentes
        st.markdown("<h2 class='titulo-secao'>Infrações Mais Frequentes</h2>", unsafe_allow_html=True)
        st.plotly_chart(create_common_infractions_chart(data_cleaned), use_container_width=True)
        
        # Multas Acumuladas
        st.markdown("<h2 class='titulo-secao'>Multas Acumuladas por Período</h2>", unsafe_allow_html=True)
        period_option = st.radio("Selecione o período:", ["Mensal", "Semanal"], horizontal=True)
        st.plotly_chart(
            create_fines_accumulated_chart(data_cleaned, 'M' if period_option == "Mensal" else 'W'),
            use_container_width=True
        )
        
        # Infrações por Dia da Semana
        st.markdown("<h2 class='titulo-secao'>Infrações por Dia da Semana</h2>", unsafe_allow_html=True)
        st.plotly_chart(create_weekday_infractions_chart(data_cleaned), use_container_width=True)
        
    except Exception as e:
        st.error(f"Erro ao criar gráficos: {str(e)}")

def main():
    """Função principal do dashboard"""
    try:
        setup_page_config()
        load_styles()
        display_header()
        
        # Carregar dados
        data_cleaned = carregar_e_limpar_dados()
        if data_cleaned is None:
            st.error("Não foi possível carregar os dados. Verifique a conexão com o Google Drive.")
            st.stop()
            
        # Exibir componentes principais
        display_metrics(data_cleaned)
        map_data = create_map(data_cleaned)
        display_charts(data_cleaned)
        
        # Footer
        st.markdown(
            "<div class='footer'>Dashboard de Multas © 2024 | Desenvolvido pela Equipe de Qualidade</div>",
            unsafe_allow_html=True
        )
        
    except Exception as e:
        st.error(f"Erro na execução do dashboard: {str(e)}")

if __name__ == "__main__":
    main()