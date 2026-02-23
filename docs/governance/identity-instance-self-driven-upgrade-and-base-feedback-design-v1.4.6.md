# Identity 实例自驱升级与基础仓反馈闭环设计（v1.4.6）

- 文档版本: v1.4.6-draft
- 更新日期: 2026-02-23
- 适用对象: 基础仓架构师、identity 维护者、审计评审人

---

## 1. 本版目标

v1.4.6 的目标不是扩张基础仓实例规模，而是**补齐过程真实性与发布稳定性**：

1. 从“字段存在校验”升级到“执行真实性校验”
2. 从“单报告合法”升级到“完整链路合法”
3. 从“经验口头复盘”升级到“防复发门禁”

---

## 2. 版本边界（必须遵守）

### 2.1 In-scope（允许）

1. 合同增强（CURRENT_TASK 合同字段）
2. validators 强化（真实性、identity-scoped、上下文对齐）
3. required-gates / e2e 稳定性增强
4. 发布收口文档模板与审计口径
5. identity-neutral 启动基线（默认不绑定业务 identity）

### 2.2 Out-of-scope（禁止）

1. 不把本地实例 pack 直接并入基础仓（例如 `identity/packs/*`）
2. 不把实例运行日志/回放临时资产作为基础仓长期资产
3. 不把未冻结的 v1.4.6 草案内容标记为已发布能力

---

## 3. 双闭环设计

### 3.1 实例自驱闭环

Trigger -> Review -> Install/Upgrade -> Validate -> Replay -> Learn

核心要点：
1. install 必须有 `plan/dry-run/install/verify` 链路证据
2. upgrade 必须有 `creator_invocation + check_results(log/hash/exit_code)` 证据
3. replay 必须回到原问题场景验证

### 3.2 基础仓反馈闭环

Real Run Evidence -> Gap Extraction -> Contract/Validator Patch -> Required Gates -> Release Snapshot

核心要点：
1. 每个改进项必须可定位到证据文件
2. 每个修复项必须有 validator 或 workflow 绑定
3. 每次发版必须输出 closure snapshot

---

## 4. v1.4.6 核心增强项

### 4.1 真实性增强（P0）

1. 自驱升级报告必须绑定 CI 运行上下文（run_id/sha）
2. replay 检查必须验证日志文件存在与 sha256 一致
3. 无真实执行证据不得通过 identity-core 变更门禁
4. 新增 role-binding 强校验：identity 创建后必须提供绑定证据，未绑定不得切 active/default

### 4.2 发布稳定性增强（P0/P1）

1. 新增 release freeze boundary gate：
   - 阻止实例 pack 误入基础仓主干
2. 新增 release readiness single entry：
   - 统一运行发布前关键 validators，降低漏跑风险
3. 保持 required check context 与实际 check-runs 一致

### 4.3 证据治理增强（P1）

1. 证据解析 identity-scoped（防串号）
2. 过期证据不作为 release 判定主依据
3. 必须有 release closure 快照记录“问题-修复-证据-残余风险”

### 4.4 identity-neutral baseline（P0）

1. 基础仓默认不应预置业务运行身份（`default_identity` 可空或显式 `none`）。
2. 初始化/CI/e2e/release-readiness 必须支持“无默认 identity”模式。
3. `store-manager` 等业务身份降级为 fixture（示例/回归样本），不作为基础仓默认 active。
4. identity 切换必须显式经过 role-binding（create success != runtime activation）。

---

## 5. 文档分类规范（治理层）

本文件属于 `docs/governance/`，原因：

1. 定义了必须执行的门禁与流程
2. 直接影响 CI、release 判定与审计结论
3. 属于组织治理规范，不是外部资料摘录

`docs/references/` 用于外部资料、行业对照、协议参考；不能替代治理强约束。

---

## 6. 发布判定（Full Go）

仅当以下条件全部满足，v1.4.6 才可 Full Go：

1. required checks 通过（check-runs 可见）
2. 真实性校验通过（self-upgrade + lifecycle + provenance）
3. release freeze boundary 通过（无实例 pack 混入）
4. release closure 快照完成并归档到 governance index

---

## 7. 深度交叉验证执行记录（Git Deep Scan + Official Web + Context7）

> 本节对应 v1.4.4 文档第 17 章的升级继承与落地复核，目标是把“审计结论”与“仓库实现”逐条对齐。

### 7.1 Git 深扫命中点（本仓落地证据）

1. role-binding 合同/门禁落地
   - `identity/store-manager/CURRENT_TASK.json:64`（`gates.role_binding_gate=required`）
   - `identity/store-manager/CURRENT_TASK.json:729`（`identity_role_binding_contract`）
