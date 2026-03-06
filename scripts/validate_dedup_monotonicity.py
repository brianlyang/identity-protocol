#!/usr/bin/env python3
from __future__ import annotations

import argparse
import glob
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from tool_vendor_governance_common import contract_required, load_json, load_yaml, resolve_pack_and_task

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_SKIPPED_NOT_REQUIRED = "SKIPPED_NOT_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_CLAIMS_SOURCE_MISSING = "IP-DEDUP-001"
ERR_REQUIRED_FIELD_MISSING = "IP-DEDUP-002"
ERR_NON_MONOTONIC = "IP-DEDUP-003"
ERR_RUN_ID_SELECTION = "IP-DEDUP-004"

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

CONTRACT_KEYS = (
    "dedup_monotonic_winner_contract_v1",
    "dedup_monotonic_winner_contract",
    "rq_018_dedup_monotonic_winner_contract_v1",
)


@dataclass
class ClaimRow:
    run_id: str
    claim_ts_raw: str
    claim_ts_norm: str
    claim_ts_sort_key: str
    stable_tiebreaker: str
    winner_id: str


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    if json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def _normalize_iso_utc(value: str) -> tuple[str, str]:
    raw = str(value or "").strip()
    if not raw:
        return "", ""
    try:
        if raw.endswith("Z"):
            dt = datetime.fromisoformat(raw[:-1] + "+00:00")
        else:
            dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        utc_dt = dt.astimezone(timezone.utc)
        norm = utc_dt.isoformat().replace("+00:00", "Z")
        sort_key = utc_dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        return norm, sort_key
    except Exception:
        return "", ""


def _nonempty(*values: Any) -> str:
    for v in values:
        s = str(v or "").strip()
        if s:
            return s
    return ""


def _iter_pattern_hits(base: Path, pattern: str) -> list[Path]:
    pat = str(pattern or "").strip()
    if not pat:
        return []
    p = Path(pat).expanduser()
    if p.is_absolute():
        return [Path(x).expanduser().resolve() for x in sorted(glob.glob(str(pat))) if Path(x).is_file()]
    preferred = sorted(base.glob(pat))
    if preferred:
        return [x.resolve() for x in preferred if x.is_file()]
    return [x.resolve() for x in Path(".").glob(pat) if x.is_file()]


def _select_contract(task: dict[str, Any]) -> dict[str, Any]:
    for key in CONTRACT_KEYS:
        node = task.get(key)
        if isinstance(node, dict):
            return node
    return {}


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


def _resolve_claims_path(*, explicit_claims: str, contract: dict[str, Any], pack_path: Path, run_id: str) -> Path | None:
    if explicit_claims.strip():
        p = Path(explicit_claims).expanduser().resolve()
        return p if p.exists() and p.is_file() else None

    contract_patterns: list[str] = []
    for key in (
        "claims_path_pattern",
        "report_path_pattern",
        "evidence_path_pattern",
        "receipt_path_pattern",
        "replay_receipt_pattern",
    ):
        v = contract.get(key)
        if isinstance(v, str) and v.strip():
            contract_patterns.append(v.strip())

    fallback_patterns = [
        "runtime/protocol-feedback/**/*dedup*claim*.json",
        "runtime/protocol-feedback/**/*dedup*.json",
        "runtime/reports/**/*dedup*.json",
        "runtime/reports/**/*orchestr*dedup*.json",
        "resource/reports/**/*dedup*.json",
    ]

    def _collect_hits(patterns: list[str]) -> list[Path]:
        rows: list[Path] = []
        for pat in patterns:
            rows.extend(_iter_pattern_hits(pack_path, pat))
        dedup_hits: dict[str, Path] = {h.resolve().as_posix(): h.resolve() for h in rows}
        return list(dedup_hits.values())

    # First prefer contract-declared patterns, but do not hard-lock to them.
    # If contract patterns are stale/misaligned, fall back to canonical runtime defaults.
    hits = _collect_hits(contract_patterns) if contract_patterns else []
    if not hits:
        hits = _collect_hits(fallback_patterns)
    if not hits:
        return None

    rows = list(hits)
    if run_id.strip():
        run_hits = [x for x in rows if run_id in x.name]
        if run_hits:
            rows = run_hits
    rows.sort(key=lambda p: p.stat().st_mtime)
    return rows[-1]


