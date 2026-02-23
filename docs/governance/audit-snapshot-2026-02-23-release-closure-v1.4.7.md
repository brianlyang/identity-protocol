# Audit snapshot — release closure v1.4.7

Date: **2026-02-23**  
Scope: `main@6800018` + `tag v1.4.7`

---

## Executive conclusion

Release readiness is **Conditional Go (strengthened)**:

- **Code-plane**: closed for local-instance persistence boundary + review-required writeback enforcement.
- **Release-plane**: ready for tag/release communication with one explicit residual item on workflow-scope patching.

---

## Closed items

1. **Severe persistence bug closed (code-plane)**  
   Runtime identities now default to local catalog/local instances and are no longer tied to repo lifecycle.

2. **Demo/runtime split codified**  
   `store-manager` is fixture/demo (`profile=fixture`, `runtime_mode=demo_only`), not runtime storage source.

3. **Creator/installer local operating boundary**  
   - creator defaults to local context and local activation switching
   - installer defaults to local target and blocks repo path without explicit override

4. **Writeback closure hardened**  
   release-readiness now enforces experience writeback verification (auto-generates execution report when omitted).

5. **Governance record + README update complete**  
   severe bug is documented and operating model is publicly visible to maintainers.

---

## Residual risk / pending item

### Workflow fail-fast for empty identity target set (High)

`_identity-required-gates.yml` still needs workflow-scoped patch application to guarantee:

- if resolver yields empty IDS, CI fails immediately (no silent skip of identity validators)

Rationale: protects against false-green required-gates when identity-neutral baseline has no active/default identity.

---

## Evidence pointers

- PR merged: `release(v1.4.6): local-instance persistence boundary and writeback closure`
- Main commit: `680001818c9ca46f6dee90e287342d3fe44a79d2`
- Release tag: `v1.4.7`
- Governance incident record: `docs/governance/local-instance-persistence-boundary-v1.4.6.md`
- Migration playbook: `docs/guides/runtime-instance-migration-guide-v1.4.7.md`

---

## Release communication baseline

For all teams consuming identity-protocol:

1. set `IDENTITY_HOME`
2. migrate legacy repo-internal runtime identities via migration script
3. validate local persistence + creator writeback chain
4. avoid runtime operations directly against repo fixture paths

