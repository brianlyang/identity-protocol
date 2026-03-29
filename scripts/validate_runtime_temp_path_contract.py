#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


STATUS_PASS_REQUIRED = "PASS_REQUIRED"
STATUS_FAIL_REQUIRED = "FAIL_REQUIRED"
ERR_RUNTIME_TEMP_PATH = "IP-TMP-CONTRACT-001"

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent

TARGET_RULES = {
    "scripts/create_identity_pack.py": {
        "required": ("identity_runtime_named_temp_root(",),
        "forbidden": ('Path("/tmp")',),
    },
    "scripts/validate_identity_switch_closure_semantics.py": {
        "required": ("identity_runtime_mkdtemp(",),
        "forbidden": ('dir="/tmp"',),
    },
    "scripts/ci/run_native_chat_bootstrap_entry_probes_ci.sh": {
        "required": ("source \"$ROOT/scripts/runtime_temp_path_common.sh\"", "identity_runtime_mktemp_dir_sh"),
        "forbidden": ("mktemp -d \"$TMP_ROOT_BASE",),
    },
    "scripts/ci/probe_runtime_tmp_common.sh": {
        "required": (
            'source "${repo_root}/scripts/runtime_temp_path_common.sh"',
            'IDENTITY_RUNTIME_TMP_ROOT:-${repo_root}/.tmp',
            'identity_runtime_mktemp_dir_sh "${temp_scope}" "${temp_prefix}"',
        ),
        "forbidden": ('mktemp -d "${TMPDIR:-/tmp}/',),
    },
    "scripts/ci/protocol_root_probe_shadow_common.sh": {
        "required": (
            'source "${ROOT}/scripts/ci/probe_runtime_tmp_common.sh"',
            'probe_runtime_tmp_bootstrap "${ROOT}" "protocol-root-probes" "${tmp_prefix}"',
        ),
        "forbidden": (
            'source "${ROOT}/scripts/runtime_temp_path_common.sh"',
            'identity_runtime_mktemp_dir_sh "protocol-root-probes" "${tmp_prefix}"',
            'mktemp -d "${TMPDIR:-/tmp}/',
        ),
    },
    "scripts/ci/run_identity_artifact_family_routing_probes_ci.sh": {
        "required": (
            'source "${ROOT}/scripts/ci/probe_runtime_tmp_common.sh"',
            'probe_runtime_tmp_bootstrap "${ROOT}" "identity-artifact-family-routing-probes" "run"',
        ),
        "forbidden": ('mktemp -d "${TMPDIR:-/tmp}/',),
    },
    "scripts/ci/run_identity_dialogue_retention_probes_ci.sh": {
        "required": (
            'source "${REPO_ROOT}/scripts/ci/probe_runtime_tmp_common.sh"',
            'probe_runtime_tmp_bootstrap "${REPO_ROOT}" "identity-dialogue-retention-probes" "run"',
        ),
        "forbidden": ('mktemp -d "${TMPDIR:-/tmp}/',),
    },
    "scripts/ci/run_identity_broadcast_delivery_probes_ci.sh": {
        "required": (
            'source "${ROOT}/scripts/ci/probe_runtime_tmp_common.sh"',
            'probe_runtime_tmp_bootstrap "${ROOT}" "identity-broadcast-delivery-probes" "run"',
        ),
        "forbidden": ('mktemp -d "${TMPDIR:-/tmp}/',),
    },
}


def main() -> int:
    violations: list[dict[str, str]] = []
    for rel, rule in TARGET_RULES.items():
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        for token in rule["required"]:
            if token not in text:
                violations.append({"file": rel, "reason": "required_temp_helper_missing", "token": token})
        for token in rule["forbidden"]:
            if token in text:
                violations.append({"file": rel, "reason": "forbidden_direct_temp_usage_present", "token": token})

    status = STATUS_PASS_REQUIRED if not violations else STATUS_FAIL_REQUIRED
    payload = {
        "runtime_temp_path_contract_status": status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else ERR_RUNTIME_TEMP_PATH,
        "checked_files": sorted(TARGET_RULES),
        "violations": violations,
    }
    print(json.dumps(payload, ensure_ascii=False))
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
