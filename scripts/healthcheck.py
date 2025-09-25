import os, requests

BASE = os.environ.get("OPENAI_API_BASE", "http://localhost:8000/v1")

def is_alive() -> bool:
    try:
        r = requests.get(f"{BASE}/models", timeout=2.5)
        return r.ok and "data" in r.json()
    except Exception:
        return False

if __name__ == "__main__":
    print("alive" if is_alive() else "dead")
