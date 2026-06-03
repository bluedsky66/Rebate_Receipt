import sys
import os
from pathlib import Path

def get_base_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    else:
        return Path(__file__).resolve().parent.parent.parent

def get_config_dir() -> Path:
    return get_base_dir() / "config"

def get_output_dir() -> Path:
    output_dir = get_base_dir() / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def get_jobs_dir() -> Path:
    jobs_dir = get_base_dir() / "jobs"
    jobs_dir.mkdir(parents=True, exist_ok=True)
    return jobs_dir

def get_store_logo_path(store_id: str) -> Path:
    return get_config_dir() / "stores" / store_id / "logo.png"

def get_store_config_path(store_id: str, filename: str) -> Path:
    return get_config_dir() / "stores" / store_id / filename
