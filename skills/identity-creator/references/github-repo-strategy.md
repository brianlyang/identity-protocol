# GitHub Repository Strategy for Identity Protocol

## Recommendation

Use a dedicated repository for identity protocol standards, then vend into project repos.

## Why

- Identity protocol is cross-project governance infrastructure.
- Versioning and audit become cleaner than embedding protocol evolution in a single app repo.
- Reuse is easier for multiple agents (store-manager, supervisor, selector, etc.).

## Suggested model

- Repo A (protocol): `identity-protocol`
  - protocol docs
  - registry/schema templates
  - identity-creator skill
- Repo B (business project): `weixinstore`
  - identity instances
  - runtime states
  - project-specific packs

## Sync method

- Option 1: Git subtree (recommended for simplicity)
- Option 2: Git submodule (stricter pinning)
- Option 3: periodic sync script (lightweight, less strict)

## Release policy

- Semantic versioning for protocol repo.
- Business repos pin protocol version and upgrade intentionally.
