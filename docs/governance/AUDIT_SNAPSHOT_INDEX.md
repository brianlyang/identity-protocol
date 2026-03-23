# Audit Snapshot Index

## Purpose

Quick entrypoint for audit history and remediation closure records.

## Policy

- `docs/governance/audit-snapshot-policy-v1.2.11.md`
- Template: `docs/governance/templates/audit-snapshot-template.md`
- Upgrade cross-validation template: `docs/governance/templates/upgrade-cross-validation-template.md`
- Identity onboarding 72h playbook template:
  - `docs/governance/templates/identity-onboarding-72h-playbook-template.md`
- Identity onboarding 72h audit-return template:
  - `docs/governance/templates/identity-onboarding-72h-audit-return-template.md`
- Architect follow-up issue template pack:
  - `docs/governance/templates/protocol-p1-followup-issue-pack-v1.4.13.md`
- Canonical SSOT rule for protocol-strengthening handoff:
  - `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md`
  - Any `artifacts/` mirror is non-normative evidence only.
- Canonical v1.6.x stream doc registry (single source for governance/review stream paths):
  - `identity/protocol/mappings/stream-doc-registry.current.yaml`
- File-level semantic boundary (mandatory for current-state judgments):
  - **Current-state authoritative set** = `stream_docs + mandatory_static_docs` resolved from `identity/protocol/mappings/stream-doc-registry.current.yaml`.
  - Any other entries in this index are archival/context references unless explicitly promoted into that registry set.
  - If archival wording conflicts with current-pointer mappings or active stream docs, archival wording is stale by definition.
- Canonical layer-targeted required-gate profile mapping (scan/inspection-only trims; strict operations stay full):
  - `identity/protocol/mappings/layer-targeted-gate-profile.current.yaml`
- Canonical actor-scoped session binding governance (v1.5.0):
  - `docs/governance/identity-actor-session-binding-governance-v1.5.0.md`
  - Scope is protocol-only; no instance business policy allowed.
- Canonical actor-scoped session binding governance (v1.6.0 planning track):
  - `docs/governance/identity-actor-session-binding-governance-v1.6.0.md`
  - Companion review ledger: `docs/review/protocol-remediation-audit-ledger-v1.6.md`
- Canonical headstamp egress governance (v1.6.1 stream):
  - `docs/governance/identity-headstamp-egress-governance-v1.6.1.md`
  - Companion review ledger: `docs/review/protocol-remediation-audit-ledger-v1.6.1-headstamp.md`
- Canonical multimodal plugin enforcement governance (v1.6.2 stream):
  - `docs/governance/identity-multimodal-plugin-enforcement-governance-v1.6.2.md`
  - Companion review ledger: `docs/review/protocol-remediation-audit-ledger-v1.6.2.md`
- Canonical GitHub-native control-plane specialization (v1.6.3 planning track):
  - `docs/governance/github-native-control-plane-specialization-v1.6.3.md`
  - Companion review ledger: `docs/review/protocol-remediation-audit-ledger-v1.6.3.md`
- Canonical fail-close monotonic hardening governance (v1.6.4 stream):
  - `docs/governance/identity-failclose-monotonic-governance-v1.6.4.md`
  - Companion review ledger: `docs/review/protocol-remediation-audit-ledger-v1.6.4.md`
- Canonical GitHub Rulesets + super-linter dual-layer governance (v1.6.5 stream):
  - `docs/governance/github-ruleset-super-linter-dual-layer-governance-v1.6.5.md`
  - Companion review ledger: `docs/review/protocol-remediation-audit-ledger-v1.6.5.md`
- Canonical host unique channel governance (v1.6.6 stream):
  - `docs/governance/identity-host-unique-channel-governance-v1.6.6.md`
  - Companion review ledger: `docs/review/protocol-remediation-audit-ledger-v1.6.6.md`
- Canonical cross-layer runtime uniqueness governance (v1.6.7 stream):
  - `docs/governance/identity-cross-layer-runtime-uniqueness-governance-v1.6.7.md`
  - Companion review ledger: `docs/review/protocol-remediation-audit-ledger-v1.6.7.md`
- Canonical downsink path immutability governance (v1.6.8 stream):
  - `docs/governance/identity-downsink-path-immutability-governance-v1.6.8.md`
  - Companion review ledger: `docs/review/protocol-remediation-audit-ledger-v1.6.8.md`
- Canonical runtime file governance boundary freeze (v1.6.10 stream):
  - `docs/governance/identity-runtime-file-governance-control-plane-v1.6.10.md`
  - Companion review ledger: `docs/review/protocol-remediation-audit-ledger-v1.6.10-runtime-file-governance.md`
- Canonical outer-agent final answer governance (v1.6.11 stream):
  - `docs/governance/agent-relay-final-answer-governance-v1.6.11.md`
  - Companion review ledger: `docs/review/protocol-remediation-audit-ledger-v1.6.11-agent-relay-final-answer.md`
