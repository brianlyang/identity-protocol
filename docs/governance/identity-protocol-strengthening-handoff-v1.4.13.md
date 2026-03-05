# Identity Protocol Strengthening Handoff (v1.4.13)

Status: Canonical handoff summary (protocol-layer only)
Governance layer: protocol
Applies to: identity protocol base-repo architecture decisions only

This handoff note exists to keep index links stable and provide a concise execution bridge
between audit findings and implementation tasks in v1.4.13.

## 2026-03-04 release lane CI hotfix addendum

To keep protocol-core release gates fail-closed without false negatives:

1. Required-gates workflow now pins `rhysd/actionlint` to a valid immutable tag.
2. Upgrade-report lookup in CI no longer uses `ls` (shellcheck `SC2012` compliance).
3. Fixture and runtime identities share compatibility fixes for:
   - runtime evidence pattern resolution (pack-local first + repo fallback),
   - repository-relative rulebook path resolution,
   - prompt quality scope arbitration (`--scope AUTO`),
   - role-binding evidence lookup fallback behavior.
   - actor-session binding validators downgrade fixture identities to
     `SKIPPED_NOT_REQUIRED` during CI inspection operations.
   - cross-actor isolation validator skips strict enforcement when catalog has
     no active identities (fixture-only catalogs).
   - session refresh status validator skips fixture identities in strict/CI
     lanes (`required_contract=false`) to prevent false P0 drift alarms.
   - send-time reply gate skips fixture identities in strict/CI lanes to avoid
     synthetic evidence enforcement against demo-only validation paths.
   - trigger-regression validator resolves fixture sample reports using
     pack-local first and repository-runtime fallback.
   - learning-loop validator resolves fixture run-report and rulebook paths
     using repository-runtime fallback where pack-local assets are absent.
4. Fixture samples were refreshed to maintain required gate freshness:
   - store-manager prompt principle token presence,
   - store-manager role-binding evidence timestamp,
   - system-requirements-analyst blocker taxonomy alias bridge normalization.

This addendum is protocol-governance guidance only; release semantics and fail-closed policy remain unchanged.

Execution directive (mandatory):

1. Execute protocol-strengthening items based on this handoff document only.
2. Any `artifacts/` mirror is evidence-only and must not be treated as normative source.
3. Core-change coupling scope is maintained in:
   - `docs/governance/templates/protocol-core-change-map.yaml`
   - update this map when protocol-core scope changes.

## Layered governance boundary (mandatory)

Protocol layer governance (this document scope):

1. Canonical SSOT/governance docs and templates under `docs/governance/`
2. Protocol validators under `scripts/validate_protocol_*` and protocol gate wiring in workflow/readiness/e2e/three-plane
3. Protocol-safe defaults and boundary contracts (no business-scene coupling)

Identity instance governance (explicitly out of scope here):

1. Runtime instance behavior in `CURRENT_TASK.json`, `IDENTITY_PROMPT.md`, `RULEBOOK.jsonl`
2. Roundtable/collaboration style, vendor-specific operation style, and per-instance execution routing preferences
3. Business-task artifacts and instance-local retros

Cross-layer interface rule:

1. Protocol layer defines machine-checkable contracts and gates.
2. Instance layer implements behavior within those contracts.
3. Instance-specific policy must not be promoted into protocol mandatory gates without explicit protocol review.

## Scope guardrails

1. Protocol layer only (no business-scene coupling)
2. No user-specific absolute path as normative requirement
3. No default-identity hardcoding in protocol-critical gates
4. Recoverable blocked states remain fail-operational; hard boundaries remain fail-closed

## Repository path governance matrix (mandatory)

This section normalizes the repository paths highlighted in protocol audits and defines their governance layer and coupling mode.

1. `identity/`
   - `identity/catalog/**` and `identity/protocol/**` are protocol-governed assets.
   - `identity/store-manager/**` and `identity/packs/**` are protocol baseline/example identities; changes must preserve protocol-level non-hardcoded semantics.
   - `identity/runtime/**` is runtime evidence/artifact surface and remains non-normative.
