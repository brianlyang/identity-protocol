# Identity Runtime Brief

## Native Chat Reply Hard Guard

Read this first before producing any assistant-authored native-chat reply.

- Never start with body text; line 1 and line 2 are mandatory.
- If `CODEX_SESSION_ID` / `IDENTITY_SESSION_ID` is missing, or the current-turn actor/session tuple cannot be resolved, line 1 and line 2 MUST fall back to the two-line withheld/conflict envelope; never drop the headstamp completely.
- Shared compiled brief examples are schematic only; resolve placeholders from the current-turn machine-attested actor/session tuple.
- Failure line 1 may claim only `requested_identity_id`; it never proves the current speaking identity.
- Compatibility pointer diagnostics, when needed, stay on `Machine-Verification` and remain diagnostic-only.
- Success path first two lines:
  1. `Identity-Context: actor_id=assistant:codex; identity_id=<current_session_identity_id>; scope=<resolved_scope>; lock=LOCK_MATCH; source=<resolved_source_layer> | Layer-Context: work_layer=<resolved_work_layer>; source_layer=<resolved_source_layer>`
  2. `Machine-Verification: authority_source=actor_session_store; identity_id=<current_session_identity_id>; status=<resolved_status>; prompt_version=<resolved_prompt_version>; source_layer=<resolved_source_layer>`
- Failure path first two lines when the current-turn machine tuple is missing, conflicted, or polluted:
  1. `Identity-Context: withheld; actor_id=assistant:codex; requested_identity_id=<requested_identity_id>; conflict=<reason>; scope=<resolved_scope>; source=<resolved_source_layer> | Layer-Context: work_layer=<resolved_work_layer>; source_layer=<resolved_source_layer>`
  2. `Machine-Verification: verification_source=<verification_source>; verification_status=FAIL_REQUIRED; current_chat_surface_native_machine_attested=false; next_hop_admission_status=FAIL_REQUIRED`
- Only after those two lines may body text begin.

This file is generated/maintained by identity runtime tooling.

Artifact classification:
- artifact_class: tracked_compiled_brief_artifact
- path_status: tracked_compiled_brief_frozen_path
- generation_mode: source_first
- runtime_mode_default: local_only
- default_machine_profile: `mini`
- shared compiled brief never acts as current-turn identity authority; success projection remains schematic until a machine-attested actor/session tuple resolves it at turn time.
- without a current-turn machine tuple, native chat must stay on the two-line withheld/conflict envelope.
- compile/runtime authority note: compile/replay metadata may read compatibility mirror; current-session authority must not.

Source-first generation inputs:
- `${IDENTITY_CATALOG}`
- `${IDENTITY_HOME}/<resolved_identity_id>/CURRENT_TASK.json`
- `${IDENTITY_HOME}/<resolved_identity_id>/IDENTITY_PROMPT.md`

