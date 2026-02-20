# Skill + MCP + Tool Collaboration Contract (v1.0)

This reference defines how skill strategy, MCP capability access, and tool execution interact at runtime.

Goal: keep identity upgrades grounded in a deterministic collaboration model instead of ad-hoc assumptions.

---

## 1) Three-layer model

1. **Skill layer (strategy layer)**
   - Defines when to act, in what sequence, with what validation/retry/fallback behavior.

2. **MCP layer (capability access layer)**
   - Exposes external system abilities (GitHub, browser, n8n, etc.) as callable tools.

3. **Tool layer (execution layer)**
   - Executes concrete actions (API call, file write, PR creation, issue query, workflow trigger).

Key statement:
- skill does not execute external API by itself
- skill does not auto-bind to one MCP server
- skill constrains model decisions that select and call tools via MCP

---

## 2) Runtime call chain

1. user request arrives
2. model checks skill metadata match (`name`, `description`)
3. if matched, model loads `SKILL.md` workflow
4. workflow steps are mapped to tool calls
5. tool calls are executed through MCP server
6. MCP returns structured result to model
7. model decides next step (continue/retry/fallback/escalate)
8. final output includes artifacts/evidence/risks

---

## 3) How skill constrains tool behavior

Skill should explicitly define:

1. **sequence constraints**
   - e.g. read -> write -> verify

2. **parameter constraints**
   - required fields, naming conventions, path/branch standards

3. **verification constraints**
   - mandatory post-write readback or status checks

4. **fallback constraints**
   - e.g. main-write blocked -> feature branch + PR

5. **error routing constraints**
   - 401/403/404/422 each routes to different remediation

---

## 4) Auth and permission model

- skill stores no secrets
- credentials live in MCP server config/runtime env
- tool availability depends on MCP startup + auth success

Skill may require auth preflight checks, but cannot bypass auth.

---

## 5) Recommended execution stages

A. capability availability
- MCP server up
- key read-only probe tools callable

B. permission/context probe
- read target repo/resource metadata
- confirm path/resource exists

C. change execution
- run write action
- capture operation identifiers (sha/id/url)

D. result verification
- readback check
- verify branch/path/message consistency

E. exception routing
- 401: token/env/config mismatch
- 403: scope/permission insufficient
- 404: target mismatch or hidden permission
- 422: validation/conflict/protection rule

---

## 6) Stability anti-patterns

- assuming skill grants external permissions
- assuming skill trigger means tools must be available
- treating single API success as completion without readback verification
- embedding hardcoded secret values in skill docs/scripts

---

## 7) Mapping to identity protocol

- skill strategy discipline -> identity routing + lifecycle contracts
- mcp capability boundary -> identity dependency and route checks
- tool evidence discipline -> identity multimodal consistency + rulebook linkage

For identity capability upgrades, this reference is part of baseline review.
