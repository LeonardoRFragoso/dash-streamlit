import os
import json
import requests
import streamlit as st

# Caminho do arquivo de cache de coordenadas
CACHE_FILE = "coordinates_cache.json"


def load_cache():
    """
    Carrega o cache do arquivo JSON.

    Returns:
        dict: O cache carregado, ou um dicionário vazio caso não exista.
    """
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as file:
                return json.load(file)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Erro ao carregar o cache: {e}")
    return {}


def save_cache(cache):
    """
    Salva o cache no arquivo JSON.

    Parameters:
        cache (dict): Dados a serem armazenados no cache.
    """
    try:
        with open(CACHE_FILE, 'w') as file:
            json.dump(cache, file, indent=4)
    except IOError as e:
        print(f"Erro ao salvar o cache: {e}")


def get_coordinates(local, api_key):
    """
    Busca as coordenadas para um local usando a API OpenCage.

    Parameters:
        local (str): O local para buscar as coordenadas.
        api_key (str): A chave de API do OpenCage.

    Returns:
        tuple: Uma tupla (latitude, longitude) ou (None, None) caso falhe.
    """
    url = f"https://api.opencagedata.com/geocode/v1/json?q={local}&key={api_key}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        if 'results' in data and data['results']:
            geometry = data['results'][0]['geometry']
            return geometry['lat'], geometry['lng']
        else:
            print(f"Nenhum resultado encontrado para o local: {local}")
    except requests.RequestException as e:
        print(f"Erro ao buscar coordenadas: {e}")
    return None, None


def get_cached_coordinates(local, api_key, cache):
    """
    Obtém coordenadas do cache ou faz a busca na API e atualiza o cache.

    Parameters:
        local (str): O local a ser buscado.
        api_key (str): A chave de API.
        cache (dict): O dicionário de cache de coordenadas.

    Returns:
        tuple: Uma tupla (latitude, longitude).
    """
    # Busca no cache
    if local in cache:
        return cache[local]

    # Caso não esteja no cache, buscar na API
    lat, lng = get_coordinates(local, api_key)
    if lat is not None and lng is not None:
        cache[local] = (lat, lng)
        save_cache(cache)  # Atualiza o cache
    return lat, lng


def get_api_key():
    """
    Obtém a chave de API do OpenCage do Streamlit secrets.

    Returns:
        str: A chave de API.
    """
    try:
        return st.secrets["API_KEY"]
    except KeyError:
        raise RuntimeError("API_KEY não configurada nos secrets do Streamlit.")
