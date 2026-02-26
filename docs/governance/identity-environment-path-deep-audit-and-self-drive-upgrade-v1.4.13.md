# identity 环境与路径治理深度审计报告（含自驱升级协同要求）v1.4.13

- 审计日期: 2026-02-25
- 审计仓库: `/Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local`
- 审计分支: `docs/readme-core-goal-snapshot-v1.4.13`
- 审计基线提交: `f5f58da`（包含 `94bf09d` 的 P0 修复并继续补边界收口）
- 审计定位: 代码层 + git 层 + 工具链交叉验证（actionlint/gitleaks/ast-grep）

## 1. 审计目标与方法

本轮目标是确认 identity 在环境与路径治理上是否达到以下能力：

1. 路径边界可硬阻断（避免 repo/runtime 混写污染）。
2. 运行态可恢复失败（fail-operational）不被错误判死。
3. 工具/技能/MCP 挂接有真实证据，不是假绿。
4. 与 skill 协议治理思想保持一致：默认项目可写域、显式例外、可审计回放。

交叉验证维度（圆桌式）:

1. Instance-plane: `identity_creator/update/e2e` 实跑语义是否闭环。
2. Repo-plane: 代码契约与文档契约是否一致。
3. Release-plane: required-gates 工具链是否真实可执行。
4. Skill parity: 是否遵循“默认安全路径 + 显式例外双确认 + 证据可追踪”。

## 2. 已验证通过项（代码声明与运行行为一致）

### 2.1 capability 认证硬化生效（非假绿）

- 代码位点:
  - `scripts/validate_identity_capability_activation.py:250`
- 实测:
  - 使用无效 `GH_TOKEN/GITHUB_TOKEN` 运行 capability 校验，返回 `BLOCKED` + `IP-CAP-003` + `RC=1`。
- 审计结论:
  - GitHub 认证未就绪时可被机器阻断，符合预期。

### 2.2 扫描模式支持目标实例收敛

- 代码位点:
  - `scripts/full_identity_protocol_scan.py:108`
  - `scripts/full_identity_protocol_scan.py:114`
- 实测:
  - `--scan-mode target --identity-ids base-repo-architect` 输出 `summary.total_identities=1`。
- 审计结论:
  - 已具备“目标实例模式”，可避免全仓噪音干扰审计口径。

### 2.3 route metrics 默认禁止 repo fallback

- 代码位点:
  - `scripts/export_route_quality_metrics.py:68`
  - `scripts/export_route_quality_metrics.py:153`
- 实测:
  1. 默认执行 -> `IP-PATH-001`（阻断）。
  2. `IDENTITY_RUNTIME_OUTPUT_ROOT=/tmp/identity-runtime` -> PASS。
  3. `--allow-repo-runtime-fallback` -> PASS（显式例外）。
- 审计结论:
  - 路径硬隔离策略已落地，默认不再隐式回流到 repo runtime。

### 2.4 入口边界双确认机制落地

- 代码位点:
  - `scripts/create_identity_pack.py:637`
  - `scripts/create_identity_pack.py:672`
  - `scripts/identity_installer.py:162`
  - `scripts/identity_installer.py:170`
  - `scripts/identity_creator.py:735`
  - `scripts/identity_creator.py:807`
- 实测:
  - `scripts/validate_identity_creation_boundary.py` 四用例通过（4/4）。
- 审计结论:
  - repo 例外写入已从“单开关”升级为“显式确认 + 用途说明 + 路径语义校验”。

### 2.5 CI 工具链门禁可执行

- 代码位点:
  - `.github/workflows/_identity-required-gates.yml:25`
  - `.github/workflows/_identity-required-gates.yml:28`
  - `.github/workflows/_identity-required-gates.yml:36`
- 实测:
  - `actionlint` 通过。
  - `gitleaks` 扫描无泄漏（`[]`）。
  - `ast-grep` 规则运行通过。
- 审计结论:
  - CI 已纳入 workflow lint / secrets / path-rule 三类基础防线。

## 3. 新发现问题（需架构师继续收口）

### P0-1: recoverable 阻断报告与 self-upgrade 证据契约冲突（在 `f5f58da` 仍可复现）

- 复现命令:
  - `source ./scripts/use_project_identity_runtime.sh`
  - `IDENTITY_IDS=base-repo-audit-expert-v3 bash scripts/e2e_smoke_test.sh`
- 复现现象:
  - 在 `IP-CAP-003`（capability preflight blocked）分支，e2e 于 step 26 后失败。
  - 报错: `report.checks must be non-empty list`。
- 代码根因:
  1. `scripts/execute_identity_upgrade.py:342` 基础报告骨架 `checks=[]`。
  2. `scripts/execute_identity_upgrade.py:577` capability 阻断分支直接返回，未填充 `checks/check_results`。
  3. `scripts/validate_identity_self_upgrade_enforcement.py:216` 强制要求 `checks` 非空。
  4. `scripts/e2e_smoke_test.sh:255` 在 recoverable 判定前先执行上述强校验。
