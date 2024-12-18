import os
import json
import requests

CACHE_FILE = "coordinates_cache.json"

# Carregar o cache uma única vez no início
cache = None
if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, 'r') as f:
            cache = json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"Erro ao carregar o cache: {e}")
        cache = {}
else:
    cache = {}

def save_cache():
    """
    Salva o cache global no arquivo JSON.
    """
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f, indent=4)
    except IOError as e:
        print(f"Erro ao salvar o cache: {e}")

def get_coordinates(local, api_key):
    """
    Busca coordenadas para um local específico usando a API OpenCage.

    Parâmetros:
        local (str): O local a ser geocodificado.
        api_key (str): Chave de API para o OpenCage.

    Retorna:
        tuple: Uma tupla com (latitude, longitude), ou (None, None) se não encontrado.
    """
    if not api_key:
        raise ValueError("API key não fornecida para a solicitação de geocodificação.")

    url = f'https://api.opencagedata.com/geocode/v1/json?q={local}&key={api_key}'
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if 'results' in data and data['results']:
            geometry = data['results'][0]['geometry']
            return geometry.get('lat'), geometry.get('lng')
    except requests.RequestException as e:
        print(f"Erro ao obter coordenadas para '{local}': {e}")
    return None, None

def get_cached_coordinates(local, api_key):
    """
    Obtém coordenadas do cache ou da API, se necessário.

    Parâmetros:
        local (str): O local a ser geocodificado.
        api_key (str): Chave de API para o OpenCage.

    Retorna:
        tuple: Uma tupla com (latitude, longitude), ou (None, None) se não encontrado.
    """
    global cache  # Usa o cache carregado no início

    if local in cache:
        return cache[local]

    # Obtém as coordenadas pela API
    lat, lng = get_coordinates(local, api_key)
    if lat is not None and lng is not None:
        cache[local] = (lat, lng)
        save_cache()  # Salva o cache imediatamente após atualizar
    return lat, lng
