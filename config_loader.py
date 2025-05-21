import json
import os

class ConfigLoader:
    def __init__(self, config_path='config/config.json'):
        self.config_path = config_path
        self.config = {}
        self.load_config()

    def load_config(self):
        if not os.path.exists(self.config_path):
            print(f"Config file '{self.config_path}' not found.")
            return

        try:
            with open(self.config_path, 'r') as file:
                self.config = json.load(file)
        except json.JSONDecodeError:
            print(f"Invalid JSON format in {self.config_path}.")
        except Exception as e:
            print(f"Error loading config: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def get_int(self, key, default=0):
        value = self.get(key, default)
        try:
            return int(value)
        except (ValueError, TypeError):
            print(f"Invalid integer for '{key}' in config. Using default: {default}")
            return default
