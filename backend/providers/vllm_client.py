import os
import mimetypes
import json
import requests
from typing import Dict, Any, List
from .base import IModelBackend
from shared.schemas import ChatResponse
from shared.errors import BackendError

# OpenAI SDK (>=1.40 önerilir). Yüklüyse kullanacağız; değilse doğrudan REST'e düşeriz.
try:
    from openai import OpenAI
except Exception:
    OpenAI = None


def _dataurl(image_b64: str, filename: str = "image.png") -> str:
    mt = mimetypes.guess_type(filename)[0] or "image/png"
    return f"data:{mt};base64,{image_b64}"


def _normalize_messages(messages: List[dict]) -> List[dict]:
    """
    OpenAI/vLLM 0.10.x şeması:
      {"role":"user","content":[
         {"type":"text","text":"..."},
         {"type":"image_url","image_url":{"url":"data:..."}}
      ]}
    Eski/karişik "input_image" tiplerini "image_url"e dönüştür.
    """
    norm = []
    for m in messages:
        new_parts = []
        for part in m.get("content", []):
            if not isinstance(part, dict):
                new_parts.append(part)
                continue

            t = part.get("type")
            if t in ("input_image", "image_url"):
                # her durumda "image_url" tipine normalize et
                iu = part.get("image_url")
                url = None
                if isinstance(iu, str):
                    url = iu
                elif isinstance(iu, dict):
                    url = iu.get("url")
                if url:
                    new_parts.append({"type": "image_url", "image_url": {"url": url}})
                else:
                    # beklenmedik durum; olduğu gibi bırak
                    new_parts.append(part)
            elif t == "text":
                # olması gerektiği gibi
                new_parts.append(part)
            else:
                # başka tip gelirse dokunma
                new_parts.append(part)

        nm = dict(m)
        nm["content"] = new_parts
        norm.append(nm)
    return norm

class VLLMBackend(IModelBackend):
    """
    vLLM OpenAI-uyumlu sunucu istemcisi.
    - Önce OpenAI SDK ile dener
    - Hata alırsa REST fallback (/v1/chat/completions)
    """
    def __init__(self, api_base: str | None = None):
        self.api_base = api_base or os.environ.get("OPENAI_API_BASE", "http://localhost:8000/v1")
        self.api_key = os.environ.get("OPENAI_API_KEY", "EMPTY")  # vLLM için key genelde kullanılmıyor
        self._sdk = None
        if OpenAI is not None:
            try:
                self._sdk = OpenAI(api_key=self.api_key, base_url=self.api_base)
            except Exception:
                self._sdk = None

    def vision_chat(self, served_name: str, messages: List[dict], gen_kwargs: Dict[str, Any]) -> ChatResponse:
        msgs = _normalize_messages(messages)
        # OpenAI SDK yolu
        if self._sdk is not None:
            try:
                resp = self._sdk.chat.completions.create(
                    model=served_name,
                    messages=msgs,
                    **gen_kwargs
                )
                text = resp.choices[0].message.content or ""
                return ChatResponse(text=text)
            except AttributeError as e:
                # SDK sürüm/glitch: fallback'e düş
                pass
            except Exception as e:
                # SDK ağ hatası vs. REST ile şans verelim
                try:
                    return self._rest_fallback(served_name, msgs, gen_kwargs)
                except Exception as e2:
                    raise BackendError(f"vLLM request failed (SDK & REST): {e2}") from e

        # REST fallback (SDK yoksa veya kapattıysak)
        try:
            return self._rest_fallback(served_name, msgs, gen_kwargs)
        except Exception as e:
            raise BackendError(f"vLLM request failed: {e}")

    def _rest_fallback(self, served_name: str, messages: List[dict], gen_kwargs: Dict[str, Any]) -> ChatResponse:
        url = self.api_base.rstrip("/") + "/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key or 'EMPTY'}"
        }
        payload = {"model": served_name, "messages": messages}
        # izin verilen anahtarları aktar (vLLM bunları anlar)
        allowed = {"max_tokens", "temperature", "top_p", "presence_penalty", "frequency_penalty"}
        for k, v in gen_kwargs.items():
            if k in allowed:
                payload[k] = v
        r = requests.post(url, headers=headers, data=json.dumps(payload), timeout=60)
        if not r.ok:
            raise BackendError(f"HTTP {r.status_code}: {r.text[:500]}")
        data = r.json()
        try:
            text = data["choices"][0]["message"]["content"]
        except Exception:
            raise BackendError(f"Unexpected response: {data}")
        return ChatResponse(text=text)

    def list_models(self):
        # küçük sağlık kontrolü: REST ile /models
        url = self.api_base.rstrip("/") + "/models"
        headers = {"Authorization": f"Bearer {self.api_key or 'EMPTY'}"}
        r = requests.get(url, headers=headers, timeout=5)
        r.raise_for_status()
        return r.json()