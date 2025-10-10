#!/usr/bin/env python3
import sys, requests
URL = "http://localhost:8000/v1/models"
try:
    r = requests.get(URL, timeout=2)
    r.raise_for_status()
    print("vLLM alive:", r.json().get("data", [])[:1], "...")
except Exception as e:
    print("vLLM dead:", e)
    sys.exit(1)
