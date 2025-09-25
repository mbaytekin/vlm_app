# --- PATH BOOTSTRAP (ilk satırlar) ---
import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# -------------------------------------

import os
import base64
from io import BytesIO

import streamlit as st
from PIL import Image

from src.shared.config import get_models_config, get_app_config
from src.backend.registry.model_registry import list_models, get_model_by_key, get_defaults
from src.backend.registry import launcher
from src.backend.providers.vllm_client import VLLMBackend

# Strategies
from src.backend.strategies.caption import CaptionStrategy
from src.backend.strategies.vqa import VQAStrategy
from src.backend.strategies.ocr import OCRStrategy
from src.backend.strategies.detection import DetectionStrategy
from src.backend.strategies.direct import DirectStrategy

# Utils
from src.backend.utils.draw import draw_boxes, file_to_b64png



# ------------------ Page config ------------------
st.set_page_config(page_title="VLM UI", layout="wide")

# ------------------ Load configs -----------------
cfg_models = get_models_config()
cfg_app = get_app_config()
defaults = get_defaults()
api_base = defaults.get("api_base", "http://localhost:8000/v1")

# ------------------ Backend client ----------------
backend = VLLMBackend(api_base=api_base)

# ------------------ Sidebar: Model & Controls -----
st.sidebar.header("Model ve Görev")

# Model list
models = list_models()
if not models:
    st.sidebar.error("configs/models.yaml içinde model tanımı bulunamadı.")
    st.stop()

model_titles = {m.title: m for m in models}
title_list = list(model_titles.keys())

sel_title = st.sidebar.selectbox("Model", title_list, index=0)
selected = model_titles[sel_title]

# Notes
if selected.notes:
    st.sidebar.caption(selected.notes)

# Dinamik görevler
ALL_TASKS = ["caption", "vqa", "ocr", "detection"]
allowed_tasks = [t for t in ALL_TASKS if t in (getattr(selected, "supported_tasks", []) or [])]
if not allowed_tasks:
    # Emniyetli varsayılan
    allowed_tasks = ["caption"]

default_task = cfg_app.get("ui", {}).get("default_task", "caption")
default_idx = 0 if default_task not in allowed_tasks else allowed_tasks.index(default_task)

task = st.sidebar.selectbox("Görev", allowed_tasks, index=default_idx)

unsupported = set(ALL_TASKS) - set(allowed_tasks)
if unsupported:
    st.sidebar.caption(f"Bu modelin desteklemediği görevler: {', '.join(sorted(unsupported))}")

# Gelişmiş üretim parametreleri
with st.sidebar.expander("Gelişmiş"):
    max_new_tokens = st.number_input(
        "max_new_tokens", min_value=1, max_value=4096,
        value=int(cfg_app.get("ui", {}).get("max_new_tokens", 256))
    )
    temperature = st.slider(
        "temperature", min_value=0.0, max_value=1.0,
        value=float(cfg_app.get("ui", {}).get("temperature", 0.2))
    )
    top_p = st.slider(
        "top_p", min_value=0.0, max_value=1.0,
        value=float(cfg_app.get("ui", {}).get("top_p", 1.0))
    )
    presence_penalty = st.slider(
        "presence_penalty", min_value=-2.0, max_value=2.0,
        value=float(cfg_app.get("ui", {}).get("presence_penalty", 0.0))
    )
    frequency_penalty = st.slider(
        "frequency_penalty", min_value=-2.0, max_value=2.0,
        value=float(cfg_app.get("ui", {}).get("frequency_penalty", 0.0))
    )

# Prompt davranışı: Serbest mod ve JSON katılığı anahtarları
with st.sidebar.expander("Prompt davranışı"):
    free_mode = st.checkbox("Serbest mod (şablon ekleme)", value=False)
    # JSON anahtarını sadece ilgili görev/ modellerde göster
    show_json_toggle = ("ocr" in allowed_tasks or "detection" in allowed_tasks)
    json_strict = False
    if show_json_toggle and task in ("ocr", "detection"):
        json_strict = st.checkbox("Yapısal JSON iste (OCR/Detection)", value=True)

