import json
from pathlib import Path
from utils.path_helper import get_config_dir

class ConfigLoader:
    @staticmethod
    def load_json(filename: str) -> dict:
        filepath = get_config_dir() / filename
        if not filepath.exists():
            raise FileNotFoundError(f"配置文件不存在: {filepath}")
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def load_store_config(store_id: str, filename: str) -> dict:
        filepath = get_config_dir() / "stores" / store_id / filename
        if not filepath.exists():
            raise FileNotFoundError(f"商家配置不存在: {filepath}")
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def list_stores() -> list[str]:
        stores_dir = get_config_dir() / "stores"
        if not stores_dir.exists():
            return []
        return [d.name for d in stores_dir.iterdir() if d.is_dir()]
