#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from tool_vendor_governance_common import contract_required, load_json, load_yaml, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

MODE_INTAKE_CONTRACT = "intake_contract"
MODE_PROMOTION_GATE = "promotion_gate"
ALLOWED_MODES = (MODE_INTAKE_CONTRACT, MODE_PROMOTION_GATE)

STRICT_OPERATIONS = {
    "activate",
    "update",
    "readiness",
    "e2e",
    "ci",
    "validate",
    "scan",
    "three-plane",
    "inspection",
    "mutation",
}

OBSERVATION_OPERATIONS = {
    "scan",
    "three-plane",
    "inspection",
    "validate",
}

ERR_BUNDLE_MISSING = "IP-INTAKE-EVID-001"
ERR_TRACK_QUORUM_MISSING = "IP-INTAKE-EVID-002"
ERR_METADATA_MISSING = "IP-INTAKE-EVID-003"
ERR_TRACK_AND_METADATA_MISSING = "IP-INTAKE-EVID-004"

MODE_STATUS_KEYS = {
    MODE_INTAKE_CONTRACT: "cross_verification_tracks_status",
    MODE_PROMOTION_GATE: "intake_evidence_quorum_status",
}

MODE_CONTRACT_KEYS = {
    MODE_INTAKE_CONTRACT: (
        "multi_track_cross_verification_contract_v1",
        "multi_track_cross_verification_contract",
        "cross_verification_tracks_contract_v1",
        "cross_verification_tracks_contract",
        "rq_017_multi_track_cross_verification_contract_v1",
    ),
    MODE_PROMOTION_GATE: (
        "intake_evidence_quorum_contract_v1",
        "intake_evidence_quorum_contract",
        "rq_030_intake_evidence_quorum_contract_v1",
    ),
}

UMBRELLA_CONTRACT_KEYS = (
    "cross_verification_intake_contract_v1",
    "cross_verification_intake_contract",
    "intake_evidence_contract_v1",
    "intake_evidence_contract",
)

TRACK_ALIASES = {
    "t1": ("t1", "roundtable", "track1", "track_1"),
    "t2": ("t2", "vendor", "track2", "track_2"),
    "t3": ("t3", "openai_context", "openai", "context7", "track3", "track_3"),
    "t4": ("t4", "protocol_spec", "spec", "mcp", "agent_skills", "track4", "track_4"),
}

TRACK_KEY_PATHS = {
    "t1": (
        "t1_status",
        "t1_roundtable_status",
        "roundtable_status",
        "tracks.t1.status",
        "tracks.roundtable.status",
    ),
    "t2": (
        "t2_status",
        "t2_vendor_status",
        "vendor_status",
        "tracks.t2.status",
        "tracks.vendor.status",
    ),
    "t3": (
        "t3_status",
        "t3_openai_context_status",
        "openai_context_status",
        "tracks.t3.status",
        "tracks.openai_context.status",
    ),
    "t4": (
        "t4_status",
        "t4_protocol_spec_status",
        "protocol_spec_status",
        "tracks.t4.status",
        "tracks.protocol_spec.status",
    ),
}

TRACK_TEXT_HINTS = {
    "t1": ("roundtable", "t1", "track-1", "track 1", "roundtables"),
    "t2": ("vendor", "t2", "track-2", "track 2", "protocol_vendor_scan"),
    "t3": ("openai", "context7", "openai_context", "t3", "track-3", "track 3"),
    "t4": ("protocol_spec", "modelcontextprotocol.io", "agentskills.io", "t4", "track-4", "track 4", "mcp"),
}

STATUS_TOKEN_PASS = ("pass_required", "pass", "ok", "satisfied", "complete")
STATUS_TOKEN_FAIL = ("fail_required", "fail", "error", "blocked", "missing", "incomplete")
STATUS_TOKEN_SKIP = ("skipped_not_required", "skip", "not_required", "not required")

URL_RE = re.compile(r"https?://[^\s)\]>]+", flags=re.IGNORECASE)
ISO_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z\b")