2. role-binding validator 落地
   - `scripts/validate_identity_role_binding.py:83`（gate required 校验）
   - `scripts/validate_identity_role_binding.py:119`（evidence pattern + identity-scoped 取证）
3. runtime/protocol 主校验器联动
   - `scripts/validate_identity_runtime_contract.py:50`
   - `scripts/validate_identity_protocol.py:176`
4. create/activate 切换前置治理
   - `scripts/create_identity_pack.py:411`（`--skip-bootstrap-check`）
   - `scripts/create_identity_pack.py:559`（bootstrap 后调用 role-binding validator）
   - `scripts/identity_creator.py:16`（activate 前强制 role-binding 校验）
5. 发布边界与收口链路
   - `scripts/validate_release_freeze_boundary.py`
   - `scripts/release_readiness_check.py:40`
   - `scripts/e2e_smoke_test.sh:50`（e2e 链路加入 role-binding 校验）

### 7.2 官方网站交叉验证记录（2026-02-23）

1. OpenAI Codex 多代理
   - 来源：`https://developers.openai.com/codex/multi-agent/#approvals-and-sandbox-controls`
   - 关键点：子代理继承 sandbox、non-interactive approvals；需要外层流程处理失败与权限边界。
2. Anthropic MCP connector
   - 来源：`https://docs.anthropic.com/en/docs/agents-and-tools/mcp-connector`
   - 关键点：`mcp_servers` 与 `mcp_toolset` 显式绑定；仅工具调用能力，不自动补齐业务绑定闭环。
3. Gemini Function Calling
   - 来源：`https://ai.google.dev/gemini-api/docs/function-calling`
   - 关键点：模型负责给出函数调用与参数，执行与回传由应用负责。
4. MCP 官方规范
   - 来源：`https://modelcontextprotocol.io/specification/latest`
   - 关键点：host/client/server 分层、capability negotiation、工具安全与用户确认、审计日志建议。

交叉结论（推断）：
1. 主流平台都提供“工具/角色能力”，但不替代“业务侧 role-binding 治理”。
2. “创建成功 ≠ 绑定成功”必须由基础仓合同与 validator 显式表达并阻断。

### 7.3 Context7 复核记录

1. resolve-library-id
   - query: `model context protocol specification`
   - selected id: `/websites/modelcontextprotocol_io_specification_2025-11-25`
2. get-library-docs 主题
   - `overview, hosts/clients/servers, capability negotiation, tools/resources/prompts, security`
3. 命中要点
   - server capabilities 声明（tools/resources/prompts/tasks）是显式协商。
   - 安全侧强调：敏感操作用户确认、工具调用审计日志、输入输出校验。

映射到本仓：
1. `identity_role_binding_contract` 是“能力显式声明 + 可验证证据”的仓内实现。
2. `validate_identity_role_binding.py` + activate 前置校验，形成“未绑定不可切换”阻断语义。

### 7.4 从 v1.4.4 第 17.4 到 v1.4.6 的三条落实（最终）

1. 结论A（v1.4.5 有创建能力，但缺绑定能力合同化）  
   -> 已落实：新增 `identity_role_binding_contract` + `role_binding_gate` + 规范文档 `docs/specs/identity-role-binding-contract-v1.4.6.md`。

2. 结论B（create 与 run 之间缺治理门禁）  
   -> 已落实：新增 `scripts/validate_identity_role_binding.py`，并在 `identity_creator.py activate` 与 e2e/release-readiness 链路中执行。

3. 结论C（v1.4.6 应优先 role-binding law，不应继续堆概念）  
   -> 已落实：本版强化集中在合同、validator、切换守卫、收口快照，不引入新的并行协议层。

### 7.5 当前残余风险（实事求是）

1. workflow 文件显式加 role-binding step 的云端接线，受当前 token `workflow` scope 限制，仍需一次权限化提交收口。
2. required-gates 默认 active-only；对 inactive 但本次改动 identity 的“按 diff 精准校验”仍建议在 v1.4.6 后续小版本补齐。
3. 当前 catalog 仍使用 `default_identity=store-manager` 语义；需在 v1.4.6 PR 中完成 identity-neutral 迁移。

### 7.6 PR 准备必带关键点（新增）

1. PR 描述必须包含“identity-neutral baseline migration”专项条目。
2. Reviewer checklist 必须新增：
   - `default_identity` 是否去业务默认依赖；
   - CI/e2e/readiness 是否在无默认 identity 下可运行；
   - fixture identity 是否仍保持 inactive-by-default；
   - role-binding 是否成为 activation/default switch 前置条件。
3. Release closure 必须单列“默认身份去业务化”证据与回滚策略。
