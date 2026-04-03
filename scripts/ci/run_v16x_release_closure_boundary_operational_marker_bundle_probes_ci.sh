#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

python3 "${REPO_ROOT}/scripts/release_closure_bundle_probe_runner.py" \
  --repo-root "${REPO_ROOT}" \
  --probe-id boundary_operational_marker
