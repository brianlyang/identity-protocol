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
cp scripts/render_control_plane_status.py "$tmpdir/scripts/"
cp scripts/render_control_plane_budget.py "$tmpdir/scripts/"
cp scripts/render_identity_context_continuity_bundle.py "$tmpdir/scripts/"
cp scripts/render_identity_context_reentry_answers.py "$tmpdir/scripts/"
cp docs/governance/identity-v1.6x-release-closure-governance.md "$tmpdir/docs/governance/"
cp docs/review/protocol-remediation-audit-ledger-v1.6x-release-closure.md "$tmpdir/docs/review/"
cp docs/release/identity-v1.6x-release-closure-summary.md "$tmpdir/docs/release/"
cp docs/governance/identity-codex-launcher-governance-v1.6.14.md "$tmpdir/docs/governance/"
cp docs/review/protocol-remediation-audit-ledger-v1.6.14-identity-codex-launcher.md "$tmpdir/docs/review/"
cp docs/governance/github-native-control-plane-specialization-v1.6.3.md "$tmpdir/docs/governance/"
cp docs/review/protocol-remediation-audit-ledger-v1.6.3.md "$tmpdir/docs/review/"
cp docs/governance/identity-context-continuity-governance-v1.6.16.md "$tmpdir/docs/governance/"
cp docs/review/protocol-remediation-audit-ledger-v1.6.16-identity-context-continuity.md "$tmpdir/docs/review/"

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

cp scripts/render_control_plane_status.py "$tmpdir/scripts/"
cp docs/governance/github-native-control-plane-specialization-v1.6.3.md "$tmpdir/docs/governance/"

python3 - "$tmpdir" <<'PY'
from pathlib import Path
import sys

tmpdir = Path(sys.argv[1])
target = tmpdir / "scripts" / "render_control_plane_status.py"
needle = '        "surface_governance": build_governed_runtime_summary_surface_payload("control_plane_status_artifact"),'
text = target.read_text(encoding="utf-8")
if needle not in text:
    raise SystemExit("probe setup failed: expected control-plane status governance assignment missing")
target.write_text(text.replace(needle, "", 1), encoding="utf-8")
PY

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-control-plane-script.json; then
  echo "[FAIL] negative control-plane status script drift probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative control-plane status script drift probe fail-closed as expected"

cp scripts/render_control_plane_status.py "$tmpdir/scripts/"
cp docs/governance/github-native-control-plane-specialization-v1.6.3.md "$tmpdir/docs/governance/"

python3 - "$tmpdir" <<'PY'
from pathlib import Path
import sys

tmpdir = Path(sys.argv[1])
target = tmpdir / "docs" / "governance" / "github-native-control-plane-specialization-v1.6.3.md"
needle = "The renderer must self-describe this bounded authority in machine-readable payload form."
text = target.read_text(encoding="utf-8")
if needle not in text:
    raise SystemExit("probe setup failed: expected control-plane governance marker missing")
target.write_text(text.replace(needle, "", 1), encoding="utf-8")
PY

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-control-plane-doc.json; then
  echo "[FAIL] negative control-plane status doc anchor probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative control-plane status doc anchor probe fail-closed as expected"

cp scripts/render_control_plane_budget.py "$tmpdir/scripts/"
cp docs/governance/github-native-control-plane-specialization-v1.6.3.md "$tmpdir/docs/governance/"

python3 - "$tmpdir" <<'PY'
from pathlib import Path
import sys

tmpdir = Path(sys.argv[1])
target = tmpdir / "scripts" / "render_control_plane_budget.py"
needle = '    payload["surface_governance"] = build_governed_runtime_summary_surface_payload("control_plane_budget_artifact")'
text = target.read_text(encoding="utf-8")
if needle not in text:
    raise SystemExit("probe setup failed: expected control-plane budget governance assignment missing")
target.write_text(text.replace(needle, "", 1), encoding="utf-8")
PY

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-budget-script.json; then
  echo "[FAIL] negative control-plane budget script drift probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative control-plane budget script drift probe fail-closed as expected"

cp scripts/render_control_plane_budget.py "$tmpdir/scripts/"
cp docs/governance/github-native-control-plane-specialization-v1.6.3.md "$tmpdir/docs/governance/"

python3 - "$tmpdir" <<'PY'
from pathlib import Path
import sys

