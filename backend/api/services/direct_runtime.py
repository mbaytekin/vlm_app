import asyncio
import base64
import gc
import os
import threading
from io import BytesIO
from typing import Any, Dict, List

import torch
from PIL import Image
from transformers import AutoModelForCausalLM, AutoProcessor, BitsAndBytesConfig

from shared.schemas import ModelInfo


class DirectRuntime:
    def __init__(self):
        self._lock = threading.RLock()
        self._model = None
        self._processor = None
        self._model_key: str | None = None
        self._served_name: str | None = None
        self._runtime = "direct"
        self._loading = False
        self._ready = False
        self._error: str | None = None

    def _clear_cuda(self):
        gc.collect()
        if torch.cuda.is_available():
            try:
                torch.cuda.empty_cache()
            except Exception:
                pass

    def _decode_image_dataurl(self, url: str) -> Image.Image | None:
        if not isinstance(url, str):
            return None
        if not url.startswith("data:image/"):
            return None
        comma = url.find(",")
        if comma < 0:
            return None
        b64 = url[comma + 1 :]
        try:
            raw = base64.b64decode(b64)
            return Image.open(BytesIO(raw)).convert("RGB")
        except Exception:
            return None

    def unload(self):
        with self._lock:
            self._model = None
            self._processor = None
            self._model_key = None
            self._served_name = None
            self._loading = False
            self._ready = False
            self._error = None
        self._clear_cuda()

    def _make_bnb_config(self, model: ModelInfo) -> BitsAndBytesConfig:
        quant = (model.direct_quant or "4bit").strip().lower()
        if quant == "8bit":
            return BitsAndBytesConfig(load_in_8bit=True)
        return BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
        )

    def load(self, model: ModelInfo):
        with self._lock:
            if self._ready and self._model_key == model.key:
                return
            self._loading = True
            self._ready = False
            self._error = None
            self._model_key = model.key
            self._served_name = model.served_name

        try:
            self.unload()
            with self._lock:
                self._loading = True
                self._ready = False
                self._error = None
                self._model_key = model.key
                self._served_name = model.served_name

            bnb = self._make_bnb_config(model)
            processor = AutoProcessor.from_pretrained(model.hf_id, trust_remote_code=True)
            loaded_model = AutoModelForCausalLM.from_pretrained(
                model.hf_id,
                quantization_config=bnb,
                torch_dtype=torch.bfloat16,
                device_map="auto",
                trust_remote_code=True,
            )

            with self._lock:
                self._processor = processor
                self._model = loaded_model
                self._loading = False
                self._ready = True
                self._error = None
        except Exception as e:
            with self._lock:
                self._loading = False
                self._ready = False
                self._error = str(e)
            # yarım yüklemeyi temizle
            with self._lock:
                self._model = None
                self._processor = None
            self._clear_cuda()
            raise

    def is_active(self) -> bool:
        with self._lock:
            return bool(self._loading or self._ready or self._model_key or self._error)

    def status(self) -> Dict[str, Any]:
        with self._lock:
            running = bool(self._loading or self._ready)
            served_models = [self._served_name] if (self._ready and self._served_name) else []
            return {
                "running": running,
                "ready": bool(self._ready),
                "pid": os.getpid() if running else None,
                "model_key": self._model_key,
                "served_name": self._served_name,
                "served_models": served_models,
                "error": self._error,
                "runtime": self._runtime,
            }

    def _to_hf_messages(self, messages: List[dict]) -> tuple[list[dict], list[Image.Image]]:
        hf_messages: list[dict] = []
        images: list[Image.Image] = []

        for m in messages:
            role = str(m.get("role", "user"))
            content = m.get("content")
            if isinstance(content, str):
                hf_messages.append({"role": role, "content": [{"type": "text", "text": content}]})
                continue

            if not isinstance(content, list):
                continue

            parts: list[dict] = []
            for p in content:
                if not isinstance(p, dict):
                    continue
                p_type = p.get("type")
                if p_type == "text":
                    txt = p.get("text")
                    if isinstance(txt, str) and txt.strip():
                        parts.append({"type": "text", "text": txt})
                elif p_type in ("image_url", "input_image"):
                    iu = p.get("image_url")
                    url = iu if isinstance(iu, str) else (iu.get("url") if isinstance(iu, dict) else None)
                    if isinstance(url, str):
                        img = self._decode_image_dataurl(url)
                        if img is not None:
                            images.append(img)
                            parts.append({"type": "image"})

            if not parts:
                continue
            hf_messages.append({"role": role, "content": parts})

        return hf_messages, images

    def chat(self, messages: List[dict], gen_kwargs: Dict[str, Any]) -> str:
        with self._lock:
            model = self._model
            processor = self._processor
            ready = self._ready
        if not ready or model is None or processor is None:
            raise RuntimeError("Direct runtime hazir degil. Once modeli baslatin.")

        hf_messages, images = self._to_hf_messages(messages)
        if not hf_messages:
            raise RuntimeError("Gecerli mesaj icerigi bulunamadi.")

        prompt = processor.apply_chat_template(
            hf_messages,
            tokenize=False,
            add_generation_prompt=True,
        )

        inputs = processor(
            text=prompt,
            images=images if images else None,
            return_tensors="pt",
        )

        # gemma direct runtime tek GPU'da calisiyor
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        for k, v in list(inputs.items()):
            if hasattr(v, "to"):
                inputs[k] = v.to(device)

        max_new_tokens = int((gen_kwargs or {}).get("max_tokens", 256))
        temperature = float((gen_kwargs or {}).get("temperature", 0.2))
        top_p = float((gen_kwargs or {}).get("top_p", 1.0))

        generate_args: Dict[str, Any] = {
            "max_new_tokens": max(1, min(max_new_tokens, 2048)),
        }
        if temperature <= 0:
            generate_args["do_sample"] = False
        else:
            generate_args["do_sample"] = True
            generate_args["temperature"] = temperature
            generate_args["top_p"] = max(0.01, min(top_p, 1.0))

        with torch.inference_mode():
            out = model.generate(**inputs, **generate_args)

        prompt_len = int(inputs["input_ids"].shape[-1])
        new_tokens = out[0][prompt_len:]
        text = processor.decode(new_tokens, skip_special_tokens=True)
        return text.strip()


_RUNTIME = DirectRuntime()


async def load_model(model: ModelInfo):
    await asyncio.to_thread(_RUNTIME.load, model)


async def unload_model():
    await asyncio.to_thread(_RUNTIME.unload)


async def chat_completions_direct(messages: List[dict], gen_kwargs: Dict[str, Any]) -> str:
    return await asyncio.to_thread(_RUNTIME.chat, messages, gen_kwargs or {})


def status() -> Dict[str, Any]:
    return _RUNTIME.status()


def is_active() -> bool:
    return _RUNTIME.is_active()