- 影响:
  - fail-operational 语义被“报告结构契约”提前打断，导致“可恢复阻断态”无法继续闭环。
- 修复要求:
  1. 二选一（推荐 A）:
     - A: capability blocked 分支写入最小 `checks/check_results`（至少含 capability gate 执行记录），保持与 validator 契约一致。
     - B: 放宽 `validate_identity_self_upgrade_enforcement.py`，允许 `capability_blocked` 的受控空检查态（需配套 `next_action`、`error_code`、`creator_invocation` 完整）。
  2. 同步调整 e2e 顺序，避免在 recoverable 判定前硬失败。
- 验收标准:
  - `IP-CAP-003` 场景下，e2e 不因 `checks` 结构报错而提前失败；流程进入 recoverable 分支并输出可执行 `next_action`。

### P1-1: capability preflight 过于“全路由并集”，导致与 skill 按需激活语义不完全一致

- 代码位点:
  - `scripts/validate_identity_capability_activation.py:111`
  - `scripts/validate_identity_capability_activation.py:125`
- 现象:
  - 当前逻辑把所有 route 的 `required_mcp` 做并集；只要其中一条 route 要 `github`，全局 preflight 就可能被 `gh auth` 阻断。
- 风险:
  - 会放大阻断面，不利于“按任务路由激活能力”的 skill 对齐治理。
- 修复要求:
  - capability 校验引入 route/task context（或 execution intent），优先按“本次任务目标路由”判定 required_mcp。

### P1-2: three-plane repo 判定未纳入 git 工作区脏态，存在“CLOSED 误感知”

- 代码位点:
  - `scripts/report_three_plane_status.py:94`
  - `scripts/report_three_plane_status.py:108`
- 现象:
  - repo-plane 当前仅看 catalog/scope/conflict/docs，不看 `git status`。
- 风险:
  - 在存在未提交关键改动时，仍可能输出 `repo_plane_status=CLOSED`。
- 修复要求:
  - 新增 `workspace_clean` 子条件（可区分 strict/non-strict），并在报告中显式输出。

### P1-3: ast-grep 路径规则覆盖面偏窄（可被模式变体绕过）

- 代码位点:
  - `.github/ast-grep/no-default-repo-runtime-fallback.yml:9`
  - `.github/ast-grep/no-default-repo-runtime-fallback.yml:15`
- 现象:
  - 规则绑定单文件且匹配单一 `if/else` 结构。
- 风险:
  - 其他文件或结构变体中的 repo fallback 可能漏检。
- 修复要求:
  - 扩展为多模式规则集（语法等价模式 + 多文件范围），并保留现有精准规则作为子规则。

## 4. 对“是否可自主升级协同”的审计结论

结论: **可以，但当前是“可运行协同”，不是“无争议闭环协同”**。

已达到:

1. 可以基于实例上下文自动发现并调用 skill/MCP/tool。
2. 可以对环境/路径问题做代码级复核并输出机器证据。
3. 可以将审计要求转成可执行门禁命令，便于架构师直接落地。

未完全达到:

1. recoverable blocked 报告在 self-upgrade 契约下仍会被误判失败（P0-1）。
2. capability 判定尚未完全按任务路由最小化阻断（P1-1）。

## 5. 给基础仓架构师的一次性执行清单

1. 先修 P0-1（报告结构契约冲突），再重跑 e2e。
2. 修 P1-1（route-aware capability 判定）以贴合 skill 按需激活治理。
3. 修 P1-2（three-plane 增加 git workspace clean 条件）提升判定可信度。
4. 修 P1-3（ast-grep 规则扩展）降低路径治理漏检风险。

建议验收命令:

```bash
cd /Users/yangxi/claude/codex_project/weixinstore/identity-protocol-local
source ./scripts/use_project_identity_runtime.sh

# 1) capability 阻断场景
GH_TOKEN=invalid_token GITHUB_TOKEN=invalid_token \
python3 scripts/validate_identity_capability_activation.py \
  --catalog "$IDENTITY_CATALOG" \
  --repo-catalog identity/catalog/identities.yaml \
  --identity-id base-repo-audit-expert-v3 \
  --require-activated || true

# 2) recoverable 流程不应因 checks 空列表误判失败
IDENTITY_IDS=base-repo-audit-expert-v3 bash scripts/e2e_smoke_test.sh

# 3) 三平面汇总
python3 scripts/report_three_plane_status.py \
  --identity-id base-repo-audit-expert-v3 \
  --catalog "$IDENTITY_CATALOG" \
  --with-docs-contract

# 4) 工具链门禁
/tmp/identity-tools/bin/actionlint .github/workflows/*.yml
gitleaks dir . -f json -r /tmp/identity-tools/reports/gitleaks-identity-protocol-local.json --redact --no-banner
/tmp/identity-tools/node_modules/.bin/ast-grep scan -r .github/ast-grep/no-default-repo-runtime-fallback.yml .
```

