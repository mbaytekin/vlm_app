# src/ui/app.py

# --- PATH BOOTSTRAP (importlardan önce) ---
import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
# ------------------------------------------

import os, time, base64
from io import BytesIO
from typing import List, Dict, Any, Optional

import streamlit as st
from PIL import Image
import httpx

from src.shared.config import get_app_config
from src.ui.api_client import ApiClient


# ---------------- Sayfa ayarı ----------------
st.set_page_config(page_title="VLM GATEWAY UI", layout="wide")
cfg_app = get_app_config()
API_URL = os.environ.get("VLM_GATEWAY_URL", "http://localhost:9000")
api = ApiClient(API_URL)


# --------------- CSS Enjeksiyonu ---------------
def inject_css(cfg: dict):
    from pathlib import Path
    css_path: Optional[str] = (cfg.get("ui", {}).get("theme", {}) or {}).get("css_path")
    if css_path:
        p = Path(css_path)
        if not p.is_absolute():
            p = (Path(__file__).resolve().parents[2] / css_path).resolve()
    else:
        p = Path(__file__).resolve().parent / "styles" / "chat.css"
    try:
        st.markdown(p.read_text(encoding="utf-8"), unsafe_allow_html=True)
    except Exception:
        st.markdown("""
        <style>
        .chat-wrap{display:flex;margin:6px 0;}
        .chat-bubble{padding:.65rem .85rem;border-radius:14px;max-width:80%;
          line-height:1.35;color:#0f172a;background:#f7f7f8;border:1px solid #e5e7eb;}
        .user{justify-content:flex-end;} .assistant{justify-content:flex-start;}
        .user .chat-bubble{background:#e9efff;}
        </style>
        """, unsafe_allow_html=True)

inject_css(cfg_app)


# --------------- Session State ----------------
def ensure_state():
    ss = st.session_state
    # threads_local[tid] = {"history":[{id,role,text,render,ts}], "preview_dataurl":str}
    ss.setdefault("threads_local", {})
    ss.setdefault("current_thread_id", None)
    ss.setdefault("selected_model_key", None)

ensure_state()


# ---------------- Yardımcılar -----------------
def light_gateway_alive() -> bool:
    try:
        return httpx.get(f"{API_URL}/health", timeout=2).status_code == 200
    except Exception:
        return False

def set_thread_preview(tid: str, dataurl: str):
    t = st.session_state.threads_local.setdefault(tid, {"history": [], "preview_dataurl": None})
    t["preview_dataurl"] = dataurl

def add_local_message(tid: str, role: str, text: str, render: Dict[str,Any] | None = None):
    """Mesajı state'e ekler; Streamlit mutation edge-case'lerini önlemek için kopya kullanır."""
    t = st.session_state.threads_local.setdefault(tid, {"history": [], "preview_dataurl": None})
    hist = list(t["history"])
    hist.append({
        "id": f"{role}-{time.time_ns()}",
        "role": role,
        "text": text,
        "render": render,
        "ts": time.time()
    })
    t["history"] = hist

def sorted_history(tid: str) -> List[Dict[str,Any]]:
    t = st.session_state.threads_local.get(tid, {"history": []})
    return sorted(t["history"], key=lambda x: x.get("ts", 0))

def show_bubble(role: str, text: str):
    import html
    cls = "user" if role == "user" else "assistant"
    st.markdown(
        f"<div class='chat-wrap {cls}'><div class='chat-bubble'>{html.escape(text)}</div></div>",
        unsafe_allow_html=True
    )

def to_image_from_dataurl(dataurl: str) -> Optional[Image.Image]:
    try:
        _, b64 = dataurl.split(",", 1)
        return Image.open(BytesIO(base64.b64decode(b64)))
    except Exception:
        return None


# ---------------- Sidebar -----------------
st.sidebar.header("Model ve Görev")

# Modelleri gateway'den çek
try:
    model_list = api.list_models()
except Exception as e:
    st.sidebar.error(f"Gateway bağlantısı yok: {e}")
    st.stop()

if not model_list:
    st.sidebar.error("Gateway üzerinde model tanımı bulunamadı.")
    st.stop()

title2model = {m["title"]: m for m in model_list}
sel_title = st.sidebar.selectbox("Model", list(title2model.keys()))
selected = title2model[sel_title]
st.session_state.selected_model_key = selected["key"]

if selected.get("notes"):
    st.sidebar.caption(selected["notes"])

ALL_TASKS = ["caption", "vqa", "ocr", "detection"]
allowed = selected.get("supported_tasks", []) or ["caption"]
allowed_tasks = [t for t in ALL_TASKS if t in allowed] or ["caption"]

default_task = cfg_app.get("ui", {}).get("default_task", "caption")
default_idx = 0 if default_task not in allowed_tasks else allowed_tasks.index(default_task)
task = st.sidebar.selectbox("Görev", allowed_tasks, index=default_idx)