2. `skills/`
   - Protocol-adjacent capability packs; changes are allowed but must not introduce protocol hard requirements unless promoted through protocol review.
3. `README.md`
   - Operator-facing protocol entry; contract-level changes must stay aligned with canonical handoff and validator command set.
4. `CHANGELOG.md`
   - Release traceability ledger; significant protocol-core changes require changelog linkage, but changelog edits alone do not define protocol contract.
5. `VERSIONING.md`
   - Version/governance semantics for protocol release policy; edits are protocol governance changes and must remain consistent with canonical handoff.
6. `requirements-dev.txt`
   - Toolchain dependency baseline for local audit parity; updates require preflight/readiness replay evidence.

## Canonical references

- `docs/governance/identity-base-protocol-runtime-retro-and-governance-feedback-v1.4.13.md`
- `docs/governance/identity-environment-path-deep-audit-and-self-drive-upgrade-v1.4.13.md`
- `docs/governance/identity-token-efficiency-and-skill-parity-governance-v1.4.13.md`
- `docs/governance/identity-token-governance-audit-checklist-v1.4.13.md`
- `docs/governance/templates/protocol-p1-followup-issue-pack-v1.4.13.md` (copy-ready architect issue templates for P1 hardening)

## Architect execution bundle (single-send)

Use this bundle in order to avoid interpretation drift:

1. Canonical directive: this handoff (`identity-protocol-strengthening-handoff-v1.4.13.md`)
2. P1 copy-ready templates: `docs/governance/templates/protocol-p1-followup-issue-pack-v1.4.13.md`
3. Core-change coupling scope: `docs/governance/templates/protocol-core-change-map.yaml`
4. Validation replay commands: "Required validation command set" section below

Required architect reply format:

1. commit sha list
2. changed file list
3. acceptance command outputs (per issue / per gate)
4. residual risks + next milestone

## Document lifecycle governance (mandatory)

Operational axiom:

`SSOT + gate binding + periodic archive`

Lifecycle rules:

1. Each protocol topic has one canonical governance entry document.
2. New governance docs must bind to at least one gate or validator; otherwise classify as evidence-only/archive.
3. Template docs stay under `docs/governance/templates/` and must be referenced by canonical documents.
4. Keep active governance set lean; periodically archive outdated snapshots to avoid protocol-doc sprawl.

## v1.4.13 implementation highlights (landed)

1. capability blocked/arbitration/report linkage hardening
2. canonical session pointer consistency + activation rollback semantics
3. repo/runtime path boundary hardening and fallback explicitization
4. dialogue governance validator chain (contract-first, optional, warn/enforce)
5. required-gates / e2e / readiness / three-plane integration

## v1.4.13 protocol closure addendum (2026-02-27, protocol-layer)

1. Execution report freshness preflight (P0 closure)
   - `release_readiness_check.py` now runs `validate_execution_report_freshness.py` before late-stage writeback/activation linkage validators.
   - freshness gate checks report binding consistency against current runtime tuple:
     - `identity_id`
     - `catalog_path`
     - `resolved_pack_path`
     - prompt path + prompt sha
     - report mtime vs key-input mtime (`IDENTITY_PROMPT.md` / `CURRENT_TASK.json`)
   - stale/mismatch is emitted as structured code `IP-REL-001` with policy control:
     - `--execution-report-policy strict|warn` (default `strict`)
   - report candidate binding is now pack-local first:
     - search `<resolved_pack>/runtime/reports` then `<resolved_pack>/runtime`
     - only fallback to shared roots (`/tmp`, `$IDENTITY_HOME`) when local reports are absent
     - purpose: prevent cross-catalog identity-id collisions from selecting another instance's report
