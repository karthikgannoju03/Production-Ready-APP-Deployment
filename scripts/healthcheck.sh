#!/usr/bin/env sh
set -eu

HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8000/health}"

python - <<'PY'
import json
import os
import sys
import urllib.request

url = os.environ.get("HEALTH_URL", "http://127.0.0.1:8000/health")

try:
    with urllib.request.urlopen(url, timeout=3) as resp:
        body = resp.read().decode("utf-8")
        data = json.loads(body)
except Exception:
    sys.exit(1)

status = data.get("status")
# Consider the service healthy only when dependencies are connected.
sys.exit(0 if status == "ok" else 1)
PY

