#!/usr/bin/env bash
set -euo pipefail

echo "[1/6] validate protocol"
python3 scripts/validate_identity_protocol.py

echo "[2/6] compile runtime brief"
python3 scripts/compile_identity_runtime.py

echo "[3/6] validate manifest semantics"
python3 scripts/validate_identity_manifest.py

echo "[4/6] test discovery contract"
python3 scripts/test_identity_discovery_contract.py >/tmp/identity_discovery_contract.protocol_repo.json

echo "[5/6] validate runtime ORRL contract"
python3 scripts/validate_identity_runtime_contract.py

echo "[6/6] ensure compile is stable"
python3 scripts/compile_identity_runtime.py >/dev/null

echo "E2E smoke test PASSED"