def _load_claim_doc(path: Path) -> Any:
    raw = path.read_text(encoding="utf-8", errors="ignore")
    try:
        return json.loads(raw)
    except Exception:
        return load_yaml(path)


def _extract_rows(doc: Any) -> list[dict[str, Any]]:
    if isinstance(doc, list):
        return [x for x in doc if isinstance(x, dict)]
    if not isinstance(doc, dict):
        return []

    for key in (
        "claims",
        "claim_rows",
        "events",
        "records",
        "candidates",
        "dedup_claims",
        "items",
    ):
        node = doc.get(key)
        if isinstance(node, list):
            rows = [x for x in node if isinstance(x, dict)]
            if rows:
                return rows

    if any(k in doc for k in ("run_id", "claim_ts", "earliest_claim_ts", "claimed_at_utc", "winner_id", "claimant_id")):
        return [doc]

    nested = doc.get("dedup_monotonicity")
    if isinstance(nested, dict):
        return _extract_rows(nested)
    return []


def _normalize_row(node: dict[str, Any], default_run_id: str) -> ClaimRow | None:
    run_id = _nonempty(node.get("run_id"), node.get("runId"), node.get("activity_run_id"), node.get("session_id"), default_run_id)
    claim_ts_raw = _nonempty(
        node.get("earliest_claim_ts"),
        node.get("claim_ts"),
        node.get("claimed_at_utc"),
        node.get("observed_at_utc"),
        node.get("timestamp_utc"),
        node.get("created_at"),
    )
    claim_ts_norm, claim_ts_sort = _normalize_iso_utc(claim_ts_raw)
    stable_tiebreaker = _nonempty(
        node.get("stable_tiebreaker"),
        node.get("tie_breaker"),
        node.get("claimant_id"),
        node.get("candidate_id"),
        node.get("event_id"),
        node.get("id"),
    )
    winner_id = _nonempty(
        node.get("winner_id"),
        node.get("claimant_id"),
        node.get("candidate_id"),
        node.get("actor_id"),
        node.get("id"),
    )

    if not run_id or not claim_ts_norm or not claim_ts_sort or not stable_tiebreaker or not winner_id:
        return None

    return ClaimRow(
        run_id=run_id,
        claim_ts_raw=claim_ts_raw,
        claim_ts_norm=claim_ts_norm,
        claim_ts_sort_key=claim_ts_sort,
        stable_tiebreaker=stable_tiebreaker,
        winner_id=winner_id,
    )


def _choose_group(rows: list[ClaimRow], run_id_hint: str) -> tuple[str, list[ClaimRow], str]:
    groups: dict[str, list[ClaimRow]] = {}
    for row in rows:
        groups.setdefault(row.run_id, []).append(row)

    if run_id_hint.strip():
        selected = groups.get(run_id_hint.strip())
        if not selected:
            return "", [], "run_id_not_found"
        return run_id_hint.strip(), selected, "explicit_run_id"

    if not groups:
        return "", [], "no_groups"
    if len(groups) == 1:
        only = next(iter(groups.keys()))
        return only, groups[only], "single_group"

    sorted_groups = sorted(groups.items(), key=lambda kv: len(kv[1]), reverse=True)
    top_size = len(sorted_groups[0][1]) if sorted_groups else 0
    top = [kv for kv in sorted_groups if len(kv[1]) == top_size]
    if len(top) > 1:
        return "", [], "ambiguous_run_id_groups"
    return top[0][0], top[0][1], "largest_group"


