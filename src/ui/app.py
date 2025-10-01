# --- PATH BOOTSTRAP (ilk satırlar) ---
import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]  # …/vlm-app
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# -------------------------------------

import os
import base64
import hashlib
from io import BytesIO
from typing import List, Dict, Any

import streamlit as st
from PIL import Image

from src.shared.config import get_models_config, get_app_config
from src.backend.registry.model_registry import list_models, get_defaults
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

# ------------------ Helpers ----------------------
def img_sha1(b: bytes) -> str:
    return hashlib.sha1(b).hexdigest()  # sadece yerel oturum için

def maybe_resize(image_bytes: bytes, max_long_side: int) -> bytes:
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

def ensure_state():
    ss = st.session_state
    ss.setdefault("threads", {})          # image_id -> {"image_bytes", "image_dataurl", "history":[{"role","text"}]}
    ss.setdefault("current_thread_id", None)
    ss.setdefault("selected_model_key", None)

ensure_state()

# ------------------ Sidebar: Model & Controls -----
st.sidebar.header("Model ve Görev")

# Model list
models = list_models()
if not models:
    st.sidebar.error("configs/models.yaml içinde model tanımı bulunamadı.")
    st.stop()
model_titles = {m.title: m for m in models}
sel_title = st.sidebar.selectbox("Model", list(model_titles.keys()), index=0)
selected = model_titles[sel_title]
st.session_state.selected_model_key = selected.key

if selected.notes:
    st.sidebar.caption(selected.notes)

ALL_TASKS = ["caption", "vqa", "ocr", "detection"]
allowed_tasks = [t for t in ALL_TASKS if t in (getattr(selected, "supported_tasks", []) or [])]
if not allowed_tasks:
    allowed_tasks = ["caption"]

default_task = cfg_app.get("ui", {}).get("default_task", "caption")
default_idx = 0 if default_task not in allowed_tasks else allowed_tasks.index(default_task)
task = st.sidebar.selectbox("Görev", allowed_tasks, index=default_idx)
unsupported = set(ALL_TASKS) - set(allowed_tasks)
if unsupported:
    st.sidebar.caption(f"Bu modelin desteklemediği görevler: {', '.join(sorted(unsupported))}")

with st.sidebar.expander("Gelişmiş"):
    max_new_tokens = st.number_input("max_new_tokens", min_value=1, max_value=4096,
                                     value=int(cfg_app.get("ui", {}).get("max_new_tokens", 256)))
    temperature = st.slider("temperature", 0.0, 1.0, float(cfg_app.get("ui", {}).get("temperature", 0.2)))
    top_p = st.slider("top_p", 0.0, 1.0, float(cfg_app.get("ui", {}).get("top_p", 1.0)))
    presence_penalty = st.slider("presence_penalty", -2.0, 2.0, float(cfg_app.get("ui", {}).get("presence_penalty", 0.0)))
    frequency_penalty = st.slider("frequency_penalty", -2.0, 2.0, float(cfg_app.get("ui", {}).get("frequency_penalty", 0.0)))

with st.sidebar.expander("Prompt davranışı"):
    free_mode = st.checkbox("Serbest mod (şablon ekleme)", value=False)
    json_strict = False
    if task in ("ocr", "detection"):
        json_strict = st.checkbox("Yapısal JSON iste (OCR/Detection)", value=True)

# vLLM süreç yönetimi
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
    alive = backend.list_models() is not None
except Exception:
    alive = False
st.toast("vLLM aktif" if alive else "vLLM kapalı", icon="✅" if alive else "⚠️")

# ------------------ Chat-like Main Area -----------
st.markdown("### Sohbet")

# 1) Görsel yükle (yeni sohbet başlatır)
max_long_side = int(cfg_app.get("limits", {}).get("max_image_long_side", 1280))
up = st.file_uploader("Yeni görsel yükle (PNG/JPG) — yeni sohbet başlatır", type=["png", "jpg", "jpeg"], accept_multiple_files=False)

if up is not None:
    original_bytes = up.read()
    image_bytes = maybe_resize(original_bytes, max_long_side)
    image_b64 = file_to_b64png(image_bytes)
    dataurl = f"data:image/png;base64,{image_b64}"
    img_id = img_sha1(image_bytes)
    st.session_state.threads[img_id] = {
        "image_bytes": image_bytes,
        "image_dataurl": dataurl,
        "history": []  # [{role:'user'/'assistant', 'text': str}]
    }
    st.session_state.current_thread_id = img_id
    st.success("Görsel yüklendi. Bu görsele bağlı sohbet başladı.")

