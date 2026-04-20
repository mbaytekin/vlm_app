import os, httpx, base64
from typing import Dict, Any

API_URL = os.environ.get("VLM_GATEWAY_URL", "http://localhost:9000")

class ApiClient:
    def __init__(self, base_url: str = API_URL):
        self.base = base_url.rstrip("/")

    # MODELS
    def list_models(self):
        r = httpx.get(f"{self.base}/models", timeout=10)
        r.raise_for_status()
        return r.json()["models"]

    def serve_model(self, key: str):
        r = httpx.post(f"{self.base}/models/{key}/serve", timeout=10)
        r.raise_for_status()
        return r.json()

    def stop_model(self):
        r = httpx.post(f"{self.base}/models/stop", timeout=10)
        r.raise_for_status()
        return r.json()

    # THREADS
    def create_thread(self, file_bytes: bytes, filename: str = "image.png"):
        files = {"file": (filename, file_bytes, "image/png")}
        r = httpx.post(f"{self.base}/threads", files=files, timeout=60)
        r.raise_for_status()
        return r.json()  # {thread_id, preview_dataurl}

    def list_threads(self):
        r = httpx.get(f"{self.base}/threads", timeout=10)
        r.raise_for_status()
        return r.json()["items"]

    def delete_thread(self, tid: str):
        r = httpx.delete(f"{self.base}/threads/{tid}", timeout=10)
        r.raise_for_status()
        return r.json()

    def chat_turn(self, tid: str, payload: Dict[str, Any]):
        r = httpx.post(f"{self.base}/threads/{tid}/messages", json=payload, timeout=120)
        r.raise_for_status()
        return r.json()
