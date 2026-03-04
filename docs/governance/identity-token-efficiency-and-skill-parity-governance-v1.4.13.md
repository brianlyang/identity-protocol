# Identity Token Efficiency And Skill-Parity Governance (v1.4.13)

## Purpose

Define a token-efficiency governance upgrade that preserves identity runtime safety and release-grade auditability.

This document is a governance baseline, not a pricing document.
All targets are token/ratio based.

## Core principles

1. stable prefix + reusable context
2. preflight token estimation before heavy chains
3. async/batch for non-urgent workloads
4. usage-metadata-driven optimization
5. quality-preserving efficiency (no gate-skipping credit)

## Plane model (mandatory)

1. **Instance-plane**: fail-operational (recoverable progress)
2. **Repo-plane**: contract consistency and anti-drift governance
3. **Release-plane**: fail-closed for Full Go

Do not mix closure claims across planes.

## Identity/Skill/MCP/Tool boundary

Execution precedence:

`Identity Contract > Skill Strategy > MCP Context > Tool Action`

Tool success is never sufficient for governance success.

## Tier model

1. `FAST` daily operation
2. `STANDARD` pre-merge confidence
3. `FULL` release-only closure

Only `FULL` can produce Release-plane promotion claims.

## Metric model

Primary dimensions:

1. closure efficiency
2. rerun waste ratio
3. governance tax ratio
4. reusable context ratio

Target direction:

- daily median token reduction >= 40%
- repeat-run token reduction >= 60%
- rerun waste ratio < 10%

## Full Go boundary

Full Go requires all planes closed.

Release-plane requires cloud closure evidence (required-gates alignment, checks green, workflow SHA aligned).

## References

- OpenAI prompt caching / batch / cost optimization / flex processing
- Anthropic prompt caching / token counting / batch / skills
- Gemini caching / tokens / live usage / batch
- Context7 cross-verification indices:
  - `/websites/developers_openai`
  - `/websites/platform_claude_en`
  - `/websites/ai_google_dev_gemini-api`