def _winner_for_group(rows: list[ClaimRow]) -> tuple[ClaimRow, int, bool]:
    ordered = sorted(rows, key=lambda r: (r.claim_ts_sort_key, r.stable_tiebreaker, r.winner_id))
    winner = ordered[0]
    tie_count = sum(
        1
        for r in ordered
        if r.claim_ts_sort_key == winner.claim_ts_sort_key and r.stable_tiebreaker == winner.stable_tiebreaker
    )
    ambiguous = tie_count > 1
    return winner, tie_count, ambiguous


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate dedup monotonic winner determinism (RQ-018).")
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--identity-id", required=True)
    ap.add_argument("--claims", default="")
    ap.add_argument("--run-id", default="")
    ap.add_argument("--parallel-claims", type=int, default=0)
    ap.add_argument(
        "--operation",
        choices=["activate", "update", "readiness", "e2e", "ci", "validate", "scan", "three-plane", "inspection", "mutation"],
        default="validate",
    )
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

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

    payload: dict[str, Any] = {
        "identity_id": args.identity_id,
        "catalog_path": str(catalog_path),
        "resolved_pack_path": str(pack_path),
        "operation": args.operation,
        "required_contract": False,
        "auto_required_signal": False,
        "claims_path": "",
        "evidence_ref": "",
        "run_id": "",
        "parallel_claims_requested": int(args.parallel_claims or 0),
        "claim_rows_total": 0,
        "grouped_run_count": 0,
        "candidate_count": 0,
        "earliest_claim_ts": "",
        "stable_tiebreaker": "",
        "winner_id": "",
        "winner_reason": "",
        "tie_candidate_count": 0,
        "monotonicity_status": STATUS_SKIPPED_NOT_REQUIRED,
        "error_code": "",
        "stale_reasons": [],
    }

    if _is_fixture_identity(catalog_path, args.identity_id):
        payload["stale_reasons"] = ["fixture_profile_scope"]
        _emit(payload, json_only=args.json_only)
        return 0

    contract = _select_contract(task)
    required = contract_required(contract) if contract else False
    auto_required = False

    if args.claims.strip() or args.run_id.strip() or args.parallel_claims > 0:
        required = True
        auto_required = True
    elif args.operation in STRICT_OPERATIONS:
        # strict ops allow deterministic requiredization when contract is declared required.
        auto_required = False

    payload["required_contract"] = required
    payload["auto_required_signal"] = auto_required

    if not required:
        payload["stale_reasons"] = ["contract_not_required"]
        _emit(payload, json_only=args.json_only)
        return 0

    claims_path = _resolve_claims_path(
        explicit_claims=args.claims,
        contract=contract if isinstance(contract, dict) else {},
        pack_path=pack_path,
        run_id=args.run_id,
    )
    if claims_path is None:
        payload["monotonicity_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_CLAIMS_SOURCE_MISSING
        payload["stale_reasons"] = ["claims_source_missing"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["claims_path"] = str(claims_path)
    payload["evidence_ref"] = str(claims_path)

    doc = _load_claim_doc(claims_path)
    raw_rows = _extract_rows(doc)
    payload["claim_rows_total"] = len(raw_rows)
    if not raw_rows:
        payload["monotonicity_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_CLAIMS_SOURCE_MISSING
        payload["stale_reasons"] = ["claims_rows_empty"]
        _emit(payload, json_only=args.json_only)
        return 1

    normalized: list[ClaimRow] = []
    invalid_count = 0
    for node in raw_rows:
        row = _normalize_row(node, default_run_id=args.run_id)
        if row is None:
            invalid_count += 1
            continue
        normalized.append(row)

    if invalid_count > 0:
        payload["monotonicity_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_REQUIRED_FIELD_MISSING
        payload["stale_reasons"] = ["required_claim_fields_missing"]
        payload["candidate_count"] = len(normalized)
        _emit(payload, json_only=args.json_only)
        return 1

    run_id, selected_rows, select_reason = _choose_group(normalized, args.run_id)
    payload["grouped_run_count"] = len({x.run_id for x in normalized})
    payload["run_id"] = run_id
    payload["candidate_count"] = len(selected_rows)

    if not run_id or not selected_rows:
        payload["monotonicity_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_RUN_ID_SELECTION
        payload["stale_reasons"] = [select_reason or "run_id_selection_failed"]
        _emit(payload, json_only=args.json_only)
        return 1

    winner, tie_count, ambiguous = _winner_for_group(selected_rows)
    payload["earliest_claim_ts"] = winner.claim_ts_norm
    payload["stable_tiebreaker"] = winner.stable_tiebreaker
    payload["winner_id"] = winner.winner_id
    payload["winner_reason"] = "earliest_claim_ts_then_stable_tiebreaker"
    payload["tie_candidate_count"] = tie_count

    if ambiguous:
        payload["monotonicity_status"] = STATUS_FAIL_REQUIRED
        payload["error_code"] = ERR_NON_MONOTONIC
        payload["stale_reasons"] = ["ambiguous_winner_after_tiebreaker"]
        _emit(payload, json_only=args.json_only)
        return 1

    payload["monotonicity_status"] = STATUS_PASS_REQUIRED
    payload["error_code"] = ""
    payload["stale_reasons"] = []
    _emit(payload, json_only=args.json_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