# 2) aktif thread var mı?
tid = st.session_state.current_thread_id
if not tid:
    st.info("Başlamak için bir görsel yükleyin; sonra alttaki chat alanından sorular sorabilirsiniz.")
    st.stop()

thread = st.session_state.threads[tid]
image_bytes = thread["image_bytes"]
image_dataurl = thread["image_dataurl"]
history: List[Dict[str, Any]] = thread["history"]

# Üstte küçük önizleme
with st.container():
    col1, col2 = st.columns([1, 3])
    with col1:
        st.image(Image.open(BytesIO(image_bytes)), caption="Aktif görsel", use_column_width=True)
    with col2:
        st.caption("Bu sohbet bu görsele bağlıdır. Yeni görsel yüklediğinizde yeni bir sohbet başlar.")

# 3) geçmişi baloncuk olarak göster
for turn in history:
    if turn["role"] == "user":
        with st.chat_message("user"):
            st.markdown(turn["text"])
    else:
        with st.chat_message("assistant"):
            # detection JSON ise kutu görseli olabilir
            if isinstance(turn.get("render"), dict) and turn["render"].get("boxes"):
                st.markdown(turn["text"])
                ann = turn["render"]["annotated_png"]
                st.image(Image.open(BytesIO(ann)), caption="Kutular çizildi")
                st.json(turn["render"]["boxes"])
            else:
                st.markdown(turn["text"])

# 4) chat input
prompt = st.chat_input("Sorunuzu yazın… (aynı görsele istediğiniz kadar soru sorabilirsiniz)")
if prompt and alive:
    # mesajları oluştur
    # a) geçmişi metin olarak iletelim (role-preserving)
    msgs: List[Dict[str, Any]] = []
    for t in history:
        if t["role"] == "user":
            msgs.append({"role": "user", "content": [{"type": "text", "text": t["text"]}]})
        else:
            msgs.append({"role": "assistant", "content": [{"type": "text", "text": t["text"]}]})

    # b) bu tur için strateji
    if free_mode:
        strat = DirectStrategy()
    else:
        if task == "caption":
            strat = CaptionStrategy()
        elif task == "vqa":
            strat = VQAStrategy()
        elif task == "ocr":
            strat = OCRStrategy() if json_strict else DirectStrategy()
        elif task == "detection":
            strat = DetectionStrategy(strict_json=json_strict)
        else:
            strat = DirectStrategy()

    # c) bu turdaki kullanıcı mesajını (görselle birlikte) ekle
    user_msg = strat.build_messages(prompt, image_dataurl)
    if not isinstance(user_msg, list):
        user_msg = [user_msg]
    msgs.extend(user_msg)

    gen_kwargs = dict(
        max_tokens=int(max_new_tokens),
        temperature=float(temperature),
        top_p=float(top_p),
        presence_penalty=float(presence_penalty),
        frequency_penalty=float(frequency_penalty),
    )
    served_name = selected.served_name

    # UI: önce kullanıcı balonunu ekle
    history.append({"role": "user", "text": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # model çağrısı
    with st.chat_message("assistant"):
        with st.spinner("Yanıt üretiliyor…"):
            try:
                resp = backend.vision_chat(served_name, msgs, gen_kwargs)
                out = strat.parse_response(resp.text)
            except Exception as e:
                st.error(f"Hata: {e}")
                st.stop()

        # detection + json_strict'te kutu çiz
        if task == "detection" and not free_mode and json_strict and isinstance(out, dict):
            # ham metin + kutular
            raw = out.get("raw", "")
            boxes = out.get("boxes", [])
            render_payload = {}
            if boxes:
                ann_png = draw_boxes(image_bytes, boxes)
                st.markdown(raw if raw else "Bulunan kutular:")
                st.image(Image.open(BytesIO(ann_png)), caption="Kutular çizildi")
                st.json(boxes)
                render_payload = {"boxes": boxes, "annotated_png": ann_png}
            else:
                st.markdown(raw if raw else "Kutu bulunamadı.")
            history.append({"role": "assistant", "text": raw if raw else " ", "render": render_payload})
        else:
            # normal metin
            if isinstance(out, (dict, list)):
                st.json(out)
                history.append({"role": "assistant", "text": str(out)})
            else:
                st.markdown(out)
                history.append({"role": "assistant", "text": out})

# 5) Alt araçlar
c1, c2 = st.columns(2)
with c1:
    if st.button("Bu sohbeti sıfırla (aynı görsel)"):
        thread["history"] = []
        st.rerun()
with c2:
    if st.button("Tüm sohbetleri temizle"):
        st.session_state.threads = {}
        st.session_state.current_thread_id = None
        st.rerun()