BUNDLE_ID_PATHS = (
    "cross_verification_bundle_id",
    "bundle_id",
    "intake_bundle_id",
    "evidence_bundle_id",
    "xverify_bundle_id",
)
SOURCE_URL_PATHS = (
    "source_url_set",
    "source_urls",
    "urls",
    "url_set",
    "references.urls",
)
REFERENCE_TS_PATHS = (
    "reference_timestamp_utc",
    "timestamp_utc",
    "observed_at_utc",
    "retrieved_at_utc",
    "generated_at_utc",
)
CONFLICT_NOTE_PATHS = (
    "conflict_reconciliation_note",
    "conflict_note",
    "reconciliation_note",
    "conflict_resolution_note",
)


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _normalize_status(v: Any) -> str:
    s = str(v or "").strip().lower()
    if not s:
        return ""
    if any(token in s for token in STATUS_TOKEN_FAIL):
        return STATUS_FAIL_REQUIRED
    if any(token in s for token in STATUS_TOKEN_SKIP):
        return STATUS_SKIPPED_NOT_REQUIRED
    if any(token in s for token in STATUS_TOKEN_PASS):
        return STATUS_PASS_REQUIRED
    return ""


def _is_fixture_identity(catalog_path: Path, identity_id: str) -> bool:
    try:
        catalog = load_yaml(catalog_path)
    except Exception:
        return False
    identities = catalog.get("identities") or []
    row = next((x for x in identities if isinstance(x, dict) and str(x.get("id", "")).strip() == identity_id), None)
    profile = str((row or {}).get("profile", "")).strip().lower()
    runtime_mode = str((row or {}).get("runtime_mode", "")).strip().lower()
    return profile == "fixture" or runtime_mode == "demo_only"


def _feedback_artifacts_present(pack_path: Path) -> bool:
    root = (pack_path / "runtime" / "protocol-feedback").resolve()
    if not root.exists():
        return False
    return any(p.is_file() for p in root.rglob("*"))


def _select_contract(task: dict[str, Any], mode: str) -> dict[str, Any]:
    for key in MODE_CONTRACT_KEYS.get(mode, ()):
        c = task.get(key)
        if isinstance(c, dict):
            return c

    for umbrella_key in UMBRELLA_CONTRACT_KEYS:
        umbrella = task.get(umbrella_key)
        if not isinstance(umbrella, dict):
            continue
        for key in MODE_CONTRACT_KEYS.get(mode, ()):
            nested = umbrella.get(key)
            if isinstance(nested, dict):
                return nested
    return {}


def _get_by_path(doc: Any, path: str) -> Any:
    node = doc
    for seg in path.split("."):
        if not isinstance(node, dict):
            return None
        if seg not in node:
            return None
        node = node.get(seg)
    return node


def _first_nonempty(doc: dict[str, Any], paths: tuple[str, ...]) -> Any:
    for p in paths:
        v = _get_by_path(doc, p)
        if isinstance(v, str) and v.strip():
            return v.strip()
        if isinstance(v, list) and v:
            return v
        if isinstance(v, dict) and v:
            return v
        if v is not None and not isinstance(v, (str, list, dict)):
            return v
    return None


def _first_present(doc: dict[str, Any], paths: tuple[str, ...]) -> tuple[bool, Any]:
    for p in paths:
        v = _get_by_path(doc, p)
        if v is not None:
            return True, v
    return False, None


def _iter_strings(value: Any) -> list[str]:
    out: list[str] = []
    if isinstance(value, str):
        out.append(value)
    elif isinstance(value, list):
        for item in value:
            out.extend(_iter_strings(item))
    elif isinstance(value, dict):
        for item in value.values():
            out.extend(_iter_strings(item))
    return out


def _dedupe_keep_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for v in values:
        k = str(v).strip()
        if not k or k in seen:
            continue
        seen.add(k)
        out.append(k)
    return out


def _collect_urls(doc: dict[str, Any], raw: str, value_hint: Any) -> list[str]:
    urls: list[str] = []
    for s in _iter_strings(value_hint):
        urls.extend(URL_RE.findall(s))
    if not urls:
        for s in _iter_strings(doc):
            urls.extend(URL_RE.findall(s))
    if not urls:
        urls.extend(URL_RE.findall(raw))
    return _dedupe_keep_order(urls)


def _is_iso8601_utc(value: str) -> bool:
    s = str(value or "").strip()
    if not s:
        return False
    if s.endswith("Z"):
        base = s[:-1] + "+00:00"
    else:
        base = s
    try:
        datetime.fromisoformat(base)
        return True
    except Exception:
        return False


def _extract_timestamp_from_text(raw: str) -> str:
    m = ISO_RE.search(raw)
    return m.group(0).strip() if m else ""


