#!/usr/bin/env python3
import sys, requests
URL = "http://localhost:9000/health"
try:
    r = requests.get(URL, timeout=2)
    r.raise_for_status()
    print("gateway alive:", r.json())
except Exception as e:
    print("gateway dead:", e)
    sys.exit(1)