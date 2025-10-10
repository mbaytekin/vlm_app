from fastapi import APIRouter, HTTPException
from src.shared.config import get_models_config
from src.backend.registry.model_registry import list_models
from src.backend.registry import launcher
from src.api.schemas import ModelsResponse, ModelInfo

router = APIRouter()

@router.get("", response_model=ModelsResponse)
async def get_models():
    items = []
    for m in list_models():
        items.append(ModelInfo(
            key=m.key, title=m.title, served_name=m.served_name,
            notes=m.notes, supported_tasks=getattr(m, "supported_tasks", ["caption","vqa"])
        ))
    return {"models": items}

@router.post("/{key}/serve")
async def serve_model(key: str):
    cfg = get_models_config()
    if not any(m["key"] == key for m in cfg.get("models", [])):
        raise HTTPException(404, f"model not found: {key}")
    launcher.stop()
    pid = launcher.start(key)
    return {"ok": True, "pid": pid}

@router.post("/stop")
async def stop_model():
    launcher.stop()
    return {"ok": True}