def _extract_conflict_note_from_text(raw: str) -> str:
    for line in raw.splitlines():
        low = line.lower()
        if "conflict_reconciliation_note" in low or "conflict note" in low or "reconciliation" in low:
            # prefer right-hand-side content when present
            if ":" in line:
                rhs = line.split(":", 1)[1].strip()
                if rhs:
                    return rhs
            if "=" in line:
                rhs = line.split("=", 1)[1].strip()
                if rhs:
                    return rhs
            return line.strip()
    return ""


def _extract_bundle_id_from_text(raw: str) -> str:
    patterns = (
        r"cross_verification_bundle_id\s*[:=]\s*([^\s,;]+)",
        r"bundle_id\s*[:=]\s*([^\s,;]+)",
        r"evidence_bundle_id\s*[:=]\s*([^\s,;]+)",
    )
    for pat in patterns:
        m = re.search(pat, raw, flags=re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return ""


def _infer_track_status_from_text(raw: str, hints: tuple[str, ...]) -> str:
    found_hint = False
    has_pass = False
    for line in raw.splitlines():
        low = line.lower()
        if not any(h in low for h in hints):
            continue
        found_hint = True
        st = _normalize_status(low)
        if st == STATUS_FAIL_REQUIRED:
            return STATUS_FAIL_REQUIRED
        if st == STATUS_PASS_REQUIRED:
            has_pass = True
    if has_pass:
        return STATUS_PASS_REQUIRED
    if found_hint:
        # hint exists but explicit status missing: treat as pass signal at intake stage.
        return STATUS_PASS_REQUIRED
    return ""


def _extract_track_statuses(doc: dict[str, Any], raw: str) -> dict[str, str]:
    out: dict[str, str] = {}

    tracks_node = doc.get("tracks")
    list_track_status: dict[str, str] = {}
    if isinstance(tracks_node, list):
        for item in tracks_node:
            if not isinstance(item, dict):
                continue
            key = str(item.get("track") or item.get("track_id") or item.get("id") or "").strip().lower().replace("-", "_")
            status = _normalize_status(item.get("status"))
            if status and key:
                for canonical, aliases in TRACK_ALIASES.items():
                    if key == canonical or key in aliases:
                        list_track_status[canonical] = status

    for canonical in ("t1", "t2", "t3", "t4"):
        status = ""
        for path in TRACK_KEY_PATHS[canonical]:
            status = _normalize_status(_get_by_path(doc, path))
            if status:
                break
        if not status and canonical in list_track_status:
            status = list_track_status[canonical]
        if not status:
            # try flat "tracks.<alias>" object shape
            tracks_map = doc.get("tracks")
            if isinstance(tracks_map, dict):
                for alias in TRACK_ALIASES[canonical]:
                    candidate = tracks_map.get(alias)
                    if isinstance(candidate, dict):
                        status = _normalize_status(candidate.get("status"))
                        if status:
                            break
                    if isinstance(candidate, str):
                        status = _normalize_status(candidate)
                        if status:
                            break
        if not status:
            status = _infer_track_status_from_text(raw, TRACK_TEXT_HINTS[canonical])
        out[canonical] = status or STATUS_FAIL_REQUIRED
    return out


def _load_bundle_doc(bundle_path: Path) -> tuple[dict[str, Any], str]:
    raw = bundle_path.read_text(encoding="utf-8", errors="ignore")

    # JSON-first
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict):
            return obj, raw
    except Exception:
        pass

    # YAML fallback
    try:
        y = yaml.safe_load(raw)
        if isinstance(y, dict):
            return y, raw
    except Exception:
        pass

    # Embedded JSON object fallback
    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        try:
            obj = json.loads(raw[start : end + 1])
            if isinstance(obj, dict):
                return obj, raw
        except Exception:
            pass

    return {}, raw


def _search_bundle_by_id(roots: list[Path], bundle_id: str) -> Path | None:
    bid = bundle_id.strip()
    if not bid:
        return None
    hits: list[Path] = []
    for root in roots:
        if not root.exists() or not root.is_dir():
            continue
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            if bid in p.name:
                hits.append(p.resolve())
    if not hits:
        return None
    hits.sort(key=lambda p: p.stat().st_mtime)
    return hits[-1]


