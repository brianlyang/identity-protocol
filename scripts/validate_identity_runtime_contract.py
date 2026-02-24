#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path
from typing import Any, Iterable

import yaml

REQ_TOP_LEVEL = [
    "objective",
    "state_machine",
    "gates",
    "source_of_truth",
    "escalation_policy",
    "evaluation_contract",
    "reasoning_loop_contract",
    "routing_contract",
    "rulebook_contract",
    "blocker_taxonomy_contract",
    "collaboration_trigger_contract",
    "capability_orchestration_contract",
    "knowledge_acquisition_contract",
    "experience_feedback_contract",
    "install_safety_contract",
    "install_provenance_contract",
    "identity_role_binding_contract",
    "ci_enforcement_contract",
    "capability_arbitration_contract",
    "self_upgrade_enforcement_contract",
]

REQ_GATES = [
    "document_gate",
    "media_gate",
    "category_compliance_gate",
    "reject_memory_gate",
    "payload_evidence_gate",
    "multimodal_consistency_gate",
    "reasoning_loop_gate",
    "routing_gate",
    "rulebook_gate",
    "collaboration_trigger_gate",
    "orchestration_gate",
    "knowledge_acquisition_gate",
    "experience_feedback_gate",
    "install_safety_gate",
    "install_provenance_gate",
    "role_binding_gate",
    "ci_enforcement_gate",
    "arbitration_gate",
]

REQUIRED_PROTOCOL_SOURCES = [
    "brianlyang/identity-protocol::identity/protocol/IDENTITY_PROTOCOL.md",
    "brianlyang/identity-protocol::docs/references/skill-installer-skill-creator-skill-update-lifecycle.md",
    "brianlyang/identity-protocol::docs/references/skill-protocol-installer-creator-update-reference-v1.2.5.md",
    "brianlyang/identity-protocol::docs/references/skill-mcp-tool-collaboration-contract-v1.0.md",
    "brianlyang/identity-protocol::docs/research/IDENTITY_PROTOCOL_BENCHMARK_SKILLS_2026-02-19.md",
    "https://developers.openai.com/codex/skills/",
    "https://agentskills.io/specification",
    "https://modelcontextprotocol.io/specification/latest",
]


def _fail(msg: str) -> int:
    print(f"[FAIL] {msg}")
    return 1


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML root must be object: {path}")
    return data


def _source_signature(item: dict[str, Any]) -> str:
    if item.get("repo") and item.get("path"):
        return f"{item.get('repo')}::{item.get('path')}"
    if item.get("url"):
        return str(item.get("url"))
    return ""


def _resolve_task_path(identity: dict[str, Any]) -> Path:
    identity_id = str(identity.get("id", "")).strip()
    pack_path = str(identity.get("pack_path", "")).strip()
    if pack_path:
        p = Path(pack_path) / "CURRENT_TASK.json"
        if p.exists():
            return p

    legacy = Path("identity") / identity_id / "CURRENT_TASK.json"
    if legacy.exists():
        return legacy

    raise FileNotFoundError(f"CURRENT_TASK.json not found for identity={identity_id}")


def _normalize_legacy_local_pattern(pattern: str, identity_id: str, pack_root: Path) -> str:
    p = pattern.replace("<identity-id>", identity_id).replace("{identity_id}", identity_id).strip()
    if not p:
        return p
    if Path(p).is_absolute():
        return p
    local_prefix = f"identity/runtime/local/{identity_id}/"
    if p.startswith(local_prefix):
        return str((pack_root / p[len(local_prefix) :]).resolve())
    identity_prefix = f"identity/{identity_id}/"
    if p.startswith(identity_prefix):
        return str((pack_root / p[len(identity_prefix) :]).resolve())
    if p.startswith("identity/runtime/local/"):
        parts = p[len("identity/runtime/local/") :].split("/", 1)
        if len(parts) == 2 and parts[0] == identity_id:
            return str((pack_root / parts[1]).resolve())
    return p