2. Required-contract coverage semantics (P1 closure)
   - added `validate_required_contract_coverage.py` to classify contract-first tool/vendor validators:
     - `PASS_REQUIRED`
     - `SKIPPED_NOT_REQUIRED`
     - `FAIL_REQUIRED`
     - `FAIL_OPTIONAL`
   - coverage metrics are machine-readable:
     - `required_contract_total`
     - `required_contract_passed`
     - `required_contract_coverage_rate`
     - `skipped_contract_count`
   - optional policy threshold:
     - `--min-required-contract-coverage <0-100>`
3. Main-chain wiring completed (protocol gates only)
   - readiness: `scripts/release_readiness_check.py`
   - e2e: `scripts/e2e_smoke_test.sh`
   - three-plane: `scripts/report_three_plane_status.py`
   - full-scan: `scripts/full_identity_protocol_scan.py`
   - creator validate chain: `scripts/identity_creator.py validate`
   - required workflow gates: `.github/workflows/_identity-required-gates.yml`
4. Protocol baseline propagation closure (P0/P1)
   - added `scripts/validate_identity_protocol_baseline_freshness.py`:
     - compares `report.protocol_commit_sha` against current protocol HEAD under `report.protocol_root`
     - emits machine-readable status: `PASS|WARN|FAIL`
     - error codes:
       - `IP-PBL-001` baseline stale
       - `IP-PBL-002` report missing/invalid
       - `IP-PBL-003` protocol sha invalid
       - `IP-PBL-004` protocol root unavailable
   - health integration:
     - `collect_identity_health_report.py` includes `protocol_baseline_freshness` with `--baseline-policy warn`
     - health contract supports `PASS/WARN/FAIL` and keeps `--require-pass` fail only on `FAIL`
   - preflight + visibility integration:
     - readiness adds protocol baseline preflight (`--baseline-policy strict|warn`, default `strict`)
     - full-scan and three-plane expose baseline freshness fields for audit visibility
     - e2e and required workflow gates run baseline freshness checks
   - baseline report selection follows the same local-first rule as freshness preflight:
     - prioritize reports under resolved pack runtime path
     - use shared-root fallback only when local reports are missing
     - avoids protocol baseline checks drifting across project/global instances with same identity id
5. Protocol upgrade wave orchestration (P1)
   - added `scripts/run_protocol_upgrade_wave.py` for catalog-driven closure:
     - discover runtime identities from catalog (or explicit `--identity-ids`)
     - detect stale protocol baseline via validator
     - dry-run inventory and optional apply mode for batched `identity_creator update`
     - emits machine-readable wave report with per-identity `baseline_status/update_rc/next_action/error_code`
6. Prompt lifecycle deferred-blocked semantics (P0 false-positive closure)
   - `validate_identity_prompt_lifecycle.py` now distinguishes:
     - mutation-required failures
     - pre-mutation blocked outcomes (`IP-UPG-001` / `IP-PERM-001`)
     - review-required deferred outcomes
       (`next_action=review_required_create_pr_from_patch_plan`,
       `identity_prompt_change_note=prompt_change_deferred_due_to_failed_validators`)
   - when execution report is `all_ok=false` due known policy/permission hard boundary,
     prompt lifecycle can remain deferred without being misclassified as malformed.
   - keeps fail-closed behavior for real lifecycle inconsistencies while avoiding
     false P0 escalation on intentionally blocked mutation paths.

## v1.4.13 follow-up closure scope (2026-02-26, protocol-layer)

1. Session pointer mirror deconfliction
   - mirror default moved to catalog-scoped path (`<catalog_dir>/session/mirror/current.json`)
   - mirror mismatch is warning-only by default; `--require-mirror` enables hard-fail mode
   - canonical pointer write/validation remains hard-fail in activation transaction
2. Capability preflight robustness
   - GitHub capability checks split into CLI presence + auth readiness semantics
   - explicit blocked code path (`IP-CAP-003`) remains recoverable/fail-operational
   - hidden/missing `gh` binary now handled without traceback