def _resolve_pattern(pack_path: Path, pattern: str) -> list[Path]:
    raw = str(pattern or "").strip()
    if not raw:
        return []
    p = Path(raw).expanduser()
    has_magic = any(ch in raw for ch in ["*", "?", "["])
    hits: list[Path] = []
    if p.is_absolute():
        if has_magic:
            hits = [Path(x).expanduser().resolve() for x in glob.glob(str(p))]
        elif p.exists():
            hits = [p.resolve()]
    else:
        preferred = [x.resolve() for x in pack_path.glob(raw)]
        fallback = [x.resolve() for x in Path(".").glob(raw)]
        hits = preferred if preferred else fallback
    return [x for x in hits if x.exists() and x.is_file()]


def _resolve_bundle_path(pack_path: Path, contract: dict[str, Any], mode: str, explicit_bundle: str, bundle_id: str) -> Path | None:
    if explicit_bundle.strip():
        p = Path(explicit_bundle).expanduser().resolve()
        return p if p.exists() and p.is_file() else None

    roots = [
        (pack_path / "runtime" / "protocol-feedback").resolve(),
        pack_path.resolve(),
        Path(".").resolve(),
    ]
    by_id = _search_bundle_by_id(roots, bundle_id)
    if by_id is not None:
        return by_id

    candidate_patterns: list[str] = []
    for key in (
        "evidence_bundle_path_pattern",
        "bundle_path_pattern",
        "feedback_batch_path_pattern",
        "cross_verification_bundle_pattern",
        "intake_bundle_pattern",
    ):
        v = contract.get(key)
        if isinstance(v, str) and v.strip():
            candidate_patterns.append(v.strip())

    if not candidate_patterns:
        candidate_patterns = [
            "runtime/protocol-feedback/outbox-to-protocol/*cross*verification*.*",
            "runtime/protocol-feedback/outbox-to-protocol/*xverify*.*",
            "runtime/protocol-feedback/outbox-to-protocol/FEEDBACK_BATCH_*.md",
            "runtime/protocol-feedback/**/*intake*evidence*.*",
            "runtime/protocol-feedback/**/*cross*verification*.*",
        ]
        if mode == MODE_PROMOTION_GATE:
            candidate_patterns.insert(0, "runtime/protocol-feedback/outbox-to-protocol/*quorum*.*")

    hits: list[Path] = []
    for pat in candidate_patterns:
        hits.extend(_resolve_pattern(pack_path, pat))
    if not hits:
        return None
    hits = _dedupe_keep_order([str(x) for x in hits])
    paths = [Path(x) for x in hits]
    paths.sort(key=lambda p: p.stat().st_mtime)
    return paths[-1]


def _build_payload_base(args: argparse.Namespace, catalog_path: Path, pack_path: Path) -> dict[str, Any]:
    return {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "mode": args.mode,
        "operation": args.operation,
        "run_profile": "observation" if args.operation in OBSERVATION_OPERATIONS else "enforcement",
        "required_contract": False,
        "auto_required_signal": False,
        "producer_readiness": False,
        "requiredization_current_round_linked": False,
        "intake_evidence_core_status": STATUS_SKIPPED_NOT_REQUIRED,
        "cross_verification_tracks_status": STATUS_SKIPPED_NOT_REQUIRED,
        "intake_evidence_quorum_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "evidence_ref": "",
        "evidence_bundle_path": "",
        "evidence_sha256": "",
        "cross_verification_bundle_id": "",
        "source_url_set": [],
        "source_url_count": 0,
        "reference_timestamp_utc": "",
        "conflict_reconciliation_note": "",
        "t1_status": STATUS_FAIL_REQUIRED,
        "t2_status": STATUS_FAIL_REQUIRED,
        "t3_status": STATUS_FAIL_REQUIRED,
        "t4_status": STATUS_FAIL_REQUIRED,
        "t1_roundtable_status": STATUS_FAIL_REQUIRED,
        "t2_vendor_status": STATUS_FAIL_REQUIRED,
        "t3_openai_context_status": STATUS_FAIL_REQUIRED,
        "t4_protocol_spec_status": STATUS_FAIL_REQUIRED,
        "track_status_map": {},
        "missing_tracks": [],
        "missing_metadata_fields": [],
        "stale_reasons": [],
    }


