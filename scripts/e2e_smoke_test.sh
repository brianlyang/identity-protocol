#!/usr/bin/env bash
set -euo pipefail

echo "[1/3] validate protocol"
python3 scripts/validate_identity_protocol.py

echo "[2/3] compile runtime brief"
python3 scripts/compile_identity_runtime.py

echo "[3/3] ensure compile is stable"
python3 scripts/compile_identity_runtime.py >/dev/null

echo "E2E smoke test PASSED"
