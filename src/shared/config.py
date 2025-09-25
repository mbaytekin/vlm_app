import os, yaml, pathlib
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

ROOT = pathlib.Path(__file__).resolve().parents[2]
MODELS_YAML = ROOT / "configs" / "models.yaml"
APP_YAML = ROOT / "configs" / "app.yaml"

def load_yaml(p: pathlib.Path) -> Dict[str, Any]:
    return yaml.safe_load(p.read_text()) if p.exists() else {}

def get_app_config():
    return load_yaml(APP_YAML)

def get_models_config():
    return load_yaml(MODELS_YAML)
