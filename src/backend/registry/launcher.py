import os
import pathlib
import shlex
import signal
import subprocess
import time
import re
import json

from src.shared.config import get_models_config

# .env yükle (HF_TOKEN vb.)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

ROOT = pathlib.Path(__file__).resolve().parents[3]
PIDFILE = ROOT / "vllm.pid"

def _dir_nonempty(p: pathlib.Path) -> bool:
    return p.exists() and p.is_dir() and any(p.iterdir())

def stop():
    if PIDFILE.exists():
        try:
            pid = int(PIDFILE.read_text().strip())
            os.kill(pid, signal.SIGTERM)
            time.sleep(0.8)
        except Exception:
            pass
        try:
            PIDFILE.unlink()
        except Exception:
            pass

def _to_json_limit(s: str) -> str:
    """image=1 gibi değerleri {'image':1} JSON'a çevir; zaten JSON ise dokunma."""
    if not s:
        return '{"image":1}'
    s = s.strip()
    if s.startswith("{") and s.endswith("}"):
        return s
    m = re.match(r'\s*([A-Za-z_]+)\s*[:=]\s*(\d+)\s*$', s)
    if m:
        k, v = m.group(1), int(m.group(2))
        return json.dumps({k: v})
    return '{"image":1}'

def _pick_model_source(model: dict) -> str:
    """
    Öncelik: explicit local_path (var/dolu) → models/<key> (var/dolu) → hf_id
    """
    # 1) explicit local_path
    lp = model.get("local_path")
    if lp:
        p = (ROOT / lp).resolve()
        if _dir_nonempty(p):
            return str(p)
    # 2) varsayılan models/<key>
    fallback = (ROOT / "models" / model["key"]).resolve()
    if _dir_nonempty(fallback):
        return str(fallback)
    # 3) HF ID
    return model["hf_id"]

def start(model_key: str):
    cfg = get_models_config()
    defaults = cfg.get("defaults", {}) or {}
    models = cfg.get("models", []) or []
    model = None
    for m in models:
        if m["key"] == model_key:
            model = m
            break
    if model is None:
        raise RuntimeError(f"model bulunamadı: {model_key}")

    source = _pick_model_source(model)
    served = model.get("served_name")
    trust = "--trust-remote-code" if defaults.get("trust_remote_code", True) else ""
    maxlen = int(defaults.get("max_model_len", 8192))
    limitmm = _to_json_limit(defaults.get("limit_mm_per_prompt", '{"image":1}'))
    util = defaults.get("gpu_memory_utilization", 0.90)

    cmd = (
        f"vllm serve {shlex.quote(source)} "
        f"--host 0.0.0.0 --port 8000 {trust} "
        f"--max-model-len {maxlen} "
        f"--limit-mm-per-prompt '{limitmm}' "
        f"--gpu-memory-utilization {util}"
    )
    if served:
        cmd += f" --served-model-name {shlex.quote(served)}"

    env = os.environ.copy()
    if os.environ.get("HF_TOKEN"):
        env["HF_TOKEN"] = os.environ["HF_TOKEN"]

    print(f"[launcher] {cmd}")
    proc = subprocess.Popen(cmd, shell=True, cwd=str(ROOT), env=env)
    PIDFILE.write_text(str(proc.pid))
    return proc.pid