Native chat assistant-visible headstamp contract:
- Apply this contract to every assistant-authored user-visible native-chat reply.
- Success order is fixed: `Identity-Context` first, `Machine-Verification` second, then body.
- Native chat machine profile default: `mini`.
- Available native chat machine profiles: `mini`, `standard`, `audit`.
- `mini`: compact human-facing default; fields = `authority_source, identity_id, status, prompt_version, source_layer`.
- `standard`: readable debug projection; fields = `authority_source, actor_id, identity_id, status, pointer_path, prompt_version, work_layer, source_layer`.
- `audit`: full lineage/debug projection; fields = `authority_source, actor_id, identity_id, status, pointer_path, catalog_path, pack_path, prompt_version, binding_version, work_layer, source_layer`.
- Failure `mini`: compact fail-close projection; fields = `verification_source, verification_status, current_chat_surface_native_machine_attested, next_hop_admission_status`.
- Failure `standard`: readable fail-close debug projection; fields = `verification_source, verification_status, compatibility_pointer_identity_id, compatibility_pointer_scope, current_chat_surface_native_machine_attested, next_hop_admission_status, source_layer`.
- Failure `audit`: full fail-close audit projection; fields = `verification_source, verification_status, compatibility_pointer_identity_id, compatibility_pointer_scope, pointer_path, current_chat_surface_native_machine_attested, next_hop_admission_status, control_state, source_layer`.
- Ordinary user-facing native chat replies must stay on `mini`; only expand to `standard` or `audit` when debug/audit context explicitly requires it.
- native-chat failure `Machine-Verification` defaults to the compact `mini` profile unless debug/audit context explicitly requires escalation.
- This native-chat path is the standard assistant-visible delivery path for host-native chat surfaces.
- Ordinary replies should stay focused on the standard native-chat output path; governed receipt or attestation boundaries are audit/debug-only.
- Native-chat display alone does not replace governed proof, admission, or runtime receipt ownership.
- Governed repo-controlled surfaces keep the separate `Display-Headstamp` + `Machine-Verification` envelope; do not replace that contract here.
- shared compiled brief never acts as current-turn identity authority; success projection remains schematic until a machine-attested actor/session tuple resolves it at turn time.
- without a current-turn machine tuple, native chat must stay on the two-line withheld/conflict envelope.
- `requested_identity_id` in native-chat failure line 1 is the requested target only; it never proves the current speaking identity.
- `compatibility_pointer_identity_id` is diagnostic-only compatibility metadata; it MUST NOT replace `identity_id` or appear as success-state identity injection.
- If machine verification is missing, conflicted, or polluted, do not emit a success identity line; emit a withheld/conflict `Identity-Context` plus `Machine-Verification: verification_status=FAIL_REQUIRED ...` instead.
- Runtime loop is fixed: `machine-verify -> assistant-visible-inject -> next turn re-verify`.

Native chat headstamp hard guard:
- template source: `/Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local/identity/protocol/plugins/templates/native-chat-headstamp.prompt_hard_guard_v1.json`.
- Apply these hard rules to every assistant-authored user-visible native-chat reply.
- Every assistant-authored user-visible native-chat reply MUST begin with a two-line headstamp before any body text.
- There is no headerless assistant-authored native-chat reply path.
- If `CODEX_SESSION_ID` / `IDENTITY_SESSION_ID` is missing, or the current-turn actor/session tuple cannot be resolved, line 1 and line 2 MUST fall back to the two-line withheld/conflict envelope; never drop the headstamp completely.
- If success-state identity injection is forbidden, the failure path still MUST emit the two-line withheld/conflict envelope; never drop the headstamp completely.
- Governed surfaces keep `Display-Headstamp -> Machine-Verification -> body`; native chat keeps `Identity-Context -> Machine-Verification -> body`.
- Failure line 1 may claim only `requested_identity_id`; it MUST NOT project a success identity when the current-turn machine tuple is missing, conflicted, or polluted.
- Compatibility pointer diagnostics, when needed, stay on `Machine-Verification` and remain diagnostic-only.
- Success visible order: `Identity-Context -> Machine-Verification -> body`.
- Failure visible order: `Identity-Context(withheld_or_conflict) -> Machine-Verification(verification_status=FAIL_REQUIRED) -> body`.
- Success example line 1 (schematic only; placeholders resolve only from current-turn machine tuple): `Identity-Context: actor_id=assistant:codex; identity_id=<current_session_identity_id>; scope=<resolved_scope>; lock=LOCK_MATCH; source=<resolved_source_layer> | Layer-Context: work_layer=<resolved_work_layer>; source_layer=<resolved_source_layer>`
- Success example line 2 (schematic only; profile `mini`): `Machine-Verification: authority_source=actor_session_store; identity_id=<current_session_identity_id>; status=<resolved_status>; prompt_version=<resolved_prompt_version>; source_layer=<resolved_source_layer>`
- Failure example line 1: `Identity-Context: withheld; actor_id=assistant:codex; requested_identity_id=<requested_identity_id>; conflict=<reason>; scope=<resolved_scope>; source=<resolved_source_layer> | Layer-Context: work_layer=<resolved_work_layer>; source_layer=<resolved_source_layer>`
- Failure example line 2: `Machine-Verification: verification_source=<verification_source>; verification_status=FAIL_REQUIRED; current_chat_surface_native_machine_attested=false; next_hop_admission_status=FAIL_REQUIRED`

