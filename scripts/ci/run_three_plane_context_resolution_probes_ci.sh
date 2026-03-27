#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

python3 - <<'PY'
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

protocol_root = Path.cwd().resolve()
repo_root = protocol_root.parent
sys.path.insert(0, str((protocol_root / "scripts").resolve()))

from report_three_plane_status import _canonicalize_three_plane_cli_paths

args = argparse.Namespace(
    catalog=".identity/catalog.local.yaml",
    repo_catalog="identity/catalog/identities.yaml",
)

os.chdir(repo_root)
catalog_path, repo_catalog_path = _canonicalize_three_plane_cli_paths(args)
expected_catalog_path = (repo_root / ".identity/catalog.local.yaml").resolve()
expected_repo_catalog_path = (protocol_root / "identity/catalog/identities.yaml").resolve()
wrong_protocol_cwd_catalog_path = (protocol_root / ".identity/catalog.local.yaml").resolve()

assert catalog_path == expected_catalog_path, {
    "catalog_path": str(catalog_path),
    "expected_catalog_path": str(expected_catalog_path),
}
assert repo_catalog_path == expected_repo_catalog_path, {
    "repo_catalog_path": str(repo_catalog_path),
    "expected_repo_catalog_path": str(expected_repo_catalog_path),
}
assert str(Path(args.catalog)).startswith("/"), args.catalog
assert str(Path(args.repo_catalog)).startswith("/"), args.repo_catalog
assert catalog_path != wrong_protocol_cwd_catalog_path, {
    "catalog_path": str(catalog_path),
    "wrong_protocol_cwd_catalog_path": str(wrong_protocol_cwd_catalog_path),
}

probe_cmd = [
    "python3",
    "scripts/validate_fixture_runtime_boundary.py",
    "--identity-id",
    "base-repo-closure-orchestrator",
    "--catalog",
    args.catalog,
    "--repo-catalog",
    args.repo_catalog,
    "--operation",
    "three-plane",
    "--json-only",
]
probe = subprocess.run(
    probe_cmd,
    cwd=protocol_root,
    text=True,
    capture_output=True,
    check=False,
)
assert probe.returncode == 0, {
    "probe_cmd": probe_cmd,
    "stdout": probe.stdout,
    "stderr": probe.stderr,
}

payload = json.loads(probe.stdout)
assert payload["catalog_path"] == str(expected_catalog_path), payload
assert str(wrong_protocol_cwd_catalog_path) not in (probe.stdout + probe.stderr), {
    "stdout": probe.stdout,
    "stderr": probe.stderr,
}

print(
    json.dumps(
        {
            "three_plane_context_resolution_probe_status": "PASS_REQUIRED",
            "catalog_path": str(catalog_path),
            "repo_catalog_path": str(repo_catalog_path),
            "wrong_protocol_cwd_catalog_path": str(wrong_protocol_cwd_catalog_path),
            "validator_catalog_path": payload["catalog_path"],
        },
        ensure_ascii=False,
    )
)
PY

echo "[PASS] three-plane context resolution probes passed"
