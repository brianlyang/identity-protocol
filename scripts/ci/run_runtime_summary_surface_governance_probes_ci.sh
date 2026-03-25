#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$repo_root"

echo "[INFO] positive: runtime summary surface governance validator"
python3 scripts/validate_runtime_summary_surface_governance.py --json-only >/tmp/runtime-summary-surface-governance-positive.json

tmpdir="$(mktemp -d)"
trap 'rm -rf "$tmpdir"' EXIT

mkdir -p "$tmpdir/scripts" "$tmpdir/docs/governance" "$tmpdir/docs/review" "$tmpdir/docs/release"
cp scripts/release_readiness_check.py "$tmpdir/scripts/"
cp scripts/report_three_plane_status.py "$tmpdir/scripts/"
cp scripts/render_protocol_lane_audit_summary.py "$tmpdir/scripts/"
cp scripts/full_identity_protocol_scan.py "$tmpdir/scripts/"
cp docs/governance/identity-v1.6x-release-closure-governance.md "$tmpdir/docs/governance/"
cp docs/review/protocol-remediation-audit-ledger-v1.6x-release-closure.md "$tmpdir/docs/review/"
cp docs/release/identity-v1.6x-release-closure-summary.md "$tmpdir/docs/release/"
cp docs/governance/identity-codex-launcher-governance-v1.6.14.md "$tmpdir/docs/governance/"
cp docs/review/protocol-remediation-audit-ledger-v1.6.14-identity-codex-launcher.md "$tmpdir/docs/review/"

python3 - "$tmpdir" <<'PY'
from pathlib import Path
import sys

tmpdir = Path(sys.argv[1])
target = tmpdir / "scripts" / "report_three_plane_status.py"
text = target.read_text(encoding="utf-8")
needle = 'payload["surface_governance"] = build_governed_runtime_summary_surface_payload("semantic_tuple_three_plane")'
if needle not in text:
    raise SystemExit("probe setup failed: expected three-plane surface governance assignment missing")
target.write_text(text.replace(needle, "", 1), encoding="utf-8")
PY

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-script.json; then
  echo "[FAIL] negative script drift probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative script drift probe fail-closed as expected"

cp scripts/release_readiness_check.py "$tmpdir/scripts/"
cp scripts/report_three_plane_status.py "$tmpdir/scripts/"

python3 - "$tmpdir" <<'PY'
from pathlib import Path
import sys

tmpdir = Path(sys.argv[1])
target = tmpdir / "docs" / "governance" / "identity-v1.6x-release-closure-governance.md"
needle = "All three surfaces must self-describe this boundary in machine-readable payload form rather than relying on operator memory."
text = target.read_text(encoding="utf-8")
if needle not in text:
    raise SystemExit("probe setup failed: expected governance marker missing")
target.write_text(text.replace(needle, "", 1), encoding="utf-8")
PY

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-doc.json; then
  echo "[FAIL] negative doc anchor probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative doc anchor probe fail-closed as expected"

cp scripts/render_protocol_lane_audit_summary.py "$tmpdir/scripts/"
cp docs/governance/identity-codex-launcher-governance-v1.6.14.md "$tmpdir/docs/governance/"
cp docs/review/protocol-remediation-audit-ledger-v1.6.14-identity-codex-launcher.md "$tmpdir/docs/review/"

python3 - "$tmpdir" <<'PY'
from pathlib import Path
import sys

tmpdir = Path(sys.argv[1])
target = tmpdir / "scripts" / "render_protocol_lane_audit_summary.py"
needle = '"surface_governance": build_governed_runtime_summary_surface_payload("protocol_lane_audit_summary"),'
text = target.read_text(encoding="utf-8")
if needle not in text:
    raise SystemExit("probe setup failed: expected lane audit summary governance assignment missing")
target.write_text(text.replace(needle, "", 1), encoding="utf-8")
PY

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-lane-script.json; then
  echo "[FAIL] negative lane-summary script drift probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative lane-summary script drift probe fail-closed as expected"

cp scripts/render_protocol_lane_audit_summary.py "$tmpdir/scripts/"

python3 - "$tmpdir" <<'PY'
from pathlib import Path
import sys

tmpdir = Path(sys.argv[1])
target = tmpdir / "docs" / "governance" / "identity-codex-launcher-governance-v1.6.14.md"
needle = "The renderer must self-describe this bounded authority in machine-readable payload form."
text = target.read_text(encoding="utf-8")
if needle not in text:
    raise SystemExit("probe setup failed: expected lane governance marker missing")
target.write_text(text.replace(needle, "", 1), encoding="utf-8")
PY

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-lane-doc.json; then
  echo "[FAIL] negative lane-summary doc anchor probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative lane-summary doc anchor probe fail-closed as expected"

cp scripts/full_identity_protocol_scan.py "$tmpdir/scripts/"
cp docs/governance/identity-v1.6x-release-closure-governance.md "$tmpdir/docs/governance/"

python3 - "$tmpdir" <<'PY'
from pathlib import Path
import sys

tmpdir = Path(sys.argv[1])
target = tmpdir / "scripts" / "full_identity_protocol_scan.py"
needle = 'payload["surface_governance"] = build_governed_runtime_summary_surface_payload("full_identity_protocol_scan_summary")'
text = target.read_text(encoding="utf-8")
if needle not in text:
    raise SystemExit("probe setup failed: expected full-scan governance assignment missing")
target.write_text(text.replace(needle, "", 1), encoding="utf-8")
PY

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-fullscan-script.json; then
  echo "[FAIL] negative full-scan script drift probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative full-scan script drift probe fail-closed as expected"

cp scripts/full_identity_protocol_scan.py "$tmpdir/scripts/"
cp docs/governance/identity-v1.6x-release-closure-governance.md "$tmpdir/docs/governance/"

python3 - "$tmpdir" <<'PY'
from pathlib import Path
import sys

tmpdir = Path(sys.argv[1])
target = tmpdir / "docs" / "governance" / "identity-v1.6x-release-closure-governance.md"
needle = "`scripts/full_identity_protocol_scan.py` remains a governed outer runtime-state scan summary surface and must not replace root-law owners, direct validator receipts, fleet-scope closure matrices, or historical replay authority."
text = target.read_text(encoding="utf-8")
if needle not in text:
    raise SystemExit("probe setup failed: expected full-scan governance marker missing")
target.write_text(text.replace(needle, "", 1), encoding="utf-8")
PY

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-fullscan-doc.json; then
  echo "[FAIL] negative full-scan doc anchor probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative full-scan doc anchor probe fail-closed as expected"
