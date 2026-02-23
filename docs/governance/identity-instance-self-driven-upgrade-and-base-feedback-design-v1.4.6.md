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

