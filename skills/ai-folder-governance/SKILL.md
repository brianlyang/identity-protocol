---
name: ai-folder-governance
description: Keep identity runtime artifacts in canonical folders and emit governance evidence.
skill_id: ai-folder-governance
version: 1.0.0
owner: identity-protocol
source: protocol-local
---

# AI Folder Governance

## Goal
Keep identity runtime artifacts in canonical folders and prevent scattered files.

## Required Canonical Paths
- Reports: `runtime/reports/`
- Temporary artifacts: `runtime/tmp/`
- State snapshots: `runtime/state/`
- Plugin bindings: `runtime/plugins/`

## Execution Checklist
1. Detect files created outside canonical runtime folders.
2. Propose deterministic relocation targets under canonical paths.
3. Apply relocation only with explicit mutation command.
4. Emit an evidence note listing moved files and final paths.

## Fail-close Rules
- If a required runtime artifact path cannot be resolved to canonical roots, stop and report `IP-SPATH-002`.
- If no governed skill declaration is present, stop and report `IP-SPATH-004`.
