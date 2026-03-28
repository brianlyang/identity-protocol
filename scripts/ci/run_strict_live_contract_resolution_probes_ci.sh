#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
TMP_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/strict-live-contract-resolution-ci.XXXXXX")"
trap 'rm -rf "${TMP_ROOT}"' EXIT

cd "${REPO_ROOT}"

python3 - <<'PY' "${TMP_ROOT}" "${REPO_ROOT}"
import json
import subprocess
import sys
from pathlib import Path

tmp_root = Path(sys.argv[1]).resolve()
repo_root = Path(sys.argv[2]).resolve()


def parse_json_line(stdout: str) -> dict:
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            return json.loads(line)
    raise AssertionError(f"json payload not found in stdout: {stdout}")


def run_validator(script_name: str, *, catalog: Path, identity_id: str) -> tuple[int, dict]:
    proc = subprocess.run(
        [
            "python3",
            str(repo_root / "scripts" / script_name),
            "--catalog",
            str(catalog),
            "--identity-id",
            identity_id,
            "--json-only",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    payload = parse_json_line(proc.stdout)
    return proc.returncode, payload


def create_pack(identity_id: str, *, root: Path) -> tuple[Path, Path]:
    catalog_path = root / "catalog.local.yaml"
    proc = subprocess.run(
        [
            "python3",
            str(repo_root / "scripts" / "create_identity_pack.py"),
            "--id",
            identity_id,
            "--title",
            "Strict Live Probe",
            "--description",
            "strict live contract resolution probe",
            "--pack-root",
            str(root / ".identity"),
            "--catalog",
            str(catalog_path),
            "--profile",
            "full-contract",
            "--register",
            "--activate",
            "--skip-bootstrap-check",
            "--skip-sample-bootstrap",
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    _ = proc.stdout
    pack_path = (root / ".identity" / identity_id).resolve()
    assert (pack_path / "CURRENT_TASK.json").exists(), pack_path
    return catalog_path, pack_path


probe_identity = "strict-live-probe"
legacy_root = (tmp_root / "legacy-locality").resolve()
catalog_path, probe_pack = create_pack(probe_identity, root=legacy_root)
legacy_task_path = probe_pack / "CURRENT_TASK.json"
legacy_task = json.loads(legacy_task_path.read_text(encoding="utf-8"))
legacy_task["capability_arbitration_contract"]["sample_report_path_pattern"] = "identity/runtime/examples/*capability-arbitration*.json"
legacy_task["experience_feedback_contract"]["sample_report_path_pattern"] = "identity/runtime/examples/*experience-feedback*.json"
legacy_task["experience_feedback_contract"]["positive_rulebook_path"] = "identity/runtime/rulebooks/positive.jsonl"
legacy_task["experience_feedback_contract"]["negative_rulebook_path"] = "identity/runtime/rulebooks/negative.jsonl"
legacy_task["experience_feedback_contract"]["feedback_log_path_pattern"] = "identity/runtime/logs/feedback/*.json"
legacy_task["knowledge_acquisition_contract"]["sample_report_path_pattern"] = "identity/runtime/examples/*knowledge-acquisition*.json"
legacy_task["trigger_regression_contract"]["sample_report_path_pattern"] = "identity/runtime/examples/*trigger-regression*.json"
legacy_task_path.write_text(json.dumps(legacy_task, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

validators = [
    ("validate_identity_capability_arbitration.py", "capability_arbitration_status", "capability_arbitration_report_missing"),
    ("validate_identity_experience_feedback.py", "experience_feedback_status", "experience_feedback_report_missing"),
    ("validate_identity_knowledge_acquisition.py", "knowledge_acquisition_status", "knowledge_acquisition_report_missing"),
    ("validate_identity_trigger_regression.py", "trigger_regression_status", "trigger_regression_report_missing"),
]

locality_rows: list[dict] = []
for script_name, status_field, missing_reason in validators:
    rc, payload = run_validator(script_name, catalog=catalog_path, identity_id=probe_identity)
    assert rc != 0, (script_name, payload)
    assert payload[status_field] == "FAIL_REQUIRED", (script_name, payload)
    selected_report_path = str(payload.get("selected_report_path", "")).strip()
    if selected_report_path:
        assert selected_report_path.startswith(str(probe_pack)), (script_name, payload)
    stale_reasons = set(payload.get("stale_reasons") or [])
    assert missing_reason in stale_reasons, (script_name, payload)
    assert not any(str(repo_root / "identity" / "runtime") in str(value) for value in payload.values()), (script_name, payload)
    locality_rows.append(
        {
            "script": script_name,
            "status_field": status_field,
            "selected_report_path": selected_report_path,
            "error_code": payload.get("error_code", ""),
        }
    )

(probe_pack / "runtime/examples").mkdir(parents=True, exist_ok=True)
(probe_pack / "runtime/rulebooks").mkdir(parents=True, exist_ok=True)

(probe_pack / "runtime/rulebooks/positive.jsonl").write_text(
    json.dumps(
        {
            "case_id": "pos-1",
            "layer": "routing",
            "pattern": "good_pattern",
            "action": "keep",
            "impact_score": 1,
            "replay_status": "PASS",
        },
        ensure_ascii=False,
    )
    + "\n",
    encoding="utf-8",
)
(probe_pack / "runtime/rulebooks/negative.jsonl").write_text(
    json.dumps(
        {
            "case_id": "neg-1",
            "layer": "routing",
            "pattern": "bad_pattern",
            "action": "block",
            "impact_score": 5,
            "replay_status": "PASS",
        },
        ensure_ascii=False,
    )
    + "\n",
    encoding="utf-8",
)
(probe_pack / "runtime/examples/strict-live-probe-capability-arbitration-sample.json").write_text(
    json.dumps(
        {
            "records": [
                {
                    "arbitration_id": "arb-1",
                    "task_id": "task-1",
                    "identity_id": probe_identity,
                    "conflict_pair": "judgement_vs_routing",
                    "inputs": {"route": "sample"},
                    "decision": "prefer_judgement",
                    "impact": "kept_route",
                    "rationale": "sample report for fail-close probe",
                    "decided_at": "2026-03-28T00:00:00Z",
                }
            ]
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)
(probe_pack / "runtime/examples/strict-live-probe-experience-feedback-sample.json").write_text(
    json.dumps(
        {
            "positive_updates": [
                {
                    "case_id": "exp-1",
                    "layer": "routing",
                    "pattern": "stable_pattern",
                    "action": "retain",
                    "impact_score": 1,
                    "replay_status": "PASS",
                }
            ],
            "negative_updates": [],
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)
(probe_pack / "runtime/examples/strict-live-probe-knowledge-acquisition-sample.json").write_text(
    json.dumps(
        {
            "records": [
                {
                    "claim": "official docs checked",
                    "source": "docs://official",
                    "source_level": "official_spec",
                    "confidence": "high",
                    "expiry": "2026-12-31",
                    "applies_to": "strict-live-probe",
                }
            ]
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)
(probe_pack / "runtime/examples/strict-live-probe-trigger-regression-sample.json").write_text(
    json.dumps(
        {
            "positive_cases": [
                {
                    "case_id": "trig-pos-1",
                    "input_summary": "positive",
                    "expected_route": "routeA",
                    "expected_trigger": True,
                    "observed_route": "routeA",
                    "observed_trigger": True,
                    "result": "PASS",
                    "notes": "positive pass",
                }
            ],
            "boundary_cases": [
                {
                    "case_id": "trig-boundary-1",
                    "input_summary": "boundary",
                    "expected_route": "routeB",
                    "expected_trigger": False,
                    "observed_route": "routeB",
                    "observed_trigger": False,
                    "result": "PASS",
                    "notes": "boundary pass",
                }
            ],
            "negative_cases": [
                {
                    "case_id": "trig-neg-1",
                    "input_summary": "negative",
                    "expected_route": "routeC",
                    "expected_trigger": False,
                    "observed_route": "routeC",
                    "observed_trigger": False,
                    "result": "PASS",
                    "notes": "negative pass for structural probe",
                }
            ],
            "summary": {
                "total_cases": 3,
                "pass_cases": 3,
                "fail_cases": 0,
                "overall_result": "PASS",
            },
        },
        ensure_ascii=False,
        indent=2,
    )
    + "\n",
    encoding="utf-8",
)

sample_failclose_rows: list[dict] = []
for script_name, status_field, _missing_reason in validators:
    rc, payload = run_validator(script_name, catalog=catalog_path, identity_id=probe_identity)
    assert rc != 0, (script_name, payload)
    assert payload[status_field] == "FAIL_REQUIRED", (script_name, payload)
    assert payload["semantic_contract_status"] == "PASS_REQUIRED", (script_name, payload)
    assert payload["strict_live_proof_status"] == "FAIL_REQUIRED", (script_name, payload)
    assert payload["evidence_origin"] == "sample", (script_name, payload)
    stale_reasons = set(payload.get("stale_reasons") or [])
    assert "strict_live_current_run_required_but_unproven" in stale_reasons, (script_name, payload)
    sample_failclose_rows.append(
        {
            "script": script_name,
            "status_field": status_field,
            "semantic_contract_status": payload["semantic_contract_status"],
            "strict_live_proof_status": payload["strict_live_proof_status"],
            "error_code": payload.get("error_code", ""),
        }
    )

abs_identity = "strict-live-backfill-probe"
absolute_root = (tmp_root / "absolute-canonicalization").resolve()
abs_catalog, abs_pack = create_pack(abs_identity, root=absolute_root)
absolute_task = json.loads((abs_pack / "CURRENT_TASK.json").read_text(encoding="utf-8"))
strict_keys = (
    "capability_arbitration_contract",
    "experience_feedback_contract",
    "knowledge_acquisition_contract",
    "trigger_regression_contract",
)
for key in strict_keys:
    node = absolute_task.get(key) or {}
    if not isinstance(node, dict):
        continue
    for field in (
        "sample_report_path_pattern",
        "positive_rulebook_path",
        "negative_rulebook_path",
        "feedback_log_path_pattern",
    ):
        raw = str(node.get(field, "")).strip()
        if raw.startswith("runtime/"):
            node[field] = str((abs_pack / raw).resolve())
    if key == "capability_arbitration_contract":
        allowlist = ((node.get("safe_auto_patch_surface") or {}).get("allowlist") or [])
        rewritten = []
        for item in allowlist:
            token = str(item).strip()
            if token.startswith("runtime/"):
                rewritten.append(str((abs_pack / token).resolve()))
            elif token == "TASK_HISTORY.md":
                rewritten.append(str((abs_pack / token).resolve()))
            elif token == "RULEBOOK.jsonl":
                rewritten.append(str((abs_pack / token).resolve()))
            else:
                rewritten.append(token)
        (node.get("safe_auto_patch_surface") or {})["allowlist"] = rewritten

(abs_pack / "CURRENT_TASK.json").write_text(
    json.dumps(absolute_task, ensure_ascii=False, indent=2) + "\n",
    encoding="utf-8",
)

repair = subprocess.run(
    [
        "python3",
        str(repo_root / "scripts" / "repair_contract_backfill.py"),
        "--catalog",
        str(abs_catalog),
        "--identity-id",
        abs_identity,
        "--apply",
        "--json-only",
    ],
    cwd=repo_root,
    capture_output=True,
    text=True,
    check=True,
)
repair_payload = parse_json_line(repair.stdout)
assert set(repair_payload["restored_strict_live_evidence_contract_keys"]) == set(strict_keys), repair_payload
repaired_task = json.loads((abs_pack / "CURRENT_TASK.json").read_text(encoding="utf-8"))
assert repaired_task["experience_feedback_contract"]["positive_rulebook_path"] == "runtime/rulebooks/positive.jsonl", repaired_task
assert repaired_task["experience_feedback_contract"]["negative_rulebook_path"] == "runtime/rulebooks/negative.jsonl", repaired_task
assert repaired_task["knowledge_acquisition_contract"]["sample_report_path_pattern"] == "runtime/examples/*knowledge-acquisition*.json", repaired_task
assert repaired_task["trigger_regression_contract"]["sample_report_path_pattern"] == "runtime/examples/*trigger-regression*.json", repaired_task
assert repaired_task["capability_arbitration_contract"]["sample_report_path_pattern"] == "runtime/examples/*capability-arbitration*.json", repaired_task
assert repaired_task["capability_arbitration_contract"]["safe_auto_patch_surface"]["allowlist"] == [
    "runtime/rulebooks/*",
    "TASK_HISTORY.md",
    "runtime/logs/*",
    "RULEBOOK.jsonl",
], repaired_task

print(
    json.dumps(
        {
            "strict_live_contract_resolution_probe_status": "PASS_REQUIRED",
            "locality_false_green_block_status": "PASS_REQUIRED",
            "sample_green_failclose_status": "PASS_REQUIRED",
            "backfill_canonicalization_status": "PASS_REQUIRED",
            "validator_probe_rows": locality_rows,
            "sample_failclose_rows": sample_failclose_rows,
            "repair_restored_keys": repair_payload["restored_strict_live_evidence_contract_keys"],
        },
        ensure_ascii=False,
    )
)
PY

echo "[PASS] strict-live contract resolution probes passed"
