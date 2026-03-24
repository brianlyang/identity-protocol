#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path
from typing import Any

import yaml
from strict_live_evidence_resolution_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    derive_strict_live_evidence_projection,
    derive_strict_live_operational_projection,
    emit_payload,
    resolve_preferred_strict_live_report,
)

REQ_RUNTIME_KEYS = [
    "required",
    "required_suites",
    "result_enum",
    "sample_report_path_pattern",
    "fail_action",
]
REQ_SUITES = ["positive_cases", "boundary_cases", "negative_cases"]
REQ_CASE_FIELDS = [
    "case_id",
    "input_summary",
    "expected_route",
    "expected_trigger",
    "observed_route",
    "observed_trigger",
    "result",
    "notes",
]
STATUS_FIELD = "trigger_regression_status"
ERR_TASK = "IP-TRIG-001"
ERR_REPORT = "IP-TRIG-002"


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be object: {path}")
    return data


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_current_task(catalog_path: Path, identity_id: str) -> Path:
    catalog = _load_yaml(catalog_path)
    identities = catalog.get("identities") or []
    target = next((x for x in identities if str((x or {}).get("id", "")).strip() == identity_id), None)
    if not target:
        raise FileNotFoundError(f"identity id not found in catalog: {identity_id}")

    pack_path = str((target or {}).get("pack_path", "")).strip()
    if pack_path:
        raw = Path(pack_path).expanduser()
        candidates: list[Path] = []
        if raw.is_absolute():
            candidates.append(raw.resolve())
        else:
            candidates.append((catalog_path.parent / raw).resolve())
            if catalog_path.parent.parent != catalog_path.parent:
                candidates.append((catalog_path.parent.parent / raw).resolve())
            protocol_root = Path(__file__).resolve().parent.parent
            candidates.append((protocol_root / raw).resolve())
        for base in candidates:
            task = (base / "CURRENT_TASK.json").resolve()
            if task.exists():
                return task

    legacy = (catalog_path.parent / "identity" / identity_id / "CURRENT_TASK.json").resolve()
    if legacy.exists():
        return legacy

    raise FileNotFoundError(f"CURRENT_TASK.json not found for identity: {identity_id}")


def _check_case(case: dict[str, Any], suite: str, idx: int) -> tuple[list[str], bool]:
    missing = [k for k in REQ_CASE_FIELDS if k not in case]
    errs: list[str] = []
    if missing:
        errs.append(f"{suite}[{idx}] missing fields: {missing}")
    if case.get("result") not in {"PASS", "FAIL"}:
        errs.append(f"{suite}[{idx}].result must be PASS|FAIL")
    if not isinstance(case.get("expected_trigger"), bool):
        errs.append(f"{suite}[{idx}].expected_trigger must be bool")
    if not isinstance(case.get("observed_trigger"), bool):
        errs.append(f"{suite}[{idx}].observed_trigger must be bool")

    semantically_pass = False
    if not errs:
        expected_route = str(case.get("expected_route"))
        observed_route = str(case.get("observed_route"))
        expected_trigger = bool(case.get("expected_trigger"))
        observed_trigger = bool(case.get("observed_trigger"))
        semantically_pass = expected_route == observed_route and expected_trigger == observed_trigger

        declared = str(case.get("result"))
        calculated = "PASS" if semantically_pass else "FAIL"
        if declared != calculated:
            errs.append(
                f"{suite}[{idx}].result inconsistent with expected/observed: declared={declared}, calculated={calculated}"
            )

    return errs, semantically_pass


def _report_pattern_candidates(pattern: str, *, pack_root: Path, identity_id: str) -> list[str]:
    if not pattern:
        return []
    candidates: list[str] = [pattern]
    local_prefix = f"identity/runtime/local/{identity_id}/"
    mapped = ""
    if pattern.startswith(local_prefix):
        mapped = str((pack_root / "runtime" / pattern[len(local_prefix) :]).as_posix())
    elif pattern.startswith("identity/runtime/"):
        mapped = str((pack_root / "runtime" / pattern[len("identity/runtime/") :]).as_posix())
    elif pattern.startswith("runtime/"):
        mapped = str((pack_root / pattern).as_posix())
    if mapped and mapped not in candidates:
        candidates.insert(0, mapped)
    return candidates


