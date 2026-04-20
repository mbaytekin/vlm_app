import os
import pathlib
import shlex
import signal
import subprocess
import time
import re
import json
import sys
from typing import Any

import requests

from shared.config import get_models_config

# .env yükle (HF_TOKEN vb.)
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

ROOT = pathlib.Path(__file__).resolve().parents[2]
PIDFILE = ROOT / "vllm.pid"
MODELFILE = ROOT / "vllm.model"

def _read_pid() -> int | None:
    if not PIDFILE.exists():
        return None
    try:
        return int(PIDFILE.read_text().strip())
    except Exception:
        return None

def _read_model_key() -> str | None:
    if not MODELFILE.exists():
        return None
    try:
        key = MODELFILE.read_text().strip()
        return key or None
    except Exception:
        return None

def _is_pid_running(pid: int | None) -> bool:
    if not pid:
        return False
    stat_path = pathlib.Path("/proc") / str(pid) / "stat"
    try:
        parts = stat_path.read_text().split()
        if len(parts) >= 3 and parts[2] == "Z":
            return False
    except Exception:
        pass
    try:
        os.kill(pid, 0)
        return True
    except Exception:
        return False

def _terminate_pid_group(pid: int):
    if not pid:
        return
    try:
        os.killpg(pid, signal.SIGTERM)
        time.sleep(0.6)
    except Exception:
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(0.6)
        except Exception:
            pass

    if _is_pid_running(pid):
        try:
            os.killpg(pid, signal.SIGKILL)
        except Exception:
            try:
                os.kill(pid, signal.SIGKILL)
            except Exception:
                pass

def _pids_listening_on_port(port: int) -> list[int]:
    try:
        out = subprocess.check_output(["ss", "-ltnp"], text=True, stderr=subprocess.DEVNULL)
    except Exception:
        return []
    pids: set[int] = set()
    for line in out.splitlines():
        if f":{port}" not in line:
            continue
        for m in re.finditer(r"pid=(\d+)", line):
            try:
                pids.add(int(m.group(1)))
            except Exception:
                continue
    return sorted(pids)

def _dir_nonempty(p: pathlib.Path) -> bool:
    return p.exists() and p.is_dir() and any(p.iterdir())

def _pick_source_from_path(base: pathlib.Path, model: dict) -> str | None:
    if not base.exists():
        return None
    if base.is_file():
        return str(base)
    if base.is_dir():
        mf = model.get("model_file")
        if mf:
            candidate = (base / str(mf)).resolve()
            if candidate.exists() and candidate.is_file():
                return str(candidate)
        if _dir_nonempty(base):
            return str(base)
    return None

def stop():
    pid = _read_pid()
    if pid:
        _terminate_pid_group(pid)

    # pidfile bozulmuşsa da 8000 portundaki vLLM sürecini temizle
    for p in _pids_listening_on_port(8000):
        if p != os.getpid():
            _terminate_pid_group(p)

    try:
        PIDFILE.unlink()
    except Exception:
        pass
    try:
        MODELFILE.unlink()
    except Exception:
        pass

def _to_json_limit(v: Any) -> str:
    """
    image=1 veya image=1,audio=1 gibi değerleri JSON'a çevirir.
    Dict veya JSON string verilirse olduğu gibi normalize eder.
    """
    if v is None:
        return '{"image":1}'
    if isinstance(v, dict):
        out: dict[str, int] = {}
        for k, raw in v.items():
            try:
                out[str(k)] = int(raw)
            except Exception:
                continue
        return json.dumps(out or {"image": 1})

    s = str(v).strip()
    if not s:
        return '{"image":1}'
    if s.startswith("{") and s.endswith("}"):
        try:
            loaded = json.loads(s)
            if isinstance(loaded, dict):
                out: dict[str, int] = {}
                for k, raw in loaded.items():
                    try:
                        out[str(k)] = int(raw)
                    except Exception:
                        continue
                return json.dumps(out or {"image": 1})
        except Exception:
            pass

    out: dict[str, int] = {}
    for chunk in s.split(","):
        m = re.match(r'\s*([A-Za-z_]+)\s*[:=]\s*(\d+)\s*$', chunk)
        if m:
            out[m.group(1)] = int(m.group(2))
    return json.dumps(out or {"image": 1})

def _pick_model_source(model: dict) -> str:
    """
    Öncelik: explicit local_path (var/dolu) → models/<key> (var/dolu) → hf_id
    """
    # 1) explicit local_path
    lp = model.get("local_path")
    if lp:
        p = (ROOT / lp).resolve()
        picked = _pick_source_from_path(p, model)
        if picked:
            return picked
    # 2) varsayılan models/<key>
    fallback = (ROOT / "models" / model["key"]).resolve()
    picked = _pick_source_from_path(fallback, model)
    if picked:
        return picked
    # 3) HF ID
    return model["hf_id"]

