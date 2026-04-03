# Root Lane Handoff Compatibility Contract

This file records the pre-existing `root-lane-handoff` artifact family as a
compatibility-only surface.
This file is admitted at protocol root only as clearly demoted support material.
It is not active-runtime truth for canonical handoff law and does not compete with the accepted lane-card handoff contract.

The canonical handoff law remains the accepted `ISSUE-040A`
`lane_card_handoff_contract_v1` surface.
Parallel root-lane-handoff artifacts must not compete with that canonical
lane-card handoff family.
Chat remains navigation-only, not durable handoff state.
No card, no handoff.
No card, no takeover.

<!-- root-lane-handoff-contract:start -->
```json
{
  "artifact_family": "root_lane_handoff",
  "artifact_classification": "compatibility",
  "canonical_contract_type": "lane_card_handoff_contract_v1",
  "canonical_governance_doc": "docs/governance/identity-lane-card-handoff-governance-v1.6.x.md",
  "canonical_review_doc": "docs/review/protocol-remediation-audit-ledger-v1.6.x-lane-card-handoff.md",
  "governing_law": "canonical_lane_card_handoff_family_must_not_compete_with_parallel_root_handoff_artifacts",
  "non_competition_rule": "competing canonical handoff semantics fail-close",
  "accepted_issue_commit": "c09a3a6"
}
```
<!-- root-lane-handoff-contract:end -->

## Compatibility boundary

- This file is compatibility-only.
- It must not originate or claim an alternate canonical handoff law.
- Validators must fail-close if this artifact family claims canonical handoff authority.
- Mappings and probes for this family exist only to reconcile legacy root-lane-handoff surfaces with the accepted `ISSUE-040A` lane-card contract.
