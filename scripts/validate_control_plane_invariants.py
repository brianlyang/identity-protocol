#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_INVARIANT = "IP-CP-INV-001"


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return data if isinstance(data, dict) else {}


def _mapping_rows(mapping_doc: dict[str, Any]) -> list[str]:
    return sorted(k for k in mapping_doc.keys() if isinstance(k, str) and k.startswith("asb16-rq-"))


def _bundle_rows() -> list[str]:
    from required_gate_bundle_runner import BUNDLE_REQUIREMENT_ORDER  # local import for script stability

    return sorted(set(str(x).strip() for x in BUNDLE_REQUIREMENT_ORDER if str(x).strip()))


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate control-plane invariants (bundle/mapping parity mode).")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument(
        "--invariants-file",
        default="identity/protocol/mappings/control-plane-invariants.v1.6.yaml",
    )
    parser.add_argument(
        "--contract-mapping",
        default="identity/protocol/mappings/contract-binding.v1.6.yaml",
    )
    parser.add_argument("--json-only", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    invariants_path = (repo_root / str(args.invariants_file)).resolve()
    mapping_path = (repo_root / str(args.contract_mapping)).resolve()

    stale_reasons: list[str] = []
    violations: list[dict[str, Any]] = []

    if not invariants_path.exists():
        stale_reasons.append(f"invariants_file_missing:{invariants_path}")
    if not mapping_path.exists():
        stale_reasons.append(f"contract_mapping_missing:{mapping_path}")

    missing_rows: list[str] = []
    extra_rows: list[str] = []
    mode = ""
    baseline_missing_rows = -1

    if not stale_reasons:
        inv_doc = _load_yaml(invariants_path)
        invariants = inv_doc.get("invariants") or {}
        parity_cfg = (invariants.get("bundle_mapping_parity") or {}) if isinstance(invariants, dict) else {}
        mode = str(parity_cfg.get("mode", "")).strip().lower() or "freeze"
        baseline_missing_rows = int(parity_cfg.get("baseline_missing_rows", -1))

        mapping_doc = _load_yaml(mapping_path)
        mapping_rows = _mapping_rows(mapping_doc)
        bundle_rows = _bundle_rows()
        missing_rows = sorted(x for x in mapping_rows if x not in bundle_rows)
        extra_rows = sorted(x for x in bundle_rows if x not in mapping_rows)

        if extra_rows:
            violations.append(
                {
                    "field": "bundle_rows_not_in_mapping",
                    "reason": "bundle_row_without_mapping",
                    "rows": extra_rows,
                }
            )

        if mode == "strict":
            if missing_rows:
                violations.append(
                    {
                        "field": "mapping_rows_missing_in_bundle",
                        "reason": "bundle_mapping_parity_strict_violation",
                        "mode": mode,
                        "missing_rows": missing_rows,
                        "missing_count": len(missing_rows),
                    }
                )
        elif mode == "freeze":
            if baseline_missing_rows < 0:
                violations.append(
                    {
                        "field": "bundle_mapping_parity_baseline",
                        "reason": "freeze_mode_baseline_missing",
                        "mode": mode,
                    }
                )
            elif len(missing_rows) > baseline_missing_rows:
                violations.append(
                    {
                        "field": "mapping_rows_missing_in_bundle",
                        "reason": "bundle_mapping_gap_growth_in_freeze_mode",
                        "mode": mode,
                        "missing_count": len(missing_rows),
                        "baseline_missing_rows": baseline_missing_rows,
                        "missing_rows": missing_rows,
                    }
                )
        else:
            violations.append(
                {
                    "field": "bundle_mapping_parity_mode",
                    "reason": "invalid_mode",
                    "mode": mode,
                }
            )

    if stale_reasons or violations:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_INVARIANT
    else:
        status = STATUS_PASS_REQUIRED
        error_code = ""

    payload = {
        "control_plane_invariants_status": status,
        "error_code": error_code,
        "invariants_file": str(invariants_path),
        "contract_mapping": str(mapping_path),
        "bundle_mapping_parity_mode": mode,
        "bundle_mapping_parity_baseline_missing_rows": baseline_missing_rows,
        "mapping_rows_missing_in_bundle_count": len(missing_rows),
        "mapping_rows_missing_in_bundle": missing_rows,
        "bundle_rows_not_in_mapping_count": len(extra_rows),
        "bundle_rows_not_in_mapping": extra_rows,
        "violation_count": len(violations),
        "violations": violations,
        "stale_reasons": stale_reasons,
    }

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(
            f"[CONTROL-PLANE-INVARIANTS] status={status} "
            f"mode={mode or '-'} "
            f"mapping_missing={len(missing_rows)} "
            f"extra_bundle_rows={len(extra_rows)} "
            f"violations={len(violations)}"
        )
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