- Canonical native-chat bootstrap entry governance (v1.6.12 stream):
  - `docs/governance/identity-native-chat-bootstrap-entry-governance-v1.6.12.md`
  - Companion review ledger: `docs/review/protocol-remediation-audit-ledger-v1.6.12-native-chat-bootstrap-entry.md`
- Canonical identity-instance pack topology governance (v1.6.13 stream):
  - `docs/governance/identity-instance-pack-topology-governance-v1.6.13.md`
  - Companion review ledger: `docs/review/protocol-remediation-audit-ledger-v1.6.13-instance-pack-topology.md`
- Canonical identity-Codex launcher governance (v1.6.14 stream):
  - `docs/governance/identity-codex-launcher-governance-v1.6.14.md`
  - Companion review ledger: `docs/review/protocol-remediation-audit-ledger-v1.6.14-identity-codex-launcher.md`
- Canonical identity-instance script orchestration governance (v1.6.15 stream):
  - `docs/governance/identity-instance-script-orchestration-governance-v1.6.15.md`
  - Companion review ledger: `docs/review/protocol-remediation-audit-ledger-v1.6.15-instance-script-orchestration.md`
- Canonical identity-context continuity governance (v1.6.16 stream):
  - `docs/governance/identity-context-continuity-governance-v1.6.16.md`
  - Companion review ledger: `docs/review/protocol-remediation-audit-ledger-v1.6.16-identity-context-continuity.md`
- Canonical identity-routing/learning strengthening governance (v1.6.17 stream):
  - `docs/governance/identity-routing-learning-strengthening-governance-v1.6.17.md`
  - Companion review ledger: `docs/review/protocol-remediation-audit-ledger-v1.6.17-routing-learning-strengthening.md`
- Canonical identity artifact-family routing governance (v1.6.18 stream):
  - `docs/governance/identity-artifact-family-routing-governance-v1.6.18.md`
  - Companion review ledger: `docs/review/protocol-remediation-audit-ledger-v1.6.18-artifact-family-routing.md`

## Snapshots

- `docs/governance/audit-snapshot-2026-02-21.md` — consolidated closure for PR #8/#9/#10/#11/#12 and residual-risk follow-up
- `docs/governance/audit-snapshot-2026-02-21-control-loop-v1.4.0.md` — control-loop contract integration evidence (orchestration/knowledge/experience/ci-enforcement)
- `docs/governance/audit-snapshot-2026-02-21-release-closure-v1.4.2.md` — release closure for PR #25/#26 and autonomous-upgrade gap mitigation progress
- `docs/governance/audit-snapshot-2026-02-22-release-closure-v1.4.4.md` — release closure for PR #29 installer-plane separation + authenticity hardening + install provenance chain enforcement
- `docs/governance/audit-snapshot-2026-02-23-v1.4.6-role-binding-bootstrap.md` — role-binding contract bootstrap, activation switch guard, release-boundary hardening
- `docs/governance/audit-snapshot-2026-02-23-release-closure-v1.4.7.md` — severe local-instance persistence bug closure + writeback enforcement release snapshot (with workflow residual risk note)
- `docs/governance/audit-snapshot-2026-02-24-self-heal-and-permission-state-v1.4.12.md` — self-heal orchestration + health diagnostics + permission-state CI contract closure
- `docs/governance/audit-snapshot-2026-02-24-release-doc-governance-closure-v1.4.12.md` — documentation-first release closure set, source-of-truth repo boundary, and audit handoff requirements
- `docs/governance/audit-snapshot-2026-02-24-identity-path-governance-final-closure-v1.4.12.md` — multi-round audit consolidation for identity path governance, skills-parity operator model, and final architect action checklist
- `docs/governance/audit-unified-result-package-v1.4.12.md` — consolidated audit package: final posture, remaining blockers, root-cause summary, and final remediation/acceptance checklist
- `docs/governance/runtime-artifact-isolation-root-cause-and-remediation-v1.4.12.md` — root-cause analysis and hardening actions for runtime artifact pollution / dirty-worktree drift
- `docs/governance/audit-snapshot-2026-02-25-protocol-runtime-boundary-closure-v1.4.12.md` — protocol/runtime hard-boundary closure (no repo runtime fallback), fixture override semantics, and cleanliness verification evidence
- `docs/governance/audit-snapshot-2026-02-25-readme-core-goal-alignment-v1.4.13.md` — root README core objective alignment (deterministic/auditable/release-safe), boundary model clarification (identity/agent/skill/MCP/tool), and prompt-lifecycle governance semantics
- `docs/governance/identity-token-efficiency-and-skill-parity-governance-v1.4.13.md` — token-consumption governance upgrade requirements with cross-vendor validation (tiered gates, incremental execution, summary/full report split, cache strategy, and skill-parity operator model)
- `docs/governance/identity-token-governance-audit-checklist-v1.4.13.md` — three-plane audit checklist (instance fail-operational / release fail-closed) and cloud-closure evidence contract
- `docs/governance/identity-environment-path-deep-audit-and-self-drive-upgrade-v1.4.13.md` — environment/path governance deep audit with 2026-02-26 closure addendum (recoverable report contract, runtime mode drift guard, and cross-validated evidence log)
- `docs/governance/identity-base-protocol-runtime-retro-and-governance-feedback-v1.4.13.md` — protocol-only retro + governance hardening baseline (anti-coupling rules, dialogue governance contract/KPI model, and implementation DoD)
- `docs/governance/identity-protocol-strengthening-handoff-v1.4.13.md` — canonical execution handoff (SSOT) for protocol strengthening: anti-sprawl budget, gate/validator/error-code mapping, DCIC + audit-ownership enforcement, and architect action checklist
- `docs/governance/office-ops-expert-instance-runtime-retro-and-protocol-feedback-v1.4.13.md` — compatibility alias that forwards to canonical protocol-only v1.4.13 governance doc