def _is_gemma4_gguf(model: dict) -> bool:
    load_format = str(model.get("load_format", "")).lower()
    if load_format != "gguf":
        return False
    text = " ".join(
        str(model.get(k, "")) for k in ("hf_id", "hf_config_path", "tokenizer", "model_file", "served_name")
    ).lower()
    return "gemma-4" in text or "gemma4" in text

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
    if _is_gemma4_gguf(model):
        raise RuntimeError(
            "Gemma4 GGUF vLLM tarafinda stabil degil. 'gemma4_e4b_it' modelini kullanin."
        )

    source = _pick_model_source(model)
    served = model.get("served_name")
    trust = "--trust-remote-code" if defaults.get("trust_remote_code", True) else ""
    maxlen = int(model.get("max_model_len", defaults.get("max_model_len", 8192)))
    limitmm = _to_json_limit(model.get("limit_mm_per_prompt", defaults.get("limit_mm_per_prompt", {"image": 1})))
    util = model.get("gpu_memory_utilization", defaults.get("gpu_memory_utilization", 0.90))

    vllm_exe = pathlib.Path(sys.executable).with_name("vllm")
    vllm_bin = str(vllm_exe) if vllm_exe.exists() else "vllm"
    vllm_cmd = f"{shlex.quote(vllm_bin)} serve"
    cmd = (
        f"{vllm_cmd} {shlex.quote(source)} "
        f"--host 0.0.0.0 --port 8000 {trust} "
        f"--max-model-len {maxlen} "
        f"--limit-mm-per-prompt '{limitmm}' "
        f"--gpu-memory-utilization {util}"
    )
    if served:
        cmd += f" --served-model-name {shlex.quote(served)}"
    if model.get("tokenizer"):
        cmd += f" --tokenizer {shlex.quote(str(model['tokenizer']))}"
    if model.get("hf_config_path"):
        cmd += f" --hf-config-path {shlex.quote(str(model['hf_config_path']))}"
    if model.get("config_format"):
        cmd += f" --config-format {shlex.quote(str(model['config_format']))}"
    if model.get("load_format"):
        cmd += f" --load-format {shlex.quote(str(model['load_format']))}"
    if model.get("dtype"):
        cmd += f" --dtype {shlex.quote(str(model['dtype']))}"
    if model.get("extra_serve_args"):
        extra = model["extra_serve_args"]
        if isinstance(extra, str):
            cmd += f" {extra}"
        elif isinstance(extra, list):
            cmd += " " + " ".join(shlex.quote(str(a)) for a in extra if str(a).strip())

    env = os.environ.copy()
    if os.environ.get("HF_TOKEN"):
        env["HF_TOKEN"] = os.environ["HF_TOKEN"]

    print(f"[launcher] {cmd}")
    proc = subprocess.Popen(f"exec {cmd}", shell=True, cwd=str(ROOT), env=env, start_new_session=True)
    PIDFILE.write_text(str(proc.pid))
    MODELFILE.write_text(model_key)
    return proc.pid

def status() -> dict[str, Any]:
    cfg = get_models_config()
    defaults = cfg.get("defaults", {}) or {}
    models = cfg.get("models", []) or []

    pid = _read_pid()
    pid_running = _is_pid_running(pid)
    model_key = _read_model_key()
    model = next((m for m in models if m.get("key") == model_key), None)
    served_name = model.get("served_name") if model else None

    api_base = os.environ.get("OPENAI_API_BASE") or defaults.get("api_base") or "http://localhost:8000/v1"
    models_url = api_base.rstrip("/") + "/models"
    served_models: list[str] = []
    error = None

    try:
        r = requests.get(models_url, timeout=2)
        r.raise_for_status()
        data = r.json()
        served_models = [str(it.get("id")) for it in data.get("data", []) if isinstance(it, dict) and it.get("id")]
    except Exception as e:
        error = str(e)

    # pidfile stale kalmışsa, gerçek servis edilen modeli infer et
    if served_models and (not served_name or served_name not in served_models):
        for m in models:
            sn = m.get("served_name")
            if sn and sn in served_models:
                model_key = m.get("key")
                served_name = sn
                break

    running = bool(pid_running or served_models)
    if not pid_running:
        pid = None

    if running and not served_models:
        try:
            # son bir deneme: servis yeni açılıyorsa kısa gecikme olabilir
            time.sleep(0.4)
            r = requests.get(models_url, timeout=2)
            r.raise_for_status()
            data = r.json()
            served_models = [str(it.get("id")) for it in data.get("data", []) if isinstance(it, dict) and it.get("id")]
            error = None
        except Exception:
            pass

    ready = bool(running and served_name and served_name in served_models)

    return {
        "running": running,
        "ready": ready,
        "pid": pid if running else None,
        "model_key": model_key,
        "served_name": served_name,
        "served_models": served_models,
        "error": error,
        "runtime": "vllm" if running or model_key else None,
    }
