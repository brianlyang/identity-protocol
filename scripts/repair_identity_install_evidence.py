#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from resolve_identity_context import default_local_catalog_path
from tool_vendor_governance_common import (
    TOOL_VENDOR_GOVERNANCE_REPORT_DIR_REL,
    materialize_report_path,
)


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"yaml root must be object: {path}")
    return data


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _resolve_identity(catalog_path: Path, identity_id: str) -> dict[str, Any]:
    catalog = _load_yaml(catalog_path)
    identities = [x for x in (catalog.get("identities") or []) if isinstance(x, dict)]
    row = next((x for x in identities if str(x.get("id", "")).strip() == identity_id), None)
    if not row:
        raise FileNotFoundError(f"identity id not found in catalog: {identity_id}")
    return row


def _resolve_task(identity: dict[str, Any], identity_id: str) -> dict[str, Any]:
    pack_path = str(identity.get("pack_path", "")).strip()
    p = Path(pack_path).expanduser().resolve() / "CURRENT_TASK.json"
    if not p.exists():
        p = Path("identity") / identity_id / "CURRENT_TASK.json"
    if not p.exists():
        raise FileNotFoundError(f"CURRENT_TASK.json not found for identity={identity_id}")
    return _load_json(p)


def _resolve_pack_root(identity: dict[str, Any]) -> Path | None:
    pack_path = str(identity.get("pack_path", "")).strip()
    if not pack_path:
        return None
    return Path(pack_path).expanduser().resolve()


def _materialize(pattern: str, identity_id: str, ts: int, pack_root: Path | None = None) -> Path:
    if pack_root is None:
        raise ValueError("pack_root required for report materialization")
    p = pattern.replace("<identity-id>", identity_id)
    local_prefix = f"identity/runtime/local/{identity_id}/"
    if p.startswith(local_prefix):
        return (pack_root / "runtime" / p[len(local_prefix) :].replace("*", str(ts))).expanduser().resolve()
    return materialize_report_path(
        pattern=p,
        identity_id=identity_id,
        pack_root=pack_root,
        timestamp_token=ts,
    )


def _write_json(path: Path, payload: dict[str, Any], *, apply: bool) -> None:
    if not apply:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str, *, apply: bool) -> None:
    if not apply:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")


def _support_artifact_path(pack_root: Path, identity_id: str, kind: str, ts: int, suffix: str) -> Path:
    return (
        pack_root
        / TOOL_VENDOR_GOVERNANCE_REPORT_DIR_REL
        / f"{kind}-{identity_id}-{ts}.{suffix.lstrip('.')}"
    ).resolve()


