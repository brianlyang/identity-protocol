#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import yaml

from instance_script_orchestration_common import orchestration_required, resolve_pack_task
from repo_root_resolution_common import resolve_protocol_repo_root

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_MIN_CHECKED = "IP-ORCH-ADOPT-001"
ERR_VALIDATOR_RED = "IP-ORCH-ADOPT-002"


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"yaml_root_not_object:{path}")
    return data


def _run_json(cmd: list[str], *, cwd: Path) -> dict[str, Any]:
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"command_failed:{' '.join(cmd)}\nstdout={proc.stdout}\nstderr={proc.stderr}")
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"json_decode_failed:{' '.join(cmd)}\nstdout={proc.stdout}\nstderr={proc.stderr}") from exc
    if not isinstance(payload, dict):
        raise RuntimeError(f"json_root_not_object:{' '.join(cmd)}")
    return payload


def _run_capability_activation(
    *,
    repo_root: Path,
    catalog_path: Path,
    identity_id: str,
    work_layer: str,
    source_layer: str,
    activation_policy: str,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="identity-orch-adoption-") as tmp_dir:
        out_path = Path(tmp_dir).resolve() / f"{identity_id}-capability-activation.json"
        cmd = [
            "python3",
            str((repo_root / "scripts" / "validate_identity_capability_activation.py").resolve()),
            "--catalog",
            str(catalog_path),
            "--identity-id",
            identity_id,
            "--work-layer",
            work_layer,
            "--source-layer",
            source_layer,
            "--activation-policy",
            activation_policy,
            "--out",
            str(out_path),
        ]
        proc = subprocess.run(cmd, cwd=str(repo_root), capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            raise RuntimeError(f"capability_activation_failed:{identity_id}\nstdout={proc.stdout}\nstderr={proc.stderr}")
        payload = json.loads(out_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise RuntimeError(f"capability_activation_payload_not_object:{identity_id}")
        return payload


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Validate non-empty cross-pack adoption proof for v1.6.15 instance-script orchestration."
    )
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--repo-root", default="")
    ap.add_argument("--work-layer", default="instance")
    ap.add_argument("--source-layer", default="project")
    ap.add_argument("--activation-policy", default="route-any-ready")
    ap.add_argument("--min-checked-identities", type=int, default=2)
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    repo_root = resolve_protocol_repo_root(args.repo_root, start=__file__)
    catalog_path = Path(args.catalog).expanduser().resolve()
    catalog_doc = _load_yaml(catalog_path)
    rows = [row for row in (catalog_doc.get("identities") or []) if isinstance(row, dict)]

    payload: dict[str, Any] = {
        "instance_script_cross_pack_adoption_status": STATUS_FAIL_REQUIRED,
        "error_code": "",
        "repo_root": str(repo_root),
        "catalog_path": str(catalog_path),
        "work_layer": str(args.work_layer),
        "source_layer": str(args.source_layer),
        "activation_policy": str(args.activation_policy),
        "min_checked_identities": int(args.min_checked_identities),
        "eligible_identity_count": 0,
        "checked_identity_count": 0,
        "adoption_ready_identity_count": 0,
        "eligible_identities": [],
        "identity_rows": [],
        "stale_reasons": [],
    }

    eligible: list[str] = []
    for row in rows:
        identity_id = str(row.get("id", "")).strip()
        if not identity_id:
            continue
        try:
            _pack_root, _task_path, task_doc = resolve_pack_task(
                catalog_path=catalog_path,
                current_task="",
                identity_id=identity_id,
            )
        except Exception:
            continue
        if orchestration_required(task_doc):
            eligible.append(identity_id)

    payload["eligible_identity_count"] = len(eligible)
    payload["eligible_identities"] = list(eligible)

    for identity_id in eligible:
        manifest = _run_json(
            [
                "python3",
                str((repo_root / "scripts" / "validate_instance_script_manifest.py").resolve()),
                "--catalog",
                str(catalog_path),
                "--identity-id",
                identity_id,
                "--json-only",
            ],
            cwd=repo_root,
        )
        orchestration = _run_json(
            [
                "python3",
                str((repo_root / "scripts" / "validate_identity_instance_script_orchestration.py").resolve()),
                "--catalog",
                str(catalog_path),
                "--identity-id",
                identity_id,
                "--work-layer",
                str(args.work_layer),
                "--source-layer",
                str(args.source_layer),
                "--json-only",
            ],
            cwd=repo_root,
        )
        receipt_join = _run_json(
            [
                "python3",
                str((repo_root / "scripts" / "validate_route_script_receipt_join.py").resolve()),
                "--catalog",
                str(catalog_path),
                "--identity-id",
                identity_id,
                "--work-layer",
                str(args.work_layer),
                "--source-layer",
                str(args.source_layer),
                "--json-only",
            ],
            cwd=repo_root,
        )
        lane_admission = _run_json(
            [
                "python3",
                str((repo_root / "scripts" / "validate_route_execution_lane_admission.py").resolve()),
                "--catalog",
                str(catalog_path),
                "--identity-id",
                identity_id,
                "--work-layer",
                str(args.work_layer),
                "--source-layer",
                str(args.source_layer),
                "--json-only",
            ],
            cwd=repo_root,
        )
        capability = _run_capability_activation(
            repo_root=repo_root,
            catalog_path=catalog_path,
            identity_id=identity_id,
            work_layer=str(args.work_layer),
            source_layer=str(args.source_layer),
            activation_policy=str(args.activation_policy),
        )

        row_payload = {
            "identity_id": identity_id,
            "manifest_status": str(manifest.get("instance_script_manifest_status", "")).strip(),
            "orchestration_status": str(orchestration.get("instance_script_orchestration_status", "")).strip(),
            "receipt_join_status": str(receipt_join.get("route_script_receipt_join_status", "")).strip(),
            "lane_admission_status": str(lane_admission.get("route_execution_lane_admission_status", "")).strip(),
            "capability_activation_status": str(capability.get("capability_activation_status", "")).strip(),
            "route_scope": str(capability.get("route_scope", "")).strip(),
            "route_selection_cardinality": str(capability.get("route_selection_cardinality", "")).strip(),
            "declared_dependency_projection_present": isinstance(
                capability.get("declared_dependency_projection"), dict
            ),
            "observed_dependency_projection_present": isinstance(
                capability.get("observed_dependency_projection"), dict
            ),
            "dependency_gap_reasons_present": isinstance(capability.get("dependency_gap_reasons"), list),
            "adoption_ready": False,
        }
        row_stale_reasons: list[str] = []
        if row_payload["manifest_status"] != STATUS_PASS_REQUIRED:
            row_stale_reasons.append("manifest_not_pass")
        if row_payload["orchestration_status"] != STATUS_PASS_REQUIRED:
            row_stale_reasons.append("orchestration_not_pass")
        if row_payload["receipt_join_status"] != STATUS_PASS_REQUIRED:
            row_stale_reasons.append("receipt_join_not_pass")
        if row_payload["lane_admission_status"] not in {STATUS_PASS_REQUIRED, STATUS_SKIPPED_NOT_REQUIRED}:
            row_stale_reasons.append("lane_admission_not_pass_or_skip")
        if row_payload["capability_activation_status"] != "ACTIVATED":
            row_stale_reasons.append("capability_activation_not_activated")
        if row_payload["route_scope"] != "aggregate":
            row_stale_reasons.append("aggregate_route_scope_missing")
        if not row_payload["declared_dependency_projection_present"]:
            row_stale_reasons.append("declared_dependency_projection_missing")
        if not row_payload["observed_dependency_projection_present"]:
            row_stale_reasons.append("observed_dependency_projection_missing")
        if not row_payload["dependency_gap_reasons_present"]:
            row_stale_reasons.append("dependency_gap_reasons_missing")
        row_payload["stale_reasons"] = row_stale_reasons
        row_payload["adoption_ready"] = not row_stale_reasons
        payload["identity_rows"].append(row_payload)

    payload["checked_identity_count"] = len(payload["identity_rows"])
    payload["adoption_ready_identity_count"] = sum(
        1 for row in payload["identity_rows"] if bool(row.get("adoption_ready"))
    )

    if payload["checked_identity_count"] < int(args.min_checked_identities):
        payload["error_code"] = ERR_MIN_CHECKED
        payload["stale_reasons"].append(
            f"checked_identity_count_below_floor:{payload['checked_identity_count']}<{int(args.min_checked_identities)}"
        )

    failing_rows = [
        f"{row['identity_id']}:{','.join(row.get('stale_reasons') or [])}"
        for row in payload["identity_rows"]
        if row.get("stale_reasons")
    ]
    if failing_rows:
        payload["error_code"] = payload["error_code"] or ERR_VALIDATOR_RED
        payload["stale_reasons"].extend(failing_rows)

    if payload["stale_reasons"]:
        _emit(payload, json_only=args.json_only)
        return 1

    payload["instance_script_cross_pack_adoption_status"] = STATUS_PASS_REQUIRED
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