## 6. 当前判定口径（2026-02-25 基线）

- Instance-plane: **IN_PROGRESS**（P0-1 未收口，recoverable 场景仍误判失败）
- Repo-plane: **IN_PROGRESS**（路径治理主线已强化，但仍有 P1 收口项）
- Release-plane: **NOT_STARTED**（无 required-gates 云端 run-id 证据输入）
- Overall: **Conditional Go**

---

## 7. 2026-02-26 收口更新（基础仓架构师复验）

> 这部分是对本报告第 3 节问题单的“代码已修复 + 实跑交叉验证”补充，避免后续新 Bug 迭代时丢失历史上下文。

### 7.1 已完成修复（对应第 3 节问题）

1. **P0-1 已修复：recoverable blocked 报告契约冲突**
   - 修复提交：`5d7ae42`
   - 关键改动：
     - `scripts/execute_identity_upgrade.py` 在 capability/metrics/path-policy blocked 分支补齐
       `checks/check_results/required_checks`、patch-plan、creator/execution context。
   - 实测结果：
     - `IP-CAP-003` 场景下报告 `checks_len > 0`；
     - `validate_identity_self_upgrade_enforcement.py --execution-report ...` 通过。

2. **P1-1 部分收口：capability route 维度可观测**
   - 修复提交：`5d7ae42`
   - 关键改动：
     - `scripts/validate_identity_capability_activation.py` 新增
       `route_activation_matrix/route_ready_count/route_total_count`；
     - 新增 `--activation-policy`（`strict-union` / `route-any-ready`）。
   - 说明：
     - 默认语义保持 `strict-union`（保证认证边界不回退）；
     - `route-any-ready` 为按任务降阻断的可选策略（供后续协议层固化）。

3. **P1-2 已修复：three-plane repo 状态纳入工作区洁净性**
   - 修复提交：`5d7ae42`
   - 关键改动：
     - `scripts/report_three_plane_status.py` 新增
       `workspace_clean/workspace_dirty_entries/workspace_status_error`；
     - tracked dirty 时 `repo_plane_status` 直接 `BLOCKED`。

4. **P1-3 已修复：路径规则扩展并可执行**
   - 修复提交：`5d7ae42`
   - 后续补强：`scripts/export_route_quality_metrics.py` 统一 repo fallback 构造 helper，
     消除 guarded 分支误报。
   - 实测：
     - `ast-grep` 规则对仓内脚本扫描通过（无 error 级诊断）。

5. **新增 P0 治理项并完成：runtime mode 漂移 fail-fast**
   - 修复提交：`728a584`
   - 新增脚本：
     - `scripts/validate_identity_runtime_mode_guard.py`
   - 接线位置：
     - `scripts/identity_creator.py`（validate/activate/update）
     - `scripts/release_readiness_check.py`
     - `scripts/e2e_smoke_test.sh`
   - 目标：
     - 在主链开始前强制校验 resolver tuple
       （`source_layer/catalog_path/pack_path/resolved_scope`），
       避免 project/global 模式漂移导致“先跑后炸”。

### 7.2 本轮交叉验证证据（2026-02-26）

1. `IDENTITY_IDS=base-repo-audit-expert-v3 bash scripts/e2e_smoke_test.sh`：**PASSED**  
   - 输出：`instance_plane_status=CLOSED`，`release_plane_status=NOT_STARTED`
2. `python3 scripts/release_readiness_check.py --identity-id base-repo-audit-expert-v3 --catalog .../.agents/identity/catalog.local.yaml`：**PASSED**
3. `python3 scripts/report_three_plane_status.py --with-docs-contract`：  
   - `instance_plane_status=CLOSED`
   - `repo_plane_status=CLOSED`
   - `release_plane_status=NOT_STARTED`
4. 强制阻断场景（invalid GH token）：
   - capability 返回 `BLOCKED/IP-CAP-003`；
   - self-upgrade enforcement 不再因空 checks 误判失败。

### 7.3 当前仍保留的发布口径

- **Release-plane 仍为 NOT_STARTED**（未填 required-gates 云端 run-id 证据）
- 因此总体口径继续保持：**Conditional Go**

---

## 8. 持续记录要求（防回归）

为避免“修完即遗忘”导致新 Bug 迭代时重复踩坑，后续每轮需至少记录：

1. 修复提交 SHA（例如 `5d7ae42` / `728a584`）  
2. 受影响脚本清单（入口脚本 + validator +报告脚本）  
3. 三平面状态输出（instance/repo/release）  
4. 一条强制异常场景回归（例如 invalid auth / path guard fail）  
5. 下一轮未收口项（只列 P0/P1）

建议将上述 5 项作为每次“bug 修复收口”的固定模板，写入治理快照或 PR 描述。
