import os, json
import httpx
from typing import List, Dict, Any

API_BASE = os.environ.get("OPENAI_API_BASE", "http://localhost:8000/v1")
API_KEY  = os.environ.get("OPENAI_API_KEY", "EMPTY")

# --- bağlantı havuzu / timeout ayarları (TEK instance) ---
_LIMITS  = httpx.Limits(max_keepalive_connections=20, max_connections=100)
_TIMEOUT = httpx.Timeout(connect=3.0, read=60.0, write=10.0, pool=5.0)
_CLIENT: httpx.AsyncClient | None = None

async def get_client() -> httpx.AsyncClient:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = httpx.AsyncClient(timeout=_TIMEOUT, limits=_LIMITS, headers={
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json",
        })
    return _CLIENT

async def close_client():
    global _CLIENT
    if _CLIENT is not None:
        await _CLIENT.aclose()
        _CLIENT = None
# -----------------------------------------------------------

def normalize_messages(messages: List[dict]) -> List[dict]:
    norm = []
    for m in messages:
        parts = []
        for p in m.get("content", []):
            if isinstance(p, dict) and p.get("type") in ("input_image","image_url"):
                iu = p.get("image_url")
                url = iu if isinstance(iu, str) else (iu.get("url") if isinstance(iu, dict) else None)
                parts.append({"type":"image_url","image_url":{"url":url}} if url else p)
            else:
                parts.append(p)
        nm = dict(m); nm["content"] = parts; norm.append(nm)
    return norm

async def chat_completions(served_name: str, messages: List[dict], gen_kwargs: Dict[str, Any]) -> str:
    msgs = normalize_messages(messages)
    url = API_BASE.rstrip("/") + "/chat/completions"
    payload = {"model": served_name, "messages": msgs}
    for k in ("max_tokens","temperature","top_p","presence_penalty","frequency_penalty"):
        if k in (gen_kwargs or {}): payload[k] = gen_kwargs[k]
    client = await get_client()
    r = await client.post(url, json=payload)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]
