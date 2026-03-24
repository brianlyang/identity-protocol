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

REQ_KEYS = [
    "required",
    "must_research_when",
    "source_priority",
    "evidence_fields",
    "sample_report_path_pattern",
    "high_frequency_domains",
]
REQ_EVIDENCE_FIELDS = ["claim", "source", "source_level", "confidence", "expiry", "applies_to"]
STATUS_FIELD = "knowledge_acquisition_status"
ERR_TASK = "IP-KNOW-001"
ERR_REPORT = "IP-KNOW-002"


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
        p = Path(pack_path) / "CURRENT_TASK.json"
        if p.exists():
            return p
    legacy = Path("identity") / identity_id / "CURRENT_TASK.json"
    if legacy.exists():
        return legacy
    raise FileNotFoundError(f"CURRENT_TASK.json not found for identity: {identity_id}")


def _glob_paths(pattern: str, *, pack_root: Path) -> list[Path]:
    raw = str(pattern or "").strip()
    if not raw:
        return []
    p = Path(raw).expanduser()
    has_magic = any(ch in raw for ch in ["*", "?", "["])
    if p.is_absolute():
        if has_magic:
            return sorted(Path(x).resolve() for x in glob.glob(str(p)))
        return [p.resolve()] if p.exists() else []
    preferred = sorted(pack_root.glob(raw))
    if preferred:
        return preferred
    return sorted(Path(".").glob(raw))


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
    ap = argparse.ArgumentParser(description="Validate knowledge acquisition contract")
    ap.add_argument("--catalog", default="")
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--report", default="")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    try:
        task_path = _resolve_current_task(Path(args.catalog), args.identity_id)
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

    print(f"[INFO] validate knowledge acquisition for identity: {args.identity_id}")
    print(f"[INFO] CURRENT_TASK: {task_path}")
    pack_root = task_path.parent.resolve()

    task = _load_json(task_path)
    c = task.get("knowledge_acquisition_contract") or {}
    if not isinstance(c, dict) or not c:
        payload = _build_payload(
            identity_id=args.identity_id,
            task_path=task_path,
            pack_root=pack_root,
            contract_doc={},
            report_path=None,
            report_doc=None,
            selection_meta=None,
            status=STATUS_FAIL_REQUIRED,
            stale_reasons=["missing_knowledge_acquisition_contract"],
            error_code=ERR_TASK,
        )
        if args.json_only:
            emit_payload(payload, json_only=True)
        else:
            print("[FAIL] missing knowledge_acquisition_contract")
        return 1

    missing = [k for k in REQ_KEYS if k not in c]
    if missing:
        payload = _build_payload(
            identity_id=args.identity_id,
            task_path=task_path,
            pack_root=pack_root,
            contract_doc=c,
            report_path=None,
            report_doc=None,
            selection_meta=None,
            status=STATUS_FAIL_REQUIRED,
            stale_reasons=[f"knowledge_acquisition_contract_missing_fields:{','.join(missing)}"],
            error_code=ERR_TASK,
        )
        if args.json_only:
            emit_payload(payload, json_only=True)
        else:
            print(f"[FAIL] knowledge_acquisition_contract missing fields: {missing}")
        return 1

    if c.get("required") is not True:
        payload = _build_payload(
            identity_id=args.identity_id,
            task_path=task_path,
            pack_root=pack_root,
            contract_doc=c,
            report_path=None,
            report_doc=None,
            selection_meta=None,
            status=STATUS_FAIL_REQUIRED,
            stale_reasons=["knowledge_acquisition_contract_not_required"],
            error_code=ERR_TASK,
        )
        if args.json_only:
            emit_payload(payload, json_only=True)
        else:
            print("[FAIL] knowledge_acquisition_contract.required must be true")
        return 1

    src_pri = c.get("source_priority") or []
    if src_pri[:2] != ["official_spec", "repo_contract"]:
        payload = _build_payload(
            identity_id=args.identity_id,
            task_path=task_path,
            pack_root=pack_root,
            contract_doc=c,
            report_path=None,
            report_doc=None,
            selection_meta=None,
            status=STATUS_FAIL_REQUIRED,
            stale_reasons=["knowledge_source_priority_mismatch"],
            error_code=ERR_TASK,
        )
        if args.json_only:
            emit_payload(payload, json_only=True)
        else:
            print("[FAIL] source_priority must prioritize official_spec and repo_contract")
        return 1

    ef = c.get("evidence_fields") or []
    if any(x not in ef for x in REQ_EVIDENCE_FIELDS):
        payload = _build_payload(
            identity_id=args.identity_id,
            task_path=task_path,
            pack_root=pack_root,
            contract_doc=c,
            report_path=None,
            report_doc=None,
            selection_meta=None,
            status=STATUS_FAIL_REQUIRED,
            stale_reasons=["knowledge_evidence_fields_missing"],
            error_code=ERR_TASK,
        )
        if args.json_only:
            emit_payload(payload, json_only=True)
        else:
            print("[FAIL] evidence_fields missing required knowledge evidence fields")
        return 1

    pattern = c.get("sample_report_path_pattern")
    report_path = (
        Path(args.report).expanduser().resolve()
        if args.report
        else (pack_root / "runtime" / "examples" / f"{args.identity_id}-knowledge-acquisition-sample.json").resolve()
    )
    if not report_path.exists():
        # fallback pattern search
        files = _glob_paths(str(pattern or ""), pack_root=pack_root)
        if files:
            report_path = files[-1]
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
        print(f"[FAIL] missing knowledge acquisition sample report: {report_path}")
        payload = _build_payload(
            identity_id=args.identity_id,
            task_path=task_path,
            pack_root=pack_root,
            contract_doc=c,
            report_path=report_path,
            report_doc=None,
            selection_meta=selection_meta,
            status=STATUS_FAIL_REQUIRED,
            stale_reasons=["knowledge_acquisition_report_missing"],
            error_code=ERR_REPORT,
        )
        if args.json_only:
            emit_payload(payload, json_only=True)
        return 1

    report = _load_json(report_path)
    records = report.get("records") or []
    if not isinstance(records, list) or not records:
        payload = _build_payload(
            identity_id=args.identity_id,
            task_path=task_path,
            pack_root=pack_root,
            contract_doc=c,
            report_path=report_path,
            report_doc=report,
            selection_meta=selection_meta,
            status=STATUS_FAIL_REQUIRED,
            stale_reasons=["knowledge_records_missing"],
            error_code=ERR_REPORT,
        )
        if args.json_only:
            emit_payload(payload, json_only=True)
        else:
            print("[FAIL] report.records must be a non-empty array")
        return 1

    allowed_levels = set(src_pri)
    rc = 0
    for i, rec in enumerate(records):
        if not isinstance(rec, dict):
            print(f"[FAIL] records[{i}] must be object")
            rc = 1
            continue
        miss = [k for k in REQ_EVIDENCE_FIELDS if k not in rec]
        if miss:
            print(f"[FAIL] records[{i}] missing fields: {miss}")
            rc = 1
        if rec.get("source_level") not in allowed_levels:
            print(f"[FAIL] records[{i}].source_level must be in {sorted(allowed_levels)}")
            rc = 1

    if not isinstance(c.get("high_frequency_domains"), dict) or not c.get("high_frequency_domains"):
        print("[FAIL] high_frequency_domains must be non-empty object")
        rc = 1

    if rc:
        return 1

    if args.self_test:
        pos = sorted(Path("identity/runtime/examples/knowledge/positive").glob("*.json"))
        neg = sorted(Path("identity/runtime/examples/knowledge/negative").glob("*.json"))
        if len(pos) < 2 or len(neg) < 1:
            print("[FAIL] knowledge self-test requires >=2 positive and >=1 negative samples")
            return 1
        # Positive samples
        for p in pos:
            r = _load_json(p)
            recs = r.get("records") or []
            if not recs:
                print(f"[FAIL] positive sample missing records: {p}")
                return 1
            for i, rec in enumerate(recs):
                miss = [k for k in REQ_EVIDENCE_FIELDS if k not in rec]
                if miss:
                    print(f"[FAIL] positive sample missing fields {miss}: {p}#{i}")
                    return 1
                if rec.get("source_level") not in allowed_levels:
                    print(f"[FAIL] positive sample source_level invalid: {p}#{i}")
                    return 1
        # Negative samples should fail at least one condition
        for p in neg:
            r = _load_json(p)
            recs = r.get("records") or []
            has_invalid = False
            for rec in recs:
                miss = [k for k in REQ_EVIDENCE_FIELDS if k not in rec]
                if miss or rec.get("source_level") not in allowed_levels:
                    has_invalid = True
                    break
            if not has_invalid:
                print(f"[FAIL] negative sample did not contain invalid condition: {p}")
                return 1
        print("[OK] knowledge self-test passed")

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
        stale_reasons=[] if rc == 0 else ["knowledge_acquisition_contract_validation_failed"],
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
    print("Knowledge acquisition contract validation PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
