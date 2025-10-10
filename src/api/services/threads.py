import time, hashlib, base64
from typing import Dict, Any

class ThreadStore:
    """Basit in-memory thread deposu."""
    def __init__(self):
        self.threads: Dict[str, Dict[str, Any]] = {}  # id -> {image_bytes, dataurl, history, created_at}

    def create(self, image_bytes: bytes, dataurl: str) -> str:
        tid = hashlib.sha1(image_bytes).hexdigest()
        self.threads[tid] = {
            "image_bytes": image_bytes,
            "image_dataurl": dataurl,
            "history": [],  # [{role:'user'/'assistant', 'text': str}]
            "created_at": time.time(),
        }
        return tid

    def get(self, tid: str):
        return self.threads.get(tid)

    def list_ids(self):
        return [{"thread_id": k, "created_at": v["created_at"]} for k, v in self.threads.items()]

    def delete(self, tid: str):
        self.threads.pop(tid, None)

store = ThreadStore()
