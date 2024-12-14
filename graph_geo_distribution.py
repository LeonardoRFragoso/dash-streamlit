import folium
import pandas as pd
from geo_utils import load_cache, save_cache, get_cached_coordinates
from streamlit_folium import st_folium

def create_geo_map(filtered_data, api_key):
    """Create a geographical map for fines distribution."""
    # Load cache
    coordinates_cache = load_cache()

    # Prepare data for the map
    required_columns = ['Local da Infração', 'Valor a ser pago R$']
    for col in required_columns:
        if col not in filtered_data.columns:
            raise KeyError(f"A coluna '{col}' não está presente no DataFrame.")

    # Ensure no missing values in 'Local da Infração'
    map_data = filtered_data.dropna(subset=['Local da Infração']).copy()
    map_data[['Latitude', 'Longitude']] = map_data['Local da Infração'].apply(
        lambda x: pd.Series(get_cached_coordinates(x, api_key, coordinates_cache))
    )

    # Save updated cache
    save_cache(coordinates_cache)

    # Create map
    if not map_data.empty:
        map_center = [map_data['Latitude'].mean(), map_data['Longitude'].mean()]
    else:
        map_center = [0, 0]  # Default center if no data available

    map_object = folium.Map(location=map_center, zoom_start=5)

    for _, row in map_data.iterrows():
        if pd.notnull(row['Latitude']) and pd.notnull(row['Longitude']):
            folium.Marker(
                location=[row['Latitude'], row['Longitude']],
                popup=(
                    f"<b>Local:</b> {row['Local da Infração']}<br>"
                    f"<b>Multa:</b> R$ {row['Valor a ser pago R$']:,.2f}"
                ),
                icon=folium.Icon(icon="exclamation-circle", prefix="fa", color="red")  # FontAwesome icon
            ).add_to(map_object)

    # Display map in Streamlit
    st_folium(map_object, width=700, height=500)

    return map_object
