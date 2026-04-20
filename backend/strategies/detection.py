import json
from typing import Any
from .base import ITaskStrategy
from backend.utils.json_sanitizer import extract_json_array

class DetectionStrategy(ITaskStrategy):
    def __init__(self, strict_json: bool = True):
        self.strict_json = strict_json

    def build_messages(self, prompt: str, image_dataurl: str | None) -> list:
        base = prompt.strip() or "Görseldeki tüm nesneleri tespit et ve koordinatlarını ver."
        if self.strict_json:
            hint = ('Sadece geçerli JSON döndür. Şema: '
                    '[{"label":str,"x":int,"y":int,"w":int,"h":int}] '
                    'Koordinatlar piksel, (0,0) sol-üst.')
            p = f"{base}\n{hint}"
        else:
            p = base  # serbest, şema dayatması yok
        content = [{"type": "text", "text": p}]
        if image_dataurl:
            content.append({"type": "input_image", "image_url": image_dataurl})
        return [{
            "role": "user",
            "content": content,
        }]

    def parse_response(self, text: str) -> Any:
        if not self.strict_json:
            return text.strip()
        arr = extract_json_array(text)
        if arr is None:
            return {"boxes": [], "raw": text}
        boxes = []
        for it in arr:
            try:
                x=int(it["x"]); y=int(it["y"]); w=int(it["w"]); h=int(it["h"])
                if w>0 and h>0:
                    boxes.append({"label":str(it.get("label","object")), "x":x,"y":y,"w":w,"h":h})
            except Exception:
                continue
        return {"boxes": boxes, "raw": text}
