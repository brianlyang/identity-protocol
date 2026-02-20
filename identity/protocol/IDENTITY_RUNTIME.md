# Identity Runtime Integration

## Integration objective

Make identity runtime behavior explicit while staying compatible with current Codex capabilities.

## Native vs extension boundary

Native Codex features:
- skill discovery and invocation
- MCP server configuration
- AGENTS instruction chain loading

Project extension features:
- identity catalog parsing
- identity pack validation
- runtime state and compile steps

## Startup sequence

1. Read `.codex/config.toml`.
2. Resolve `model_instructions_file` relative to `.codex/config.toml` directory.
   - Example in this repo: `../identity/runtime/IDENTITY_COMPILED.md`.
3. Read active identity from `identity/catalog/identities.yaml` (`default_identity` or override).
4. Validate identity pack exists and required files are present.
5. Validate CURRENT_TASK minimum required blocks.
6. Validate baseline-review evidence if `protocol_baseline_review_gate` is `required`.
7. Allow execution.

If validation fails, block high-impact actions and require repair.

## Compile artifact

`identity/runtime/IDENTITY_COMPILED.md` is a compact runtime brief containing:
- active identity metadata
- hard guardrails summary
- current objective and state
- allowed skills and MCP dependencies

## Execution guard checks

Before high-impact actions (listing/relisting/repricing):
- guardrails present
- reject-memory gate present
- payload evidence path present

Before identity-level capability upgrade conclusions:
- protocol baseline review gate must pass
- review evidence must include mandatory sources and decision trace

## Post-action requirements

After each high-impact action:
- update CURRENT_TASK state
- append TASK_HISTORY entry
- persist evidence artifact paths
