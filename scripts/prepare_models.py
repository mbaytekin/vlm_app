#!/usr/bin/env python3
import argparse, os, sys, pathlib, socket, yaml
from typing import Dict, Any, List, Tuple

# .env yükle
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# huggingface_hub
try:
    from huggingface_hub import snapshot_download
except Exception:
    snapshot_download = None

ROOT = pathlib.Path(__file__).resolve().parents[1]
CFG_PATH = ROOT / "configs" / "models.yaml"

def load_cfg() -> Dict[str, Any]:
    if not CFG_PATH.exists():
        print(f"[error] config yok: {CFG_PATH}", file=sys.stderr); sys.exit(1)
    return yaml.safe_load(CFG_PATH.read_text())

def has_internet(timeout: float = 2.5) -> bool:
    try:
        socket.create_connection(("huggingface.co", 443), timeout=timeout)
        return True
    except OSError:
        return False

def is_dir_nonempty(p: pathlib.Path) -> bool:
    return p.exists() and p.is_dir() and any(p.iterdir())

def ensure_local_path(model: Dict[str, Any]) -> pathlib.Path:
    lp = model.get("local_path")
    return ((ROOT / lp) if lp else (ROOT / "models" / model["key"])).resolve()

def download_model(hf_id: str, local_dir: pathlib.Path, token: str | None, force: bool) -> Tuple[bool, str]:
    if snapshot_download is None:
        return False, "huggingface_hub kurulu değil (pip install huggingface_hub)"
    if is_dir_nonempty(local_dir) and not force:
        return True, f"zaten mevcut: {local_dir}"
    local_dir.parent.mkdir(parents=True, exist_ok=True)
    try:
        kwargs = {
            "repo_id": hf_id,
            "local_dir": str(local_dir),
            "local_dir_use_symlinks": False,
        }
        # sadece varsa token ver; yoksa hiç verme (public repo’lar tokensız çalışır)
        if token:
            kwargs["token"] = token
        snapshot_download(**kwargs)
        return True, f"indirildi → {local_dir}"
    except Exception as e:
        return False, f"indirme hatası: {e}"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keys", type=str, default="", help="virgüllü model key listesi")
    ap.add_argument("--force", action="store_true", help="mevcutsa da yeniden indir")
    args = ap.parse_args()

    cfg = load_cfg()
    models = cfg.get("models", [])
    wanted = set(k.strip() for k in args.keys.split(",")) if args.keys else None

    net = has_internet()
    hf_token = os.environ.get("HF_TOKEN")

    rows: List[Tuple[str, str, str]] = []

    for m in models:
        key = m["key"]
        if wanted and key not in wanted:
            continue
        hf_id = m["hf_id"]
        local_dir = ensure_local_path(m)

        if is_dir_nonempty(local_dir) and not args.force:
            rows.append((key, "OK (local)", str(local_dir))); continue

        if not net:
            rows.append((key, "MISSING (offline)", f"indirilemedi, beklenen: {local_dir}")); continue

        ok, note = download_model(hf_id, local_dir, hf_token, args.force)
        rows.append((key, "OK (downloaded)" if ok else "ERROR", note))

    print("\n== MODEL HAZIRLIK RAPORU ==")
    for k, status, note in rows:
        print(f"- {k:20s} | {status:16s} | {note}")
    print("\nBitti.")

if __name__ == "__main__":
    main()
