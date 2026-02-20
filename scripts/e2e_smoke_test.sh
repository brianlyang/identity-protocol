#!/usr/bin/env bash
set -euo pipefail

echo "[1/8] validate protocol"
python3 scripts/validate_identity_protocol.py

echo "[2/8] compile runtime brief"
python3 scripts/compile_identity_runtime.py

echo "[3/8] validate manifest semantics"
python3 scripts/validate_identity_manifest.py

echo "[4/8] test discovery contract"
python3 scripts/test_identity_discovery_contract.py >/tmp/identity_discovery_contract.protocol_repo.json

echo "[5/8] validate runtime ORRL contract"
python3 scripts/validate_identity_runtime_contract.py

echo "[6/8] validate update prereq baseline gate"
python3 scripts/validate_identity_upgrade_prereq.py --identity-id store-manager

echo "[7/8] validate learning-loop linkage (reasoning + rulebook)"
python3 scripts/validate_identity_learning_loop.py --run-report identity/runtime/examples/store-manager-learning-sample.json

echo "[8/8] ensure compile is stable"
python3 scripts/compile_identity_runtime.py >/dev/null

echo "E2E smoke test PASSED"