3. Install/adopt relocation safety
   - install flow now runs path rewrite (aligned with adopt)
   - rewrite coverage expanded to runtime JSON evidence surfaces and path-bearing fields
   - rewrite counters emitted in install report for audit traceability
4. Validator portability + path governance hardening
   - validator subprocess calls are cwd-agnostic where required
   - contract pattern resolution supports absolute and pack-relative forms
   - migrated instances with absolute historical patterns no longer fail on `Path.glob` limitations
5. Local audit parity
   - preflight now checks `actionlint + ast-grep + gitleaks + gh-auth`
   - strict profile (`--require-gh-auth`) makes auth readiness gating explicit
6. Historical changelog linkage closure
   - changelog gate supports explicit backfill linkage for historical ranges
   - strict in-range mode remains available via `--strict-range-only`
7. Release freeze boundary track separation
   - fixture/demo catalog rows under `identity/packs/*` are explicitly allowed
   - non-fixture rows under `identity/packs/*` remain hard-fail
   - keeps A-track protocol hardening executable while preserving B-track asset isolation semantics
8. Full-scan environment-aware capability severity
   - `full_identity_protocol_scan.py` marks `IP-CAP-003` as environment-auth blocker (`P1`) instead of protocol-regression `P0`
   - capability output now carries parsed status/code hints for deterministic downstream audit interpretation
9. Governance templates (protocol-safe extension)
   - onboarding playbook/audit-return templates add dual-ledger + roundtable evidence structure
   - templates remain non-normative unless promoted via canonical SSOT workflow
10. Scope-arbitrated full-scan + fixture noise suppression
   - `resolve_identity_context.py` now classifies fixture/demo identities as `SYSTEM`
     scope independent of source layer (`repo` or `local`) to avoid split semantics.
   - scope validators accept explicit arbitration (`--scope`) as conflict-closure signal:
     - `validate_identity_scope_resolution.py`
     - `validate_identity_scope_isolation.py`
   - `report_three_plane_status.py` now supports explicit `--scope` pass-through to
     keep three-plane runs deterministic under dual-catalog overlap.
   - `full_identity_protocol_scan.py` now propagates catalog-derived scope hints
     into resolve/scope/three-plane checks and avoids false P1 on fixture/demo-only
     prompt-quality + baseline-warn combinations.
   - runtime identities keep strict semantics unchanged; only fixture/demo
     non-runtime paths are downgraded from false-blocking P1 noise to non-blocking visibility.

## Required validation command set

Run environment preflight first (toolchain + auth readiness visibility):

```bash
bash scripts/preflight_protocol_audit_env.sh
```

For release-grade strict profiles that require GitHub capability auth readiness:

```bash
bash scripts/preflight_protocol_audit_env.sh --require-gh-auth
```

Notes:

1. If `gh auth` is not ready, strict-union readiness may fail with `IP-CAP-003`.
2. This is an environment-auth state, not a protocol-regression signal.
3. Local protocol-gate replay can still proceed without `--require-gh-auth`.

```bash
python3 scripts/validate_identity_protocol.py
python3 scripts/validate_identity_local_persistence.py
python3 scripts/validate_identity_creation_boundary.py
python3 scripts/docs_command_contract_check.py
python3 scripts/validate_release_workspace_cleanliness.py
python3 scripts/validate_protocol_ssot_source.py
python3 scripts/validate_protocol_handoff_coupling.py --base HEAD~1 --head HEAD
python3 scripts/validate_execution_report_freshness.py --identity-id <id> --catalog <catalog> --repo-catalog identity/catalog/identities.yaml --execution-report-policy strict
python3 scripts/validate_identity_protocol_baseline_freshness.py --identity-id <id> --catalog <catalog> --repo-catalog identity/catalog/identities.yaml --baseline-policy warn
python3 scripts/validate_required_contract_coverage.py --identity-id <id> --catalog <catalog>
python3 scripts/run_protocol_upgrade_wave.py --catalog <catalog> --dry-run --out /tmp/identity-upgrade-wave-dryrun.json
```