def _latest_evidence(pattern: str, identity_id: str, pack_root: Path) -> Path | None:
    candidates = []
    raw = pattern.replace("<identity-id>", identity_id).replace("{identity_id}", identity_id).strip()
    norm = _normalize_legacy_local_pattern(pattern, identity_id, pack_root)
    for c in [raw, norm]:
        if c and c not in candidates:
            candidates.append(c)
    for c in list(candidates):
        if "/examples/" in c:
            tail = c.split("/examples/", 1)[1]
            alt = f"identity/runtime/examples/{tail}"
            if alt not in candidates:
                candidates.append(alt)
    files: list[Path] = []
    for c in candidates:
        if Path(c).is_absolute():
            files.extend(Path(p) for p in glob.glob(c))
        else:
            files.extend(Path(".").glob(c))
    if not files:
        return None
    dedup = sorted({f.resolve() for f in files if f.exists()}, key=lambda p: p.stat().st_mtime)
    if not dedup:
        return None
    scoped = [p for p in dedup if identity_id in p.name]
    if scoped:
        return sorted(scoped, key=lambda p: p.stat().st_mtime)[-1]
    return dedup[-1]


def _validate_protocol_review_contract(data: dict[str, Any], identity_id: str, pack_root: Path) -> tuple[int, list[str]]:
    rc = 0
    logs: list[str] = []

    gates = data.get("gates") or {}
    needs_protocol_gate = gates.get("protocol_baseline_review_gate") == "required"
    if not needs_protocol_gate:
        return rc, logs

    logs.append("[OK]   gates.protocol_baseline_review_gate=required")

    prc = data.get("protocol_review_contract") or {}
    if not isinstance(prc, dict) or not prc:
        return 1, logs + ["[FAIL] protocol_review_contract must exist when protocol_baseline_review_gate is required"]

    sources = prc.get("must_review_sources") or []
    if not isinstance(sources, list) or not sources:
        rc = 1
        logs.append("[FAIL] protocol_review_contract.must_review_sources must be non-empty array")
    else:
        logs.append("[OK]   protocol_review_contract.must_review_sources is non-empty")

    req_fields = prc.get("required_evidence_fields") or []
    if not isinstance(req_fields, list) or not req_fields:
        rc = 1
        logs.append("[FAIL] protocol_review_contract.required_evidence_fields must be non-empty array")
    else:
        logs.append("[OK]   protocol_review_contract.required_evidence_fields is non-empty")

    pattern = str(prc.get("evidence_report_path_pattern") or "")
    if not pattern:
        rc = 1
        logs.append("[FAIL] protocol_review_contract.evidence_report_path_pattern missing")
        return rc, logs

    latest = _latest_evidence(pattern, identity_id, pack_root)
    if not latest:
        rc = 1
        logs.append(f"[FAIL] no protocol review evidence file matched: {pattern}")
        return rc, logs

    logs.append(f"[OK]   found protocol review evidence: {latest}")
    try:
        evidence = _load_json(latest)
    except Exception as e:
        return 1, logs + [f"[FAIL] protocol review evidence invalid json: {e}"]

    missing_fields = [k for k in req_fields if k not in evidence]
    if missing_fields:
        rc = 1
        logs.append(f"[FAIL] protocol review evidence missing fields: {missing_fields}")
    else:
        logs.append("[OK]   protocol review evidence required fields present")

    reviewer = str(evidence.get("reviewer_identity", "")).strip()
    if reviewer and reviewer != identity_id:
        rc = 1
        logs.append(f"[FAIL] protocol review evidence reviewer_identity mismatch: expected={identity_id}, got={reviewer}")

    source_sig: set[str] = set()
    for s in evidence.get("sources_reviewed") or []:
        if isinstance(s, dict):
            sig = _source_signature(s)
            if sig:
                source_sig.add(sig)

    expected_sig = [_source_signature(s) for s in sources if isinstance(s, dict)]
    missing_sources = [sig for sig in expected_sig if sig and sig not in source_sig]
    if missing_sources:
        rc = 1
        logs.append(f"[FAIL] protocol review evidence missing mandatory source(s): {missing_sources}")
    else:
        logs.append("[OK]   protocol review evidence covers mandatory sources")

    baseline_missing = [sig for sig in REQUIRED_PROTOCOL_SOURCES if sig not in source_sig]
    if baseline_missing:
        rc = 1
        logs.append(f"[FAIL] protocol review evidence missing baseline source(s): {baseline_missing}")
    else:
        logs.append("[OK]   protocol review evidence covers skill/mcp/protocol baseline set")

    return rc, logs