Headstamp semantic clarity freeze:
- canonical semantic matrix template: `/Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local/identity/protocol/plugins/templates/headstamp-surface-semantics.matrix_v1.json`.
- surface semantics matrix:
- `native chat`: visible order = `Identity-Context -> Machine-Verification -> body`; first literal = `Identity-Context: ... | Layer-Context: ...`; proof owner = `machine_headstamp + headstamp_admission_receipt + controlled-runtime artifacts`.
- `governed wrapper`: visible order = `Display-Headstamp -> Machine-Verification -> body`; first literal = `Display-Headstamp: Identity-Context: ... | Layer-Context: ...`; proof owner = `machine_headstamp + headstamp_admission_receipt + controlled-runtime artifacts`.
- `explanatory host-native`: visible order = `Display-Headstamp -> Machine-Verification -> body`; first literal = `Display-Headstamp: Identity-Context: ... | Layer-Context: ...`; proof owner = `explanatory only; governed proof remains external`.
- `controlled-runtime artifact`: visible order = `Identity-Context artifact line -> Machine-Verification receipt or projection -> structured payload`; first literal = `Identity-Context: ... | Layer-Context: ...`; proof owner = `authoritative proof surface`.
- three orders matrix:
- `processing order` (v1.6.6 control plane): `Display render -> Machine truth resolve -> Consistency review -> Business next-hop admission`; do not collapse with `visible line order`.
- `runtime loop` (v1.6.1 native chat injection): `machine-verify -> assistant-visible-inject -> next turn re-verify`; do not collapse with `visible line order`.
- `native chat visible order` (native chat assistant-visible injection): `Identity-Context -> Machine-Verification -> body`; do not collapse with `processing order`.
- `governed visible order` (governed wrapper or explanatory envelope): `Display-Headstamp -> Machine-Verification -> body`; do not collapse with `processing order`.
- object vs literal mapping:
- `display_headstamp`: native literal = `Identity-Context: ... | Layer-Context: ...`; governed literal = `Display-Headstamp: Identity-Context: ... | Layer-Context: ...`; rule = display object never becomes an authority source
- `machine_headstamp`: native literal = `Machine-Verification: ...`; governed literal = `Machine-Verification: ...`; rule = machine truth stays machine-authoritative in control plane
- `headstamp_admission_receipt`: native literal = `not directly rendered; projected through Machine-Verification status fields when needed`; governed literal = `not directly rendered; governs admission and correction state`; rule = admission verdict object for next-hop legality
- `identity_context_literal`: native literal = `Identity-Context: ... | Layer-Context: ...`; governed literal = `embedded after Display-Headstamp prefix`; rule = literal projection only; not a separate truth object
- `requested_identity_id`: native literal = `Identity-Context: withheld; ... requested_identity_id=...`; governed literal = `rendered only inside failure envelopes when needed`; rule = requested target only; never the current speaking identity
- `compatibility_pointer_identity_id`: native literal = `Machine-Verification: ... compatibility_pointer_identity_id=...`; governed literal = `diagnostic-only when explicitly rendered`; rule = compatibility diagnostic only; never replace current-turn authoritative identity
- `manual_headstamp` = render_origin tag only; never verdict axis.
- `EXCLUDED_NON_BLOCKING` only removes blocker aggregation; it never upgrades next-hop admission.
- Ordinary replies should stay focused on the standard native-chat output path; governed receipt or attestation boundaries are audit/debug-only.
- shared compiled brief never acts as current-turn identity authority; success projection remains schematic until a machine-attested actor/session tuple resolves it at turn time.
- without a current-turn machine tuple, native chat must stay on the two-line withheld/conflict envelope.

See source:
- ${IDENTITY_CATALOG}
- ${IDENTITY_HOME}/<resolved_identity_id>/CURRENT_TASK.json  # resolved via catalog pack_path
- ${IDENTITY_HOME}/<resolved_identity_id>/IDENTITY_PROMPT.md  # resolved via catalog pack_path
- /Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local/identity/protocol/plugins/templates/native-chat-headstamp.machine_verification_profiles_v1.json
- /Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local/identity/protocol/plugins/templates/native-chat-headstamp.prompt_hard_guard_v1.json
- /Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local/identity/protocol/plugins/templates/headstamp-surface-semantics.matrix_v1.json
