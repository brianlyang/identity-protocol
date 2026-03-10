#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import yaml

STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"

ERR_PROFILE_PARSE = "IP-GATE-ENTRY-001"
ERR_PROFILE_CONTRACT = "IP-GATE-ENTRY-002"

DEFAULT_PROFILE_FILE = "identity/protocol/mappings/layer-targeted-gate-profile.v1.6.yaml"


def _load_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError(f"invalid yaml root: {path}")
    return data


def _as_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        token = str(item or "").strip()
        if token:
            out.append(token)
    return out


def _resolve_contract_mapping(repo_root: Path, explicit: str) -> Path:
    if str(explicit or "").strip():
        return Path(explicit).expanduser().resolve()
    mapping_dir = repo_root / "identity" / "protocol" / "mappings"
    candidates = sorted(mapping_dir.glob("contract-binding.v*.yaml"))
    if candidates:
        return candidates[-1]
    return mapping_dir / "contract-binding.yaml"


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate layer-targeted gate profile mapping for strict fail-close safety.")
    ap.add_argument("--repo-root", default=".")
    ap.add_argument("--profile-file", default=DEFAULT_PROFILE_FILE)
    ap.add_argument("--contract-mapping", default="")
    ap.add_argument("--json-only", action="store_true")
    args = ap.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    profile_path = (repo_root / str(args.profile_file)).resolve()
    mapping_path = _resolve_contract_mapping(repo_root, str(args.contract_mapping or ""))

    stale_reasons: list[str] = []
    violations: list[dict[str, Any]] = []
    parse_errors: list[str] = []

    profile_doc: dict[str, Any] = {}
    mapping_doc: dict[str, Any] = {}
    try:
        profile_doc = _load_yaml(profile_path)
    except Exception as exc:
        parse_errors.append(f"profile_file_invalid:{profile_path}:{exc}")
    try:
        mapping_doc = _load_yaml(mapping_path)
    except Exception as exc:
        parse_errors.append(f"contract_mapping_invalid:{mapping_path}:{exc}")

    requirement_rows = sorted(
        key
        for key in mapping_doc.keys()
        if isinstance(key, str) and key.startswith("asb16-rq-")
    )
    requirement_set = set(requirement_rows)

    if not parse_errors:
        default_profile = str(profile_doc.get("default_profile", "")).strip()
        profiles = profile_doc.get("profiles")
        strict_no_trim_operations = set(_as_str_list(profile_doc.get("strict_no_trim_operations")))
        if not default_profile:
            violations.append({"field": "default_profile", "reason": "default_profile_missing"})
        if not isinstance(profiles, dict) or not profiles:
            violations.append({"field": "profiles", "reason": "profiles_missing"})
            profiles = {}
        if not strict_no_trim_operations:
            violations.append(
                {"field": "strict_no_trim_operations", "reason": "strict_no_trim_operations_missing"}
            )

        for profile_name, raw in profiles.items():
            if not isinstance(raw, dict):
                violations.append(
                    {"field": f"profiles.{profile_name}", "reason": "profile_row_not_object"}
                )
                continue
            mode = str(raw.get("mode", "")).strip().lower() or "full"
            if mode not in {"full", "targeted"}:
                violations.append(
                    {
                        "field": f"profiles.{profile_name}.mode",
                        "reason": "profile_mode_invalid",
                        "value": mode,
                    }
                )
                continue

            allowed_operations = _as_str_list(raw.get("allowed_operations"))
            if not allowed_operations:
                violations.append(
                    {
                        "field": f"profiles.{profile_name}.allowed_operations",
                        "reason": "allowed_operations_missing",
                    }
                )
            requirement_keys = _as_str_list(raw.get("requirement_keys"))
            unknown_keys = [key for key in requirement_keys if key not in requirement_set]
            if unknown_keys:
                violations.append(
                    {
                        "field": f"profiles.{profile_name}.requirement_keys",
                        "reason": "unknown_requirement_keys",
                        "keys": unknown_keys,
                    }
                )

            if mode == "targeted":
                if not requirement_keys:
                    violations.append(
                        {
                            "field": f"profiles.{profile_name}.requirement_keys",
                            "reason": "targeted_profile_requires_requirement_keys",
                        }
                    )
                overlap = sorted(set(allowed_operations) & strict_no_trim_operations)
                if overlap:
                    violations.append(
                        {
                            "field": f"profiles.{profile_name}.allowed_operations",
                            "reason": "targeted_profile_forbidden_strict_operations",
                            "operations": overlap,
                        }
                    )
            else:
                if requirement_keys and set(requirement_keys) != requirement_set:
                    violations.append(
                        {
                            "field": f"profiles.{profile_name}.requirement_keys",
                            "reason": "full_profile_must_not_trim_requirement_set",
                            "requirement_count": len(requirement_keys),
                            "expected_requirement_count": len(requirement_set),
                        }
                    )
                if "*" not in allowed_operations:
                    violations.append(
                        {
                            "field": f"profiles.{profile_name}.allowed_operations",
                            "reason": "full_profile_requires_wildcard_operation",
                        }
                    )

        if default_profile and default_profile not in profiles:
            violations.append(
                {
                    "field": "default_profile",
                    "reason": "default_profile_not_found",
                    "value": default_profile,
                }
            )
        strict_profile = profiles.get("strict_full") if isinstance(profiles, dict) else None
        if not isinstance(strict_profile, dict):
            violations.append({"field": "profiles.strict_full", "reason": "strict_full_missing"})
        elif str(strict_profile.get("mode", "")).strip().lower() != "full":
            violations.append(
                {"field": "profiles.strict_full.mode", "reason": "strict_full_mode_must_be_full"}
            )

    if parse_errors:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_PROFILE_PARSE
        stale_reasons.extend(parse_errors)
    elif violations:
        status = STATUS_FAIL_REQUIRED
        error_code = ERR_PROFILE_CONTRACT
        stale_reasons.append("layer_targeted_gate_profile_violation")
    else:
        status = STATUS_PASS_REQUIRED
        error_code = ""

    payload: dict[str, Any] = {
        "layer_targeted_gate_profile_status": status,
        "error_code": error_code,
        "profile_file": str(profile_path),
        "contract_mapping": str(mapping_path),
        "profile_count": len((profile_doc.get("profiles") or {})) if isinstance(profile_doc, dict) else 0,
        "default_profile": str((profile_doc.get("default_profile") or "")) if isinstance(profile_doc, dict) else "",
        "strict_no_trim_operations": _as_str_list((profile_doc or {}).get("strict_no_trim_operations")),
        "requirement_row_count": len(requirement_rows),
        "parse_errors": parse_errors,
        "violation_count": len(violations),
        "violations": violations,
        "stale_reasons": stale_reasons,
    }

    if args.json_only:
        print(json.dumps(payload, ensure_ascii=False))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