def _build_payload(
    *,
    identity_id: str,
    task_path: Path | None,
    pack_root: Path | None,
    contract_doc: dict[str, Any] | None,
    report_path: Path | None,
    report_doc: dict[str, Any] | None,
    selection_meta: dict[str, Any] | None,
    status: str,
    stale_reasons: list[str],
    error_code: str,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "identity_id": identity_id,
        "task_path": str(task_path) if task_path is not None else "",
        STATUS_FIELD: status,
        "error_code": error_code,
    }
    if pack_root is not None:
        if isinstance(selection_meta, dict):
            payload.update(
                {
                    "report_selection_mode": str(selection_meta.get("report_selection_mode", "")).strip() or "missing",
                    "live_candidate_paths": list(selection_meta.get("live_candidate_paths") or []),
                    "live_candidate_selected_path": str(selection_meta.get("live_candidate_selected_path", "")).strip(),
                }
            )
        evidence_projection = derive_strict_live_evidence_projection(
            pack_root=pack_root,
            contract_doc=contract_doc if isinstance(contract_doc, dict) else {},
            selected_report_path=report_path,
            report_doc=report_doc if isinstance(report_doc, dict) else {},
        )
        payload.update(evidence_projection)
        payload.update(
            derive_strict_live_operational_projection(
                semantic_status=status,
                evidence_projection=payload,
            )
        )
    else:
        payload.update(
            {
                "selected_report_path": str(report_path) if report_path is not None else "",
                "current_run_pointer": "",
                "current_run_report_path": "",
                "current_run_id": "",
                "report_selection_mode": "missing",
                "live_candidate_paths": [],
                "live_candidate_selected_path": "",
                "evidence_origin": "missing",
                "report_freshness_status": STATUS_FAIL_REQUIRED,
                "run_id_binding_status": STATUS_FAIL_REQUIRED,
                "strict_live_proof_status": STATUS_FAIL_REQUIRED,
                "selected_report_run_ids": [],
                "selected_report_age_seconds": None,
            }
        )
        payload.update(
            derive_strict_live_operational_projection(
                semantic_status=status,
                evidence_projection=payload,
            )
        )
    payload["stale_reasons"] = sorted(
        set([str(item).strip() for item in stale_reasons if str(item).strip()] + list(payload.pop("stale_reasons", [])))
    )
    return payload


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate identity trigger regression contract")
    ap.add_argument("--catalog", default="")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--report", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    catalog_path = Path(args.catalog)
    if not catalog_path.exists():
        payload = _build_payload(
            identity_id=args.identity_id,
            task_path=None,
            pack_root=None,
            contract_doc=None,
            report_path=None,
            report_doc=None,
            selection_meta=None,
            status=STATUS_FAIL_REQUIRED,
            stale_reasons=[f"missing_catalog:{catalog_path}"],
            error_code=ERR_TASK,
        )
        if args.json_only:
            emit_payload(payload, json_only=True)
        else:
            print(f"[FAIL] missing catalog: {catalog_path}")
        return 1

    try:
        task_path = _resolve_current_task(catalog_path, args.identity_id)
    except Exception as e:
        payload = _build_payload(
            identity_id=args.identity_id,
            task_path=None,
            pack_root=None,
            contract_doc=None,
            report_path=None,
            report_doc=None,
            selection_meta=None,
            status=STATUS_FAIL_REQUIRED,
            stale_reasons=[str(e)],
            error_code=ERR_TASK,
        )
        if args.json_only:
            emit_payload(payload, json_only=True)
        else:
            print(f"[FAIL] {e}")
        return 1

    print(f"[INFO] validate trigger regression for identity: {args.identity_id}")
    print(f"[INFO] CURRENT_TASK: {task_path}")

    try:
        task = _load_json(task_path)
    except Exception as e:
        payload = _build_payload(
            identity_id=args.identity_id,
            task_path=task_path,
            pack_root=task_path.parent.resolve(),
            contract_doc=None,
            report_path=None,
            report_doc=None,
            selection_meta=None,
            status=STATUS_FAIL_REQUIRED,
            stale_reasons=[f"invalid_current_task:{e}"],
            error_code=ERR_TASK,
        )
        if args.json_only:
            emit_payload(payload, json_only=True)
        else:
            print(f"[FAIL] invalid CURRENT_TASK json: {e}")
        return 1

    c = task.get("trigger_regression_contract") or {}
    if not isinstance(c, dict) or not c:
        payload = _build_payload(
            identity_id=args.identity_id,
            task_path=task_path,
            pack_root=task_path.parent.resolve(),
            contract_doc={},
            report_path=None,
            report_doc=None,
            selection_meta=None,
            status=STATUS_FAIL_REQUIRED,
            stale_reasons=["missing_trigger_regression_contract"],
            error_code=ERR_TASK,
        )
        if args.json_only:
            emit_payload(payload, json_only=True)
        else:
            print("[FAIL] missing trigger_regression_contract")
        return 1

    missing_runtime = [k for k in REQ_RUNTIME_KEYS if k not in c]
    if missing_runtime:
        payload = _build_payload(
            identity_id=args.identity_id,
            task_path=task_path,
            pack_root=task_path.parent.resolve(),
            contract_doc=c,
            report_path=None,
            report_doc=None,
            selection_meta=None,
            status=STATUS_FAIL_REQUIRED,
            stale_reasons=[f"trigger_regression_contract_missing_fields:{','.join(missing_runtime)}"],
            error_code=ERR_TASK,
        )
        if args.json_only:
            emit_payload(payload, json_only=True)
        else:
            print(f"[FAIL] trigger_regression_contract missing fields: {missing_runtime}")
        return 1

    if c.get("required") is not True:
        payload = _build_payload(
            identity_id=args.identity_id,
            task_path=task_path,
            pack_root=task_path.parent.resolve(),
            contract_doc=c,
            report_path=None,
            report_doc=None,
            selection_meta=None,
            status=STATUS_FAIL_REQUIRED,
            stale_reasons=["trigger_regression_contract_not_required"],
            error_code=ERR_TASK,
        )
        if args.json_only:
            emit_payload(payload, json_only=True)
        else:
            print("[FAIL] trigger_regression_contract.required must be true")
        return 1

    suites = c.get("required_suites") or []
    if set(REQ_SUITES) - set(suites):
        payload = _build_payload(
            identity_id=args.identity_id,
            task_path=task_path,
            pack_root=task_path.parent.resolve(),
            contract_doc=c,
            report_path=None,
            report_doc=None,
            selection_meta=None,
            status=STATUS_FAIL_REQUIRED,
            stale_reasons=["trigger_required_suites_missing"],
            error_code=ERR_TASK,
        )
        if args.json_only:
            emit_payload(payload, json_only=True)
        else:
            print(f"[FAIL] trigger_regression_contract.required_suites missing: {sorted(set(REQ_SUITES) - set(suites))}")
        return 1

    if set(c.get("result_enum") or []) != {"PASS", "FAIL"}:
        payload = _build_payload(
            identity_id=args.identity_id,
            task_path=task_path,
            pack_root=task_path.parent.resolve(),
            contract_doc=c,
            report_path=None,
            report_doc=None,
            selection_meta=None,
            status=STATUS_FAIL_REQUIRED,
            stale_reasons=["trigger_result_enum_mismatch"],
            error_code=ERR_TASK,
        )
        if args.json_only:
            emit_payload(payload, json_only=True)
        else:
            print("[FAIL] trigger_regression_contract.result_enum must be [PASS, FAIL]")
        return 1

    pack_root = task_path.parent.resolve()

    if args.report:
        report_path = Path(args.report).expanduser()
        if not report_path.is_absolute():
            report_path = (pack_root / report_path).resolve()
        else:
            report_path = report_path.resolve()
    else:
        pattern = str(c.get("sample_report_path_pattern", "")).replace("<identity-id>", args.identity_id)
        if pattern:
            matched: list[Path] = []
            for candidate in _report_pattern_candidates(pattern, pack_root=pack_root, identity_id=args.identity_id):
                if Path(candidate).is_absolute():
                    matched = sorted(Path(p) for p in glob.glob(candidate))
                else:
                    matched = sorted(Path(".").glob(candidate))
                if matched:
                    break
            default_pack = (pack_root / "runtime" / "examples" / f"{args.identity_id}-trigger-regression-sample.json").resolve()
            default_repo = (Path("identity") / "runtime" / "examples" / f"{args.identity_id}-trigger-regression-sample.json").resolve()
            report_path = (
                matched[-1]
                if matched
                else (default_pack if default_pack.exists() else default_repo)
            )
        else:
            default_pack = (pack_root / "runtime" / "examples" / f"{args.identity_id}-trigger-regression-sample.json").resolve()
            default_repo = (Path("identity") / "runtime" / "examples" / f"{args.identity_id}-trigger-regression-sample.json").resolve()
            report_path = default_pack if default_pack.exists() else default_repo
    selection_meta = resolve_preferred_strict_live_report(
        pack_root=pack_root,
        contract_doc=c,
        fallback_report_path=report_path,
        explicit_report_path=Path(args.report).expanduser().resolve() if args.report else None,
    )
    selected_report_path = selection_meta.get("selected_report_path")
    if isinstance(selected_report_path, Path):
        report_path = selected_report_path
    if not report_path.exists():
        payload = _build_payload(
            identity_id=args.identity_id,
            task_path=task_path,
            pack_root=pack_root,
            contract_doc=c,
            report_path=report_path,
            report_doc=None,
            selection_meta=selection_meta,
            status=STATUS_FAIL_REQUIRED,
            stale_reasons=["trigger_regression_report_missing"],
            error_code=ERR_REPORT,
        )
        if args.json_only:
            emit_payload(payload, json_only=True)
        else:
            print(f"[FAIL] IP-CWD-001 missing trigger regression report (pack-root anchored): {report_path}")
        return 1

    try:
        report = _load_json(report_path)
    except Exception as e:
        payload = _build_payload(
            identity_id=args.identity_id,
            task_path=task_path,
            pack_root=pack_root,
            contract_doc=c,
            report_path=report_path,
            report_doc=None,
            selection_meta=selection_meta,
            status=STATUS_FAIL_REQUIRED,
            stale_reasons=[f"invalid_trigger_regression_report:{e}"],
            error_code=ERR_REPORT,
        )
        if args.json_only:
            emit_payload(payload, json_only=True)
        else:
            print(f"[FAIL] invalid trigger regression report json: {e}")
        return 1

    rc = 0
    total_cases = 0
    pass_cases = 0
    fail_cases = 0

    for suite in REQ_SUITES:
        items = report.get(suite)
        if not isinstance(items, list) or not items:
            print(f"[FAIL] report.{suite} must be a non-empty array")
            rc = 1
            continue
        for idx, case in enumerate(items):
            total_cases += 1
            if not isinstance(case, dict):
                print(f"[FAIL] {suite}[{idx}] must be object")
                fail_cases += 1
                rc = 1
                continue
            errs, semantically_pass = _check_case(case, suite, idx)
            for err in errs:
                print(f"[FAIL] {err}")
                rc = 1
            if errs:
                fail_cases += 1
            else:
                if semantically_pass:
                    pass_cases += 1
                else:
                    fail_cases += 1

    summary = report.get("summary") or {}
    expected_overall = "PASS" if fail_cases == 0 else "FAIL"

    if summary.get("total_cases") != total_cases:
        print(f"[FAIL] report.summary.total_cases mismatch: expected={total_cases}, got={summary.get('total_cases')}")
        rc = 1
    if summary.get("pass_cases") != pass_cases:
        print(f"[FAIL] report.summary.pass_cases mismatch: expected={pass_cases}, got={summary.get('pass_cases')}")
        rc = 1
    if summary.get("fail_cases") != fail_cases:
        print(f"[FAIL] report.summary.fail_cases mismatch: expected={fail_cases}, got={summary.get('fail_cases')}")
        rc = 1
    if summary.get("overall_result") != expected_overall:
        print(
            f"[FAIL] report.summary.overall_result mismatch: expected={expected_overall}, got={summary.get('overall_result')}"
        )
        rc = 1

    status = STATUS_PASS_REQUIRED if rc == 0 else STATUS_FAIL_REQUIRED
    payload = _build_payload(
        identity_id=args.identity_id,
        task_path=task_path,
        pack_root=pack_root,
        contract_doc=c,
        report_path=report_path,
        report_doc=report,
        selection_meta=selection_meta,
        status=status,
        stale_reasons=[] if rc == 0 else ["trigger_regression_contract_validation_failed"],
        error_code="" if rc == 0 else ERR_TASK,
    )
    if rc:
        if args.json_only:
            emit_payload(payload, json_only=True)
        return 1

    if args.json_only:
        emit_payload(payload, json_only=True)
        return 0

    print(
        "[INFO] strict-live projection: "
        f"evidence_origin={payload['evidence_origin']} "
        f"report_freshness_status={payload['report_freshness_status']} "
        f"run_id_binding_status={payload['run_id_binding_status']} "
        f"strict_live_proof_status={payload['strict_live_proof_status']}"
    )
    print("Trigger regression contract validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
