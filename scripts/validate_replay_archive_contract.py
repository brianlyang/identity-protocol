#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"

ERR_EXEC = "IP-RARCH-001"
ERR_EXPECTATION = "IP-RARCH-002"
ERR_OUTPUT_PARSE = "IP-RARCH-003"


@dataclass
class ReplayCase:
    case_id: str
    rq_id: str
    cmd: list[str]
    status_key: str
    expected_status: str
    expected_rc: int
    expected_error_code: str = ""


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _json_from_stdout(stdout: str) -> dict[str, Any]:
    text = (stdout or "").strip()
    if not text:
        raise ValueError("empty stdout")

    # json-only validators normally emit single-line json, but we still parse from tail safely.
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    for line in reversed(lines):
        if not line.startswith("{"):
            continue
        try:
            node = json.loads(line)
        except Exception:
            continue
        if isinstance(node, dict):
            return node

    # fallback: try full-text json parse
    node = json.loads(text)
    if not isinstance(node, dict):
        raise ValueError("stdout json is not object")
    return node


def _write_json(path: Path, doc: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _run_probe_required_skills(
    *,
    python_bin: str,
    scripts_dir: Path,
    catalog: str,
    identity_id: str,
    operation: str,
    active_root: Path,
) -> list[str]:
    cmd = [
        python_bin,
        str(scripts_dir / "validate_v16_skill_path_integrity.py"),
        "--catalog",
        catalog,
        "--identity-id",
        identity_id,
        "--operation",
        operation,
        "--layout-mode",
        "custom",
        "--active-repo-root",
        str(active_root),
        "--active-runtime-root",
        str(active_root),
        "--json-only",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    try:
        payload = _json_from_stdout(proc.stdout)
    except Exception:
        return []

    rows = payload.get("required_skills")
    if not isinstance(rows, list):
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in rows:
        token = str(item or "").strip()
        if not token or token in seen:
            continue
        seen.add(token)
        out.append(token)
    return out


def _catalog_identity_meta(catalog_path: Path, identity_id: str) -> tuple[bool, bool]:
    try:
        doc = yaml.safe_load(catalog_path.read_text(encoding="utf-8")) or {}
    except Exception:
        return False, False
    rows = [x for x in (doc.get("identities") or []) if isinstance(x, dict)]
    row = next((x for x in rows if str(x.get("id", "")).strip() == identity_id), None)
    if not isinstance(row, dict):
        return False, False
    profile = str(row.get("profile", "")).strip().lower()
    runtime_mode = str(row.get("runtime_mode", "")).strip().lower()
    is_fixture = profile == "fixture" or runtime_mode == "demo_only"
    return True, is_fixture


def _build_cases(
    *,
    python_bin: str,
    scripts_dir: Path,
    catalog: str,
    identity_id: str,
    operation: str,
    tmp_root: Path,
) -> list[ReplayCase]:
    bundle_pos = tmp_root / "rq017_030_bundle_positive.json"
    bundle_neg_track = tmp_root / "rq017_bundle_negative_missing_track.json"
    bundle_neg_meta = tmp_root / "rq030_bundle_negative_missing_metadata.json"

    dedup_pos = tmp_root / "rq018_claims_positive.json"
    dedup_neg = tmp_root / "rq018_claims_negative_ambiguous.json"

    xwf_pos = tmp_root / "rq019_schema_positive.json"
    xwf_neg = tmp_root / "rq019_schema_negative_missing_field.json"

    skill_fixture = tmp_root / "skills" / "task14-fixture" / "SKILL.md"
    skill_fixture.parent.mkdir(parents=True, exist_ok=True)
    skill_fixture.write_text("# task14 fixture skill\n", encoding="utf-8")

    pin_receipt = tmp_root / "rq021_pin_receipt.json"

    _write_json(
        bundle_pos,
        {
            "cross_verification_bundle_id": "replay-task14-bundle-pos",
            "source_url_set": [
                "https://example.com/t1",
                "https://example.com/t2",
                "https://example.com/t3",
                "https://example.com/t4",
            ],
            "reference_timestamp_utc": "2026-03-06T12:00:00Z",
            "conflict_reconciliation_note": "none",
            "t1_status": STATUS_PASS_REQUIRED,
            "t2_status": STATUS_PASS_REQUIRED,
            "t3_status": STATUS_PASS_REQUIRED,
            "t4_status": STATUS_PASS_REQUIRED,
        },
    )
    _write_json(
        bundle_neg_track,
        {
            "cross_verification_bundle_id": "replay-task14-bundle-neg-track",
            "source_url_set": ["https://example.com/t1"],
            "reference_timestamp_utc": "2026-03-06T12:00:00Z",
            "conflict_reconciliation_note": "missing_t4",
            "t1_status": STATUS_PASS_REQUIRED,
            "t2_status": STATUS_PASS_REQUIRED,
            "t3_status": STATUS_PASS_REQUIRED,
        },
    )
    _write_json(
        bundle_neg_meta,
        {
            "cross_verification_bundle_id": "replay-task14-bundle-neg-meta",
            "source_url_set": [
                "https://example.com/t1",
                "https://example.com/t2",
                "https://example.com/t3",
                "https://example.com/t4",
            ],
            "reference_timestamp_utc": "2026-03-06T12:00:00Z",
            "t1_status": STATUS_PASS_REQUIRED,
            "t2_status": STATUS_PASS_REQUIRED,
            "t3_status": STATUS_PASS_REQUIRED,
            "t4_status": STATUS_PASS_REQUIRED,
        },
    )

    _write_json(
        dedup_pos,
        {
            "claims": [
                {
                    "run_id": "replay-task14-run-pos",
                    "earliest_claim_ts": "2026-03-06T10:00:00Z",
                    "stable_tiebreaker": "a",
                    "winner_id": "winner-a",
                },
                {
                    "run_id": "replay-task14-run-pos",
                    "earliest_claim_ts": "2026-03-06T10:01:00Z",
                    "stable_tiebreaker": "b",
                    "winner_id": "winner-b",
                },
                {
                    "run_id": "replay-task14-run-pos",
                    "earliest_claim_ts": "2026-03-06T10:02:00Z",
                    "stable_tiebreaker": "c",
                    "winner_id": "winner-c",
                },
            ]
        },
    )
    _write_json(
        dedup_neg,
        {
            "claims": [
                {
                    "run_id": "replay-task14-run-neg",
                    "earliest_claim_ts": "2026-03-06T10:00:00Z",
                    "stable_tiebreaker": "a",
                    "winner_id": "winner-a",
                },
                {
                    "run_id": "replay-task14-run-neg",
                    "earliest_claim_ts": "2026-03-06T10:00:00Z",
                    "stable_tiebreaker": "a",
                    "winner_id": "winner-b",
                },
            ]
        },
    )

    _write_json(
        xwf_pos,
        {
            "run_id": "replay-task14-xwf-pos",
            "route_action": "route:pinning-check",
            "quality_meta_state": "quality_ok",
            "dedup_state": "dedup_ok",
            "schema_version": "v1",
        },
    )
    _write_json(
        xwf_neg,
        {
            "run_id": "replay-task14-xwf-neg",
            "route_action": "route:pinning-check",
            "quality_meta_state": "quality_ok",
            "schema_version": "v1",
        },
    )

    required_skills = _run_probe_required_skills(
        python_bin=python_bin,
        scripts_dir=scripts_dir,
        catalog=catalog,
        identity_id=identity_id,
        operation=operation,
        active_root=tmp_root,
    )
    if not required_skills:
        required_skills = ["task14-skill"]

    skill_overrides_positive: list[str] = []
    for skill in required_skills:
        skill_overrides_positive.extend(["--skill-path", f"{skill}={skill_fixture}"])

    negative_skill_name = required_skills[0]
    skill_missing_path = tmp_root / "missing" / "SKILL.md"
    skill_overrides_negative: list[str] = []
    for skill in required_skills:
        target = skill_missing_path if skill == negative_skill_name else skill_fixture
        skill_overrides_negative.extend(["--skill-path", f"{skill}={target}"])

    return [
        ReplayCase(
            case_id="rq017_positive",
            rq_id="ASB16-RQ-017",
            cmd=[
                python_bin,
                str(scripts_dir / "validate_v16_intake_evidence_core.py"),
                "--mode",
                "intake_contract",
                "--catalog",
                catalog,
                "--identity-id",
                identity_id,
                "--bundle",
                str(bundle_pos),
                "--operation",
                operation,
                "--json-only",
            ],
            status_key="cross_verification_tracks_status",
            expected_status=STATUS_PASS_REQUIRED,
            expected_rc=0,
        ),
        ReplayCase(
            case_id="rq017_negative_missing_track",
            rq_id="ASB16-RQ-017",
            cmd=[
                python_bin,
                str(scripts_dir / "validate_v16_intake_evidence_core.py"),
                "--mode",
                "intake_contract",
                "--catalog",
                catalog,
                "--identity-id",
                identity_id,
                "--bundle",
                str(bundle_neg_track),
                "--operation",
                operation,
                "--json-only",
            ],
            status_key="cross_verification_tracks_status",
            expected_status=STATUS_FAIL_REQUIRED,
            expected_rc=1,
            expected_error_code="IP-INTAKE-EVID-002",
        ),
        ReplayCase(
            case_id="rq030_positive",
            rq_id="ASB16-RQ-030",
            cmd=[
                python_bin,
                str(scripts_dir / "validate_v16_intake_evidence_core.py"),
                "--mode",
                "promotion_gate",
                "--catalog",
                catalog,
                "--identity-id",
                identity_id,
                "--bundle",
                str(bundle_pos),
                "--operation",
                operation,
                "--json-only",
            ],
            status_key="intake_evidence_quorum_status",
            expected_status=STATUS_PASS_REQUIRED,
            expected_rc=0,
        ),
        ReplayCase(
            case_id="rq030_negative_missing_metadata",
            rq_id="ASB16-RQ-030",
            cmd=[
                python_bin,
                str(scripts_dir / "validate_v16_intake_evidence_core.py"),
                "--mode",
                "promotion_gate",
                "--catalog",
                catalog,
                "--identity-id",
                identity_id,
                "--bundle",
                str(bundle_neg_meta),
                "--operation",
                operation,
                "--json-only",
            ],
            status_key="intake_evidence_quorum_status",
            expected_status=STATUS_FAIL_REQUIRED,
            expected_rc=1,
            expected_error_code="IP-INTAKE-EVID-003",
        ),
        ReplayCase(
            case_id="rq018_positive",
            rq_id="ASB16-RQ-018",
            cmd=[
                python_bin,
                str(scripts_dir / "validate_v16_dedup_monotonicity.py"),
                "--catalog",
                catalog,
                "--identity-id",
                identity_id,
                "--claims",
                str(dedup_pos),
                "--run-id",
                "replay-task14-run-pos",
                "--parallel-claims",
                "3",
                "--operation",
                operation,
                "--json-only",
            ],
            status_key="monotonicity_status",
            expected_status=STATUS_PASS_REQUIRED,
            expected_rc=0,
        ),
        ReplayCase(
            case_id="rq018_negative_ambiguous",
            rq_id="ASB16-RQ-018",
            cmd=[
                python_bin,
                str(scripts_dir / "validate_v16_dedup_monotonicity.py"),
                "--catalog",
                catalog,
                "--identity-id",
                identity_id,
                "--claims",
                str(dedup_neg),
                "--run-id",
                "replay-task14-run-neg",
                "--parallel-claims",
                "2",
                "--operation",
                operation,
                "--json-only",
            ],
            status_key="monotonicity_status",
            expected_status=STATUS_FAIL_REQUIRED,
            expected_rc=1,
            expected_error_code="IP-DEDUP-003",
        ),
        ReplayCase(
            case_id="rq019_positive",
            rq_id="ASB16-RQ-019",
            cmd=[
                python_bin,
                str(scripts_dir / "validate_v16_cross_workflow_schema.py"),
                "--catalog",
                catalog,
                "--identity-id",
                identity_id,
                "--evidence",
                str(xwf_pos),
                "--operation",
                operation,
                "--json-only",
            ],
            status_key="cross_workflow_schema_status",
            expected_status=STATUS_PASS_REQUIRED,
            expected_rc=0,
        ),
        ReplayCase(
            case_id="rq019_negative_missing_field",
            rq_id="ASB16-RQ-019",
            cmd=[
                python_bin,
                str(scripts_dir / "validate_v16_cross_workflow_schema.py"),
                "--catalog",
                catalog,
                "--identity-id",
                identity_id,
                "--evidence",
                str(xwf_neg),
                "--operation",
                operation,
                "--json-only",
            ],
            status_key="cross_workflow_schema_status",
            expected_status=STATUS_FAIL_REQUIRED,
            expected_rc=1,
            expected_error_code="IP-XWF-002",
        ),
        ReplayCase(
            case_id="rq020_positive",
            rq_id="ASB16-RQ-020",
            cmd=[
                python_bin,
                str(scripts_dir / "validate_v16_skill_path_integrity.py"),
                "--catalog",
                catalog,
                "--identity-id",
                identity_id,
                "--operation",
                operation,
                "--layout-mode",
                "custom",
                "--active-repo-root",
                str(tmp_root),
                "--active-runtime-root",
                str(tmp_root),
                *skill_overrides_positive,
                "--json-only",
            ],
            status_key="path_integrity_status",
            expected_status=STATUS_PASS_REQUIRED,
            expected_rc=0,
        ),
        ReplayCase(
            case_id="rq020_negative_missing_skill_path",
            rq_id="ASB16-RQ-020",
            cmd=[
                python_bin,
                str(scripts_dir / "validate_v16_skill_path_integrity.py"),
                "--catalog",
                catalog,
                "--identity-id",
                identity_id,
                "--operation",
                operation,
                "--layout-mode",
                "custom",
                "--active-repo-root",
                str(tmp_root),
                "--active-runtime-root",
                str(tmp_root),
                *skill_overrides_negative,
                "--json-only",
            ],
            status_key="path_integrity_status",
            expected_status=STATUS_FAIL_REQUIRED,
            expected_rc=1,
            expected_error_code="IP-SPATH-001",
        ),
        ReplayCase(
            case_id="rq021_emit_receipt_positive",
            rq_id="ASB16-RQ-021",
            cmd=[
                python_bin,
                str(scripts_dir / "emit_route_version_pin_receipt.py"),
                "--catalog",
                catalog,
                "--identity-id",
                identity_id,
                "--operation",
                operation,
                "--route-endpoint",
                "/runtime/replay/task14",
                "--workflow-id",
                "wf-task14",
                "--workflow-publish-version",
                "v2026.03.06",
                "--pin-proof-ref",
                "proof://replay/task14",
                "--out",
                str(pin_receipt),
                "--json-only",
            ],
            status_key="pin_status",
            expected_status=STATUS_PASS_REQUIRED,
            expected_rc=0,
        ),
        ReplayCase(
            case_id="rq021_validate_positive",
            rq_id="ASB16-RQ-021",
            cmd=[
                python_bin,
                str(scripts_dir / "validate_route_version_pinning.py"),
                "--catalog",
                catalog,
                "--identity-id",
                identity_id,
                "--operation",
                operation,
                "--receipt",
                str(pin_receipt),
                "--expected-route-endpoint",
                "/runtime/replay/task14",
                "--expected-workflow-id",
                "wf-task14",
                "--expected-workflow-publish-version",
                "v2026.03.06",
                "--json-only",
            ],
            status_key="pin_status",
            expected_status=STATUS_PASS_REQUIRED,
            expected_rc=0,
        ),
        ReplayCase(
            case_id="rq021_validate_negative_mismatch",
            rq_id="ASB16-RQ-021",
            cmd=[
                python_bin,
                str(scripts_dir / "validate_route_version_pinning.py"),
                "--catalog",
                catalog,
                "--identity-id",
                identity_id,
                "--operation",
                operation,
                "--receipt",
                str(pin_receipt),
                "--expected-route-endpoint",
                "/runtime/replay/task14-mismatch",
                "--expected-workflow-id",
                "wf-task14",
                "--expected-workflow-publish-version",
                "v2026.03.06",
                "--json-only",
            ],
            status_key="pin_status",
            expected_status=STATUS_FAIL_REQUIRED,
            expected_rc=1,
            expected_error_code="IP-PIN-003",
        ),
        ReplayCase(
            case_id="rq022_positive",
            rq_id="ASB16-RQ-022",
            cmd=[
                python_bin,
                str(scripts_dir / "validate_fallback_taxonomy_normalization.py"),
                "--catalog",
                catalog,
                "--identity-id",
                identity_id,
                "--operation",
                operation,
                "--fallback-reason",
                "no_intent_signal",
                "--json-only",
            ],
            status_key="normalization_status",
            expected_status=STATUS_PASS_REQUIRED,
            expected_rc=0,
        ),
        ReplayCase(
            case_id="rq022_negative_unmapped",
            rq_id="ASB16-RQ-022",
            cmd=[
                python_bin,
                str(scripts_dir / "validate_fallback_taxonomy_normalization.py"),
                "--catalog",
                catalog,
                "--identity-id",
                identity_id,
                "--operation",
                operation,
                "--fallback-reason",
                "unknown_vendor_glitch",
                "--json-only",
            ],
            status_key="normalization_status",
            expected_status=STATUS_FAIL_REQUIRED,
            expected_rc=1,
            expected_error_code="IP-FBTAX-001",
        ),
    ]


def main() -> int:
    ap = argparse.ArgumentParser(description="Run deterministic positive+negative replay archive for Batch-6/7 contracts.")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection", "mutation"],
        default="validate",
    )
    ap.add_argument("--tmp-root", default="")
    ap.add_argument("--out", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    scripts_dir = Path(__file__).resolve().parent
    catalog_path = Path(args.catalog).expanduser().resolve()

    if not catalog_path.exists():
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(catalog_path),
            "operation": args.operation,
            "replay_archive_contract_status": STATUS_FAIL_REQUIRED,
            "error_code": ERR_EXEC,
            "stale_reasons": ["catalog_missing"],
            "cases": [],
        }
        _emit(payload, json_only=args.json_only)
        return 1

    found_identity, is_fixture_identity = _catalog_identity_meta(catalog_path, args.identity_id)
    if not found_identity:
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(catalog_path),
            "operation": args.operation,
            "replay_archive_contract_status": STATUS_FAIL_REQUIRED,
            "error_code": ERR_EXEC,
            "stale_reasons": ["identity_not_found_in_catalog"],
            "cases": [],
        }
        if args.out.strip():
            out_path = Path(args.out).expanduser().resolve()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            payload["out_path"] = str(out_path)
        _emit(payload, json_only=args.json_only)
        return 1

    if is_fixture_identity:
        payload = {
            "identity_id": args.identity_id,
            "catalog_path": str(catalog_path),
            "operation": args.operation,
            "replay_archive_contract_status": STATUS_SKIPPED_NOT_REQUIRED,
            "error_code": "",
            "stale_reasons": ["fixture_profile_scope"],
            "replay_case_total": 0,
            "replay_case_passed": 0,
            "replay_case_failed": 0,
            "cases": [],
            "evidence_ref": "",
        }
        if args.out.strip():
            out_path = Path(args.out).expanduser().resolve()
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            payload["out_path"] = str(out_path)
        _emit(payload, json_only=args.json_only)
        return 0

    if args.tmp_root.strip():
        tmp_root = Path(args.tmp_root).expanduser().resolve()
        tmp_root.mkdir(parents=True, exist_ok=True)
    else:
        tmp_root = Path(tempfile.mkdtemp(prefix="replay-archive-"))

    python_bin = sys.executable or "python3"
    cases = _build_cases(
        python_bin=python_bin,
        scripts_dir=scripts_dir,
        catalog=str(catalog_path),
        identity_id=args.identity_id,
        operation=args.operation,
        tmp_root=tmp_root,
    )

    case_rows: list[dict[str, Any]] = []
    failed_cases: list[str] = []

    for case in cases:
        proc = subprocess.run(case.cmd, capture_output=True, text=True, check=False)
        row: dict[str, Any] = {
            "case_id": case.case_id,
            "rq_id": case.rq_id,
            "command": " ".join(shlex.quote(x) for x in case.cmd),
            "returncode": int(proc.returncode),
            "expected_returncode": case.expected_rc,
            "status_key": case.status_key,
            "expected_status": case.expected_status,
            "expected_error_code": case.expected_error_code,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
            "observed_status": "",
            "observed_error_code": "",
            "case_status": STATUS_FAIL_REQUIRED,
            "case_error_code": "",
            "stale_reasons": [],
        }

        try:
            payload = _json_from_stdout(proc.stdout)
            row["observed_status"] = str(payload.get(case.status_key, "")).strip()
            row["observed_error_code"] = str(
                payload.get("error_code")
                or payload.get("normalization_error_code")
                or payload.get("pin_error_code")
                or payload.get("path_integrity_error_code")
                or ""
            ).strip()
        except Exception:
            row["case_error_code"] = ERR_OUTPUT_PARSE
            row["stale_reasons"] = ["json_output_parse_failed"]
            row["case_status"] = STATUS_FAIL_REQUIRED
            case_rows.append(row)
            failed_cases.append(case.case_id)
            continue

        reasons: list[str] = []
        case_error_code = ""

        if proc.returncode != case.expected_rc:
            reasons.append("unexpected_returncode")
            case_error_code = case_error_code or ERR_EXEC
        if row["observed_status"] != case.expected_status:
            reasons.append("unexpected_status")
            case_error_code = case_error_code or ERR_EXPECTATION
        if case.expected_error_code and row["observed_error_code"] != case.expected_error_code:
            reasons.append("unexpected_error_code")
            case_error_code = case_error_code or ERR_EXPECTATION

        if reasons:
            row["case_status"] = STATUS_FAIL_REQUIRED
            row["case_error_code"] = case_error_code
            row["stale_reasons"] = reasons
            failed_cases.append(case.case_id)
        else:
            row["case_status"] = STATUS_PASS_REQUIRED
            row["case_error_code"] = ""
            row["stale_reasons"] = []

        case_rows.append(row)

    pass_count = sum(1 for x in case_rows if x.get("case_status") == STATUS_PASS_REQUIRED)
    fail_count = len(case_rows) - pass_count
    overall_ok = fail_count == 0

    summary: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "operation": args.operation,
        "tmp_root": str(tmp_root),
        "replay_case_total": len(case_rows),
        "replay_case_passed": pass_count,
        "replay_case_failed": fail_count,
        "replay_archive_contract_status": STATUS_PASS_REQUIRED if overall_ok else STATUS_FAIL_REQUIRED,
        "error_code": "" if overall_ok else ERR_EXPECTATION,
        "stale_reasons": [] if overall_ok else [f"failed_case:{cid}" for cid in failed_cases],
        "cases": case_rows,
        "evidence_ref": str(tmp_root),
    }

    if args.out.strip():
        out_path = Path(args.out).expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        summary["out_path"] = str(out_path)

    _emit(summary, json_only=args.json_only)
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
