#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from typing import Any

from repo_root_resolution_common import resolve_repo_root
from root_contract_anchor_checks_common import (
    append_root_doc_anchor_registry_structure_violations,
    evaluate_root_doc_anchor_checks,
    validate_expected_root_doc_anchor_checks,
)
from root_contract_integration_checks_common import append_membership_delta_violations
from root_contract_row_validation_common import validate_contract_row_batches
from root_corpus_authority_common import entry_authority_projections_from_doc, load_root_corpus_authority
from root_corpus_gateway_admissibility_common import gateway_effect_targets_from_doc, load_root_corpus_gateway_admissibility
from root_corpus_governance_common import load_root_corpus_registry, root_corpus_entries_from_registry
from root_corpus_ordering_common import load_root_corpus_ordering, reading_order_rows_from_doc
from root_corpus_question_routing_common import (
    STATUS_FAIL_REQUIRED,
    STATUS_PASS_REQUIRED,
    adjudication_redirect_from_doc,
    entry_summary_stages_from_doc,
    entry_question_projections_from_doc,
    gateway_question_projections_from_doc,
    load_root_corpus_question_routing,
    question_routing_completeness_rows_from_doc,
    question_class_profiles_from_doc,
    question_routing_anchor_checks_from_doc,
    readme_question_routing_completeness_surface,
    readme_root_question_discipline_surface,
    readme_entry_summary_surface,
    root_question_discipline_stages_from_doc,
)
from root_row_family_projection_common import aggregate_row_family_status, project_root_contract_support_projection, project_row_families

STATUS_KEY = "protocol_root_corpus_question_routing_status"
ERR_REGISTRY = "IP-RCQR-001"
ERR_STRUCTURE = "IP-RCQR-002"
ERR_ROUTING = "IP-RCQR-003"

EXPECTED_QUESTION_RULES = {
    "generative_why": {
        "answer_mode": "interpretive_answer_only",
        "current_turn_authority_allowed": False,
        "root_entry_required": True,
        "authority_mode": "interpretive_only",
        "corpus_class": "bottom_theory",
    },
    "root_entry_navigation": {
        "answer_mode": "navigational_answer_only",
        "current_turn_authority_allowed": False,
        "root_entry_required": True,
        "authority_mode": "navigational_only",
        "corpus_class": "root_index",
    },
    "frozen_protocol_law": {
        "answer_mode": "frozen_law_answer",
        "current_turn_authority_allowed": False,
        "root_entry_required": True,
        "authority_mode": "frozen_law_only",
        "corpus_class": "constitution",
    },
    "frozen_runtime_law": {
        "answer_mode": "frozen_law_answer",
        "current_turn_authority_allowed": False,
        "root_entry_required": True,
        "authority_mode": "frozen_law_only",
        "corpus_class": "runtime_constitution",
    },
    "frozen_domain_contract_law": {
        "answer_mode": "frozen_law_answer",
        "current_turn_authority_allowed": False,
        "root_entry_required": True,
        "authority_mode": "frozen_law_only",
        "corpus_class": "root_contract",
    },
    "registry_resolution": {
        "answer_mode": "machine_registry_answer",
        "current_turn_authority_allowed": True,
        "root_entry_required": True,
        "authority_mode": "machine_consumed_family",
        "corpus_class": "machine_registry_directory",
    },
    "governed_extension_law": {
        "answer_mode": "extension_answer",
        "current_turn_authority_allowed": False,
        "root_entry_required": True,
        "authority_mode": "extension_family",
        "corpus_class": "governed_subdomain_extension",
    },
    "support_material_lookup": {
        "answer_mode": "support_material_answer",
        "current_turn_authority_allowed": False,
        "root_entry_required": True,
        "authority_mode": "demoted_support_only",
        "corpus_class": "demoted_support_directory",
    },
    "current_turn_legality": {
        "answer_mode": "redirect_to_machine_enforcement",
        "current_turn_authority_allowed": True,
        "root_entry_required": False,
        "authority_mode": "",
        "corpus_class": "",
    },
}
ALLOWED_ANSWER_MODES = {
    "interpretive_answer_only",
    "navigational_answer_only",
    "frozen_law_answer",
    "machine_registry_answer",
    "extension_answer",
    "support_material_answer",
    "redirect_to_machine_enforcement",
}
EXPECTED_TERMINAL_MACHINE_SURFACES = (
    "mappings",
    "validators",
    "probes",
    "runtime_state",
    "receipts",
)
EXPECTED_ENTRY_SUMMARY_STAGES = {
    "bottom theory first": {
        "order": 1,
        "bound_question_classes": ("generative_why",),
        "required_markers": (
            "read `IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md` to understand the bottom theory.",
        ),
        "terminal_machine_surfaces": (),
    },
    "constitutions next": {
        "order": 2,
        "bound_question_classes": ("frozen_protocol_law", "frozen_runtime_law"),
        "required_markers": (
            "read `IDENTITY_PROTOCOL.md` and `IDENTITY_RUNTIME.md` to understand protocol and runtime constitutions.",
        ),
        "terminal_machine_surfaces": (),
    },
    "relevant root contract after that": {
        "order": 3,
        "bound_question_classes": ("frozen_domain_contract_law",),
        "required_markers": (
            "read the relevant root contract file for the concrete domain being executed.",
        ),
        "terminal_machine_surfaces": (),
    },
    "machine-consumed verdict surfaces last": {
        "order": 4,
        "bound_question_classes": ("current_turn_legality",),
        "required_markers": (
            "read mappings, validators, probes, runtime state, and receipts for the final machine-consumed verdict.",
        ),
        "terminal_machine_surfaces": EXPECTED_TERMINAL_MACHINE_SURFACES,
    },
}
EXPECTED_QUESTION_ROUTING_COMPLETENESS_ROWS = {
    "explicit_question_routing_row_families": {
        "order": 1,
        "contract_phrase": "required question-class-profile, root-entry-question-projection, root-question-discipline-stage, root-question-discipline-stage-surface, entry-summary-stage, entry-summary-stage-surface, and gateway-question-projection rows must remain explicit as separate machine-readable row families;",
    },
    "congruent_question_routing_row_family_totals": {
        "order": 2,
        "contract_phrase": "expected row-family total and emitted row-family total must remain congruent under machine-readable coverage completeness rather than being left implicit;",
    },
    "explicit_question_routing_row_identity_sets": {
        "order": 3,
        "contract_phrase": "expected row identity set and emitted row identity set for each family must also remain machine-readable rather than being collapsed into aggregate counts;",
    },
    "hidden_question_routing_identity_drift_forbidden": {
        "order": 4,
        "contract_phrase": "runtime or validator code must not finalize question-routing legality while missing or unexpected question-class, root-question-discipline-stage, entry-summary-stage, or route identities remain known only internally;",
    },
    "fail_close_preserves_question_routing_identity_projection": {
        "order": 5,
        "contract_phrase": "fail-close machine output must preserve missing/unexpected row identity projection rather than hiding drift behind row-count shorthand or generic structure failure.",
    },
}
EXPECTED_ROOT_QUESTION_DISCIPLINE_STAGES = {
    "generative why-question": {
        "order": 1,
        "bound_question_classes": ("generative_why",),
        "bound_corpus_classes": ("bottom_theory",),
        "bound_gateway_classes": (),
        "required_markers": (
            "`IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md`",
            "why identity protocol law exists in this shape at all.",
        ),
    },
    "root-entry question": {
        "order": 2,
        "bound_question_classes": ("root_entry_navigation",),
        "bound_corpus_classes": ("root_index",),
        "bound_gateway_classes": (),
        "required_markers": (
            "`README.md`",
            "how to enter the root corpus without semantic confusion.",
        ),
    },
    "constitutional law question": {
        "order": 3,
        "bound_question_classes": ("frozen_protocol_law", "frozen_runtime_law"),
        "bound_corpus_classes": ("constitution", "runtime_constitution"),
        "bound_gateway_classes": (),
        "required_markers": (
            "`IDENTITY_PROTOCOL.md`",
            "`IDENTITY_RUNTIME.md`",
            "what protocol-law and runtime-law are concretely frozen.",
        ),
    },
    "domain-law question": {
        "order": 4,
        "bound_question_classes": ("frozen_domain_contract_law",),
        "bound_corpus_classes": ("root_contract",),
        "bound_gateway_classes": (),
        "required_markers": (
            "root contract files.",
            "what concrete root-domain contract law is frozen.",
        ),
    },
    "machine-registry question": {
        "order": 5,
        "bound_question_classes": ("registry_resolution",),
        "bound_corpus_classes": ("machine_registry_directory",),
        "bound_gateway_classes": (),
        "required_markers": (
            "`mappings/`",
            "which aliases, active files, bindings, and registry rows are machine-consumed truth.",
        ),
    },
    "governed extension question": {
        "order": 6,
        "bound_question_classes": ("governed_extension_law",),
        "bound_corpus_classes": ("governed_subdomain_extension",),
        "bound_gateway_classes": (),
        "required_markers": (
            "`broadcast/`",
            "`plugins/`",
            "what narrower subdomain law is frozen under the root corpus.",
        ),
    },
    "support-material question": {
        "order": 7,
        "bound_question_classes": ("support_material_lookup",),
        "bound_corpus_classes": ("demoted_support_directory",),
        "bound_gateway_classes": (),
        "required_markers": (
            "`fixtures/`",
            "what demoted support material exists without becoming runtime truth.",
        ),
    },
    "gateway target question class preserved": {
        "order": 8,
        "bound_question_classes": (
            "frozen_protocol_law",
            "frozen_runtime_law",
            "frozen_domain_contract_law",
            "registry_resolution",
        ),
        "bound_corpus_classes": (),
        "bound_gateway_classes": (
            "constitution",
            "runtime_constitution",
            "root_contract",
            "machine_registry_directory",
        ),
        "required_markers": (
            "gateway-mediated refreezing or projection keeps the question class governed by the gateway target layer.",
            "it does not inherit a new answer class from incoming motivation or local convenience.",
        ),
    },
}
EXPECTED_FORBIDDEN_ROOT_CLASSES = (
    "bottom_theory",
    "root_index",
    "constitution",
    "runtime_constitution",
    "root_contract",
    "governed_subdomain_extension",
    "demoted_support_directory",
)
EXPECTED_ROOT_DOC_ANCHOR_CHECKS = {
    "identity/protocol/README.md": (
        "## Root question-routing discipline",
        "This question-routing discipline must remain bound to canonical root-question-discipline stage rows rather than becoming a freehand alternate question ladder.",
        "## Root question-routing completeness discipline",
        "These question-routing-completeness rules must remain bound to canonical question-routing-completeness rows rather than drifting into soft summary prose.",
        "required question-class-profile, root-entry-question-projection, root-question-discipline-stage, root-question-discipline-stage-surface, entry-summary-stage, entry-summary-stage-surface, and gateway-question-projection rows must remain explicit as separate machine-readable row families;",
        "runtime or validator code must not finalize question-routing legality while missing or unexpected question-class, root-question-discipline-stage, entry-summary-stage, or route identities remain known only internally;",
        "gateway-mediated refreezing or projection keeps the question class governed by the gateway target layer.",
        "current-turn legality question must never terminate in philosophy text, README text, or frozen contract prose alone.",
        "## Machine-world entry summary",
        "This minimum-correct-path summary must remain bound to canonical entry-summary-stage rows rather than becoming oral navigation advice.",
        "That is the canonical reading order for this directory.",
    ),
    "identity/protocol/IDENTITY_PROTOCOL_DESIGN_PHILOSOPHY.md": (
        "### Question class and answer surface must stay paired",
        "No layer should answer a question that belongs to a different layer.",
        "Gateway-mediated refreezing or projection must preserve the question class of its governed target layer rather than inheriting a new answer class from incoming motivation.",
        "README root question-routing discipline must therefore stay congruent with admitted root-question-discipline-stage rows rather than becoming a freehand alternate question ladder.",
        "Required question-class-profile, root-entry-question-projection, root-question-discipline-stage, root-question-discipline-stage-surface, entry-summary-stage, entry-summary-stage-surface, and gateway-question-projection families must remain explicit as separate machine-readable row families.",
        "The machine world must not finalize question-routing legality while required question-class, root-question-discipline-stage, entry-summary-stage, or route identity drift remains known only internally.",
        "### Question-routing row-family completeness must stay explicit",
        "README machine-world entry summary must therefore stay congruent with admitted entry-summary-stage rows rather than becoming oral navigation advice.",
        "README root question-routing completeness discipline must therefore stay congruent with admitted question-routing-completeness rows rather than becoming a freehand completeness summary.",
    ),
    "identity/protocol/IDENTITY_PROTOCOL.md": (
        "## Root question-routing completeness boundary",
        "Question-routing law must remain machine-readable as separate question-class-profile, root-entry-question-projection, root-question-discipline-stage, root-question-discipline-stage-surface, entry-summary-stage, entry-summary-stage-surface, and gateway-question-projection row families.",
        "README root question-routing discipline rendered at protocol root must remain congruent with admitted root-question-discipline-stage rows rather than silently authoring an alternate question ladder.",
        "README machine-world entry summary rendered at protocol root must remain congruent with admitted entry-summary-stage rows rather than silently authoring an alternate minimum-correct path.",
        "README root question-routing completeness discipline rendered at protocol root must remain congruent with admitted question-routing-completeness rows rather than silently authoring an alternate completeness summary.",
    ),
    "identity/protocol/IDENTITY_RUNTIME.md": (
        "## Runtime question-routing consumption boundary",
        "Runtime consumes question-routing law as separate question-class-profile, root-entry-question-projection, root-question-discipline-stage, root-question-discipline-stage-surface, entry-summary-stage, entry-summary-stage-surface, and gateway-question-projection row families rather than as undifferentiated routing prose.",
        "Runtime consumes README root question-routing discipline as a governed stage projection bound to admitted root-question-discipline-stage rows rather than as a freehand alternate question ladder.",
        "Runtime consumes README machine-world entry summary as a governed stage projection bound to admitted entry-summary-stage rows rather than as oral navigation advice.",
        "Runtime consumes README root question-routing completeness discipline as a governed completeness projection bound to admitted question-routing-completeness rows rather than as a freehand completeness summary.",
    ),
    "identity/protocol/MACHINE_LAW_PRIMACY_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn machine-law primacy legality must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/MACHINE_WORLD_ONTOLOGY_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn machine-world ontology legality must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/CURRENT_TRUTH_EPISTEMOLOGY_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn epistemic legality must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/DECISION_EVIDENCE_ADMISSIBILITY_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn decision-evidence legality must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/SUCCESS_PATH_STATE_ADMISSIBILITY_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn success-path state legality must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/ENTRY_SURFACE_LEGITIMACY_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn entry-surface legality must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/ERROR_TERMINALITY_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn error terminality must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/ARTIFACT_FAMILY_ADMISSIBILITY_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn artifact-family admissibility must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/IDENTITY_PROMPT_BOOTSTRAP_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn prompt legality must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/IDENTITY_DISCOVERY.md": (
        "## Runtime adjudication boundary",
        "Current-turn discovery legality must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/IDENTITY_INSTANCE_SELF_JUDGEMENT_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn self-judgement legality must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/AGENT_HANDOFF_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn handoff legality must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/PROTOCOL_INSTANCE_RESPONSIBILITY_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn responsibility legality must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/STREAM_DESIGN_ADMISSIBILITY_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn stream-design legality must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/TRUTH_LIFECYCLE_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn truth lifecycle legality must still resolve from machine-consumed enforcement surfaces",
    ),
    "identity/protocol/OPERATOR_ANSWER_SURFACE_CONTRACT.md": (
        "## Runtime adjudication boundary",
        "Current-turn answer-surface legality must still resolve from machine-consumed enforcement surfaces",
    ),
}


def _emit(payload: dict[str, Any], *, json_only: bool) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=None if json_only else 2))


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate protocol root-corpus question-routing and answer-surface discipline.")
    ap.add_argument("--repo-root", default="", help="optional protocol repo root override")
    ap.add_argument("--json-only", action="store_true", help="emit compact json payload only")
    args = ap.parse_args()

    repo_root = resolve_repo_root(args.repo_root, start=__file__)
    routing_doc, routing_entry_path, routing_active_path, routing_alias_error = load_root_corpus_question_routing(repo_root)
    registry_doc, registry_entry_path, registry_active_path, registry_alias_error = load_root_corpus_registry(repo_root)
    ordering_doc, ordering_entry_path, ordering_active_path, ordering_alias_error = load_root_corpus_ordering(repo_root)
    authority_doc, authority_entry_path, authority_active_path, authority_alias_error = load_root_corpus_authority(repo_root)
    gateway_doc, gateway_entry_path, gateway_active_path, gateway_alias_error = load_root_corpus_gateway_admissibility(repo_root)

    stale_reasons: list[str] = []
    structure_violations: list[dict[str, Any]] = []
    routing_violations: list[dict[str, Any]] = []
    anchor_violations: list[dict[str, Any]] = []
    row_family_projection_rows: list[dict[str, Any]] = []
    error_code = ""

    if routing_alias_error:
        stale_reasons.append(f"root_corpus_question_routing_alias_error:{routing_alias_error}")
        error_code = ERR_REGISTRY
    elif not routing_doc:
        stale_reasons.append("root_corpus_question_routing_empty_or_invalid")
        error_code = ERR_REGISTRY

    if registry_alias_error:
        stale_reasons.append(f"root_corpus_registry_alias_error:{registry_alias_error}")
        error_code = ERR_REGISTRY
    elif not registry_doc:
        stale_reasons.append("root_corpus_registry_empty_or_invalid")
        error_code = ERR_REGISTRY

    if ordering_alias_error:
        stale_reasons.append(f"root_corpus_ordering_alias_error:{ordering_alias_error}")
        error_code = ERR_REGISTRY
    elif not ordering_doc:
        stale_reasons.append("root_corpus_ordering_empty_or_invalid")
        error_code = ERR_REGISTRY

    if authority_alias_error:
        stale_reasons.append(f"root_corpus_authority_alias_error:{authority_alias_error}")
        error_code = ERR_REGISTRY
    elif not authority_doc:
        stale_reasons.append("root_corpus_authority_empty_or_invalid")
        error_code = ERR_REGISTRY
    if gateway_alias_error:
        stale_reasons.append(f"root_corpus_gateway_admissibility_alias_error:{gateway_alias_error}")
        error_code = ERR_REGISTRY
    elif not gateway_doc:
        stale_reasons.append("root_corpus_gateway_admissibility_empty_or_invalid")
        error_code = ERR_REGISTRY

    anchor_checks = question_routing_anchor_checks_from_doc(routing_doc) if routing_doc else ()
    question_profiles = question_class_profiles_from_doc(routing_doc) if routing_doc else ()
    root_question_discipline_stages = root_question_discipline_stages_from_doc(routing_doc) if routing_doc else ()
    entry_summary_stages = entry_summary_stages_from_doc(routing_doc) if routing_doc else ()
    question_routing_completeness_rows = (
        question_routing_completeness_rows_from_doc(routing_doc) if routing_doc else ()
    )
    entry_projections = entry_question_projections_from_doc(routing_doc) if routing_doc else ()
    gateway_question_projections = gateway_question_projections_from_doc(routing_doc) if routing_doc else ()
    adjudication_redirect = adjudication_redirect_from_doc(routing_doc) if routing_doc else adjudication_redirect_from_doc({})
    root_question_discipline_surface = readme_root_question_discipline_surface(repo_root)
    entry_summary_surface = readme_entry_summary_surface(repo_root)
    question_routing_completeness_surface = readme_question_routing_completeness_surface(repo_root)
    registry_entries = root_corpus_entries_from_registry(registry_doc) if registry_doc else ()
    reading_rows = reading_order_rows_from_doc(ordering_doc) if ordering_doc else ()
    authority_entry_projections = entry_authority_projections_from_doc(authority_doc) if authority_doc else ()
    gateway_effect_targets = gateway_effect_targets_from_doc(gateway_doc) if gateway_doc else ()
    sorted_question_routing_completeness_rows = sorted(
        question_routing_completeness_rows,
        key=lambda item: item.order,
    )

    if not stale_reasons:
        if str(routing_doc.get("routing_family") or "").strip() != "protocol_root_corpus_question_routing":
            stale_reasons.append("root_corpus_question_routing_family_invalid")
            error_code = ERR_REGISTRY
        if str(routing_doc.get("routing_version") or "").strip() != "v1":
            stale_reasons.append("root_corpus_question_routing_version_invalid")
            error_code = ERR_REGISTRY
        if str(routing_doc.get("root_dir") or "").strip() != str(registry_doc.get("root_dir") or "").strip():
            stale_reasons.append("root_corpus_question_routing_root_dir_mismatch")
            error_code = ERR_REGISTRY
        if str(routing_doc.get("registry_current_file") or "").strip() != "identity/protocol/mappings/root-corpus-registry.current.yaml":
            stale_reasons.append("root_corpus_question_routing_registry_current_file_invalid")
            error_code = ERR_REGISTRY
        if str(routing_doc.get("ordering_current_file") or "").strip() != "identity/protocol/mappings/root-corpus-ordering.current.yaml":
            stale_reasons.append("root_corpus_question_routing_ordering_current_file_invalid")
            error_code = ERR_REGISTRY
        if str(routing_doc.get("authority_current_file") or "").strip() != "identity/protocol/mappings/root-corpus-authority.current.yaml":
            stale_reasons.append("root_corpus_question_routing_authority_current_file_invalid")
            error_code = ERR_REGISTRY
        if str(routing_doc.get("gateway_admissibility_current_file") or "").strip() != "identity/protocol/mappings/root-corpus-gateway-admissibility.current.yaml":
            stale_reasons.append("root_corpus_question_routing_gateway_admissibility_current_file_invalid")
            error_code = ERR_REGISTRY
        if str(routing_doc.get("validator_script") or "").strip() != "scripts/validate_protocol_root_corpus_question_routing.py":
            stale_reasons.append("root_corpus_question_routing_validator_script_invalid")
            error_code = ERR_REGISTRY
        if str(routing_doc.get("probe_script") or "").strip() != "scripts/ci/run_protocol_root_corpus_question_routing_probes_ci.sh":
            stale_reasons.append("root_corpus_question_routing_probe_script_invalid")
            error_code = ERR_REGISTRY
        if str(routing_doc.get("common_script") or "").strip() != "scripts/root_corpus_question_routing_common.py":
            stale_reasons.append("root_corpus_question_routing_common_script_invalid")
            error_code = ERR_REGISTRY
        for field in ("validator_script", "probe_script", "common_script"):
            rel_path = str(routing_doc.get(field) or "").strip()
            if rel_path and not (repo_root / rel_path).exists():
                stale_reasons.append(f"root_corpus_question_routing_surface_missing:{field}:{rel_path}")
                error_code = ERR_REGISTRY
        if not anchor_checks:
            stale_reasons.append("root_corpus_question_routing_anchor_checks_missing")
            error_code = ERR_REGISTRY
        if not question_profiles:
            stale_reasons.append("root_corpus_question_routing_profiles_missing")
            error_code = ERR_REGISTRY
        if not root_question_discipline_stages:
            stale_reasons.append("root_corpus_question_routing_root_question_discipline_stages_missing")
            error_code = ERR_REGISTRY
        if not entry_summary_stages:
            stale_reasons.append("root_corpus_question_routing_entry_summary_stages_missing")
            error_code = ERR_REGISTRY
        if not question_routing_completeness_rows:
            stale_reasons.append("root_corpus_question_routing_completeness_rows_missing")
            error_code = ERR_REGISTRY
        if not entry_projections:
            stale_reasons.append("root_corpus_question_routing_entry_projection_missing")
            error_code = ERR_REGISTRY
        if not gateway_question_projections:
            stale_reasons.append("root_corpus_question_routing_gateway_question_projection_missing")
            error_code = ERR_REGISTRY
        if not adjudication_redirect.question_class:
            stale_reasons.append("root_corpus_question_routing_adjudication_redirect_missing")
        anchor_reason_count_before = len(stale_reasons)
        stale_reasons.extend(
            validate_expected_root_doc_anchor_checks(
                anchor_checks,
                EXPECTED_ROOT_DOC_ANCHOR_CHECKS,
                stale_reason_prefix="root_corpus_question_routing",
            )
        )
        if len(stale_reasons) > anchor_reason_count_before:
            error_code = ERR_REGISTRY
            error_code = ERR_REGISTRY

    registry_paths = [entry.rel_path for entry in registry_entries]
    registry_entry_class_map = {entry.rel_path: entry.corpus_class for entry in registry_entries}
    registry_entry_kind_map = {entry.rel_path: entry.entry_kind for entry in registry_entries}
    registry_entry_law_bearing_map = {entry.rel_path: entry.law_bearing for entry in registry_entries}
    registry_classes = sorted({entry.corpus_class for entry in registry_entries})
    question_profile_map = {row.question_class: row for row in question_profiles}
    root_question_discipline_stage_map = {row.stage_label: row for row in root_question_discipline_stages}
    entry_summary_stage_map = {row.stage_label: row for row in entry_summary_stages}
    entry_projection_map = {row.rel_path: row for row in entry_projections}
    gateway_question_projection_map = {row.gateway_class: row for row in gateway_question_projections}
    gateway_effect_target_map = {row.gateway_class: row for row in gateway_effect_targets}
    authority_entry_map = {row.rel_path: row for row in authority_entry_projections}
    root_index_entry = str(ordering_doc.get("root_index_entry") or "").strip() if ordering_doc else ""
    reading_paths = [row.rel_path for row in sorted(reading_rows, key=lambda item: item.order)]

    if not stale_reasons:
        append_root_doc_anchor_registry_structure_violations(
            structure_violations,
            anchor_checks,
            field_name="question_routing_anchor_checks",
            registry_paths=registry_paths,
            registry_entry_kind_map=registry_entry_kind_map,
            registry_entry_law_bearing_map=registry_entry_law_bearing_map,
            require_file_entry=True,
            require_law_bearing=True,
        )

        append_membership_delta_violations(
            structure_violations,
            field_name="question_class_profiles",
            expected_ids=EXPECTED_QUESTION_RULES,
            actual_ids=question_profile_map,
            payload_key="question_classes",
            missing_reason="missing_expected_question_classes",
            extra_reason="extra_question_classes",
            duplicate_reason="duplicate_question_class",
            actual_total_count=len(question_profiles),
        )
        append_membership_delta_violations(
            structure_violations,
            field_name="entry_question_projection",
            expected_ids=registry_paths,
            actual_ids=entry_projection_map,
            payload_key="rel_paths",
            missing_reason="missing_registered_entries",
            extra_reason="extra_unregistered_entries",
            duplicate_reason="duplicate_rel_path",
            actual_total_count=len(entry_projections),
        )
        append_membership_delta_violations(
            structure_violations,
            field_name="root_question_discipline_stages",
            expected_ids=EXPECTED_ROOT_QUESTION_DISCIPLINE_STAGES,
            actual_ids=root_question_discipline_stage_map,
            payload_key="stage_labels",
            missing_reason="missing_root_question_discipline_stages",
            extra_reason="extra_root_question_discipline_stages",
            duplicate_reason="duplicate_root_question_discipline_stage",
            actual_total_count=len(root_question_discipline_stages),
        )
        append_membership_delta_violations(
            structure_violations,
            field_name="entry_summary_stages",
            expected_ids=EXPECTED_ENTRY_SUMMARY_STAGES,
            actual_ids=entry_summary_stage_map,
            payload_key="stage_labels",
            missing_reason="missing_entry_summary_stages",
            extra_reason="extra_entry_summary_stages",
            duplicate_reason="duplicate_entry_summary_stage",
            actual_total_count=len(entry_summary_stages),
        )
        append_membership_delta_violations(
            structure_violations,
            field_name="gateway_question_projection",
            expected_ids=gateway_effect_target_map,
            actual_ids=gateway_question_projection_map,
            payload_key="gateway_classes",
            missing_reason="missing_gateway_classes",
            extra_reason="extra_gateway_classes",
            duplicate_reason="duplicate_gateway_class",
            actual_total_count=len(gateway_question_projections),
        )
        append_membership_delta_violations(
            structure_violations,
            field_name="root_question_discipline_stage_surface",
            expected_ids=EXPECTED_ROOT_QUESTION_DISCIPLINE_STAGES,
            actual_ids={row.stage_label: row for row in root_question_discipline_surface.rows},
            payload_key="stage_labels",
            missing_reason="missing_root_question_discipline_surface_stages",
            extra_reason="extra_root_question_discipline_surface_stages",
            duplicate_reason="duplicate_root_question_discipline_surface_stage",
            actual_total_count=len(root_question_discipline_surface.rows),
        )
        append_membership_delta_violations(
            structure_violations,
            field_name="entry_summary_stage_surface",
            expected_ids=EXPECTED_ENTRY_SUMMARY_STAGES,
            actual_ids={row.stage_label: row for row in entry_summary_surface.rows},
            payload_key="stage_labels",
            missing_reason="missing_entry_summary_surface_stages",
            extra_reason="extra_entry_summary_surface_stages",
            duplicate_reason="duplicate_entry_summary_surface_stage",
            actual_total_count=len(entry_summary_surface.rows),
        )

        for row in question_profiles:
            if row.answer_mode not in ALLOWED_ANSWER_MODES:
                structure_violations.append(
                    {
                        "field": "question_class_profiles",
                        "reason": "invalid_answer_mode",
                        "question_class": row.question_class,
                        "answer_mode": row.answer_mode,
                    }
                )
            expected = EXPECTED_QUESTION_RULES.get(row.question_class)
            if expected is None:
                continue
            if row.answer_mode != expected["answer_mode"]:
                routing_violations.append(
                    {
                        "field": "question_class_profiles",
                        "reason": "answer_mode_mismatch",
                        "question_class": row.question_class,
                        "expected": expected["answer_mode"],
                        "actual": row.answer_mode,
                    }
                )
            if bool(row.current_turn_authority_allowed) != bool(expected["current_turn_authority_allowed"]):
                routing_violations.append(
                    {
                        "field": "question_class_profiles",
                        "reason": "current_turn_authority_allowed_mismatch",
                        "question_class": row.question_class,
                        "expected": bool(expected["current_turn_authority_allowed"]),
                        "actual": bool(row.current_turn_authority_allowed),
                    }
                )
            if bool(row.root_entry_required) != bool(expected["root_entry_required"]):
                routing_violations.append(
                    {
                        "field": "question_class_profiles",
                        "reason": "root_entry_required_mismatch",
                        "question_class": row.question_class,
                        "expected": bool(expected["root_entry_required"]),
                        "actual": bool(row.root_entry_required),
                    }
                )

        root_question_stage_orders = [row.order for row in root_question_discipline_stages]
        root_question_stage_labels = [row.stage_label for row in root_question_discipline_stages]
        root_question_surface_orders = [row.order for row in root_question_discipline_surface.rows]
        root_question_surface_labels = [row.stage_label for row in root_question_discipline_surface.rows]
        expected_root_question_stage_labels = list(EXPECTED_ROOT_QUESTION_DISCIPLINE_STAGES.keys())
        expected_root_question_stage_orders = [
            int(stage["order"]) for stage in EXPECTED_ROOT_QUESTION_DISCIPLINE_STAGES.values()
        ]
        question_routing_completeness_surface_orders = [
            row.order for row in question_routing_completeness_surface.rows
        ]
        question_routing_completeness_surface_phrases = [
            row.contract_phrase for row in question_routing_completeness_surface.rows
        ]
        if len(set(root_question_stage_orders)) != len(root_question_stage_orders) or sorted(
            root_question_stage_orders
        ) != list(range(1, len(root_question_stage_orders) + 1)):
            structure_violations.append(
                {"field": "root_question_discipline_stages", "reason": "stage_order_non_contiguous"}
            )
        if len(set(root_question_stage_labels)) != len(root_question_stage_labels):
            structure_violations.append(
                {"field": "root_question_discipline_stages", "reason": "duplicate_stage_label"}
            )
        if root_question_surface_orders and (
            len(set(root_question_surface_orders)) != len(root_question_surface_orders)
            or sorted(root_question_surface_orders) != list(range(1, len(root_question_surface_orders) + 1))
        ):
            structure_violations.append(
                {"field": "root_question_discipline_stage_surface", "reason": "stage_order_non_contiguous"}
            )
        if root_question_surface_labels and tuple(root_question_surface_labels) != tuple(
            expected_root_question_stage_labels
        ):
            routing_violations.append(
                {
                    "field": "root_question_discipline_stage_surface",
                    "reason": "root_question_discipline_surface_order_mismatch",
                    "expected": expected_root_question_stage_labels,
                    "actual": root_question_surface_labels,
                }
            )
        if root_question_surface_orders and tuple(root_question_surface_orders) != tuple(
            expected_root_question_stage_orders
        ):
            routing_violations.append(
                {
                    "field": "root_question_discipline_stage_surface",
                    "reason": "root_question_discipline_surface_stage_order_mismatch",
                    "expected": expected_root_question_stage_orders,
                    "actual": root_question_surface_orders,
                }
            )

        stage_orders = [row.order for row in entry_summary_stages]
        stage_labels = [row.stage_label for row in entry_summary_stages]
        surface_orders = [row.order for row in entry_summary_surface.rows]
        surface_labels = [row.stage_label for row in entry_summary_surface.rows]
        expected_stage_labels = list(EXPECTED_ENTRY_SUMMARY_STAGES.keys())
        expected_stage_orders = [
            int(stage["order"]) for stage in EXPECTED_ENTRY_SUMMARY_STAGES.values()
        ]
        if len(set(stage_orders)) != len(stage_orders) or sorted(stage_orders) != list(range(1, len(stage_orders) + 1)):
            structure_violations.append(
                {"field": "entry_summary_stages", "reason": "stage_order_non_contiguous"}
            )
        if len(set(stage_labels)) != len(stage_labels):
            structure_violations.append(
                {"field": "entry_summary_stages", "reason": "duplicate_stage_label"}
            )
        if surface_orders and (
            len(set(surface_orders)) != len(surface_orders)
            or sorted(surface_orders) != list(range(1, len(surface_orders) + 1))
        ):
            structure_violations.append(
                {"field": "entry_summary_stage_surface", "reason": "stage_order_non_contiguous"}
            )
        if surface_labels and tuple(surface_labels) != tuple(expected_stage_labels):
            routing_violations.append(
                {
                    "field": "entry_summary_stage_surface",
                    "reason": "entry_summary_surface_order_mismatch",
                    "expected": expected_stage_labels,
                    "actual": surface_labels,
                }
            )
        if surface_orders and tuple(surface_orders) != tuple(expected_stage_orders):
            routing_violations.append(
                {
                    "field": "entry_summary_stage_surface",
                    "reason": "entry_summary_surface_stage_order_mismatch",
                    "expected": expected_stage_orders,
                    "actual": surface_orders,
                }
            )
        for stage_label, expected in EXPECTED_ROOT_QUESTION_DISCIPLINE_STAGES.items():
            stage_row = root_question_discipline_stage_map.get(stage_label)
            if stage_row is None:
                continue
            if stage_row.order != int(expected["order"]):
                routing_violations.append(
                    {
                        "field": "root_question_discipline_stages",
                        "reason": "stage_order_mismatch",
                        "stage_label": stage_label,
                        "expected": int(expected["order"]),
                        "actual": stage_row.order,
                    }
                )
            if tuple(stage_row.bound_question_classes) != tuple(expected["bound_question_classes"]):
                routing_violations.append(
                    {
                        "field": "root_question_discipline_stages",
                        "reason": "bound_question_classes_mismatch",
                        "stage_label": stage_label,
                        "expected": list(expected["bound_question_classes"]),
                        "actual": list(stage_row.bound_question_classes),
                    }
                )
            if tuple(stage_row.bound_corpus_classes) != tuple(expected["bound_corpus_classes"]):
                routing_violations.append(
                    {
                        "field": "root_question_discipline_stages",
                        "reason": "bound_corpus_classes_mismatch",
                        "stage_label": stage_label,
                        "expected": list(expected["bound_corpus_classes"]),
                        "actual": list(stage_row.bound_corpus_classes),
                    }
                )
            if tuple(stage_row.bound_gateway_classes) != tuple(expected["bound_gateway_classes"]):
                routing_violations.append(
                    {
                        "field": "root_question_discipline_stages",
                        "reason": "bound_gateway_classes_mismatch",
                        "stage_label": stage_label,
                        "expected": list(expected["bound_gateway_classes"]),
                        "actual": list(stage_row.bound_gateway_classes),
                    }
                )
            if tuple(stage_row.required_markers) != tuple(expected["required_markers"]):
                routing_violations.append(
                    {
                        "field": "root_question_discipline_stages",
                        "reason": "required_markers_mismatch",
                        "stage_label": stage_label,
                        "expected": list(expected["required_markers"]),
                        "actual": list(stage_row.required_markers),
                    }
                )
            if stage_row.bound_corpus_classes:
                derived_rel_paths = sorted(
                    rel_path
                    for rel_path, corpus_class in registry_entry_class_map.items()
                    if corpus_class in set(stage_row.bound_corpus_classes)
                )
                derived_question_classes = sorted(
                    {
                        question_class
                        for rel_path in derived_rel_paths
                        for question_class in (
                            entry_projection_map.get(rel_path).question_classes
                            if entry_projection_map.get(rel_path) is not None
                            else ()
                        )
                    }
                )
                if derived_question_classes != sorted(set(stage_row.bound_question_classes)):
                    routing_violations.append(
                        {
                            "field": "root_question_discipline_stages",
                            "reason": "stage_entry_question_classes_mismatch",
                            "stage_label": stage_label,
                            "expected": sorted(set(stage_row.bound_question_classes)),
                            "actual": derived_question_classes,
                        }
                    )
            if stage_row.bound_gateway_classes:
                missing_gateway_classes = sorted(
                    gateway_class
                    for gateway_class in stage_row.bound_gateway_classes
                    if gateway_class not in gateway_question_projection_map
                )
                if missing_gateway_classes:
                    routing_violations.append(
                        {
                            "field": "root_question_discipline_stages",
                            "reason": "stage_bound_gateway_classes_missing_projection",
                            "stage_label": stage_label,
                            "gateway_classes": missing_gateway_classes,
                        }
                    )
                derived_gateway_question_classes = sorted(
                    {
                        gateway_question_projection_map[gateway_class].question_class
                        for gateway_class in stage_row.bound_gateway_classes
                        if gateway_class in gateway_question_projection_map
                    }
                )
                if derived_gateway_question_classes != sorted(set(stage_row.bound_question_classes)):
                    routing_violations.append(
                        {
                            "field": "root_question_discipline_stages",
                            "reason": "stage_gateway_question_classes_mismatch",
                            "stage_label": stage_label,
                            "expected": sorted(set(stage_row.bound_question_classes)),
                            "actual": derived_gateway_question_classes,
                        }
                    )

        for stage_label, expected in EXPECTED_ENTRY_SUMMARY_STAGES.items():
            stage_row = entry_summary_stage_map.get(stage_label)
            if stage_row is None:
                continue
            if stage_row.order != int(expected["order"]):
                routing_violations.append(
                    {
                        "field": "entry_summary_stages",
                        "reason": "stage_order_mismatch",
                        "stage_label": stage_label,
                        "expected": int(expected["order"]),
                        "actual": stage_row.order,
                    }
                )
            if tuple(stage_row.bound_question_classes) != tuple(expected["bound_question_classes"]):
                routing_violations.append(
                    {
                        "field": "entry_summary_stages",
                        "reason": "bound_question_classes_mismatch",
                        "stage_label": stage_label,
                        "expected": list(expected["bound_question_classes"]),
                        "actual": list(stage_row.bound_question_classes),
                    }
                )
            if tuple(stage_row.terminal_machine_surfaces) != tuple(expected["terminal_machine_surfaces"]):
                routing_violations.append(
                    {
                        "field": "entry_summary_stages",
                        "reason": "terminal_machine_surfaces_mismatch",
                        "stage_label": stage_label,
                        "expected": list(expected["terminal_machine_surfaces"]),
                        "actual": list(stage_row.terminal_machine_surfaces),
                    }
                )
            if tuple(stage_row.required_markers) != tuple(expected["required_markers"]):
                routing_violations.append(
                    {
                        "field": "entry_summary_stages",
                        "reason": "required_markers_mismatch",
                        "stage_label": stage_label,
                        "expected": list(expected["required_markers"]),
                        "actual": list(stage_row.required_markers),
                    }
                )

        for rel_path, row in entry_projection_map.items():
            expected_corpus_class = registry_entry_class_map.get(rel_path, "")
            expected_question_classes = sorted(
                question_class
                for question_class, expected in EXPECTED_QUESTION_RULES.items()
                if expected.get("corpus_class") == expected_corpus_class and expected.get("root_entry_required")
            )
            actual_question_classes = sorted(set(row.question_classes))
            if actual_question_classes != expected_question_classes:
                routing_violations.append(
                    {
                        "field": "entry_question_projection",
                        "reason": "entry_question_classes_mismatch",
                        "rel_path": rel_path,
                        "expected": expected_question_classes,
                        "actual": actual_question_classes,
                    }
                )
            if "current_turn_legality" in actual_question_classes:
                routing_violations.append(
                    {
                        "field": "entry_question_projection",
                        "reason": "current_turn_legality_must_not_bind_to_root_entry",
                        "rel_path": rel_path,
                    }
                )
            authority_row = authority_entry_map.get(rel_path)
            for question_class in actual_question_classes:
                expected = EXPECTED_QUESTION_RULES.get(question_class)
                if expected is None or authority_row is None:
                    continue
                expected_mode = str(expected.get("authority_mode") or "")
                if expected_mode and authority_row.authority_mode != expected_mode:
                    routing_violations.append(
                        {
                            "field": "entry_question_projection",
                            "reason": "entry_authority_mode_incompatible_with_question_class",
                            "rel_path": rel_path,
                            "question_class": question_class,
                            "expected": expected_mode,
                            "actual": authority_row.authority_mode,
                        }
                    )

        for gateway_class, row in gateway_question_projection_map.items():
            gateway_effect_target = gateway_effect_target_map.get(gateway_class)
            if gateway_effect_target is None:
                routing_violations.append(
                    {
                        "field": "gateway_question_projection",
                        "reason": "unbound_gateway_class",
                        "gateway_class": gateway_class,
                    }
                )
                continue
            if row.effect_target_class != gateway_effect_target.effect_target_class:
                routing_violations.append(
                    {
                        "field": "gateway_question_projection",
                        "reason": "effect_target_class_mismatch",
                        "gateway_class": gateway_class,
                        "expected": gateway_effect_target.effect_target_class,
                        "actual": row.effect_target_class,
                    }
                )
            if row.question_class != gateway_effect_target.effect_target_question_class:
                routing_violations.append(
                    {
                        "field": "gateway_question_projection",
                        "reason": "question_class_mismatch",
                        "gateway_class": gateway_class,
                        "expected": gateway_effect_target.effect_target_question_class,
                        "actual": row.question_class,
                    }
                )
            if row.answer_mode != gateway_effect_target.effect_target_answer_mode:
                routing_violations.append(
                    {
                        "field": "gateway_question_projection",
                        "reason": "answer_mode_mismatch",
                        "gateway_class": gateway_class,
                        "expected": gateway_effect_target.effect_target_answer_mode,
                        "actual": row.answer_mode,
                    }
                )
            question_profile = question_profile_map.get(row.question_class)
            if question_profile is None:
                routing_violations.append(
                    {
                        "field": "gateway_question_projection",
                        "reason": "question_profile_missing",
                        "gateway_class": gateway_class,
                        "question_class": row.question_class,
                    }
                )
                continue
            if row.answer_mode != question_profile.answer_mode:
                routing_violations.append(
                    {
                        "field": "gateway_question_projection",
                        "reason": "question_profile_answer_mode_mismatch",
                        "gateway_class": gateway_class,
                        "question_class": row.question_class,
                        "expected": question_profile.answer_mode,
                        "actual": row.answer_mode,
                    }
                )
            if bool(row.current_turn_authority_allowed) != bool(question_profile.current_turn_authority_allowed):
                routing_violations.append(
                    {
                        "field": "gateway_question_projection",
                        "reason": "current_turn_authority_allowed_mismatch",
                        "gateway_class": gateway_class,
                        "question_class": row.question_class,
                        "expected": bool(question_profile.current_turn_authority_allowed),
                        "actual": bool(row.current_turn_authority_allowed),
                    }
                )
            if bool(row.root_entry_required) != bool(question_profile.root_entry_required):
                routing_violations.append(
                    {
                        "field": "gateway_question_projection",
                        "reason": "root_entry_required_mismatch",
                        "gateway_class": gateway_class,
                        "question_class": row.question_class,
                        "expected": bool(question_profile.root_entry_required),
                        "actual": bool(row.root_entry_required),
                    }
                )
            expected_rule = EXPECTED_QUESTION_RULES.get(row.question_class)
            if expected_rule is not None and row.effect_target_class != str(expected_rule.get("corpus_class") or ""):
                routing_violations.append(
                    {
                        "field": "gateway_question_projection",
                        "reason": "effect_target_class_incompatible_with_question_class",
                        "gateway_class": gateway_class,
                        "question_class": row.question_class,
                        "expected": str(expected_rule.get("corpus_class") or ""),
                        "actual": row.effect_target_class,
                    }
                )

        if root_index_entry:
            root_index_projection = entry_projection_map.get(root_index_entry)
            if root_index_projection is None:
                routing_violations.append(
                    {"field": "entry_question_projection", "reason": "root_index_entry_missing_projection", "rel_path": root_index_entry}
                )
            elif sorted(set(root_index_projection.question_classes)) != ["root_entry_navigation"]:
                routing_violations.append(
                    {
                        "field": "entry_question_projection",
                        "reason": "root_index_entry_wrong_question_class",
                        "rel_path": root_index_entry,
                        "actual": sorted(set(root_index_projection.question_classes)),
                    }
                )

        if set(reading_paths) != set(registry_paths):
            structure_violations.append(
                {"field": "entry_question_projection", "reason": "reading_order_registry_mismatch"}
            )

        if adjudication_redirect.question_class != "current_turn_legality":
            routing_violations.append(
                {
                    "field": "adjudication_redirect",
                    "reason": "adjudication_redirect_wrong_question_class",
                    "actual": adjudication_redirect.question_class,
                }
            )
        if tuple(adjudication_redirect.terminal_machine_surfaces) != EXPECTED_TERMINAL_MACHINE_SURFACES:
            routing_violations.append(
                {
                    "field": "adjudication_redirect",
                    "reason": "terminal_machine_surfaces_mismatch",
                    "expected": list(EXPECTED_TERMINAL_MACHINE_SURFACES),
                    "actual": list(adjudication_redirect.terminal_machine_surfaces),
                }
            )
        if tuple(adjudication_redirect.forbidden_root_corpus_classes) != EXPECTED_FORBIDDEN_ROOT_CLASSES:
            routing_violations.append(
                {
                    "field": "adjudication_redirect",
                    "reason": "forbidden_root_corpus_classes_mismatch",
                    "expected": list(EXPECTED_FORBIDDEN_ROOT_CLASSES),
                    "actual": list(adjudication_redirect.forbidden_root_corpus_classes),
                }
            )
        if "machine_registry_directory" in set(adjudication_redirect.forbidden_root_corpus_classes):
            routing_violations.append(
                {
                    "field": "adjudication_redirect",
                    "reason": "machine_registry_directory_must_not_be_forbidden_for_current_turn_legality",
                }
            )
        root_question_surface_map = {row.stage_label: row for row in root_question_discipline_surface.rows}
        for reason in root_question_discipline_surface.extraction_violations:
            structure_violations.append(
                {
                    "field": "root_question_discipline_stage_surface",
                    "reason": f"root_question_discipline_surface_{reason}",
                }
            )
        for stage_label, expected in EXPECTED_ROOT_QUESTION_DISCIPLINE_STAGES.items():
            surface_row = root_question_surface_map.get(stage_label)
            if surface_row is None:
                continue
            surface_text = "\n".join(surface_row.body_lines)
            for marker in expected["required_markers"]:
                if marker not in surface_text:
                    routing_violations.append(
                        {
                            "field": "root_question_discipline_stage_surface",
                            "reason": "required_marker_missing",
                            "stage_label": stage_label,
                            "marker": marker,
                        }
                    )
        stage_surface_map = {row.stage_label: row for row in entry_summary_surface.rows}
        for reason in entry_summary_surface.extraction_violations:
            structure_violations.append(
                {
                    "field": "entry_summary_stage_surface",
                    "reason": f"entry_summary_surface_{reason}",
                }
            )
        for stage_label, expected in EXPECTED_ENTRY_SUMMARY_STAGES.items():
            surface_row = stage_surface_map.get(stage_label)
            if surface_row is None:
                continue
            surface_text = "\n".join(surface_row.body_lines)
            for marker in expected["required_markers"]:
                if marker not in surface_text:
                    routing_violations.append(
                        {
                            "field": "entry_summary_stage_surface",
                            "reason": "required_marker_missing",
                            "stage_label": stage_label,
                            "marker": marker,
                        }
                    )
        terminal_surface_stage = entry_summary_stage_map.get("machine-consumed verdict surfaces last")
        if terminal_surface_stage is not None and tuple(terminal_surface_stage.terminal_machine_surfaces) != tuple(
            adjudication_redirect.terminal_machine_surfaces
        ):
            routing_violations.append(
                {
                    "field": "entry_summary_stages",
                    "reason": "terminal_machine_surfaces_not_aligned_with_adjudication_redirect",
                    "stage_label": terminal_surface_stage.stage_label,
                    "expected": list(adjudication_redirect.terminal_machine_surfaces),
                    "actual": list(terminal_surface_stage.terminal_machine_surfaces),
                }
            )
        for reason in question_routing_completeness_surface.extraction_violations:
            structure_violations.append(
                {
                    "field": "question_routing_completeness_surface",
                    "reason": f"question_routing_completeness_surface_{reason}",
                }
            )
        validate_contract_row_batches(
            batches=(
                {
                    "actual_rows": question_routing_completeness_rows,
                    "expected_rows": EXPECTED_QUESTION_ROUTING_COMPLETENESS_ROWS,
                    "field_name": "question_routing_completeness_rows",
                    "id_attr": "completeness_id",
                    "compare_fields": ("contract_phrase",),
                    "duplicate_reason": "duplicate_question_routing_completeness_id",
                    "non_contiguous_reason": "question_routing_completeness_row_order_non_contiguous",
                    "missing_reason": "missing_question_routing_completeness_rows",
                    "extra_reason": "extra_question_routing_completeness_rows",
                    "missing_ids_key": "completeness_ids",
                    "extra_ids_key": "completeness_ids",
                    "violation_id_key": "completeness_id",
                    "order_reason": "question_routing_completeness_row_order_mismatch",
                },
                {
                    "actual_rows": question_routing_completeness_surface.rows,
                    "expected_rows": {
                        row["contract_phrase"]: {"order": int(row["order"])}
                        for row in EXPECTED_QUESTION_ROUTING_COMPLETENESS_ROWS.values()
                    },
                    "field_name": "question_routing_completeness_surface",
                    "id_attr": "contract_phrase",
                    "compare_fields": (),
                    "duplicate_reason": "duplicate_question_routing_completeness_surface_phrase",
                    "non_contiguous_reason": "question_routing_completeness_surface_order_non_contiguous",
                    "missing_reason": "missing_question_routing_completeness_surface_rows",
                    "extra_reason": "extra_question_routing_completeness_surface_rows",
                    "missing_ids_key": "contract_phrases",
                    "extra_ids_key": "contract_phrases",
                    "violation_id_key": "contract_phrase",
                    "order_reason": "question_routing_completeness_surface_order_mismatch",
                },
            ),
            structure_violations=structure_violations,
            support_violations=routing_violations,
        )
        expected_question_routing_completeness_phrases = [
            row["contract_phrase"] for row in EXPECTED_QUESTION_ROUTING_COMPLETENESS_ROWS.values()
        ]
        expected_question_routing_completeness_orders = [
            int(row["order"]) for row in EXPECTED_QUESTION_ROUTING_COMPLETENESS_ROWS.values()
        ]
        if question_routing_completeness_surface_phrases and tuple(
            question_routing_completeness_surface_phrases
        ) != tuple(expected_question_routing_completeness_phrases):
            routing_violations.append(
                {
                    "field": "question_routing_completeness_surface",
                    "reason": "question_routing_completeness_surface_phrase_order_mismatch",
                    "expected": expected_question_routing_completeness_phrases,
                    "actual": question_routing_completeness_surface_phrases,
                }
            )
        if question_routing_completeness_surface_orders and tuple(
            question_routing_completeness_surface_orders
        ) != tuple(expected_question_routing_completeness_orders):
            routing_violations.append(
                {
                    "field": "question_routing_completeness_surface",
                    "reason": "question_routing_completeness_surface_order_mismatch",
                    "expected": expected_question_routing_completeness_orders,
                    "actual": question_routing_completeness_surface_orders,
                }
            )

        anchor_violations.extend(
            evaluate_root_doc_anchor_checks(
                repo_root,
                anchor_checks,
                field_name="question_routing_anchor_checks",
            )
        )

    if not error_code and structure_violations:
        error_code = ERR_STRUCTURE
    if not error_code and (routing_violations or anchor_violations):
        error_code = ERR_ROUTING

    stale_reasons.extend(f"structure_violation:{row['field']}:{row['reason']}" for row in structure_violations)
    stale_reasons.extend(f"routing_violation:{row['field']}:{row['reason']}" for row in routing_violations)
    stale_reasons.extend(f"anchor_violation:{row['rel_path']}:{row['reason']}" for row in anchor_violations)

    status = STATUS_PASS_REQUIRED if not stale_reasons else STATUS_FAIL_REQUIRED
    row_family_projection_rows = project_row_families(
        families=(
            {
                "family_id": "question_class_profiles",
                "member_id_key": "question_class",
                "actual_rows": question_profiles,
                "expected_rows": EXPECTED_QUESTION_RULES,
                "id_attr": "question_class",
            },
            {
                "family_id": "entry_question_projection",
                "member_id_key": "rel_path",
                "actual_rows": entry_projections,
                "expected_rows": {rel_path: {} for rel_path in registry_paths},
                "id_attr": "rel_path",
            },
            {
                "family_id": "root_question_discipline_stages",
                "member_id_key": "stage_label",
                "actual_rows": root_question_discipline_stages,
                "expected_rows": {
                    stage_label: {} for stage_label in EXPECTED_ROOT_QUESTION_DISCIPLINE_STAGES
                },
                "id_attr": "stage_label",
            },
            {
                "family_id": "root_question_discipline_stage_surface",
                "member_id_key": "stage_label",
                "actual_rows": root_question_discipline_surface.rows,
                "expected_rows": {
                    stage_label: {} for stage_label in EXPECTED_ROOT_QUESTION_DISCIPLINE_STAGES
                },
                "id_attr": "stage_label",
            },
            {
                "family_id": "entry_summary_stages",
                "member_id_key": "stage_label",
                "actual_rows": entry_summary_stages,
                "expected_rows": {stage_label: {} for stage_label in EXPECTED_ENTRY_SUMMARY_STAGES},
                "id_attr": "stage_label",
            },
            {
                "family_id": "entry_summary_stage_surface",
                "member_id_key": "stage_label",
                "actual_rows": entry_summary_surface.rows,
                "expected_rows": {stage_label: {} for stage_label in EXPECTED_ENTRY_SUMMARY_STAGES},
                "id_attr": "stage_label",
            },
            {
                "family_id": "question_routing_completeness_rows",
                "member_id_key": "completeness_id",
                "actual_rows": question_routing_completeness_rows,
                "expected_rows": {
                    completeness_id: {} for completeness_id in EXPECTED_QUESTION_ROUTING_COMPLETENESS_ROWS
                },
                "id_attr": "completeness_id",
            },
            {
                "family_id": "question_routing_completeness_surface",
                "member_id_key": "contract_phrase",
                "actual_rows": question_routing_completeness_surface.rows,
                "expected_rows": {
                    row["contract_phrase"]: {} for row in EXPECTED_QUESTION_ROUTING_COMPLETENESS_ROWS.values()
                },
                "id_attr": "contract_phrase",
            },
            {
                "family_id": "gateway_question_projection",
                "member_id_key": "gateway_class",
                "actual_rows": gateway_question_projections,
                "expected_rows": {gateway_class: {} for gateway_class in gateway_effect_target_map},
                "id_attr": "gateway_class",
            },
        ),
        pass_status=STATUS_PASS_REQUIRED,
        fail_status=STATUS_FAIL_REQUIRED,
    )
    payload: dict[str, Any] = {
        STATUS_KEY: status,
        "error_code": "" if status == STATUS_PASS_REQUIRED else (error_code or ERR_ROUTING),
        "routing_entry_path": str(routing_entry_path),
        "routing_active_path": str(routing_active_path),
        "registry_entry_path": str(registry_entry_path),
        "registry_active_path": str(registry_active_path),
        "ordering_entry_path": str(ordering_entry_path),
        "ordering_active_path": str(ordering_active_path),
        "authority_entry_path": str(authority_entry_path),
        "authority_active_path": str(authority_active_path),
        "root_dir": str(routing_doc.get("root_dir") or ""),
        "root_index_entry": root_index_entry,
        "question_routing_anchor_check_count": len(anchor_checks),
        "question_class_profile_count": len(question_profiles),
        "root_question_discipline_stage_count": len(root_question_discipline_stages),
        "entry_summary_stage_count": len(entry_summary_stages),
        "question_routing_completeness_row_count": len(question_routing_completeness_rows),
        "entry_question_projection_count": len(entry_projections),
        "gateway_question_projection_count": len(gateway_question_projections),
        **project_root_contract_support_projection(
            prefix="question_routing",
            row_family_projection_rows=row_family_projection_rows,
            anchor_checks=anchor_checks,
            anchor_violations=anchor_violations,
            pass_status=STATUS_PASS_REQUIRED,
            fail_status=STATUS_FAIL_REQUIRED,
        ),
        "row_family_projection_rows": row_family_projection_rows,
        "question_class_profiles": [
            {
                "question_class": row.question_class,
                "answer_mode": row.answer_mode,
                "current_turn_authority_allowed": row.current_turn_authority_allowed,
                "root_entry_required": row.root_entry_required,
            }
            for row in question_profiles
        ],
        "entry_question_projection": [
            {
                "rel_path": row.rel_path,
                "question_classes": list(row.question_classes),
            }
            for row in entry_projections
        ],
        "root_question_discipline_stages": [
            {
                "order": row.order,
                "stage_label": row.stage_label,
                "bound_question_classes": list(row.bound_question_classes),
                "bound_corpus_classes": list(row.bound_corpus_classes),
                "bound_gateway_classes": list(row.bound_gateway_classes),
                "required_markers": list(row.required_markers),
            }
            for row in sorted(root_question_discipline_stages, key=lambda item: item.order)
        ],
        "entry_summary_stages": [
            {
                "order": row.order,
                "stage_label": row.stage_label,
                "bound_question_classes": list(row.bound_question_classes),
                "terminal_machine_surfaces": list(row.terminal_machine_surfaces),
                "required_markers": list(row.required_markers),
            }
            for row in sorted(entry_summary_stages, key=lambda item: item.order)
        ],
        "question_routing_completeness_rows": [
            {
                "order": row.order,
                "completeness_id": row.completeness_id,
                "contract_phrase": row.contract_phrase,
            }
            for row in sorted_question_routing_completeness_rows
        ],
        "gateway_question_projection": [
            {
                "gateway_class": row.gateway_class,
                "effect_target_class": row.effect_target_class,
                "question_class": row.question_class,
                "answer_mode": row.answer_mode,
                "current_turn_authority_allowed": row.current_turn_authority_allowed,
                "root_entry_required": row.root_entry_required,
            }
            for row in gateway_question_projections
        ],
        "root_question_discipline_stage_surface": {
            "rel_path": root_question_discipline_surface.rel_path,
            "entry_count": len(root_question_discipline_surface.rows),
            "entries": [
                {
                    "order": row.order,
                    "stage_label": row.stage_label,
                    "body_lines": list(row.body_lines),
                }
                for row in root_question_discipline_surface.rows
            ],
            "extraction_violations": list(root_question_discipline_surface.extraction_violations),
        },
        "entry_summary_stage_surface": {
            "rel_path": entry_summary_surface.rel_path,
            "entry_count": len(entry_summary_surface.rows),
            "entries": [
                {
                    "order": row.order,
                    "stage_label": row.stage_label,
                    "body_lines": list(row.body_lines),
                }
                for row in entry_summary_surface.rows
            ],
            "extraction_violations": list(entry_summary_surface.extraction_violations),
        },
        "question_routing_completeness_surface": {
            "rel_path": question_routing_completeness_surface.rel_path,
            "entry_count": len(question_routing_completeness_surface.rows),
            "entries": [
                {
                    "order": row.order,
                    "contract_phrase": row.contract_phrase,
                }
                for row in question_routing_completeness_surface.rows
            ],
            "extraction_violations": list(question_routing_completeness_surface.extraction_violations),
        },
        "adjudication_redirect": {
            "question_class": adjudication_redirect.question_class,
            "terminal_machine_surfaces": list(adjudication_redirect.terminal_machine_surfaces),
            "forbidden_root_corpus_classes": list(adjudication_redirect.forbidden_root_corpus_classes),
        },
        "structure_violations": structure_violations,
        "routing_violations": routing_violations,
        "anchor_violations": anchor_violations,
        "stale_reasons": stale_reasons,
    }
    _emit(payload, json_only=args.json_only)
    return 0 if status == STATUS_PASS_REQUIRED else 1


if __name__ == "__main__":
    raise SystemExit(main())
