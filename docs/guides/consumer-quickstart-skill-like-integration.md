# Consumer Quickstart: Skill-like Identity Integration

Goal: integrate identity protocol with skill-like bottom guardrails and deterministic checks.

## 1) Pin protocol version

In consumer repo:

```yaml
# identity/PROTOCOL_PIN.yaml
protocol_repo: "https://github.com/<org>/identity-protocol"
pinned_tag: "vX.Y.Z"
pinned_commit: "<full_sha>"
```

## 2) Wire model instructions to compiled identity runtime

In `.codex/config.toml`:

```toml
model_instructions_file = "../identity/runtime/IDENTITY_COMPILED.md"
```

## 3) Enable required skills

Add `[[skills.config]]` entries for role-critical skills and route dependencies.

## 4) Validate bottom guardrails

Run in consumer repo:

```bash
python3 scripts/identity/check_protocol_pin.py
python3 scripts/identity/validate_identity_manifest.py
python3 scripts/identity/test_identity_discovery_contract.py
python3 scripts/identity/validate_identity_runtime_contract.py
```

Optional one-shot:

```bash
bash scripts/identity/upgrade_and_verify_v1.sh
```

## 5) Validate learning loop (#2 and #4)

```bash
python3 scripts/identity/validate_identity_learning_loop.py \
  --run-report identity/runtime/examples/store-manager-learning-sample.json
```

## 6) Release gate

Only publish consumer update when:
- pin matches remote tag commit
- runtime contract validation passes
- learning-loop validation passes
- route resolvability checks pass for critical problem types

## Notes

Identity should remain protocol-driven and scenario-agnostic.
Business-specific routes and thresholds belong to consumer/runtime layers, not core protocol semantics.
