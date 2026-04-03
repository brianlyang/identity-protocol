#!/usr/bin/env python3
from __future__ import annotations


RUNTIME_SUMMARY_SURFACE_GOVERNANCE_VALIDATOR = (
    "scripts/validate_runtime_summary_surface_governance.py"
)
RUNTIME_SUMMARY_SURFACE_GOVERNANCE_PROBE = (
    "scripts/ci/run_runtime_summary_surface_governance_probes_ci.sh"
)
RUNTIME_SUMMARY_SURFACE_GOVERNANCE_VALIDATOR_COMMAND: tuple[str, ...] = (
    "python3",
    RUNTIME_SUMMARY_SURFACE_GOVERNANCE_VALIDATOR,
    "--json-only",
)
RUNTIME_SUMMARY_SURFACE_GOVERNANCE_PROBE_COMMAND: tuple[str, ...] = (
    "bash",
    RUNTIME_SUMMARY_SURFACE_GOVERNANCE_PROBE,
)
RUNTIME_SUMMARY_SURFACE_GOVERNANCE_PROBE_SUMMARY_KEY = (
    "runtime_summary_surface_governance_probe"
)
RUNTIME_SUMMARY_SURFACE_GOVERNANCE_PROBE_ONE_LOOK_FIELD = (
    "runtime_summary_surface_governance_probe_status"
)
RUNTIME_SUMMARY_SURFACE_GOVERNANCE_PROBE_STATUS_FIELDS: tuple[str, ...] = (
    RUNTIME_SUMMARY_SURFACE_GOVERNANCE_PROBE_ONE_LOOK_FIELD,
)
RUNTIME_SUMMARY_SURFACE_GOVERNANCE_PROBE_KEEP_FIELDS: tuple[str, ...] = (
    "positive_validator_output",
)
