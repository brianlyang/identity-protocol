# Identity Onboarding 72h Audit Return Template

Purpose:

1. Standardize architect ↔ audit-expert handoff for onboarding closure.
2. Enforce A-track/B-track separation to avoid mixed-layer conclusions.
3. Keep output machine-checkable and replayable.
4. Preserve domain-learning depth while keeping protocol governance records clean.

Status: template

---

## 0) Report metadata

- Date (UTC):
- Reporter:
- Branch:
- Target identity:
- Runtime mode:
- Catalog path:
- Scope:

---

## 1) Layer declaration (mandatory)

- A-track layer declaration: protocol
- B-track layer declaration: instance
- Mixed-layer statement: prohibited
- Dual-ledger statement:
  - governance ledger carries capability-upgrade facts and evidence references only
  - domain ledger carries business details and learning artifacts
  - governance must link domain artifacts via references, not inline non-redacted business details

---

## 2) A-track (protocol) return block

### 2.1 Commit SHA list

- SHA-1:
- SHA-2:

### 2.2 Changed file list

- File:
- File:

### 2.3 Acceptance command outputs

Provide exact command + terminal summary:

1. SSOT source validator
   - command:
   - rc:
   - output summary:
2. Handoff coupling validator
   - command:
   - rc:
   - output summary:
3. Docs command contract checker
   - command:
   - rc:
   - output summary:

### 2.4 Residual risks + next milestone

- Residual risks:
- Next milestone:

---

## 3) B-track (instance) return block

### 3.1 Commit SHA list

- SHA-1:
- SHA-2:

### 3.2 Changed file list

- File:
- File:

### 3.3 Acceptance command outputs

Minimum recommended set:

1. Identity protocol baseline validator
   - command:
   - rc:
   - output summary:
2. Runtime contract validator
   - command:
   - rc:
   - output summary:
3. Role-binding validator
   - command:
   - rc:
   - output summary:
4. Prompt quality validator
   - command:
   - rc:
   - output summary:
5. Learning-loop validator
   - command:
   - rc:
   - output summary:
6. Capability arbitration self-test
   - command:
   - rc:
   - output summary:
7. e2e smoke (target identity)
   - command:
   - rc:
   - output summary:
8. Readiness (policy declared)
   - command:
   - rc:
   - output summary:
9. Three-plane status
   - command:
   - rc:
   - output summary:
10. Self-driven upgrade ledger validator (when available)
   - command:
   - rc:
   - output summary:
11. Roundtable/cross-validation output check
   - command:
   - rc:
   - output summary:

### 3.4 Residual risks + next milestone

- Residual risks:
- Next milestone:

---

## 4) Self-driven upgrade ledger summary (mandatory)

Rules:

1. Include one row per upgrade event in the reporting window.
2. `trigger_mode` must be `active` or `passive`.
3. If `result_status` is not `PASS`, `next_action` must be non-empty.
4. `domain_artifact_refs` is required when business learning is part of upgrade evidence.

| upgrade_id | run_id | ts_utc | trigger_mode | capability_axis | acceptance_command | evidence_ref | domain_artifact_refs | result_status | next_action |
|---|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  |  |

---

## 5) Roundtable and cross-vendor validation evidence (mandatory for complex upgrades)

Roundtable summary:

- roundtable_required: yes/no
- roundtable_decision_ref:
- decision_matrix_ref:
- participants_role_set:
- unresolved_items_count:
- skip_reason_if_not_required:

Cross-vendor matrix (fact/inference separated):

| Vendor | Source URL | Retrieved at (UTC) | Claim | Claim type (`fact`/`inference`) | Mapped contract/validator | Risk note |
|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |

Constraint:

1. Final claims must reference at least one `fact` row.
2. `inference` rows must include risk notes and mapped validator/contract.

---

## 6) Three-plane final declaration (mandatory)

- instance_plane_status:
- repo_plane_status:
- release_plane_status:
- overall_release_decision:

Rule:

1. Any plane not CLOSED => overall decision must remain Conditional Go.
2. Full Go requires release-plane cloud closure evidence.

---

## 7) Identity context tuple evidence (mandatory)

Attach tuple from resolver:

- source_layer:
- catalog_path:
- pack_path:
- resolved_scope:
- resolved_pack_path:

If catalog_path is unexpected for current runtime mode, report as misconfiguration.

---

## 8) Sign-off

- Architect sign-off:
- Audit expert sign-off:
- Pending follow-ups:
