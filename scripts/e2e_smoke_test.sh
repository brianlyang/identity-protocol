#!/usr/bin/env bash
set -euo pipefail

echo "[1/9] validate protocol"
python3 scripts/validate_identity_protocol.py

echo "[2/9] compile runtime brief"
python3 scripts/compile_identity_runtime.py

echo "[3/9] validate manifest semantics"
python3 scripts/validate_identity_manifest.py

echo "[4/9] test discovery contract"
python3 scripts/test_identity_discovery_contract.py >/tmp/identity_discovery_contract.protocol_repo.json

echo "[5/9] validate runtime ORRL contract"
python3 scripts/validate_identity_runtime_contract.py

echo "[6/9] validate update prereq baseline gate"
python3 scripts/validate_identity_upgrade_prereq.py --identity-id store-manager

echo "[7/9] validate update lifecycle contract (skill-style trigger/patch/validate/replay)"
python3 scripts/validate_identity_update_lifecycle.py --identity-id store-manager

echo "[8/9] validate learning-loop linkage (reasoning + rulebook)"
python3 scripts/validate_identity_learning_loop.py --run-report identity/runtime/examples/store-manager-learning-sample.json

echo "[9/9] ensure compile is stable"
python3 scripts/compile_identity_runtime.py >/dev/null

echo "E2E smoke test PASSED"
