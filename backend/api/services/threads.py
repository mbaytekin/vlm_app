import time
import uuid
from typing import Dict, Any

class ThreadStore:
    """Basit in-memory thread deposu."""
    def __init__(self):
        self.threads: Dict[str, Dict[str, Any]] = {}  # id -> {image_bytes, dataurl, history, created_at}

    def create(self, image_bytes: bytes | None, dataurl: str | None, model_key: str | None = None) -> str:
        tid = uuid.uuid4().hex
        self.threads[tid] = {
            "image_bytes": image_bytes,
            "image_dataurl": dataurl,
            "model_key": model_key,
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