def _validate_single_identity(identity_id: str, task_path: Path) -> int:
    print(f"[INFO] validating CURRENT_TASK for identity={identity_id}: {task_path}")

    try:
        data = _load_json(task_path)
    except Exception as e:
        return _fail(f"invalid json in {task_path}: {e}")

    rc = 0
    for key in REQ_TOP_LEVEL:
        if key not in data:
            print(f"[FAIL] CURRENT_TASK missing top-level key: {key}")
            rc = 1
        else:
            print(f"[OK]   top-level key present: {key}")

    gates = data.get("gates") or {}
    if not isinstance(gates, dict):
        print("[FAIL] gates must be object")
        rc = 1
    else:
        for g in REQ_GATES:
            if gates.get(g) != "required":
                print(f"[FAIL] gates.{g} must be 'required'")
                rc = 1
            else:
                print(f"[OK]   gates.{g}=required")

    ec = data.get("evaluation_contract") or {}
    triplet = ec.get("required_evidence_triplet") or []
    if sorted(triplet) != sorted(["api_evidence", "event_evidence", "ui_evidence"]):
        print("[FAIL] evaluation_contract.required_evidence_triplet must include api/event/ui evidence")
        rc = 1
    else:
        print("[OK]   evaluation_contract.required_evidence_triplet contains api/event/ui")

    if ec.get("consistency_required") is not True:
        print("[FAIL] evaluation_contract.consistency_required must be true")
        rc = 1
    else:
        print("[OK]   evaluation_contract.consistency_required=true")

    pack_root = task_path.parent
    prc_rc, prc_logs = _validate_protocol_review_contract(data, identity_id, pack_root)
    for ln in prc_logs:
        print(ln)
    rc = max(rc, prc_rc)

    rl = data.get("reasoning_loop_contract") or {}
    required_attempt_fields = {"attempt", "hypothesis", "patch", "expected_effect", "result"}
    got_fields = set(rl.get("mandatory_fields_per_attempt") or [])
    if not required_attempt_fields.issubset(got_fields):
        print("[FAIL] reasoning_loop_contract.mandatory_fields_per_attempt missing required fields")
        rc = 1
    else:
        print("[OK]   reasoning_loop_contract mandatory attempt fields complete")

    rt = data.get("routing_contract") or {}
    if rt.get("auto_route_enabled") is not True:
        print("[FAIL] routing_contract.auto_route_enabled must be true")
        rc = 1
    else:
        print("[OK]   routing_contract.auto_route_enabled=true")

    if not isinstance(rt.get("problem_type_routes"), dict) or not rt.get("problem_type_routes"):
        print("[FAIL] routing_contract.problem_type_routes must be non-empty object")
        rc = 1
    else:
        print("[OK]   routing_contract.problem_type_routes is non-empty")

    rb = data.get("rulebook_contract") or {}
    rulebook_path = Path(rb.get("rulebook_path", ""))
    if not rulebook_path or not rulebook_path.exists():
        print(f"[FAIL] rulebook_contract.rulebook_path missing or not found: {rulebook_path}")
        rc = 1
    else:
        print(f"[OK]   rulebook exists: {rulebook_path}")

    if rb.get("append_only") is not True:
        print("[FAIL] rulebook_contract.append_only must be true")
        rc = 1
    else:
        print("[OK]   rulebook_contract.append_only=true")

    required_rule_fields = set(rb.get("required_fields") or [])
    if rulebook_path.exists():
        lines = [ln.strip() for ln in rulebook_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        if not lines:
            print("[FAIL] rulebook file is empty")
            rc = 1
        else:
            ok_rows = 0
            for i, ln in enumerate(lines[:50], start=1):
                try:
                    row = json.loads(ln)
                except Exception as e:
                    print(f"[FAIL] rulebook line {i} invalid json: {e}")
                    rc = 1
                    continue
                missing = [k for k in required_rule_fields if k not in row]
                if missing:
                    print(f"[FAIL] rulebook line {i} missing fields: {missing}")
                    rc = 1
                else:
                    ok_rows += 1
            if ok_rows:
                print(f"[OK]   validated {ok_rows} rulebook rows against required_fields")

    taxonomy = data.get("blocker_taxonomy_contract") or {}
    if not isinstance(taxonomy, dict) or not taxonomy:
        print("[FAIL] blocker_taxonomy_contract must be non-empty object")
        rc = 1
    else:
        required_blockers = set(taxonomy.get("required_blocker_types") or [])
        expected_blockers = {"login_required", "captcha_required", "session_expired", "manual_verification_required"}
        if not expected_blockers.issubset(required_blockers):
            print(
                f"[FAIL] blocker_taxonomy_contract.required_blocker_types missing: "
                f"{sorted(expected_blockers - required_blockers)}"
            )
            rc = 1
        else:
            print("[OK]   blocker taxonomy includes required blocker classes")

    collab = data.get("collaboration_trigger_contract") or {}
    if not isinstance(collab, dict) or not collab:
        print("[FAIL] collaboration_trigger_contract must be non-empty object")
        rc = 1
    else:
        notify_policy = str(collab.get("notify_policy") or "").strip()
        if not notify_policy:
            print("[FAIL] collaboration_trigger_contract.notify_policy must be non-empty string")
            rc = 1
        else:
            print(f"[OK]   collaboration_trigger_contract.notify_policy={notify_policy}")
        notify_timing = str(collab.get("notify_timing") or "").strip().lower()
        if notify_timing != "immediate":
            print("[FAIL] collaboration_trigger_contract.notify_timing must be 'immediate'")
            rc = 1
        else:
            print("[OK]   collaboration_trigger_contract.notify_timing=immediate")
        if collab.get("state_change_bypass_dedupe") is not True:
            print("[FAIL] collaboration_trigger_contract.state_change_bypass_dedupe must be true")
            rc = 1
        else:
            print("[OK]   collaboration_trigger_contract.state_change_bypass_dedupe=true")
        if collab.get("must_emit_receipt_in_chat") is not True:
            print("[FAIL] collaboration_trigger_contract.must_emit_receipt_in_chat must be true")
            rc = 1
        else:
            print("[OK]   collaboration_trigger_contract.must_emit_receipt_in_chat=true")

    install = data.get("install_safety_contract") or {}
    if not isinstance(install, dict) or not install:
        print("[FAIL] install_safety_contract must be non-empty object")
        rc = 1
    else:
        if install.get("preserve_existing_default") is not True:
            print("[FAIL] install_safety_contract.preserve_existing_default must be true")
            rc = 1
        else:
            print("[OK]   install_safety_contract.preserve_existing_default=true")
        if str(install.get("on_conflict", "")).strip() != "abort_and_explain":
            print("[FAIL] install_safety_contract.on_conflict must be 'abort_and_explain'")
            rc = 1
        else:
            print("[OK]   install_safety_contract.on_conflict=abort_and_explain")

    role_binding = data.get("identity_role_binding_contract") or {}
    if not isinstance(role_binding, dict) or not role_binding:
        print("[FAIL] identity_role_binding_contract must be non-empty object")
        rc = 1
    else:
        required_rb_fields = {
            "required",
            "role_type",
            "catalog_registration_required",
            "runtime_bootstrap_pass_required",
            "runtime_bootstrap_live_revalidate",
            "activation_policy",
            "switch_guard_required",
            "evidence_max_age_days",
            "active_binding_status_required",
            "binding_evidence_path_pattern",
            "enforcement_validator",
        }
        missing_rb = sorted(required_rb_fields - set(role_binding.keys()))
        if missing_rb:
            print(f"[FAIL] identity_role_binding_contract missing fields: {missing_rb}")
            rc = 1
        else:
            print("[OK]   identity_role_binding_contract required fields present")
        if role_binding.get("required") is not True:
            print("[FAIL] identity_role_binding_contract.required must be true")
            rc = 1
        if int(role_binding.get("evidence_max_age_days", 0)) <= 0:
            print("[FAIL] identity_role_binding_contract.evidence_max_age_days must be > 0")
            rc = 1
        if str(role_binding.get("active_binding_status_required", "")).strip() != "BOUND_ACTIVE":
            print("[FAIL] identity_role_binding_contract.active_binding_status_required must be BOUND_ACTIVE")
            rc = 1
        pattern = str(role_binding.get("binding_evidence_path_pattern", "")).strip()
        if not pattern:
            print("[FAIL] identity_role_binding_contract.binding_evidence_path_pattern missing")
            rc = 1
        else:
            latest = _latest_evidence(pattern.replace("<identity-id>", identity_id), identity_id, pack_root)
            if not latest:
                print(f"[FAIL] role binding evidence not found by pattern: {pattern}")
                rc = 1
            else:
                print(f"[OK]   role binding evidence found: {latest}")
                try:
                    ev = _load_json(latest)
                except Exception as e:
                    print(f"[FAIL] role binding evidence invalid json: {e}")
                    rc = 1
                else:
                    if str(ev.get("identity_id", "")).strip() != identity_id:
                        print("[FAIL] role binding evidence identity_id mismatch")
                        rc = 1
                    if str(ev.get("role_type", "")).strip() != str(role_binding.get("role_type", "")).strip():
                        print("[FAIL] role binding evidence role_type mismatch")
                        rc = 1
                    if str(ev.get("binding_status", "")).strip() not in {"BOUND_READY", "BOUND_ACTIVE"}:
                        print("[FAIL] role binding evidence binding_status must be BOUND_READY or BOUND_ACTIVE")
                        rc = 1

    if rc == 0:
        print(f"Identity runtime contract validation PASSED for identity={identity_id}")
    else:
        print(f"Identity runtime contract validation FAILED for identity={identity_id}")
    return rc


def _iter_target_identities(catalog: dict[str, Any], only_identity: str, all_identities: bool) -> Iterable[dict[str, Any]]:
    identities = [x for x in (catalog.get("identities") or []) if isinstance(x, dict)]
    if only_identity:
        return [x for x in identities if str(x.get("id", "")).strip() == only_identity]

    if all_identities:
        return identities

    active = [x for x in identities if str(x.get("status", "")).strip().lower() == "active"]
    if active:
        return active

    default_id = str(catalog.get("default_identity", "")).strip()
    return [x for x in identities if str(x.get("id", "")).strip() == default_id]


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate identity runtime ORRL contract")
    ap.add_argument("--catalog", default="identity/catalog/identities.yaml")
    ap.add_argument("--current-task", default="", help="optional explicit CURRENT_TASK path")
    ap.add_argument("--identity-id", default="", help="validate only this identity id")
    ap.add_argument("--all-identities", action="store_true", help="validate all identities from catalog")
    args = ap.parse_args()

    catalog_path = Path(args.catalog)
    if not catalog_path.exists():
        return _fail(f"missing catalog: {catalog_path}")

    if args.current_task:
        path = Path(args.current_task)
        if not path.exists():
            return _fail(f"override current task not found: {path}")
        rc = _validate_single_identity(args.identity_id or "(override)", path)
        return rc

    try:
        catalog = _load_yaml(catalog_path)
    except Exception as e:
        return _fail(f"invalid catalog yaml: {e}")

    targets = list(_iter_target_identities(catalog, args.identity_id, args.all_identities))
    if not targets:
        return _fail("no target identities selected for runtime validation")

    rc = 0
    for item in targets:
        identity_id = str(item.get("id", "")).strip() or "(unknown)"
        try:
            task_path = _resolve_task_path(item)
        except Exception as e:
            print(f"[FAIL] identity={identity_id} {e}")
            rc = 1
            continue

        print("\n" + "=" * 72)
        rc = max(rc, _validate_single_identity(identity_id, task_path))

    return rc


if __name__ == "__main__":
    raise SystemExit(main())
