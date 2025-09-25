from io import BytesIO
from typing import List, Dict
from PIL import Image, ImageDraw, ImageFont
import base64

def draw_boxes(image_bytes: bytes, boxes: List[Dict]) -> bytes:
    im = Image.open(BytesIO(image_bytes)).convert("RGB")
    dr = ImageDraw.Draw(im)
    for b in boxes:
        x,y,w,h = b["x"],b["y"],b["w"],b["h"]
        dr.rectangle([x,y,x+w,y+h], width=3, outline=(0,255,0))
        lbl = b.get("label","obj")
        dr.text((x+3, y+3), lbl, fill=(0,255,0))
    out = BytesIO(); im.save(out, format="PNG"); return out.getvalue()

def file_to_b64png(file_bytes: bytes) -> str:
    return base64.b64encode(file_bytes).decode("utf-8")