tmpdir = Path(sys.argv[1])
target = tmpdir / "docs" / "governance" / "github-native-control-plane-specialization-v1.6.3.md"
needle = "`scripts/render_control_plane_budget.py` remains a machine control-plane budget summary surface on an outer control-plane layer."
text = target.read_text(encoding="utf-8")
if needle not in text:
    raise SystemExit("probe setup failed: expected control-plane budget governance marker missing")
target.write_text(text.replace(needle, "", 1), encoding="utf-8")
PY

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-budget-doc.json; then
  echo "[FAIL] negative control-plane budget doc anchor probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative control-plane budget doc anchor probe fail-closed as expected"

cp scripts/render_identity_context_continuity_bundle.py "$tmpdir/scripts/"
cp docs/governance/identity-context-continuity-governance-v1.6.16.md "$tmpdir/docs/governance/"

python3 - "$tmpdir" <<'PY'
from pathlib import Path
import sys

tmpdir = Path(sys.argv[1])
target = tmpdir / "scripts" / "render_identity_context_continuity_bundle.py"
needle = '        "surface_governance": build_governed_runtime_summary_surface_payload('
text = target.read_text(encoding="utf-8")
if needle not in text:
    raise SystemExit("probe setup failed: expected continuity bundle governance assignment missing")
target.write_text(text.replace(needle, '        "surface_governance_removed": build_governed_runtime_summary_surface_payload(', 1), encoding="utf-8")
PY

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-continuity-script.json; then
  echo "[FAIL] negative continuity bundle script drift probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative continuity bundle script drift probe fail-closed as expected"

cp scripts/render_identity_context_continuity_bundle.py "$tmpdir/scripts/"
cp docs/governance/identity-context-continuity-governance-v1.6.16.md "$tmpdir/docs/governance/"

python3 - "$tmpdir" <<'PY'
from pathlib import Path
import sys

tmpdir = Path(sys.argv[1])
target = tmpdir / "docs" / "governance" / "identity-context-continuity-governance-v1.6.16.md"
needle = "Both renderers must self-describe this bounded authority in machine-readable payload form."
text = target.read_text(encoding="utf-8")
if needle not in text:
    raise SystemExit("probe setup failed: expected continuity governance marker missing")
target.write_text(text.replace(needle, "", 1), encoding="utf-8")
PY

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-continuity-doc.json; then
  echo "[FAIL] negative continuity bundle doc anchor probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative continuity bundle doc anchor probe fail-closed as expected"

cp scripts/render_identity_context_reentry_answers.py "$tmpdir/scripts/"
cp docs/review/protocol-remediation-audit-ledger-v1.6.16-identity-context-continuity.md "$tmpdir/docs/review/"

python3 - "$tmpdir" <<'PY'
from pathlib import Path
import sys

tmpdir = Path(sys.argv[1])
target = tmpdir / "scripts" / "render_identity_context_reentry_answers.py"
needle = '        "surface_governance": build_governed_runtime_summary_surface_payload('
text = target.read_text(encoding="utf-8")
if needle not in text:
    raise SystemExit("probe setup failed: expected reentry answer governance assignment missing")
target.write_text(text.replace(needle, '        "surface_governance_removed": build_governed_runtime_summary_surface_payload(', 1), encoding="utf-8")
PY

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-reentry-script.json; then
  echo "[FAIL] negative reentry answer script drift probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative reentry answer script drift probe fail-closed as expected"

cp scripts/render_identity_context_reentry_answers.py "$tmpdir/scripts/"
cp docs/review/protocol-remediation-audit-ledger-v1.6.16-identity-context-continuity.md "$tmpdir/docs/review/"

python3 - "$tmpdir" <<'PY'
from pathlib import Path
import sys

tmpdir = Path(sys.argv[1])
target = tmpdir / "docs" / "review" / "protocol-remediation-audit-ledger-v1.6.16-identity-context-continuity.md"
needle = "Neither surface may become a new terminal command family, thread-UUID lookup authority, or raw-transcript authority."
text = target.read_text(encoding="utf-8")
if needle not in text:
    raise SystemExit("probe setup failed: expected reentry answer review marker missing")
target.write_text(text.replace(needle, "", 1), encoding="utf-8")
PY

if python3 scripts/validate_runtime_summary_surface_governance.py --repo-root "$tmpdir" --json-only >/tmp/runtime-summary-surface-governance-negative-reentry-doc.json; then
  echo "[FAIL] negative reentry answer doc anchor probe unexpectedly passed"
  exit 1
fi
echo "[PASS] negative reentry answer doc anchor probe fail-closed as expected"
