import sys, pathlib
from typing import List, Dict, Any
from io import BytesIO
import base64

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from PIL import Image

from src.api.schemas import ThreadCreateResponse, ThreadsListResponse, ChatTurnRequest, ChatTurnResponse
from src.api.services.threads import store
from src.api.services.vllm_async import chat_completions
from src.backend.utils.draw import draw_boxes
from src.backend.strategies.caption import CaptionStrategy
from src.backend.strategies.vqa import VQAStrategy
from src.backend.strategies.ocr import OCRStrategy
from src.backend.strategies.detection import DetectionStrategy
from src.backend.strategies.direct import DirectStrategy
from src.backend.registry.model_registry import get_model_by_key, get_defaults

router = APIRouter()

def file_to_b64png(b: bytes) -> str:
    return base64.b64encode(b).decode("utf-8")

def resize_if_needed(image_bytes: bytes, max_long_side: int) -> bytes:
    try:
        im = Image.open(BytesIO(image_bytes)).convert("RGB")
    except Exception:
        return image_bytes
    w,h = im.size; long_side = max(w,h)
    if long_side <= max_long_side:
        return image_bytes
    scale = max_long_side/float(long_side)
    new = im.resize((int(w*scale), int(h*scale)))
    buf = BytesIO(); new.save(buf, format="PNG")
    return buf.getvalue()

@router.post("", response_model=ThreadCreateResponse)
async def create_thread(file: UploadFile = File(...)):
    b = await file.read()
    from src.shared.config import get_app_config
    max_side = int(get_app_config().get("limits", {}).get("max_image_long_side", 1280))
    b = resize_if_needed(b, max_side)
    dataurl = f"data:image/png;base64,{file_to_b64png(b)}"
    tid = store.create(b, dataurl)
    return {"thread_id": tid, "preview_dataurl": dataurl}

@router.get("", response_model=ThreadsListResponse)
async def list_threads():
    return {"items": store.list_ids()}

@router.delete("/{tid}")
async def delete_thread(tid: str):
    store.delete(tid)
    return {"ok": True}

def pick_strategy(task: str, free_mode: bool, json_strict: bool):
    if free_mode:
        return DirectStrategy()
    if task == "caption":
        return CaptionStrategy()
    if task == "vqa":
        return VQAStrategy()
    if task == "ocr":
        return OCRStrategy() if json_strict else DirectStrategy()
    if task == "detection":
        return DetectionStrategy(strict_json=json_strict)
    return DirectStrategy()

@router.post("/{tid}/messages", response_model=ChatTurnResponse)
async def chat_turn(tid: str, req: ChatTurnRequest):
    th = store.get(tid)
    if not th:
        raise HTTPException(404, "thread not found")
    image_dataurl = th["image_dataurl"]
    history = th["history"]

    # geçmişi metin olarak hazırla
    msgs: List[Dict[str, Any]] = []
    for t in history:
        role = t["role"]
        msgs.append({"role": role, "content": [{"type":"text","text": t["text"]}]})

    # bu tur
    strat = pick_strategy(req.task, req.free_mode, req.json_strict)
    cur = strat.build_messages(req.prompt, image_dataurl)
    if not isinstance(cur, list):
        cur = [cur]
    msgs.extend(cur)

    # model seçimi/servis ayarları
    defaults = get_defaults()
    served_name = get_model_by_key(th.get("model_key") or defaults.get("default_model_key","qwen2_5_vl_7b_awq")).served_name

    # çağrı
    text = await chat_completions(served_name, msgs, req.gen_kwargs or {})
    out = strat.parse_response(text)

    # çıktı ve geçmişi kaydet
    history.append({"role":"user","text": req.prompt})
    if req.task == "detection" and (not req.free_mode) and req.json_strict and isinstance(out, dict):
        raw = out.get("raw","")
        boxes = out.get("boxes", [])
        payload = {"text": raw or " ", "boxes": boxes}
        if boxes:
            ann = draw_boxes(th["image_bytes"], boxes)
            payload["annotated_png_b64"] = base64.b64encode(ann).decode("utf-8")
        history.append({"role":"assistant","text": payload["text"]})
        return payload
    else:
        txt = out if isinstance(out, str) else str(out)
        history.append({"role":"assistant","text": txt})
        return {"text": txt}
