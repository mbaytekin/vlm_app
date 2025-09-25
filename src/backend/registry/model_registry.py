from typing import List, Dict, Any
from src.shared.schemas import ModelInfo
from src.shared.config import get_models_config

def load_registry() -> Dict[str,Any]:
    return get_models_config()

def list_models() -> List[ModelInfo]:
    cfg = load_registry()
    return [ModelInfo(**m) for m in cfg.get("models",[])]

def get_defaults() -> Dict[str,Any]:
    return load_registry().get("defaults",{})

def get_model_by_key(key:str) -> ModelInfo|None:
    for m in list_models():
        if m.key == key:
            return m
    return None