# vLLM süreci yönetimi
colA, colB, colC = st.sidebar.columns(3)
if colA.button("Başlat"):
    launcher.stop()
    pid = launcher.start(selected.key)
    st.sidebar.success(f"PID {pid}")
if colB.button("Durdur"):
    launcher.stop()
    st.sidebar.info("Durduruldu")
if colC.button("Yenile"):
    st.rerun()

# Healthcheck
try:
    # Basit kontrol: /v1/models erişilebiliyor mu?
    alive = backend.list_models() is not None
except Exception:
    alive = False

if not alive:
    st.warning("vLLM servisi çalışmıyor. Sidebar'dan 'Başlat' deyip tekrar deneyin.")
else:
    st.success("vLLM aktif")

# ------------------ Main Area ---------------------
st.subheader("Girdi")

# Prompt
prompt = st.text_input("Prompt", value="")

# Görsel yükleme
up = st.file_uploader("Görsel yükle (PNG/JPG)", type=["png", "jpg", "jpeg"])

# İsteğe bağlı: uzun kenarı sınırlama
max_long_side = int(cfg_app.get("limits", {}).get("max_image_long_side", 1280))

def maybe_resize(image_bytes: bytes) -> bytes:
    try:
        im = Image.open(BytesIO(image_bytes)).convert("RGB")
    except Exception:
        return image_bytes
    w, h = im.size
    long_side = max(w, h)
    if long_side <= max_long_side:
        return image_bytes
    scale = max_long_side / float(long_side)
    new_w, new_h = int(w * scale), int(h * scale)
    rim = im.resize((new_w, new_h), Image.LANCZOS)
    out = BytesIO()
    rim.save(out, format="PNG")
    return out.getvalue()

run = st.button("Çalıştır", type="primary")

if run:
    if task not in allowed_tasks:
        st.error(f"Seçili model '{selected.title}' için '{task}' desteklenmiyor.")
        st.stop()

    if not up:
        st.error("Lütfen bir görsel yükleyin.")
        st.stop()

    # Görseli oku ve gerekirse yeniden boyutlandır
    original_bytes = up.read()
    image_bytes = maybe_resize(original_bytes)

    # DataURL
    b64 = file_to_b64png(image_bytes)
    dataurl = f"data:image/png;base64,{b64}"

    # Strategy seçimi
    if free_mode:
        strat = DirectStrategy()
    else:
        if task == "caption":
            strat = CaptionStrategy()
        elif task == "vqa":
            strat = VQAStrategy()
        elif task == "ocr":
            # JSON katı ise OCRStrategy, değilse tamamen serbest akış
            strat = OCRStrategy() if json_strict else DirectStrategy()
        elif task == "detection":
            strat = DetectionStrategy(strict_json=json_strict)
        else:
            strat = DirectStrategy()

    messages = strat.build_messages(prompt, dataurl)
    gen_kwargs = dict(
        max_tokens=int(max_new_tokens),
        temperature=float(temperature),
        top_p=float(top_p),
        presence_penalty=float(presence_penalty),
        frequency_penalty=float(frequency_penalty),
    )
    served_name = selected.served_name

    with st.spinner("Model çalışıyor..."):
        try:
            resp = backend.vision_chat(served_name, messages, gen_kwargs)
            out = strat.parse_response(resp.text)
        except Exception as e:
            st.error(f"Hata: {e}")
            st.stop()

    st.subheader("Çıktı")
    if task == "detection" and not free_mode and json_strict and isinstance(out, dict):
        # Yapısal JSON beklentisi varsa kutuları çiz
        st.text_area("Ham Yanıt", value=out.get("raw", ""), height=120)
        boxes = out.get("boxes", [])
        if boxes:
            ann = draw_boxes(image_bytes, boxes)
            st.image(Image.open(BytesIO(ann)), caption="Kutular çizildi")
            st.json(boxes)
        else:
            st.info("Geçerli kutu bulunamadı.")
    else:
        # Diğer tüm durumlarda metni yaz
        if isinstance(out, (dict, list)):
            st.json(out)
        else:
            st.write(out)

    # Girdi görseli
    st.image(Image.open(BytesIO(image_bytes)), caption="Girdi görseli", use_column_width=True)
