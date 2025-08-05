import yaml
import threading

_CONFIG_PATH = 'config.yaml'
_config_cache = None
_config_lock = threading.Lock()

def get_config():
    global _config_cache
    with _config_lock:
        try:
            with open(_CONFIG_PATH, 'r') as f:
                _config_cache = yaml.safe_load(f)
        except Exception as e:
            raise RuntimeError(f'Failed to load config: {e}')
        return _config_cache

# Optionally, add a reload_config() if you want to force reload

def reload_config():
    global _config_cache
    with _config_lock:
        _config_cache = None
    return get_config() 