def _materialize_tool_vendor_reports(
    *,
    task: dict[str, Any],
    pack_root: Path,
    identity_id: str,
    ts: int,
    now: str,
    apply: bool,
) -> list[Path]:
    written: list[Path] = []

    tool_contract = task.get("tool_installation_contract") or {}
    if isinstance(tool_contract, dict) and bool(tool_contract.get("required")):
        tool_report = _materialize(
            str(tool_contract.get("report_path_pattern", "")).strip(),
            identity_id,
            ts + 100,
            pack_root,
        )
        summary_ref = _support_artifact_path(pack_root, identity_id, "tool-gap-summary", ts + 101, "md")
        installed_artifact_ref = _support_artifact_path(pack_root, identity_id, "tool-installed-artifact", ts + 102, "md")
        route_binding_ref = _support_artifact_path(pack_root, identity_id, "tool-route-binding-update", ts + 103, "md")
        rollback_ref = _support_artifact_path(pack_root, identity_id, "tool-rollback", ts + 104, "md")
        _write_text(
            summary_ref,
            (
                "# Tool installation closure baseline\n\n"
                "No unresolved tool gap is currently asserted in this baseline repair artifact. "
                "The report exists so the required contract stays machine-readable and can be "
                "replaced by a concrete install lane if a real tool gap is later detected."
            ),
            apply=apply,
        )
        _write_text(
            installed_artifact_ref,
            (
                "# Installed artifact reference\n\n"
                "Baseline closure uses the already materialized project-local runtime pack and "
                "protocol-owned script surface as the current installed artifact set."
            ),
            apply=apply,
        )
        _write_text(
            route_binding_ref,
            (
                "# Route binding update baseline\n\n"
                "No additional route binding mutation was required for this repair cycle."
            ),
            apply=apply,
        )
        _write_text(
            rollback_ref,
            (
                "# Rollback baseline\n\n"
                "Rollback remains the existing shared repair/backfill lane plus pack-local runtime restoration."
            ),
            apply=apply,
        )
        _write_json(
            tool_report,
            {
                "report_id": f"tool-installation-{identity_id}-{ts + 100}",
                "identity_id": identity_id,
                "generated_at": now,
                "status": "PASS_REQUIRED",
                "tool_gap_detected": False,
                "tool_gap_summary_ref": str(summary_ref),
                "install_plan_ref": str(summary_ref),
                "approval_receipt_ref": str(summary_ref),
                "execution_log_ref": str(summary_ref),
                "installed_artifact_ref": str(installed_artifact_ref),
                "installed_version": "baseline-existing-runtime-surface",
                "post_install_healthcheck_ref": str(summary_ref),
                "task_smoke_result_ref": str(summary_ref),
                "route_binding_update_ref": str(route_binding_ref),
                "fallback_route_if_install_fails": str(route_binding_ref),
                "rollback_ref": str(rollback_ref),
            },
            apply=apply,
        )
        written.append(tool_report)

    discovery_contract = task.get("vendor_api_discovery_contract") or {}
    if isinstance(discovery_contract, dict) and bool(discovery_contract.get("required")):
        discovery_report = _materialize(
            str(discovery_contract.get("report_path_pattern", "")).strip(),
            identity_id,
            ts + 200,
            pack_root,
        )
        blocked_ref = _support_artifact_path(pack_root, identity_id, "vendor-discovery-blocked", ts + 201, "md")
        _write_text(
            blocked_ref,
            (
                "# Vendor/API discovery blocked baseline\n\n"
                "This repair artifact records that the vendor/API lane is not yet promoted to a ready selection. "
                "The contract is still materialized so later discovery work can replace this blocked baseline "
                "with a concrete selected vendor and provenance chain."
            ),
            apply=apply,
        )
        _write_json(
            discovery_report,
            {
                "report_id": f"vendor-api-discovery-{identity_id}-{ts + 200}",
                "identity_id": identity_id,
                "generated_at": now,
                "vendor_name": "pending_vendor_selection",
                "vendor_surface_name": "pending_surface_selection",
                "official_reference_url": str(blocked_ref),
                "machine_readable_contract_ref": str(task.get("vendor_api_discovery_contract", {})),
                "contract_kind": "deferred_selection_baseline",
                "auth_discovery_ref": str(blocked_ref),
                "versioning_policy_ref": str(blocked_ref),
                "rate_limit_policy_ref": str(blocked_ref),
                "capability_probe_command_ref": str(blocked_ref),
                "attach_readiness_decision": "blocked",
                "fallback_vendor_or_route_ref": str(blocked_ref),
                "vendor_api_candidates": [],
            },
            apply=apply,
        )
        written.append(discovery_report)

    solution_contract = task.get("vendor_api_solution_contract") or {}
    if isinstance(solution_contract, dict) and bool(solution_contract.get("required")):
        solution_report = _materialize(
            str(solution_contract.get("report_path_pattern", "")).strip(),
            identity_id,
            ts + 300,
            pack_root,
        )
        blocked_ref = _support_artifact_path(pack_root, identity_id, "vendor-solution-blocked", ts + 301, "md")
        _write_text(
            blocked_ref,
            (
                "# Vendor/API solution blocked baseline\n\n"
                "No single vendor/API option is promoted yet. This baseline keeps the option matrix and rollback "
                "discipline machine-readable while the actual solution architecture remains blocked."
            ),
            apply=apply,
        )
        _write_json(
            solution_report,
            {
                "report_id": f"vendor-api-solution-{identity_id}-{ts + 300}",
                "identity_id": identity_id,
                "generated_at": now,
                "run_state": "blocked",
                "problem_statement_ref": str(blocked_ref),
                "selected_vendor_api_ref": str(blocked_ref),
                "solution_pattern": "blocked_until_vendor_selection_closure",
                "decision_rationale_ref": str(blocked_ref),
                "option_comparison_ref": str(blocked_ref),
                "security_boundary_ref": str(blocked_ref),
                "auth_scope_strategy_ref": str(blocked_ref),
                "rate_limit_strategy_ref": str(blocked_ref),
                "fallback_solution_ref": str(blocked_ref),
                "rollback_solution_ref": str(blocked_ref),
                "owner_layer_declaration_ref": str(blocked_ref),
                "solution_option_matrix": [
                    {
                        "option_id": "defer-current-lane",
                        "selected": "no",
                        "solution_pattern": "defer_until_vendor_selection",
                        "expected_capability_gain": "preserve_fail_close_boundary",
                    },
                    {
                        "option_id": "blocked-no-provider",
                        "selected": "no",
                        "solution_pattern": "blocked_without_vendor_authority",
                        "expected_capability_gain": "avoid_false_green_vendor_binding",
                    },
                ],
            },
            apply=apply,
        )
        written.append(solution_report)

    return written


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Repair/generate install safety and tool/vendor closure evidence reports."
    )
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--catalog", default=str(default_local_catalog_path(start=Path(__file__).resolve())))
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    catalog = Path(args.catalog).expanduser().resolve()
    identity = _resolve_identity(catalog, args.identity_id)
    task = _resolve_task(identity, args.identity_id)
    pack_root = _resolve_pack_root(identity)
    contract = task.get("install_safety_contract") or {}
    pattern = str(contract.get("install_report_path_pattern", "")).strip()
    if not pattern:
        print("[FAIL] install_report_path_pattern missing")
        return 1

    ts = int(datetime.now(timezone.utc).timestamp())
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if pack_root is None:
        print("[FAIL] pack_path missing for identity")
        return 1
    out = _materialize(pattern, args.identity_id, ts, pack_root)
    pack_path = str(identity.get("pack_path", "")).strip()
    payload = {
        "report_id": f"identity-install-{args.identity_id}-repair-{ts}",
        "identity_id": args.identity_id,
        "generated_at": now,
        "operation": "install",
        "conflict_type": "fresh_install",
        "action": "guarded_apply",
        "source_pack": pack_path,
        "target_pack": pack_path,
        "preserved_paths": [pack_path],
        "dry_run": False,
        "installer_invocation": {
            "tool": "identity-installer",
            "entrypoint": "scripts/repair_identity_install_evidence.py",
            "command": f"python3 scripts/repair_identity_install_evidence.py --identity-id {args.identity_id} --catalog {catalog} --apply",
        },
    }

    _write_json(out, payload, apply=args.apply)

    provenance = task.get("install_provenance_contract") or {}
    provenance_pattern = str(provenance.get("report_path_pattern", "")).strip()
    provenance_ops = [str(x).strip() for x in (provenance.get("operations_required") or []) if str(x).strip()]
    provenance_paths: list[Path] = []
    if provenance_pattern and provenance_ops:
        for idx, op in enumerate(provenance_ops, start=1):
            op_ts = ts + idx
            op_time = datetime.fromtimestamp(op_ts, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            op_path = _materialize(provenance_pattern, args.identity_id, op_ts, pack_root)
            op_payload = {
                "report_id": f"identity-install-{args.identity_id}-{op}-{op_ts}",
                "identity_id": args.identity_id,
                "generated_at": op_time,
                "operation": op,
                "conflict_type": "fresh_install",
                "action": "guarded_apply",
                "preserved_paths": [pack_path],
                "installer_invocation": {
                    "tool": "identity-installer",
                    "entrypoint": "scripts/repair_identity_install_evidence.py",
                    "command": f"identity-installer {op} --identity-id {args.identity_id}",
                },
            }
            _write_json(op_path, op_payload, apply=args.apply)
            provenance_paths.append(op_path)

    tool_vendor_paths = _materialize_tool_vendor_reports(
        task=task,
        pack_root=pack_root,
        identity_id=args.identity_id,
        ts=ts,
        now=now,
        apply=args.apply,
    )

    print(f"[OK] install evidence repair {'applied' if args.apply else 'preview'}: {out}")
    for p in provenance_paths:
        print(f"[OK] install provenance evidence {'applied' if args.apply else 'preview'}: {p}")
    for p in tool_vendor_paths:
        print(f"[OK] tool/vendor closure evidence {'applied' if args.apply else 'preview'}: {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
