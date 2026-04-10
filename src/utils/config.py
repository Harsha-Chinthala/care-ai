import yaml
import os

def load_config():
    config_path = 'config.yaml'
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as file:
                return yaml.safe_load(file)
        except Exception as e:
            print(f"Error loading config: {e}")
            return get_default_config()
    else:
        print("Config file not found, using defaults")
        return get_default_config()

def get_default_config():
    """Return default configuration"""
    return {
        'data': {
            'raw_path': 'data/raw/',
            'processed_path': 'data/processed/',
            'models_path': 'data/models/'
        },
        'model_params': {
            'test_size': 0.2,
            'random_state': 42
        }
    }

def get_data_paths():
    config = load_config()
    return config['data']

def get_model_params():
    config = load_config()
    return config['model_params']