import folium
import pandas as pd
from geo_utils import load_cache, save_cache, get_cached_coordinates

def create_geo_map(filtered_data, api_key):
    """Create a geographical map for fines distribution."""
    # Load cache
    coordinates_cache = load_cache()

    # Prepare data for the map
    map_data = filtered_data.dropna(subset=['Local']).copy()
    map_data[['Latitude', 'Longitude']] = map_data['Local'].apply(
        lambda x: pd.Series(get_cached_coordinates(x, api_key, coordinates_cache))
    )

    # Save updated cache
    save_cache(coordinates_cache)

    # Create map
    map_center = [map_data['Latitude'].mean(), map_data['Longitude'].mean()] if not map_data.empty else [0, 0]
    map_object = folium.Map(location=map_center, zoom_start=5)

    for _, row in map_data.iterrows():
      if pd.notnull(row['Latitude']) and pd.notnull(row['Longitude']):
          folium.Marker(
              location=[row['Latitude'], row['Longitude']],
              popup=f"Local: {row['Local']}<br>Multa: {row['Valor a Pagar (R$)']:,.2f}",
              icon=folium.Icon(icon="exclamation-circle", prefix="fa", color="red")  # Ícone FontAwesome
          ).add_to(map_object)


    # Display map
    st_folium(map_object, width=700, height=500)


    return map_object