with st.sidebar.expander("Gelişmiş"):
    max_new_tokens = st.number_input("max_new_tokens", min_value=1, max_value=4096,
                                     value=int(cfg_app.get("ui", {}).get("max_new_tokens", 256)))
    temperature = st.slider("temperature", 0.0, 1.0, float(cfg_app.get("ui", {}).get("temperature", 0.2)))
    top_p = st.slider("top_p", 0.0, 1.0, float(cfg_app.get("ui", {}).get("top_p", 1.0)))
    presence_penalty = st.slider("presence_penalty", -2.0, 2.0, float(cfg_app.get("ui", {}).get("presence_penalty", 0.0)))
    frequency_penalty = st.slider("frequency_penalty", -2.0, 2.0, float(cfg_app.get("ui", {}).get("frequency_penalty", 0.0)))

with st.sidebar.expander("Prompt davranışı"):
    free_mode = st.checkbox("Serbest mod (şablon ekleme)", value=False)
    json_strict = st.checkbox("Yapısal JSON iste (OCR/Detection)", value=True) if task in ("ocr","detection") else False

c1, c2 = st.sidebar.columns(2)
if c1.button("Başlat"):
    try:
        api.serve_model(selected["key"])
        st.sidebar.success("Model başlatıldı")
    except Exception as e:
        st.sidebar.error(f"Hata: {e}")
if c2.button("Durdur"):
    try:
        api.stop_model()
        st.sidebar.info("Durduruldu")
    except Exception as e:
        st.sidebar.error(f"Hata: {e}")

st.toast("Gateway aktif" if light_gateway_alive() else "Gateway kapalı",
         icon="✅" if light_gateway_alive() else "⚠️")


# ---------------- Main (chat) ----------------
st.markdown("### Sohbet")

# 1) Görsel yükleyip thread oluştur
up = st.file_uploader("Yeni görsel yükle (PNG/JPG) — yeni sohbet başlatır",
                      type=["png","jpg","jpeg"], accept_multiple_files=False)
if up is not None:
    try:
        b = up.read()
        res = api.create_thread(b, up.name)
        tid = res["thread_id"]
        st.session_state.current_thread_id = tid
        set_thread_preview(tid, res["preview_dataurl"])
        st.success("Görsel yüklendi; bu görsele bağlı sohbet başladı.")
    except Exception as e:
        st.error(f"Thread oluşturulamadı: {e}")

# 2) Aktif thread kontrol
tid = st.session_state.current_thread_id
if not tid:
    st.info("Başlamak için bir görsel yükleyin; ardından aşağıdan soru sorun.")
    st.stop()

# 3) Header: küçük önizleme
with st.container():
    col1, col2 = st.columns([1, 3])
    with col1:
        purl = st.session_state.threads_local.get(tid, {}).get("preview_dataurl") or ""
        im = to_image_from_dataurl(purl) if purl else None
        if im:
            st.image(im, caption="Aktif görsel", use_container_width=True)
        else:
            st.caption("Önizleme yok.")
    with col2:
        st.caption("Bu sohbet bu görsele bağlı. Yeni görsel yüklenince yeni sohbet başlar.")

# 4) Chat inputu ÖNCE işle (stabilite için kritik)
prompt = st.chat_input("Sorunuzu yazın… (aynı görsele birden çok soru)")
if prompt:
    # a) kullanıcı mesajını hemen ekle
    add_local_message(tid, "user", prompt)

    # b) gateway'e isteği gönder ve asistan yanıtını ekle
    payload = dict(
        prompt=prompt, task=task, free_mode=free_mode, json_strict=json_strict,
        gen_kwargs=dict(
            max_tokens=int(max_new_tokens),
            temperature=float(temperature),
            top_p=float(top_p),
            presence_penalty=float(presence_penalty),
            frequency_penalty=float(frequency_penalty),
        ),
    )
    with st.spinner("Yanıt üretiliyor…"):
        try:
            resp = api.chat_turn(tid, payload)
        except Exception as e:
            add_local_message(tid, "assistant", f"Hata: {e}")
        else:
            if isinstance(resp, dict) and ("annotated_png_b64" in resp or "boxes" in resp):
                txt = resp.get("text", "")
                render = {
                    "annotated_png_b64": resp.get("annotated_png_b64"),
                    "boxes": resp.get("boxes")
                }
                add_local_message(tid, "assistant", txt or " ", render=render)
            else:
                txt = resp.get("text", str(resp)) if isinstance(resp, dict) else str(resp)
                add_local_message(tid, "assistant", txt)

# 5) TÜM geçmişi ts'e göre sıralı render et (kullanıcı sağ, asistan sol)
for m in sorted_history(tid):
    show_bubble(m["role"], m["text"])
    if m["role"] == "assistant" and isinstance(m.get("render"), dict):
        r = m["render"]
        if r.get("annotated_png_b64"):
            try:
                st.image(Image.open(BytesIO(base64.b64decode(r["annotated_png_b64"]))), caption="Kutular")
            except Exception:
                pass
        if r.get("boxes"):
            st.json(r["boxes"])

# 6) Araçlar
cL, cR = st.columns(2)
with cL:
    if st.button("Bu sohbeti sıfırla (aynı görsel)"):
        st.session_state.threads_local[tid]["history"] = []
        st.rerun()
with cR:
    if st.button("Tüm sohbetleri temizle"):
        st.session_state.threads_local = {}
        st.session_state.current_thread_id = None
        st.rerun()
