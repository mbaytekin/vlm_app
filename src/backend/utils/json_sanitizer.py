import json, re
from typing import Optional, Any

JSON_ARRAY_RE = re.compile(r"\[.*\]", re.DOTALL)

def extract_json_array(text:str) -> Optional[list]:
    m = JSON_ARRAY_RE.search(text)
    if not m: return None
    snippet = m.group(0)
    # kaba parantez dengeleme
    open_sq = snippet.count("["); close_sq = snippet.count("]")
    if close_sq < open_sq:
        snippet += "]" * (open_sq - close_sq)
    try:
        data = json.loads(snippet)
        return data if isinstance(data, list) else None
    except Exception:
        # son çare: quote düzeltmeleri vs. çok agresif olmayalım
        return None
