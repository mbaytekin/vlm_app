from fastapi import APIRouter, HTTPException
from shared.config import get_models_config
from backend.registry.model_registry import list_models
from backend.registry import launcher
from backend.api.schemas import ModelsResponse, ModelInfo, ModelStatusResponse
import backend.api.services.direct_runtime as direct_runtime

router = APIRouter()

@router.get("", response_model=ModelsResponse)
async def get_models():
    items = []
    for m in list_models():
        items.append(ModelInfo(
            key=m.key, title=m.title, served_name=m.served_name,
            notes=m.notes,
            runtime=getattr(m, "runtime", "vllm"),
            supported_tasks=getattr(m, "supported_tasks", ["caption","vqa"])
        ))
    return {"models": items}

@router.post("/{key}/serve")
async def serve_model(key: str):
    cfg = get_models_config()
    model = None
    for m in cfg.get("models", []):
        if m.get("key") == key:
            model = m
            break
    if model is None:
        raise HTTPException(404, f"model not found: {key}")

    runtime = str(model.get("runtime", "vllm")).lower()
    if runtime == "direct":
        launcher.stop()
        from backend.registry.model_registry import get_model_by_key

        info = get_model_by_key(key)
        if info is None:
            raise HTTPException(404, f"model not found: {key}")
        try:
            await direct_runtime.load_model(info)
        except Exception as e:
            raise HTTPException(500, str(e))
        return {"ok": True, "pid": None}

    await direct_runtime.unload_model()
    launcher.stop()
    pid = launcher.start(key)
    return {"ok": True, "pid": pid}

@router.post("/stop")
async def stop_model():
    launcher.stop()
    await direct_runtime.unload_model()
    return {"ok": True}

@router.get("/status", response_model=ModelStatusResponse)
async def model_status():
    if direct_runtime.is_active():
        return direct_runtime.status()
    return launcher.status()