def _mark_track_status_skipped(payload: dict[str, Any]) -> None:
    payload["t1_status"] = STATUS_SKIPPED_NOT_REQUIRED
    payload["t2_status"] = STATUS_SKIPPED_NOT_REQUIRED
    payload["t3_status"] = STATUS_SKIPPED_NOT_REQUIRED
    payload["t4_status"] = STATUS_SKIPPED_NOT_REQUIRED
    payload["t1_roundtable_status"] = STATUS_SKIPPED_NOT_REQUIRED
    payload["t2_vendor_status"] = STATUS_SKIPPED_NOT_REQUIRED
    payload["t3_openai_context_status"] = STATUS_SKIPPED_NOT_REQUIRED
    payload["t4_protocol_spec_status"] = STATUS_SKIPPED_NOT_REQUIRED
    payload["track_status_map"] = {
        "t1": STATUS_SKIPPED_NOT_REQUIRED,
        "t2": STATUS_SKIPPED_NOT_REQUIRED,
        "t3": STATUS_SKIPPED_NOT_REQUIRED,
        "t4": STATUS_SKIPPED_NOT_REQUIRED,
    }


def _emit_non_applicable_skip(payload: dict[str, Any], *, mode: str, reason: str, json_only: bool) -> int:
    _mark_track_status_skipped(payload)
    payload["intake_evidence_core_status"] = STATUS_SKIPPED_NOT_REQUIRED
    payload["cross_verification_tracks_status"] = STATUS_SKIPPED_NOT_REQUIRED
    payload["intake_evidence_quorum_status"] = STATUS_SKIPPED_NOT_REQUIRED
    payload[MODE_STATUS_KEYS[mode]] = STATUS_SKIPPED_NOT_REQUIRED
    payload["error_code"] = ""
    payload["stale_reasons"] = [reason]
    _emit(payload, json_only=json_only)
    return 0


def _build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Validate v1.6 intake evidence core parser (RQ-017/RQ-030 dual-mode).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--mode", choices=ALLOWED_MODES, default=MODE_INTAKE_CONTRACT)
    ap.add_argument("--bundle", default="")
    ap.add_argument("--bundle-id", default="")
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection", "mutation"],
        default="validate",
    )
    ap.add_argument("--json-only", action="store_true")
    return ap


