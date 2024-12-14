import os
import json
import requests

CACHE_FILE = "coordinates_cache.json"

def load_cache():
    """
    Load the cache from a JSON file.
    
    Returns:
        dict: The cached coordinates if the file exists, otherwise an empty dictionary.
    """
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Erro ao carregar o cache: {e}")
    return {}

def save_cache(cache):
    """
    Save the cache to a JSON file.
    
    Parameters:
        cache (dict): The cache data to save.
    """
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f, indent=4)
    except IOError as e:
        print(f"Erro ao salvar o cache: {e}")

def get_coordinates(local, api_key):
    """
    Fetch coordinates for a given location using the OpenCage API.
    
    Parameters:
        local (str): The location to geocode.
        api_key (str): The API key for OpenCage.

    Returns:
        tuple: A tuple with (latitude, longitude), or (None, None) if not found.
    """
    if not api_key:
        raise ValueError("API key não fornecida para a solicitação de geocodificação.")

    url = f'https://api.opencagedata.com/geocode/v1/json?q={local}&key={api_key}'
    try:
        response = requests.get(url, timeout=10)  # Adicionado timeout para evitar travamentos
        response.raise_for_status()  # Levanta erro para códigos de status HTTP >= 400
        data = response.json()
        if 'results' in data and data['results']:
            geometry = data['results'][0]['geometry']
            return geometry.get('lat'), geometry.get('lng')
    except requests.RequestException as e:
        print(f"Erro ao obter coordenadas para '{local}': {e}")
    return None, None

def get_cached_coordinates(local, api_key, cache):
    """
    Get coordinates from cache or API.
    
    Parameters:
        local (str): The location to geocode.
        api_key (str): The API key for OpenCage.
        cache (dict): The cache data for coordinates.

    Returns:
        tuple: A tuple with (latitude, longitude), or (None, None) if not found.
    """
    try:
        if local in cache:
            return cache[local]
        lat, lng = get_coordinates(local, api_key)
        if lat is not None and lng is not None:
            cache[local] = (lat, lng)
            save_cache(cache)  # Atualiza o cache imediatamente para persistir novos dados
        return lat, lng
    except Exception as e:
        print(f"Erro ao obter ou armazenar coordenadas para '{local}': {e}")
        return None, None
