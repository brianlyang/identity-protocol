from __future__ import annotations

STATUS_PROFILE_STRICT_FULL = "strict_full"
STATUS_PROFILE_LAUNCHER_WORKSPACE_CONVERGENCE = "launcher_workspace_convergence"
STATUS_PROFILE_WORKSPACE_RUNTIME_CONVERGENCE = "workspace_runtime_convergence"

CURRENT_RUN_PROJECTION_ENFORCEMENT_BLOCKING = "blocking"
CURRENT_RUN_PROJECTION_ENFORCEMENT_OBSERVE_NON_BLOCKING = "observe_non_blocking"

OBSERVE_NON_BLOCKING_STATUS_PROFILES: tuple[str, ...] = (
    STATUS_PROFILE_LAUNCHER_WORKSPACE_CONVERGENCE,
    STATUS_PROFILE_WORKSPACE_RUNTIME_CONVERGENCE,
)


def repair_contract_backfill_status_profile_choices() -> tuple[str, ...]:
    return (
        STATUS_PROFILE_STRICT_FULL,
        STATUS_PROFILE_LAUNCHER_WORKSPACE_CONVERGENCE,
        STATUS_PROFILE_WORKSPACE_RUNTIME_CONVERGENCE,
    )


def resolve_current_run_projection_enforcement_mode(*, status_profile: str) -> str:
    profile = str(status_profile or "").strip()
    if profile in OBSERVE_NON_BLOCKING_STATUS_PROFILES:
        return CURRENT_RUN_PROJECTION_ENFORCEMENT_OBSERVE_NON_BLOCKING
    return CURRENT_RUN_PROJECTION_ENFORCEMENT_BLOCKING


def repair_contract_backfill_status_profile_boundary_note() -> str:
    return (
        "strict_full keeps current-run weak-live / terminal-truth projection integrity failures fail-closed; "
        "launcher_workspace_convergence and workspace_runtime_convergence keep those failures machine-visible as "
        "observation-only residuals so workspace migration/adoption lanes do not claim terminal-truth or live-linkage closure"
    )