def main(argv: list[str] | None = None, *, forced_mode: str | None = None) -> int:
    ap = _build_parser()
    args = ap.parse_args(argv)
    if forced_mode:
        args.mode = forced_mode

    catalog_path = Path(args.catalog).expanduser().resolve()
    if not catalog_path.exists():
        print(f"[FAIL] catalog not found: {catalog_path}")
        return 2

    try:
        pack_path, task_path = resolve_pack_and_task(catalog_path, args.identity_id)
        task = load_json(task_path)
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    payload = _build_payload_base(args, catalog_path, pack_path)

    if _is_fixture_identity(catalog_path, args.identity_id):
        _mark_track_status_skipped(payload)
        payload["stale_reasons"] = ["fixture_profile_scope"]
        _emit(payload, json_only=args.json_only)
        return 0

    contract = _select_contract(task, args.mode)
    required = contract_required(contract) if contract else False
    auto_required = False
    explicit_current_round_linked = bool(args.bundle.strip() or args.bundle_id.strip())

    if explicit_current_round_linked:
        required = True
        auto_required = True
    elif args.operation in STRICT_OPERATIONS and _feedback_artifacts_present(pack_path):
        if args.operation in OBSERVATION_OPERATIONS:
            # observation lanes should not force requiredization from historical feedback artifacts.
            auto_required = False
        else:
            required = True
            auto_required = True

    payload["required_contract"] = required
    payload["auto_required_signal"] = auto_required
    payload["requiredization_current_round_linked"] = explicit_current_round_linked

    if not required:
        _mark_track_status_skipped(payload)
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    bundle_path = _resolve_bundle_path(
        pack_path=pack_path,
        contract=contract if isinstance(contract, dict) else {},
        mode=args.mode,
        explicit_bundle=args.bundle,
        bundle_id=args.bundle_id,
    )
    payload["producer_readiness"] = bundle_path is not None
    if bundle_path is not None:
        payload["evidence_ref"] = str(bundle_path)
        payload["evidence_bundle_path"] = str(bundle_path)
    if bundle_path is not None and not payload["requiredization_current_round_linked"]:
        return _emit_non_applicable_skip(
            payload,
            mode=args.mode,
            reason="required_contract_not_applicable_no_current_round_evidence_source",
            json_only=args.json_only,
        )
    if bundle_path is None:
        if not payload["requiredization_current_round_linked"] and args.operation in STRICT_OPERATIONS:
            return _emit_non_applicable_skip(
                payload,
                mode=args.mode,
                reason="required_contract_not_applicable_no_current_round_evidence_source",
                json_only=args.json_only,
            )
        payload["intake_evidence_core_status"] = STATUS_FAIL_REQUIRED
        payload[MODE_STATUS_KEYS[args.mode]] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_BUNDLE_MISSING
        payload["stale_reasons"] = ["evidence_bundle_not_found"]
        _emit(payload, json_only=args.json_only)
        return 1

    doc, raw = _load_bundle_doc(bundle_path)
    evidence_sha = hashlib.sha256(raw.encode("utf-8", errors="ignore")).hexdigest()

    bundle_present, bundle_raw = _first_present(doc, BUNDLE_ID_PATHS)
    bundle_id = str(bundle_raw).strip() if bundle_present and bundle_raw is not None else ""
    if not bundle_id:
        bundle_id = _extract_bundle_id_from_text(raw) or args.bundle_id.strip() or bundle_path.stem

    source_url_hint = _first_nonempty(doc, SOURCE_URL_PATHS)
    source_urls = _collect_urls(doc, raw, source_url_hint)

    ts_present, ts_raw = _first_present(doc, REFERENCE_TS_PATHS)
    ref_ts = str(ts_raw).strip() if ts_present and ts_raw is not None else ""
    if not ref_ts and not ts_present:
        ref_ts = _extract_timestamp_from_text(raw)

    note_present, note_raw = _first_present(doc, CONFLICT_NOTE_PATHS)
    conflict_note = str(note_raw).strip() if note_present and note_raw is not None else ""
    if not conflict_note and not note_present:
        conflict_note = _extract_conflict_note_from_text(raw)

    track_status = _extract_track_statuses(doc, raw)
    missing_tracks = sorted([k for k, v in track_status.items() if v != STATUS_PASS_REQUIRED])

    missing_meta: list[str] = []
    if not bundle_id:
        missing_meta.append("cross_verification_bundle_id")
    if not source_urls:
        missing_meta.append("source_url_set")
    if not ref_ts:
        missing_meta.append("reference_timestamp_utc")
    elif not _is_iso8601_utc(ref_ts):
        missing_meta.append("reference_timestamp_utc_invalid_format")
    if not conflict_note:
        missing_meta.append("conflict_reconciliation_note")

    payload.update(
        {
            "evidence_ref": str(bundle_path),
            "evidence_bundle_path": str(bundle_path),
            "evidence_sha256": evidence_sha,
            "cross_verification_bundle_id": bundle_id,
            "source_url_set": source_urls,
            "source_url_count": len(source_urls),
            "reference_timestamp_utc": ref_ts,
            "conflict_reconciliation_note": conflict_note,
            "t1_status": track_status["t1"],
            "t2_status": track_status["t2"],
            "t3_status": track_status["t3"],
            "t4_status": track_status["t4"],
            "t1_roundtable_status": track_status["t1"],
            "t2_vendor_status": track_status["t2"],
            "t3_openai_context_status": track_status["t3"],
            "t4_protocol_spec_status": track_status["t4"],
            "track_status_map": track_status,
            "missing_tracks": missing_tracks,
            "missing_metadata_fields": missing_meta,
        }
    )

    stale_reasons: list[str] = []
    error_code = ""
    if missing_tracks:
        stale_reasons.append("track_quorum_not_satisfied")
        error_code = ERR_TRACK_QUORUM_MISSING
    if missing_meta:
        stale_reasons.append("metadata_quorum_not_satisfied")
        if not error_code:
            error_code = ERR_METADATA_MISSING
    if missing_tracks and missing_meta:
        error_code = ERR_TRACK_AND_METADATA_MISSING

    if stale_reasons:
        payload["intake_evidence_core_status"] = STATUS_FAIL_REQUIRED
        payload["cross_verification_tracks_status"] = STATUS_FAIL_REQUIRED
        payload["intake_evidence_quorum_status"] = STATUS_FAIL_REQUIRED
        payload[MODE_STATUS_KEYS[args.mode]] = STATUS_FAIL_REQUIRED
        payload["error_code"] = error_code
        payload["stale_reasons"] = stale_reasons
        _emit(payload, json_only=args.json_only)
        return 1

    payload["intake_evidence_core_status"] = STATUS_PASS_REQUIRED
    payload["cross_verification_tracks_status"] = STATUS_PASS_REQUIRED
    payload["intake_evidence_quorum_status"] = STATUS_PASS_REQUIRED
    payload[MODE_STATUS_KEYS[args.mode]] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    payload["stale_reasons"] = []
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