## Protocol hardening plans

- `docs/governance/p1-human-collab-trigger-upgrade-plan-2026-02-21.md` — protocol-level standardization plan for mandatory human-collaboration notification triggers (taxonomy + contract + validator + CI gate), **implemented in v1.3.0**
- `docs/governance/github-native-control-plane-specialization-v1.6.3.md` — v1.6.3 dedicated migration stream for GitHub-native control-plane offload (rulesets/merge-queue/codeowners/actions-policy) with semantic fail-close retention in protocol validators.
- `docs/governance/identity-failclose-monotonic-governance-v1.6.4.md` — v1.6.4 dedicated semantic hardening stream for config-first plugin flow, upgrade-only (no-downgrade) enforcement, and newcomer-safe continuity.
- `docs/governance/github-ruleset-super-linter-dual-layer-governance-v1.6.5.md` — v1.6.5 dedicated dual-layer stream for platform-native file governance (rulesets) plus repository lint convergence (super-linter) while retaining protocol semantic fail-close contracts in-repo.
- `docs/governance/identity-host-unique-channel-governance-v1.6.6.md` — v1.6.6 dedicated host-channel closure stream for mandatory per-instance ingress/egress wrappers, wrapper-only dispatch/release against protocol canonical gates, and required `stream_pr_binding.json` + host replay evidence package.
- `docs/governance/identity-cross-layer-runtime-uniqueness-governance-v1.6.7.md` — v1.6.7 dedicated runtime-source arbitration stream for single active runtime owner per identity across project/global catalogs, with fail-close duplicate detection and repair tooling.
- `docs/governance/identity-downsink-path-immutability-governance-v1.6.8.md` — v1.6.8 dedicated path-immutability stream for protocol-governed downsink assets (`runtime/gate`, `runtime/state`, `runtime/reports`, `runtime/protocol-feedback`, and protocol broadcast source paths), including core contract registry + required CI negative probes.
- `docs/governance/identity-runtime-file-governance-control-plane-v1.6.10.md` — v1.6.10 dedicated boundary-freeze stream for runtime dynamic file governance: wrapper strong-control, mirror constrained, runtime default autonomy, all machine-checked via semantic clarity + boundary validator surfaces.
- `docs/governance/identity-instance-pack-topology-governance-v1.6.13.md` — v1.6.13 dedicated topology-lock stream for canonical identity-pack root layout (`agents/`, `runtime/`, `scripts/`), root-level instance script ownership, and fail-close drift gating.
- `docs/governance/identity-codex-launcher-governance-v1.6.14.md` — v1.6.14 dedicated launcher-governance stream for canonical identity-bound Codex command names, install-path ownership, compatibility-bridge classification, and fail-close startup boundaries.
- `docs/governance/identity-instance-script-orchestration-governance-v1.6.15.md` — v1.6.15 dedicated orchestration stream for route-to-script declarative binding, pack-local script manifests, explicit script-to-skill/MCP/tool joins, and reusable execution receipt-family governance.
- `docs/governance/identity-context-continuity-governance-v1.6.16.md` — v1.6.16 dedicated continuity stream for governed checkpoints, migration handoff checkpoints, startup-consumable re-entry briefing, and the authority boundary that keeps continuity artifacts subordinate to protocol truth.
- `docs/governance/identity-routing-learning-strengthening-governance-v1.6.17.md` — v1.6.17 dedicated strengthening stream for lifting the kernel `Auto-routing contract` and `Rule learning contract` into symmetric runtime-consumable upper-layer bindings, without redefining the kernel source contracts or introducing backward-compatibility backstops.
- `docs/governance/identity-artifact-family-routing-governance-v1.6.18.md` — v1.6.18 dedicated routing stream for freezing the protocol-scoped artifact-family matrix across pack rulebook, pack task-history, dialogue-governance, experience-feedback, protocol-feedback, continuity/reentry, and memory-absorption quarantine surfaces so they cannot collapse back into generic "memory" wording.
