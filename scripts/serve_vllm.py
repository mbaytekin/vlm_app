#!/usr/bin/env python3
"""
serve_vllm.py — vLLM'i yerel modeli ÖNCELEYEREK (local_path -> models/<key> -> hf_id) başlatır.
- limit-mm-per-prompt argümanını JSON biçimine ({"image":1}) normalize eder.
- .env (HF_TOKEN vb.) otomatik yüklenir.
Kullanım:
  python scripts/serve_vllm.py --model-key qwen2_5_vl_7b_awq
  # veya VLM_MODEL_KEY ortam değişkeniyle
"""
import argparse, os, pathlib, shlex, signal, subprocess, sys, time, yaml, re, json
from typing import Any

# .env yükle
try:
  from dotenv import load_dotenv
  load_dotenv()
except Exception:
  pass

ROOT = pathlib.Path(__file__).resolve().parents[1]
PIDFILE = ROOT / "vllm.pid"
MODELS_YAML = ROOT / "configs" / "models.yaml"

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
  pids = set()
  for line in out.splitlines():
    if f":{port}" not in line:
      continue
    for m in re.finditer(r"pid=(\d+)", line):
      try:
        pids.add(int(m.group(1)))
      except Exception:
        pass
  return sorted(pids)

def _load_cfg():
  if not MODELS_YAML.exists():
    print(f"[serve_vllm] config yok: {MODELS_YAML}", file=sys.stderr); sys.exit(1)
  return yaml.safe_load(MODELS_YAML.read_text())

def _pick_model(cfg: dict, model_key: str) -> dict:
  for m in cfg.get("models", []):
    if m["key"] == model_key:
      return m
  print(f"[serve_vllm] model bulunamadı: {model_key}", file=sys.stderr); sys.exit(1)

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

def _to_json_limit(v: Any) -> str:
  """image=1,audio=1 dahil farklı formatları JSON limit nesnesine çevir."""
  if v is None:
    return '{"image":1}'
  if isinstance(v, dict):
    out = {}
    for k, raw in v.items():
      try:
        out[str(k)] = int(raw)
      except Exception:
        pass
    return json.dumps(out or {"image": 1})

  s = str(v).strip()
  if not s:
    return '{"image":1}'
  if s.startswith("{") and s.endswith("}"):
    try:
      loaded = json.loads(s)
      if isinstance(loaded, dict):
        out = {}
        for k, raw in loaded.items():
          try:
            out[str(k)] = int(raw)
          except Exception:
            pass
        return json.dumps(out or {"image": 1})
    except Exception:
      pass

  out = {}
  for chunk in s.split(","):
    m = re.match(r'\s*([A-Za-z_]+)\s*[:=]\s*(\d+)\s*$', chunk)
    if m:
      out[m.group(1)] = int(m.group(2))
  return json.dumps(out or {"image": 1})

def _pick_source(model: dict) -> str:
  """Öncelik: explicit local_path (dolu) -> models/<key> (dolu) -> hf_id."""
  lp = model.get("local_path")
  if lp:
    p = (ROOT / lp).resolve()
    picked = _pick_source_from_path(p, model)
    if picked:
      return picked
  p2 = (ROOT / "models" / model["key"]).resolve()
  picked = _pick_source_from_path(p2, model)
  if picked:
    return picked
  return model["hf_id"]

def _is_gemma4_gguf(model: dict) -> bool:
  load_format = str(model.get("load_format", "")).lower()
  if load_format != "gguf":
    return False
  text = " ".join(
    str(model.get(k, "")) for k in ("hf_id", "hf_config_path", "tokenizer", "model_file", "served_name")
  ).lower()
  return "gemma-4" in text or "gemma4" in text

def stop_existing():
  if PIDFILE.exists():
    try:
      pid = int(PIDFILE.read_text().strip())
      _terminate_pid_group(pid)
    except Exception:
      pass
    try:
      PIDFILE.unlink()
    except Exception:
      pass
  for p in _pids_listening_on_port(8000):
    if p != os.getpid():
      _terminate_pid_group(p)

def build_cmd(model_key: str):
  cfg = _load_cfg()
  defaults = cfg.get("defaults", {}) or {}
  model = _pick_model(cfg, model_key)
  if _is_gemma4_gguf(model):
    print("[serve_vllm] Gemma4 GGUF vLLM tarafinda stabil degil. --model-key gemma4_e4b_it kullanin.", file=sys.stderr)
    sys.exit(1)

  source = _pick_source(model)
  served = model.get("served_name")
  trust = "--trust-remote-code" if defaults.get("trust_remote_code", True) else ""
  maxlen = int(model.get("max_model_len", defaults.get("max_model_len", 8192)))
  limitmm = _to_json_limit(model.get("limit_mm_per_prompt", defaults.get("limit_mm_per_prompt", {"image":1})))
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
  return cmd, env

def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("--model-key", default=os.environ.get("VLM_MODEL_KEY"))
  ap.add_argument("--restart", action="store_true", help="Varsa mevcut vLLM sürecini sonlandırır")
  args = ap.parse_args()

  if not args.model_key:
    print("[serve_vllm] --model-key gerekli (veya VLM_MODEL_KEY ortam değişkeni).", file=sys.stderr)
    sys.exit(1)

  if args.restart:
    stop_existing()

  cmd, env = build_cmd(args.model_key)
  print(f"[serve_vllm] starting: {cmd}")
  proc = subprocess.Popen(f"exec {cmd}", shell=True, cwd=str(ROOT), env=env, start_new_session=True)
  PIDFILE.write_text(str(proc.pid))
  print(f"[serve_vllm] pid={proc.pid}")

if __name__ == "__main__":
  main()
