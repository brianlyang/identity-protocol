#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

import yaml
from governed_reply_transport_lifecycle_common import (
    REPLY_TRANSPORT_RESOLUTION_MODE_MATERIALIZE_RUNTIME_SENTINEL,
)
from protocol_infra_contract import HOST_VISIBLE_POST_CHECK_RECOVERY_REPLY_TRANSPORT_REF
from registry_alias_control_plane_common import STREAM_DOC_REGISTRY_CURRENT, resolve_current_yaml_alias

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_STREAM = "IP-NCHAT-BOOT-001"

DEFAULT_STREAM_VERSION = "v1.6.12"
DEFAULT_STREAM_SLUG = "v1612-native-chat-bootstrap-entry"
DEFAULT_GOV_DOC = "docs/governance/identity-native-chat-bootstrap-entry-governance-v1.6.12.md"
DEFAULT_REVIEW_DOC = "docs/review/protocol-remediation-audit-ledger-v1.6.12-native-chat-bootstrap-entry.md"
DEFAULT_AUDIT_INDEX = "docs/governance/AUDIT_SNAPSHOT_INDEX.md"
DEFAULT_STREAM_DOC_REGISTRY = STREAM_DOC_REGISTRY_CURRENT
DEFAULT_DOC_EVIDENCE_ALLOWLIST = "identity/protocol/mappings/doc-evidence-allowlist.current.yaml"
DEFAULT_SUMMARY_NAME = "bootstrap_entry_summary.v1.6.12.json"
DEFAULT_MANIFEST_NAME = "EVIDENCE_MANIFEST.v1.6.12-native-chat-bootstrap-entry.json"
DEFAULT_ACTIVITY_EVIDENCE_ROOT = Path("activity") / "evidence"
DEFAULT_CANONICAL_FIXTURE_ROOT = Path("identity") / "protocol" / "fixtures"

CHECK_SCOPE_FULL = "full"
CHECK_SCOPE_BUNDLE_ONLY = "bundle_only"
ALLOWED_CHECK_SCOPES = (CHECK_SCOPE_FULL, CHECK_SCOPE_BUNDLE_ONLY)

