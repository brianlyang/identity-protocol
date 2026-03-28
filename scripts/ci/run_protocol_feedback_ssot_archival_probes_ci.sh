#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
cd "${REPO_ROOT}"

TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/protocol-feedback-ssot-archival-ci.XXXXXX")"
trap 'rm -rf "${TMP_DIR}"' EXIT

python3 - <<'PY' "${TMP_DIR}"
from __future__ import annotations

import json
import sys
from pathlib import Path

repo_root = Path.cwd().resolve()
sys.path.insert(0, str((repo_root / "scripts").resolve()))

from repair_protocol_feedback_ssot_archival import repair_protocol_feedback_ssot_archival

tmp_dir = Path(sys.argv[1]).resolve()
feedback_root = (tmp_dir / "runtime" / "protocol-feedback").resolve()
outbox_dir = (feedback_root / "outbox-to-protocol").resolve()
atomic_dir = (feedback_root / "atomic").resolve()
index_path = (feedback_root / "evidence-index" / "INDEX.md").resolve()
issues_dir = (feedback_root / "issues").resolve()

outbox_dir.mkdir(parents=True, exist_ok=True)
atomic_dir.mkdir(parents=True, exist_ok=True)
issues_dir.mkdir(parents=True, exist_ok=True)
index_path.parent.mkdir(parents=True, exist_ok=True)

(outbox_dir / "DISCOVERY_REQUIREDIZATION_RECEIPT_20260324-133602.json").write_text("{}\n", encoding="utf-8")
(atomic_dir / "pf-probe.batch.json").write_text(json.dumps({"transaction_id": "pf-probe"}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(atomic_dir / "pf-probe.index.json").write_text(json.dumps({"transaction_id": "pf-probe"}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(atomic_dir / "pf-probe.receipt.json").write_text(json.dumps({"transaction_id": "pf-probe"}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(issues_dir / "issue-1.md").write_text("# Issue\n\nNeed protocol closure.\n", encoding="utf-8")
index_path.write_text("# Protocol Feedback Evidence Index\n\n", encoding="utf-8")

preview = repair_protocol_feedback_ssot_archival(
    feedback_root=feedback_root,
    outbox_dir=outbox_dir,
    index_path=index_path,
    identity_id="probe-identity",
    catalog_path="/tmp/probe-catalog.yaml",
    batch_pattern="FEEDBACK_BATCH_*.md",
    activity_dirs=["issues"],
    apply=False,
)
assert preview["protocol_feedback_ssot_archival_repair_status"] == "FAIL_REQUIRED", preview
assert preview["error_code"] == "IP-GOV-FEEDBACK-001", preview
assert preview["triggered"] is True, preview

applied = repair_protocol_feedback_ssot_archival(
    feedback_root=feedback_root,
    outbox_dir=outbox_dir,
    index_path=index_path,
    identity_id="probe-identity",
    catalog_path="/tmp/probe-catalog.yaml",
    batch_pattern="FEEDBACK_BATCH_*.md",
    activity_dirs=["issues"],
    apply=True,
)
assert applied["protocol_feedback_ssot_archival_repair_status"] == "PASS_REQUIRED", applied
assert applied["materialized_batch_path"], applied
assert applied["materialized_receipt_path"], applied
assert applied["index_linked"] is True, applied

index_text = index_path.read_text(encoding="utf-8")
assert "FEEDBACK_BATCH_" in index_text, index_text
assert "PROTOCOL_FEEDBACK_RECEIPT_" in index_text, index_text

second_pass = repair_protocol_feedback_ssot_archival(
    feedback_root=feedback_root,
    outbox_dir=outbox_dir,
    index_path=index_path,
    identity_id="probe-identity",
    catalog_path="/tmp/probe-catalog.yaml",
    batch_pattern="FEEDBACK_BATCH_*.md",
    activity_dirs=["issues"],
    apply=True,
)
assert second_pass["protocol_feedback_ssot_archival_repair_status"] == "PASS_REQUIRED", second_pass
assert second_pass["batch_file_count_before"] >= 1, second_pass

print(
    json.dumps(
        {
            "protocol_feedback_ssot_archival_probe_status": "PASS_REQUIRED",
            "preview_status": preview["protocol_feedback_ssot_archival_repair_status"],
            "applied_status": applied["protocol_feedback_ssot_archival_repair_status"],
            "second_pass_status": second_pass["protocol_feedback_ssot_archival_repair_status"],
            "materialized_batch_path": applied["materialized_batch_path"],
        },
        ensure_ascii=False,
    )
)
PY

echo "[PASS] protocol-feedback ssot archival probes passed"
