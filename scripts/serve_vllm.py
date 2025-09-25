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

# .env yükle
try:
  from dotenv import load_dotenv
  load_dotenv()
except Exception:
  pass

ROOT = pathlib.Path(__file__).resolve().parents[1]
PIDFILE = ROOT / "vllm.pid"
MODELS_YAML = ROOT / "configs" / "models.yaml"

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

def _to_json_limit(s: str) -> str:
  """image=1 veya image:1 gibi değerleri {'image':1} JSON'a çevir; zaten JSON ise dokunma."""
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

def _pick_source(model: dict) -> str:
  """Öncelik: explicit local_path (dolu) -> models/<key> (dolu) -> hf_id."""
  lp = model.get("local_path")
  if lp:
    p = (ROOT / lp).resolve()
    if _dir_nonempty(p):
      return str(p)
  p2 = (ROOT / "models" / model["key"]).resolve()
  if _dir_nonempty(p2):
    return str(p2)
  return model["hf_id"]

def stop_existing():
  if PIDFILE.exists():
    try:
      pid = int(PIDFILE.read_text().strip())
      os.kill(pid, signal.SIGTERM); time.sleep(0.8)
    except Exception:
      pass
    try:
      PIDFILE.unlink()
    except Exception:
      pass

def build_cmd(model_key: str):
  cfg = _load_cfg()
  defaults = cfg.get("defaults", {}) or {}
  model = _pick_model(cfg, model_key)

  source = _pick_source(model)
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
  proc = subprocess.Popen(cmd, shell=True, cwd=str(ROOT), env=env)
  PIDFILE.write_text(str(proc.pid))
  print(f"[serve_vllm] pid={proc.pid}")

if __name__ == "__main__":
  main()