ALLOWED_LIVE_SMOKE_STATUSES = {
    STATUS_PASS_REQUIRED,
    "INCONCLUSIVE_HOST_RUNTIME_PANIC",
}
REQUIRED_POSITIVE_RECORD_KINDS = {
    "stream_summary",
    "fast_audit_summary",
    "protocol_authority_resolve",
    "wrapper_dry_run_resume",
    "wrapper_dry_run_exec",
}
REQUIRED_INCONCLUSIVE_RECORD_KINDS = {
    "live_smoke_timeout_audit",
    "live_smoke_stderr",
}
CONTINUITY_COMPENSATION_RECORD_KIND = "host_visible_continuity_proof"
REQUIRED_RECORD_FIELDS = ("mirror_path", "sha256", "command", "rc", "timestamp")
PROMOTION_LOCK = "NON_PROMOTIONAL_LOCK"
PROMOTION_ELIGIBLE = "PROMOTION_REVIEW_ELIGIBLE"
PROMOTION_UNKNOWN = "UNKNOWN"
STANDARD_CLOSURE_CLOSED = "CLOSED"
STANDARD_CLOSURE_BLOCKED = "BLOCKED"
PROMOTION_ENHANCEMENT_OPEN = "OPEN"
PROMOTION_ENHANCEMENT_READY = "READY"
PROMOTION_ENHANCEMENT_CLOSED = "CLOSED"
HOST_VISIBLE_PROBE_SUITE = "host_visible_surface_live_probes"
HOST_VISIBLE_REQUIRED_PROMOTION_PROBES = {
    "host_visible_live_receipts_pass": 0,
    "host_visible_final_channel_relay_missing_blocked": 1,
    "host_visible_post_check_recovery_reseeds_final_channel_relay": 0,
    "host_visible_post_check_recovery_materializes_governed_source": 0,
    "host_visible_post_check_recovery_shadow_runtime_isolated": 0,
    "send_time_governed_pass_headstamp_required": 0,
    "protocol_lane_headstamp_continuity_live_receipt_pass": 0,
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError(f"json root must be object: {path}")
    return data


def _norm_path(value: str) -> str:
    return str(value or "").strip().replace("\\", "/")


def _relative(repo_root: Path, path: Path) -> str:
    return _norm_path(str(path.resolve().relative_to(repo_root.resolve())))


def _discover_latest_bundle_root(repo_root: Path, stream_slug: str) -> tuple[Path, str]:
    candidates = (
        ("canonical_fixture", (repo_root / DEFAULT_CANONICAL_FIXTURE_ROOT / stream_slug).resolve()),
        ("activity_evidence", (repo_root / DEFAULT_ACTIVITY_EVIDENCE_ROOT / stream_slug).resolve()),
    )
    missing_roots: list[str] = []
    for source_kind, root in candidates:
        if not root.exists():
            missing_roots.append(str(root))
            continue
        dated_roots = sorted(path for path in root.iterdir() if path.is_dir())
        if not dated_roots:
            missing_roots.append(f"{root}#bundle_date_missing")
            continue
        return dated_roots[-1], source_kind
    raise RuntimeError("bundle_root_missing:" + "|".join(missing_roots))


def _matches_any(patterns: list[str], rel_path: str) -> bool:
    for pattern in patterns:
        token = str(pattern or "").strip()
        if not token:
            continue
        if re.match(token, rel_path):
            return True
    return False


def _failure(payload: dict[str, Any], reason: str) -> None:
    failures = payload.setdefault("failures", [])
    if reason not in failures:
        failures.append(reason)


def _promotion_lock(payload: dict[str, Any], reason: str) -> None:
    reasons = payload.setdefault("promotion_unlock_failures", [])
    if reason not in reasons:
        reasons.append(reason)


def _resolve_summary_ref(repo_root: Path, summary_path: Path, value: str) -> Path | None:
    token = _norm_path(value)
    if not token:
        return None
    raw_path = Path(token)
    if raw_path.is_absolute():
        return raw_path.expanduser().resolve()
    repo_candidate = (repo_root / token).resolve()
    if repo_candidate.exists():
        return repo_candidate
    return (summary_path.parent / token).resolve()


def _derive_live_no_headstamp_status(live_smoke_status: str) -> str:
    if live_smoke_status == STATUS_PASS_REQUIRED:
        return STATUS_PASS_REQUIRED
    if live_smoke_status == "INCONCLUSIVE_HOST_RUNTIME_PANIC":
        return "INCONCLUSIVE_HOST_RUNTIME_PANIC"
    return STATUS_FAIL_REQUIRED


def _derive_no_silent_headerless_turn_status(
    *,
    live_smoke_status: str,
    governed_headstamp_continuity_status: str,
) -> str:
    if live_smoke_status == STATUS_PASS_REQUIRED:
        return STATUS_PASS_REQUIRED
    if governed_headstamp_continuity_status == STATUS_PASS_REQUIRED:
        return STATUS_PASS_REQUIRED
    if live_smoke_status == "INCONCLUSIVE_HOST_RUNTIME_PANIC":
        return "INCONCLUSIVE_HOST_RUNTIME_PANIC"
    return STATUS_FAIL_REQUIRED


def _derive_standard_closure_ready(payload: dict[str, Any]) -> bool:
    return (
        payload.get("stream_opening_status") == STATUS_PASS_REQUIRED
        and payload.get("tuple_present_status") == STATUS_PASS_REQUIRED
        and payload.get("authoritative_resolve_status") == STATUS_PASS_REQUIRED
    )


def _read_probe_doc(path: Path) -> dict[str, Any]:
    data = _load_json(path)
    return data if isinstance(data, dict) else {}


def _resolve_manifest_member_path(manifest_path: Path, value: str) -> Path:
    token = _norm_path(value)
    raw = Path(token)
    if raw.is_absolute():
        return raw.expanduser().resolve()
    return (manifest_path.parent / raw).resolve()


def _inspect_host_visible_probe_manifest(repo_root: Path, manifest_path: Path) -> dict[str, Any]:
    doc = _load_json(manifest_path)
    payload: dict[str, Any] = {
        "status": STATUS_PASS_REQUIRED,
        "suite": str(doc.get("suite", "")).strip(),
        "probe_manifest_ref": _relative(repo_root, manifest_path),
        "required_probe_count": len(HOST_VISIBLE_REQUIRED_PROMOTION_PROBES),
        "checked_probe_names": [],
        "failures": [],
        "final_channel_relay_receipt_status": STATUS_FAIL_REQUIRED,
        "controlled_emitter_path_status": STATUS_FAIL_REQUIRED,
        "unsupported_bypass_status": STATUS_FAIL_REQUIRED,
        "post_check_recovery_status": STATUS_FAIL_REQUIRED,
        "post_check_recovery_materialization_status": STATUS_FAIL_REQUIRED,
        "post_check_recovery_shadow_isolation_status": STATUS_FAIL_REQUIRED,
        "governed_headstamp_continuity_status": STATUS_FAIL_REQUIRED,
    }
    if payload["suite"] != HOST_VISIBLE_PROBE_SUITE:
        payload["status"] = STATUS_FAIL_REQUIRED
        payload["failures"].append("host_visible_probe_suite_mismatch")
        return payload

    results = doc.get("results") or []
    if not isinstance(results, list):
        payload["status"] = STATUS_FAIL_REQUIRED
        payload["failures"].append("host_visible_probe_results_invalid")
        return payload
    index = {
        str((row or {}).get("probe_name", "")).strip(): row
        for row in results
        if isinstance(row, dict) and str((row or {}).get("probe_name", "")).strip()
    }

    for probe_name, expected_rc in HOST_VISIBLE_REQUIRED_PROMOTION_PROBES.items():
        row = index.get(probe_name)
        if row is None:
            payload["status"] = STATUS_FAIL_REQUIRED
            payload["failures"].append(f"host_visible_probe_missing:{probe_name}")
            continue
        payload["checked_probe_names"].append(probe_name)
        rc = int(row.get("rc", -999))
        if rc != expected_rc:
            payload["status"] = STATUS_FAIL_REQUIRED
            payload["failures"].append(f"host_visible_probe_rc_mismatch:{probe_name}")

    bypass_row = index.get("host_visible_commentary_bypass_blocked")
    inline_row = index.get("send_time_inline_reply_text_host_direct_blocked")
    if bypass_row is not None and inline_row is not None and int(bypass_row.get("rc", 0)) != 0 and int(inline_row.get("rc", 0)) != 0:
        payload["unsupported_bypass_status"] = STATUS_PASS_REQUIRED
    else:
        payload["failures"].append("host_visible_unsupported_bypass_proof_missing")

    positive_row = index.get("host_visible_live_receipts_pass")
    if positive_row is not None:
        positive_doc = _read_probe_doc(
            _resolve_manifest_member_path(manifest_path, str(positive_row.get("stdout_path", "")))
        )
        relay_status = str(positive_doc.get("host_transport_wiring_attestation_final_channel_relay_status", "")).strip()
        payload["host_visible_live_receipts_status"] = str(
            positive_doc.get("host_transport_wiring_attestation_status", "")
        ).strip()
        payload["final_channel_relay_receipt_status"] = relay_status or STATUS_FAIL_REQUIRED
        payload["final_channel_relay_receipt_path"] = str(
            positive_doc.get("host_transport_wiring_attestation_final_channel_relay_receipt_path", "")
        ).strip()
        if relay_status != STATUS_PASS_REQUIRED:
            payload["status"] = STATUS_FAIL_REQUIRED
            payload["failures"].append("host_visible_final_channel_relay_not_pass_required")

    recovery_row = index.get("host_visible_post_check_recovery_reseeds_final_channel_relay")
    if recovery_row is not None:
        recovery_stdout = str(recovery_row.get("stdout_path", "")).strip()
        if not recovery_stdout:
            payload["status"] = STATUS_FAIL_REQUIRED
            payload["failures"].append("host_visible_post_check_recovery_stdout_missing")
        else:
            recovery_doc = _read_probe_doc(
                _resolve_manifest_member_path(manifest_path, recovery_stdout)
            )
            payload["post_check_recovery_observed"] = {
                "recovery_status": str(recovery_doc.get("recovery_status", "")).strip(),
                "attestation_status": str(recovery_doc.get("attestation_status", "")).strip(),
                "seeded_final_channel_relay_status": str(
                    recovery_doc.get("seeded_final_channel_relay_status", "")
                ).strip(),
            }
            payload["post_check_recovery_status"] = str(
                recovery_doc.get("recovery_status", "")
            ).strip() or STATUS_FAIL_REQUIRED
            if payload["post_check_recovery_status"] != STATUS_PASS_REQUIRED:
                payload["status"] = STATUS_FAIL_REQUIRED
                payload["failures"].append("host_visible_post_check_recovery_not_pass_required")
            if str(recovery_doc.get("attestation_status", "")).strip() != STATUS_PASS_REQUIRED:
                payload["status"] = STATUS_FAIL_REQUIRED
                payload["failures"].append("host_visible_post_check_recovery_attestation_not_pass_required")
            if str(recovery_doc.get("seeded_final_channel_relay_status", "")).strip() != STATUS_PASS_REQUIRED:
                payload["status"] = STATUS_FAIL_REQUIRED
                payload["failures"].append("host_visible_post_check_recovery_relay_seed_not_pass_required")
            if not str(recovery_doc.get("seeded_final_channel_relay_receipt_path", "")).strip():
                payload["status"] = STATUS_FAIL_REQUIRED
                payload["failures"].append("host_visible_post_check_recovery_relay_receipt_path_missing")

    materialization_row = index.get("host_visible_post_check_recovery_materializes_governed_source")
    if materialization_row is not None:
        materialization_stdout = str(materialization_row.get("stdout_path", "")).strip()
        if not materialization_stdout:
            payload["status"] = STATUS_FAIL_REQUIRED
            payload["failures"].append("host_visible_post_check_recovery_materialization_stdout_missing")
        else:
            materialization_doc = _read_probe_doc(
                _resolve_manifest_member_path(manifest_path, materialization_stdout)
            )
            payload["post_check_recovery_materialization_observed"] = {
                "recovery_status": str(materialization_doc.get("recovery_status", "")).strip(),
                "attestation_status": str(materialization_doc.get("attestation_status", "")).strip(),
                "reply_transport_requested_ref": str(
                    materialization_doc.get("reply_transport_requested_ref", "")
                ).strip(),
                "reply_transport_resolution_mode": str(
                    materialization_doc.get("reply_transport_resolution_mode", "")
                ).strip(),
                "reply_transport_source_materialized": bool(
                    materialization_doc.get("reply_transport_source_materialized", False)
                ),
                "reply_transport_source_status": str(
                    materialization_doc.get("reply_transport_source_status", "")
                ).strip(),
                "reply_transport_source_headstamp_present": bool(
                    materialization_doc.get("reply_transport_source_headstamp_present", False)
                ),
                "host_visible_runtime_scope": str(
                    materialization_doc.get("host_visible_runtime_scope", "")
                ).strip(),
            }
            observed = payload["post_check_recovery_materialization_observed"]
            if (
                observed["recovery_status"] == STATUS_PASS_REQUIRED
                and observed["attestation_status"] == STATUS_PASS_REQUIRED
                and observed["reply_transport_requested_ref"]
                == HOST_VISIBLE_POST_CHECK_RECOVERY_REPLY_TRANSPORT_REF
                and observed["reply_transport_resolution_mode"]
                == REPLY_TRANSPORT_RESOLUTION_MODE_MATERIALIZE_RUNTIME_SENTINEL
                and observed["reply_transport_source_materialized"] is True
                and observed["reply_transport_source_status"] == STATUS_PASS_REQUIRED
                and observed["reply_transport_source_headstamp_present"] is True
                and observed["host_visible_runtime_scope"] == "shadow"
            ):
                payload["post_check_recovery_materialization_status"] = STATUS_PASS_REQUIRED
            else:
                payload["status"] = STATUS_FAIL_REQUIRED
                payload["failures"].append(
                    "host_visible_post_check_recovery_materialization_not_pass_required"
                )

    shadow_isolation_row = index.get("host_visible_post_check_recovery_shadow_runtime_isolated")
    if shadow_isolation_row is not None:
        shadow_isolation_stdout = str(shadow_isolation_row.get("stdout_path", "")).strip()
        if not shadow_isolation_stdout:
            payload["status"] = STATUS_FAIL_REQUIRED
            payload["failures"].append("host_visible_post_check_recovery_shadow_isolation_stdout_missing")
        else:
            shadow_isolation_doc = _read_probe_doc(
                _resolve_manifest_member_path(manifest_path, shadow_isolation_stdout)
            )
            payload["post_check_recovery_shadow_isolation_observed"] = {
                "recovery_status": str(shadow_isolation_doc.get("recovery_status", "")).strip(),
                "attestation_status": str(shadow_isolation_doc.get("attestation_status", "")).strip(),
                "host_visible_runtime_scope": str(
                    shadow_isolation_doc.get("host_visible_runtime_scope", "")
                ).strip(),
                "live_runtime_snapshot_unchanged": bool(
                    shadow_isolation_doc.get("live_runtime_snapshot_unchanged", False)
                ),
                "shadow_runtime_distinct_from_live": bool(
                    shadow_isolation_doc.get("shadow_runtime_distinct_from_live", False)
                ),
                "shadow_runtime_state_exists": bool(
                    shadow_isolation_doc.get("shadow_runtime_state_exists", False)
                ),
                "shadow_runtime_post_check_closure_state_exists": bool(
                    shadow_isolation_doc.get("shadow_runtime_post_check_closure_state_exists", False)
                ),
                "shadow_runtime_seeded_receipt_count": int(
                    shadow_isolation_doc.get("shadow_runtime_seeded_receipt_count", 0) or 0
                ),
            }
            observed = payload["post_check_recovery_shadow_isolation_observed"]
            if (
                observed["recovery_status"] == STATUS_PASS_REQUIRED
                and observed["attestation_status"] == STATUS_PASS_REQUIRED
                and observed["host_visible_runtime_scope"] == "shadow"
                and observed["live_runtime_snapshot_unchanged"] is True
                and observed["shadow_runtime_distinct_from_live"] is True
                and observed["shadow_runtime_state_exists"] is True
                and observed["shadow_runtime_post_check_closure_state_exists"] is True
                and observed["shadow_runtime_seeded_receipt_count"] > 0
            ):
                payload["post_check_recovery_shadow_isolation_status"] = STATUS_PASS_REQUIRED
            else:
                payload["status"] = STATUS_FAIL_REQUIRED
                payload["failures"].append("host_visible_post_check_recovery_shadow_isolation_not_pass_required")

    send_time_row = index.get("send_time_governed_pass_headstamp_required")
    if send_time_row is not None:
        send_time_doc = _read_probe_doc(
            _resolve_manifest_member_path(manifest_path, str(send_time_row.get("stdout_path", "")))
        )
        controlled_fields = {
            "send_time_gate_status": str(send_time_doc.get("send_time_gate_status", "")).strip(),
            "current_surface_transport_attestation_status": str(
                send_time_doc.get("current_surface_transport_attestation_status", "")
            ).strip(),
            "chat_egress_uniqueness_status": str(send_time_doc.get("chat_egress_uniqueness_status", "")).strip(),
            "next_hop_admission_status": str(send_time_doc.get("next_hop_admission_status", "")).strip(),
            "headstamp_consistency_status": str(send_time_doc.get("headstamp_consistency_status", "")).strip(),
            "output_governance_mode": str(send_time_doc.get("output_governance_mode", "")).strip(),
        }
        payload["controlled_emitter_observed"] = controlled_fields
        if (
            controlled_fields["send_time_gate_status"] == STATUS_PASS_REQUIRED
            and controlled_fields["current_surface_transport_attestation_status"] == STATUS_PASS_REQUIRED
            and controlled_fields["chat_egress_uniqueness_status"] == STATUS_PASS_REQUIRED
            and controlled_fields["next_hop_admission_status"] == STATUS_PASS_REQUIRED
            and controlled_fields["headstamp_consistency_status"] == STATUS_PASS_REQUIRED
            and controlled_fields["output_governance_mode"] == "governed"
        ):
            payload["controlled_emitter_path_status"] = STATUS_PASS_REQUIRED
        else:
            payload["failures"].append("host_visible_controlled_emitter_not_pass_required")
            payload["status"] = STATUS_FAIL_REQUIRED

    continuity_row = index.get("protocol_lane_headstamp_continuity_live_receipt_pass")
    if continuity_row is not None:
        continuity_doc = _read_probe_doc(
            _resolve_manifest_member_path(manifest_path, str(continuity_row.get("stdout_path", "")))
        )
        continuity_fields = {
            "protocol_lane_headstamp_status": str(
                continuity_doc.get("protocol_lane_headstamp_status", "")
            ).strip(),
            "protocol_lane_activation_status": str(
                continuity_doc.get("protocol_lane_activation_status", "")
            ).strip(),
            "headstamp_continuity_status": str(
                continuity_doc.get("headstamp_continuity_status", "")
            ).strip(),
            "headstamp_live_receipt_binding_status": str(
                continuity_doc.get("headstamp_live_receipt_binding_status", "")
            ).strip(),
            "route_source_ref": str(continuity_doc.get("route_source_ref", "")).strip(),
        }
        payload["governed_headstamp_continuity_observed"] = continuity_fields
        if (
            continuity_fields["protocol_lane_headstamp_status"] == STATUS_PASS_REQUIRED
            and continuity_fields["protocol_lane_activation_status"] == STATUS_PASS_REQUIRED
            and continuity_fields["headstamp_continuity_status"] == STATUS_PASS_REQUIRED
            and continuity_fields["headstamp_live_receipt_binding_status"] == STATUS_PASS_REQUIRED
            and continuity_fields["route_source_ref"] == "host_visible_live_receipt_fallback"
        ):
            payload["governed_headstamp_continuity_status"] = STATUS_PASS_REQUIRED
        else:
            payload["failures"].append("host_visible_governed_headstamp_continuity_not_pass_required")
            payload["status"] = STATUS_FAIL_REQUIRED

    if payload["failures"]:
        payload["status"] = STATUS_FAIL_REQUIRED
    return payload


def _validate_promotion_unlock_bundle(
    payload: dict[str, Any],
    *,
    repo_root: Path,
    summary_path: Path,
    summary: dict[str, Any],
    live_smoke_status: str,
) -> None:
    bundle = summary.get("promotion_unlock_evidence") or {}
    if not isinstance(bundle, dict):
        bundle = {}
    payload["promotion_unlock_bundle_present"] = bool(bundle)
    payload["promotion_unlock_bundle_status"] = str(bundle.get("status", "")).strip() or PROMOTION_LOCK

    derived_tuple_present_status = STATUS_PASS_REQUIRED
    derived_authoritative_resolve_status = STATUS_PASS_REQUIRED
    derived_live_no_headstamp_status = _derive_live_no_headstamp_status(live_smoke_status)
    payload["tuple_present_status"] = str(bundle.get("tuple_present_status", "")).strip() or derived_tuple_present_status
    payload["authoritative_resolve_status"] = (
        str(bundle.get("authoritative_resolve_status", "")).strip() or derived_authoritative_resolve_status
    )
    bundle_no_headstamp_status = str(bundle.get("no_silent_headerless_turn_status", "")).strip()
    payload["live_smoke_no_silent_headerless_turn_status"] = derived_live_no_headstamp_status
    payload["final_channel_relay_receipt_status"] = str(bundle.get("final_channel_relay_receipt_status", "")).strip() or PROMOTION_UNKNOWN
    payload["controlled_emitter_path_status"] = str(bundle.get("controlled_emitter_path_status", "")).strip() or PROMOTION_UNKNOWN
    payload["unsupported_bypass_status"] = str(bundle.get("unsupported_bypass_status", "")).strip() or PROMOTION_UNKNOWN

    if payload["tuple_present_status"] != derived_tuple_present_status:
        _promotion_lock(payload, "tuple_present_status_not_pass_required")
    if payload["authoritative_resolve_status"] != derived_authoritative_resolve_status:
        _promotion_lock(payload, "authoritative_resolve_status_not_pass_required")

    probe_manifest_ref = str(bundle.get("host_visible_surface_probe_manifest_ref", "")).strip()
    payload["host_visible_surface_probe_manifest_ref"] = probe_manifest_ref
    if probe_manifest_ref:
        manifest_path = _resolve_summary_ref(repo_root, summary_path, probe_manifest_ref)
        if manifest_path is None or not manifest_path.exists():
            _promotion_lock(payload, "host_visible_surface_probe_manifest_missing")
        else:
            probe_payload = _inspect_host_visible_probe_manifest(repo_root, manifest_path)
            payload["host_visible_surface_probe_status"] = str(probe_payload.get("status", "")).strip()
            payload["host_visible_surface_probe_suite"] = str(probe_payload.get("suite", "")).strip()
            payload["host_visible_surface_probe_checked_probe_names"] = probe_payload.get("checked_probe_names", [])
            payload["host_visible_surface_probe_failures"] = probe_payload.get("failures", [])
            payload["final_channel_relay_receipt_status"] = str(
                probe_payload.get("final_channel_relay_receipt_status", payload["final_channel_relay_receipt_status"])
            ).strip()
            payload["controlled_emitter_path_status"] = str(
                probe_payload.get("controlled_emitter_path_status", payload["controlled_emitter_path_status"])
            ).strip()
            payload["unsupported_bypass_status"] = str(
                probe_payload.get("unsupported_bypass_status", payload["unsupported_bypass_status"])
            ).strip()
            payload["post_check_recovery_status"] = str(
                probe_payload.get("post_check_recovery_status", "")
            ).strip()
            payload["post_check_recovery_materialization_status"] = str(
                probe_payload.get("post_check_recovery_materialization_status", "")
            ).strip()
            payload["post_check_recovery_materialization_observed"] = probe_payload.get(
                "post_check_recovery_materialization_observed", {}
            )
            payload["post_check_recovery_shadow_isolation_status"] = str(
                probe_payload.get("post_check_recovery_shadow_isolation_status", "")
            ).strip()
            payload["post_check_recovery_shadow_isolation_observed"] = probe_payload.get(
                "post_check_recovery_shadow_isolation_observed", {}
            )
            payload["post_check_recovery_observed"] = probe_payload.get("post_check_recovery_observed", {})
            payload["final_channel_relay_receipt_path"] = str(
                probe_payload.get("final_channel_relay_receipt_path", "")
            ).strip()
            payload["governed_headstamp_continuity_status"] = str(
                probe_payload.get("governed_headstamp_continuity_status", "")
            ).strip()
            payload["governed_headstamp_continuity_observed"] = probe_payload.get(
                "governed_headstamp_continuity_observed", {}
            )
            if payload["host_visible_surface_probe_status"] != STATUS_PASS_REQUIRED:
                _promotion_lock(payload, "host_visible_surface_probe_status_not_pass_required")
    else:
        _promotion_lock(payload, "host_visible_surface_probe_manifest_ref_missing")

    derived_no_headstamp_status = _derive_no_silent_headerless_turn_status(
        live_smoke_status=live_smoke_status,
        governed_headstamp_continuity_status=str(payload.get("governed_headstamp_continuity_status", "")).strip(),
    )
    payload["no_silent_headerless_turn_proof_source"] = (
        "live_smoke"
        if live_smoke_status == STATUS_PASS_REQUIRED
        else (
            "host_visible_continuity_bundle"
            if str(payload.get("governed_headstamp_continuity_status", "")).strip() == STATUS_PASS_REQUIRED
            else "host_runtime_inconclusive"
        )
    )
    payload["no_silent_headerless_turn_status"] = bundle_no_headstamp_status or derived_no_headstamp_status
    if payload["no_silent_headerless_turn_status"] != derived_no_headstamp_status:
        _promotion_lock(payload, "no_silent_headerless_turn_status_not_aligned_with_governed_proof")

    all_promotion_requirements_pass = (
        payload["tuple_present_status"] == STATUS_PASS_REQUIRED
        and payload["authoritative_resolve_status"] == STATUS_PASS_REQUIRED
        and str(payload.get("host_visible_surface_probe_status", "")).strip() == STATUS_PASS_REQUIRED
        and payload["final_channel_relay_receipt_status"] == STATUS_PASS_REQUIRED
        and str(payload.get("post_check_recovery_materialization_status", "")).strip() == STATUS_PASS_REQUIRED
        and str(payload.get("post_check_recovery_shadow_isolation_status", "")).strip() == STATUS_PASS_REQUIRED
        and payload["controlled_emitter_path_status"] == STATUS_PASS_REQUIRED
        and payload["no_silent_headerless_turn_status"] == STATUS_PASS_REQUIRED
    )
    payload["promotion_unlock_ready"] = bool(all_promotion_requirements_pass)


def _validate_closure_decision(
    payload: dict[str, Any],
    *,
    summary: dict[str, Any],
) -> None:
    decision = summary.get("closure_decision") or {}
    if not isinstance(decision, dict):
        decision = {}

    payload["standard_implementation_mode"] = str(decision.get("standard_implementation_mode", "")).strip()
    payload["standard_closure_status"] = str(decision.get("standard_closure_status", "")).strip() or STANDARD_CLOSURE_BLOCKED
    payload["promotion_enhancement_mode"] = str(decision.get("promotion_enhancement_mode", "")).strip()
    payload["promotion_enhancement_status"] = str(decision.get("promotion_enhancement_status", "")).strip() or PROMOTION_ENHANCEMENT_OPEN

    if payload["standard_implementation_mode"] != "assistant_visible_inject":
        _failure(payload, "standard_implementation_mode_invalid")
    if payload["promotion_enhancement_mode"] != "host_final_surface_controlled_display":
        _failure(payload, "promotion_enhancement_mode_invalid")
    if payload["standard_closure_status"] not in {STANDARD_CLOSURE_CLOSED, STANDARD_CLOSURE_BLOCKED}:
        _failure(payload, "standard_closure_status_invalid")
    if payload["promotion_enhancement_status"] not in {
        PROMOTION_ENHANCEMENT_OPEN,
        PROMOTION_ENHANCEMENT_READY,
        PROMOTION_ENHANCEMENT_CLOSED,
    }:
        _failure(payload, "promotion_enhancement_status_invalid")

    standard_ready = _derive_standard_closure_ready(payload)
    payload["standard_closure_ready"] = bool(standard_ready)
    if payload["standard_closure_status"] == STANDARD_CLOSURE_CLOSED and not standard_ready:
        _failure(payload, "standard_closure_claim_not_supported")
    if payload["standard_closure_status"] == STANDARD_CLOSURE_BLOCKED and standard_ready:
        _failure(payload, "standard_closure_status_not_closed")

    if payload["promotion_status"] == PROMOTION_LOCK:
        if payload["promotion_enhancement_status"] != PROMOTION_ENHANCEMENT_OPEN:
            _failure(payload, "promotion_enhancement_status_not_open_while_locked")
    elif payload["promotion_status"] == PROMOTION_ELIGIBLE:
        if payload["promotion_enhancement_status"] == PROMOTION_ENHANCEMENT_OPEN:
            _failure(payload, "promotion_enhancement_status_still_open_while_eligible")


def _validate_registry(payload: dict[str, Any], *, repo_root: Path, stream_version: str, governance_doc: str, review_doc: str, registry_rel: str) -> None:
    resolved_path, active_file, alias_error = resolve_current_yaml_alias(repo_root, registry_rel)
    payload["stream_doc_registry_entry"] = str((repo_root / registry_rel).resolve())
    payload["stream_doc_registry_resolved"] = str(resolved_path)
    payload["stream_doc_registry_active_file"] = active_file
    payload["stream_doc_registry_alias_error"] = alias_error
    if alias_error:
        _failure(payload, f"stream_doc_registry_alias_error:{alias_error}")
        return
    data = _load_yaml(resolved_path)
    rows = data.get("stream_docs") or []
    if not isinstance(rows, list):
        _failure(payload, "stream_doc_registry_stream_docs_invalid")
        return
    row = next(
        (
            item
            for item in rows
            if isinstance(item, dict) and str(item.get("stream_version", "")).strip() == stream_version
        ),
        None,
    )
    if row is None:
        _failure(payload, f"stream_doc_registry_missing_stream:{stream_version}")
        return
    if _norm_path(row.get("governance_doc", "")) != governance_doc:
        _failure(payload, "stream_doc_registry_governance_doc_mismatch")
    if _norm_path(row.get("review_doc", "")) != review_doc:
        _failure(payload, "stream_doc_registry_review_doc_mismatch")


def _validate_allowlist(
    payload: dict[str, Any],
    *,
    repo_root: Path,
    governance_doc: str,
    review_doc: str,
    allowlist_rel: str,
    manifest_rel: str,
    summary_rel: str,
) -> None:
    resolved_path, active_file, alias_error = resolve_current_yaml_alias(repo_root, allowlist_rel)
    payload["doc_evidence_allowlist_entry"] = str((repo_root / allowlist_rel).resolve())
    payload["doc_evidence_allowlist_resolved"] = str(resolved_path)
    payload["doc_evidence_allowlist_active_file"] = active_file
    payload["doc_evidence_allowlist_alias_error"] = alias_error
    if alias_error:
        _failure(payload, f"doc_evidence_allowlist_alias_error:{alias_error}")
        return
    data = _load_yaml(resolved_path)
    strict_docs = data.get("strict_docs") or {}
    if not isinstance(strict_docs, dict):
        _failure(payload, "doc_evidence_allowlist_strict_docs_invalid")
        return
    for doc_key in (governance_doc, review_doc):
        row = strict_docs.get(doc_key) or {}
        if not isinstance(row, dict):
            _failure(payload, f"doc_evidence_allowlist_missing_doc:{doc_key}")
            continue
        patterns = row.get("allowed_activity_patterns") or row.get("allowed_evidence") or []
        if not isinstance(patterns, list):
            _failure(payload, f"doc_evidence_allowlist_patterns_invalid:{doc_key}")
            continue
        if not _matches_any(patterns, manifest_rel):
            _failure(payload, f"doc_evidence_allowlist_manifest_missing:{doc_key}")
        if not _matches_any(patterns, summary_rel):
            _failure(payload, f"doc_evidence_allowlist_summary_missing:{doc_key}")


def _validate_audit_index(payload: dict[str, Any], *, repo_root: Path, audit_index_rel: str, governance_doc: str, review_doc: str) -> None:
    audit_index = (repo_root / audit_index_rel).resolve()
    payload["audit_snapshot_index"] = str(audit_index)
    if not audit_index.exists():
        _failure(payload, f"audit_snapshot_index_missing:{audit_index_rel}")
        return
    text = audit_index.read_text(encoding="utf-8")
    if governance_doc not in text:
        _failure(payload, "audit_snapshot_index_governance_doc_missing")
    if review_doc not in text:
        _failure(payload, "audit_snapshot_index_review_doc_missing")


def _validate_summary_and_manifest(
    payload: dict[str, Any],
    *,
    repo_root: Path,
    stream_version: str,
    manifest_path: Path,
    summary_path: Path,
    governance_doc: str,
    review_doc: str,
) -> None:
    summary = _load_json(summary_path)
    manifest = _load_json(manifest_path)
    payload["summary_path"] = str(summary_path)
    payload["manifest_path"] = str(manifest_path)
    payload["summary_ref"] = _relative(repo_root, summary_path)
    payload["manifest_ref"] = _relative(repo_root, manifest_path)

    if str(summary.get("stream_version", "")).strip() != stream_version:
        _failure(payload, "summary_stream_version_mismatch")
    if str(manifest.get("stream_version", "")).strip() != stream_version:
        _failure(payload, "manifest_stream_version_mismatch")
    if str(summary.get("status", "")).strip() != STATUS_PASS_REQUIRED:
        _failure(payload, "summary_status_not_pass_required")

    four_track = summary.get("four_track_alignment") or {}
    if not isinstance(four_track, dict):
        _failure(payload, "summary_four_track_alignment_invalid")
    else:
        if _norm_path(four_track.get("t1_roundtable", "")) == "":
            _failure(payload, "summary_t1_roundtable_missing")
        if _norm_path(four_track.get("t2_execution_runtime", "")) == "":
            _failure(payload, "summary_t2_execution_runtime_missing")
        t3 = four_track.get("t3_protocol_kernel") or []
        if not isinstance(t3, list) or len(t3) < 2:
            _failure(payload, "summary_t3_protocol_kernel_missing")
        if _norm_path(four_track.get("t4_replay_bundle", "")) != _relative(repo_root, manifest_path):
            _failure(payload, "summary_t4_replay_bundle_mismatch")

    fast_audit = summary.get("fast_audit") or {}
    if not isinstance(fast_audit, dict) or str(fast_audit.get("status", "")).strip() != STATUS_PASS_REQUIRED:
        _failure(payload, "fast_audit_not_pass_required")

    wrapper_dry_runs = summary.get("wrapper_dry_runs") or []
    if not isinstance(wrapper_dry_runs, list) or len(wrapper_dry_runs) < 2:
        _failure(payload, "wrapper_dry_runs_missing")
    else:
        for row in wrapper_dry_runs:
            if not isinstance(row, dict) or str(row.get("status", "")).strip() != STATUS_PASS_REQUIRED:
                _failure(payload, "wrapper_dry_runs_not_pass_required")
                break

    authority = summary.get("protocol_authority_resolve") or {}
    if not isinstance(authority, dict) or str(authority.get("status", "")).strip() != STATUS_PASS_REQUIRED:
        _failure(payload, "protocol_authority_resolve_not_pass_required")

    live_smoke = summary.get("live_smoke") or {}
    live_smoke_status = str(live_smoke.get("status", "")).strip()
    payload["live_smoke_status"] = live_smoke_status
    if live_smoke_status not in ALLOWED_LIVE_SMOKE_STATUSES:
        _failure(payload, "live_smoke_status_not_allowed_for_stream_opening")
    if live_smoke_status == "INCONCLUSIVE_HOST_RUNTIME_PANIC":
        payload["live_smoke_contract_classification"] = "HOST_RUNTIME_INCONCLUSIVE_NON_PROMOTIONAL"
        payload["promotion_status"] = PROMOTION_LOCK
    elif live_smoke_status == STATUS_PASS_REQUIRED:
        payload["live_smoke_contract_classification"] = "PROMOTION_SIGNAL_PASS"
        payload["promotion_status"] = PROMOTION_ELIGIBLE
    else:
        payload["live_smoke_contract_classification"] = "FAIL_REQUIRED"
        payload["promotion_status"] = STATUS_FAIL_REQUIRED

    _validate_promotion_unlock_bundle(
        payload,
        repo_root=repo_root,
        summary_path=summary_path,
        summary=summary,
        live_smoke_status=live_smoke_status,
    )
    if payload.get("promotion_unlock_ready") is True and payload["promotion_status"] != STATUS_FAIL_REQUIRED:
        payload["promotion_status"] = PROMOTION_ELIGIBLE
        if live_smoke_status == "INCONCLUSIVE_HOST_RUNTIME_PANIC":
            payload["live_smoke_contract_classification"] = "HOST_RUNTIME_INCONCLUSIVE_BUNDLE_COMPENSATED"
    elif payload["promotion_status"] != STATUS_FAIL_REQUIRED:
        payload["promotion_status"] = PROMOTION_LOCK

    _validate_closure_decision(
        payload,
        summary=summary,
    )

    if str(manifest.get("summary_ref", "")).strip() != _relative(repo_root, summary_path):
        _failure(payload, "manifest_summary_ref_mismatch")

    evidence_records = manifest.get("evidence_records") or []
    if not isinstance(evidence_records, list) or not evidence_records:
        _failure(payload, "manifest_evidence_records_missing")
        return

    kinds: list[str] = []
    for idx, row in enumerate(evidence_records, start=1):
        if not isinstance(row, dict):
            _failure(payload, f"manifest_record_invalid:{idx}")
            continue
        kind = str(row.get("kind", "")).strip()
        if kind:
            kinds.append(kind)
        missing_fields = [field for field in REQUIRED_RECORD_FIELDS if row.get(field, "") == ""]
        if missing_fields:
            _failure(payload, f"manifest_record_missing_fields:{idx}:{','.join(missing_fields)}")

    payload["manifest_record_kinds"] = sorted(set(kinds))
    for required_kind in REQUIRED_POSITIVE_RECORD_KINDS:
        if required_kind not in kinds:
            _failure(payload, f"manifest_missing_record_kind:{required_kind}")
    if kinds.count("fast_audit_identity") < 1:
        _failure(payload, "manifest_missing_fast_audit_identity_record")
    if live_smoke_status == "INCONCLUSIVE_HOST_RUNTIME_PANIC":
        for required_kind in REQUIRED_INCONCLUSIVE_RECORD_KINDS:
            if required_kind not in kinds:
                _failure(payload, f"manifest_missing_inconclusive_record_kind:{required_kind}")
    if payload.get("no_silent_headerless_turn_proof_source") == "host_visible_continuity_bundle":
        if CONTINUITY_COMPENSATION_RECORD_KIND not in kinds:
            _failure(payload, f"manifest_missing_record_kind:{CONTINUITY_COMPENSATION_RECORD_KIND}")

    notes = manifest.get("notes") or []
    if not isinstance(notes, list) or len(notes) < 2:
        _failure(payload, "manifest_notes_missing")

    payload["governance_doc"] = governance_doc
    payload["review_doc"] = review_doc


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Validate the v1.6.12 native-chat bootstrap entry stream opening contract without reopening stream semantics."
    )
    ap.add_argument("--stream-version", default=DEFAULT_STREAM_VERSION)
    ap.add_argument("--stream-slug", default=DEFAULT_STREAM_SLUG)
    ap.add_argument("--repo-root", default="")
    ap.add_argument("--summary", default="")
    ap.add_argument("--manifest", default="")
    ap.add_argument("--governance-doc", default=DEFAULT_GOV_DOC)
    ap.add_argument("--review-doc", default=DEFAULT_REVIEW_DOC)
    ap.add_argument("--audit-index", default=DEFAULT_AUDIT_INDEX)
    ap.add_argument("--stream-doc-registry", default=DEFAULT_STREAM_DOC_REGISTRY)
    ap.add_argument("--doc-evidence-allowlist", default=DEFAULT_DOC_EVIDENCE_ALLOWLIST)
    ap.add_argument("--check-scope", choices=ALLOWED_CHECK_SCOPES, default=CHECK_SCOPE_FULL)
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve() if str(args.repo_root).strip() else _repo_root()
    summary_path = Path(args.summary).expanduser().resolve() if str(args.summary).strip() else None
    manifest_path = Path(args.manifest).expanduser().resolve() if str(args.manifest).strip() else None
    bundle_root_source = "explicit"
    if summary_path is None or manifest_path is None:
        bundle_root, bundle_root_source = _discover_latest_bundle_root(repo_root, args.stream_slug)
        summary_path = summary_path or (bundle_root / DEFAULT_SUMMARY_NAME).resolve()
        manifest_path = manifest_path or (bundle_root / DEFAULT_MANIFEST_NAME).resolve()

    payload: dict[str, Any] = {
        "status": STATUS_PASS_REQUIRED,
        "error_code": "",
        "stream_version": str(args.stream_version).strip(),
        "stream_slug": str(args.stream_slug).strip(),
        "check_scope": str(args.check_scope).strip(),
        "stream_opening_status": STATUS_PASS_REQUIRED,
        "promotion_status": "UNKNOWN",
        "live_smoke_contract_classification": "UNKNOWN",
        "bundle_root_source": bundle_root_source,
        "failures": [],
    }

    try:
        if args.check_scope == CHECK_SCOPE_FULL:
            manifest_rel = _relative(repo_root, manifest_path)
            summary_rel = _relative(repo_root, summary_path)
            _validate_registry(
                payload,
                repo_root=repo_root,
                stream_version=args.stream_version,
                governance_doc=_norm_path(args.governance_doc),
                review_doc=_norm_path(args.review_doc),
                registry_rel=_norm_path(args.stream_doc_registry),
            )
            _validate_allowlist(
                payload,
                repo_root=repo_root,
                governance_doc=_norm_path(args.governance_doc),
                review_doc=_norm_path(args.review_doc),
                allowlist_rel=_norm_path(args.doc_evidence_allowlist),
                manifest_rel=manifest_rel,
                summary_rel=summary_rel,
            )
            _validate_audit_index(
                payload,
                repo_root=repo_root,
                audit_index_rel=_norm_path(args.audit_index),
                governance_doc=_norm_path(args.governance_doc),
                review_doc=_norm_path(args.review_doc),
            )
        _validate_summary_and_manifest(
            payload,
            repo_root=repo_root,
            stream_version=args.stream_version,
            manifest_path=manifest_path,
            summary_path=summary_path,
            governance_doc=_norm_path(args.governance_doc),
            review_doc=_norm_path(args.review_doc),
        )
    except Exception as exc:
        _failure(payload, f"exception:{exc}")

    if payload["failures"]:
        payload["status"] = STATUS_FAIL_REQUIRED
        payload["stream_opening_status"] = STATUS_FAIL_REQUIRED
        payload["promotion_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_STREAM

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["status"] == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
