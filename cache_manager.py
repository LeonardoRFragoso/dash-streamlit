import json
import os
import streamlit as st

# Caminho para o arquivo de cache
CACHE_FILE = os.path.join(os.getcwd(), "coordinates_cache.json")

def load_cache():
    """Carregar o cache de coordenadas se disponível ou do secrets.toml"""
    cache = {}
    
    # Verificar se há coordenadas no secrets.toml
    if "coordinates" in st.secrets["image"]:
        coordinates = st.secrets["image"]["coordinates"]
        # Caso as coordenadas estejam no secrets, as retornamos
        cache["coordinates"] = coordinates
        return cache
    
    # Caso contrário, buscamos o cache do arquivo
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                cache = json.load(f)
        except json.JSONDecodeError:
            print("Erro ao carregar o cache. O arquivo está corrompido ou não pode ser lido.")
            return {}
    return cache

def save_cache(cache):
    """Salvar as coordenadas no cache"""
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f)
    except Exception as e:
        print(f"Erro ao salvar o cache: {e}")

def clear_cache():
    """Limpar o cache"""
    if os.path.exists(CACHE_FILE):
        try:
            os.remove(CACHE_FILE)
            print("Cache limpo com sucesso.")
        except Exception as e:
            print(f"Erro ao limpar o cache: {e}")
