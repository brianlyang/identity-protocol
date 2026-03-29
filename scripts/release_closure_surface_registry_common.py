#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReleaseClosureSurfaceSpec:
    name: str
    validator_script_rel: str
    status_key: str
    probe_script_rel: str
    docs_command_contract_failure_tag: str
    bundle_surface_id: str | None = None

    def validator_command(self, *, json_only: bool = True) -> tuple[str, ...]:
        command: list[str] = ["python3", self.validator_script_rel]
        if json_only:
            command.append("--json-only")
        return tuple(command)

    def probe_command(self) -> tuple[str, ...]:
        return ("bash", self.probe_script_rel)


RELEASE_DOC_SURFACE_GOVERNANCE_SPEC = ReleaseClosureSurfaceSpec(
    name="release_doc_surface_governance",
    validator_script_rel="scripts/validate_release_doc_surface_governance.py",
    status_key="release_doc_surface_governance_status",
    probe_script_rel="scripts/ci/run_release_doc_surface_governance_probes_ci.sh",
    docs_command_contract_failure_tag="RELEASE_DOC_SURFACE_GOVERNANCE_FAIL",
)

RELEASE_CLOSURE_BOUNDARY_SURFACE_SPEC = ReleaseClosureSurfaceSpec(
    name="v16x_release_closure_boundary",
    validator_script_rel="scripts/validate_v16x_release_closure_boundary.py",
    status_key="v16x_release_closure_boundary_status",
    probe_script_rel="scripts/ci/run_v16x_release_closure_boundary_probes_ci.sh",
    docs_command_contract_failure_tag="RELEASE_CLOSURE_BOUNDARY_FAIL",
    bundle_surface_id="boundary",
)

RELEASE_CLOSURE_SUMMARY_SURFACE_SPEC = ReleaseClosureSurfaceSpec(
    name="v16x_release_closure_summary",
    validator_script_rel="scripts/validate_v16x_release_closure_summary.py",
    status_key="v16x_release_closure_summary_status",
    probe_script_rel="scripts/ci/run_v16x_release_closure_summary_probes_ci.sh",
    docs_command_contract_failure_tag="RELEASE_CLOSURE_SUMMARY_FAIL",
    bundle_surface_id="summary",
)

RELEASE_CLOSURE_SURFACE_SPECS: tuple[ReleaseClosureSurfaceSpec, ...] = (
    RELEASE_DOC_SURFACE_GOVERNANCE_SPEC,
    RELEASE_CLOSURE_BOUNDARY_SURFACE_SPEC,
    RELEASE_CLOSURE_SUMMARY_SURFACE_SPEC,
)


def release_closure_surface_specs() -> tuple[ReleaseClosureSurfaceSpec, ...]:
    return RELEASE_CLOSURE_SURFACE_SPECS


def release_closure_bundle_surface_specs() -> tuple[ReleaseClosureSurfaceSpec, ...]:
    return tuple(spec for spec in RELEASE_CLOSURE_SURFACE_SPECS if spec.bundle_surface_id)


def release_closure_surface_check_names() -> tuple[str, ...]:
    return tuple(spec.name for spec in RELEASE_CLOSURE_SURFACE_SPECS)


def release_closure_surface_post_closure_governance_commands() -> tuple[tuple[str, ...], ...]:
    return tuple(spec.probe_command() for spec in RELEASE_CLOSURE_SURFACE_SPECS)


def release_closure_surface_spec_by_name(name: str) -> ReleaseClosureSurfaceSpec | None:
    return next((spec for spec in RELEASE_CLOSURE_SURFACE_SPECS if spec.name == name), None)


def release_closure_surface_spec_by_bundle_surface_id(
    bundle_surface_id: str,
) -> ReleaseClosureSurfaceSpec | None:
    return next(
        (
            spec
            for spec in RELEASE_CLOSURE_SURFACE_SPECS
            if spec.bundle_surface_id == bundle_surface_id
        ),
        None,
    )


def _validate_release_closure_surface_specs() -> None:
    seen_names: set[str] = set()
    seen_validator_paths: set[str] = set()
    seen_status_keys: set[str] = set()
    seen_probe_paths: set[str] = set()
    seen_bundle_surface_ids: set[str] = set()
    for spec in RELEASE_CLOSURE_SURFACE_SPECS:
        if spec.name in seen_names:
            raise RuntimeError(f"release_closure_surface_duplicate_name:{spec.name}")
        seen_names.add(spec.name)
        if spec.validator_script_rel in seen_validator_paths:
            raise RuntimeError(
                f"release_closure_surface_duplicate_validator:{spec.validator_script_rel}"
            )
        seen_validator_paths.add(spec.validator_script_rel)
        if spec.status_key in seen_status_keys:
            raise RuntimeError(f"release_closure_surface_duplicate_status_key:{spec.status_key}")
        seen_status_keys.add(spec.status_key)
        if spec.probe_script_rel in seen_probe_paths:
            raise RuntimeError(
                f"release_closure_surface_duplicate_probe:{spec.probe_script_rel}"
            )
        seen_probe_paths.add(spec.probe_script_rel)
        if spec.bundle_surface_id:
            if spec.bundle_surface_id in seen_bundle_surface_ids:
                raise RuntimeError(
                    "release_closure_surface_duplicate_bundle_surface_id:"
                    + spec.bundle_surface_id
                )
            seen_bundle_surface_ids.add(spec.bundle_surface_id)


_validate_release_closure_surface_specs()
