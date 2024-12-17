import json
import os

# Caminho para o arquivo de cache
CACHE_FILE = "coordinates_cache.json"

def load_cache():
    """Carregar o cache de coordenadas se disponível."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_cache(cache):
    """Salvar as coordenadas no cache."""
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f)
    except Exception as e:
        print(f"Erro ao salvar o cache: {e}")

def clear_cache():
    """Limpar o cache."""
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)
