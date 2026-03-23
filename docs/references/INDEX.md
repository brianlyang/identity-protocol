# Protocol Reference Visual Atlas Inventory

Status: Active canonical inventory for protocol-owned visual atlas families.
Layer: protocol
Scope: canonical inventory and discoverability surface for atlas-family docs, asset roots, validators, and onboarding ownership.

## Current control-plane alias refs

- `identity/protocol/mappings/stream-doc-registry.current.yaml`
- `identity/protocol/mappings/contract-binding.current.yaml`
- `identity/protocol/mappings/semantic-term-registry.current.yaml`
- `identity/protocol/mappings/reference-visual-atlas-registry.current.yaml`

## Fixed role boundary

1. This file is the canonical inventory/discoverability surface for protocol-owned visual atlas families under `docs/references/`.
2. `docs/references/README.md` remains the onboarding contract and generator/probe playbook; this file is the atlas-family inventory, not the onboarding guide.
3. Individual atlas markdown docs remain the family-specific explanatory surfaces.
4. Normative semantic truth remains with owner governance/review docs, the protocol motherline, contract binding, and machine validators.
5. The machine-readable inventory backing this page is:
   - `identity/protocol/mappings/reference-visual-atlas-registry.current.yaml`

## Shared onboarding control surfaces

- Scaffold generator:
  - `python3 scripts/generate_reference_visual_atlas_scaffold.py --help`
- Shared anti-rot probe:
  - `bash scripts/ci/run_reference_visual_atlas_scaffold_probes_ci.sh`
- Shared validator common:
  - `scripts/reference_visual_atlas_governance_common.py`

## Canonical atlas families

| Family | Canonical doc | Asset root | Validator | Owner docs | Scope mode |
| --- | --- | --- | --- | --- | --- |
| `loop_visual_atlas` | `docs/references/identity-protocol-loop-visual-atlas-v1.6.md` | `docs/references/assets/identity-protocol-loop-visual-atlas/` | `scripts/validate_loop_visual_atlas_governance.py` | `docs/governance/identity-multimodal-plugin-enforcement-governance-v1.6.2.md`; `docs/governance/identity-routing-learning-strengthening-governance-v1.6.17.md`; `docs/review/protocol-remediation-audit-ledger-v1.6.17-routing-learning-strengthening.md` | `protocol_repo_internal_only` |
| `artifact_family_routing_visual_atlas` | `docs/references/identity-protocol-artifact-family-routing-visual-atlas-v1.6.md` | `docs/references/assets/identity-protocol-artifact-family-routing-visual-atlas/` | `scripts/validate_artifact_family_visual_atlas_governance.py` | `docs/governance/identity-artifact-family-routing-governance-v1.6.18.md`; `docs/review/protocol-remediation-audit-ledger-v1.6.18-artifact-family-routing.md` | `protocol_repo_internal_only` |

## Inventory discipline

1. Every canonical atlas family must appear in both:
   - `identity/protocol/mappings/reference-visual-atlas-registry.current.yaml`
   - this inventory page
2. Every registered family must point to:
   - one canonical atlas markdown doc,
   - one canonical asset root,
   - one thin validator script,
   - one or more owner docs.
3. Future atlas-family growth must update this inventory in the same closure as the registry row, owner-doc backlinks, stream-doc-registry entry, and validator landing.
4. The inventory is stale if it omits a landed atlas validator or lists a family whose canonical doc/asset root/validator no longer exists.
