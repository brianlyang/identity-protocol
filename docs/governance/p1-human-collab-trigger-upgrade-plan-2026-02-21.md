# P1 底层协议升级计划：Human-Collab Trigger（2026-02-21）

## 实施状态

- Status: **Implemented (2026-02-21)**
- Protocol revision: `v1.3.0`
- Merge evidence: pending current PR merge

### 已落地项

1. blocker taxonomy 已写入 runtime contract（`blocker_taxonomy_contract`）。
2. Human-Collab Auto-Notify contract 已写入 runtime contract（`collaboration_trigger_contract`）。
3. 新增 validator：`scripts/validate_identity_collab_trigger.py`（含正/负样例自测）。
4. CI required-gates 已纳入该校验（3 条 workflow 链路同步）。

## 背景

在实际运行中已确认：当流程命中 `login_required / CAPTCHA / session_expired` 等“必须人工配合”阻断时，实例层可通过 `ops-notification-router` 发协作邮件，但**底层协议尚未将该能力标准化为 required contract + CI gate**，存在复发风险。

## 决策

采用“两层并行”策略：

1. **实例层（P0）先落地**：已在 `identity/store-manager` 完成 hard rule，确保当前任务不中断。
2. **底层协议层（P1）同轮补齐**：将能力上升为 protocol 规范、validator 与 CI required gate。

> 结论：不是“后续再看”，而是纳入本轮升级闭环；若当日未完成，必须保留可审计待办与验收条件。

## P1 升级范围（本轮冻结）

### 1) 统一 blocker taxonomy（协议层）

新增标准阻断类型（至少）：

- `login_required`
- `captcha_required`
- `session_expired`
- `manual_verification_required`

落点建议：

- `docs/specs/identity-protocol-contract-*.md`
- `identity/protocol/IDENTITY_RUNTIME.md`

### 2) Human-Collab Auto-Notify Contract

新增协议字段（建议）：

- `collaboration_trigger_contract.hard_rule`
- `collaboration_trigger_contract.trigger_conditions[]`
- `collaboration_trigger_contract.notify_policy`
- `collaboration_trigger_contract.notify_timing`（`immediate`）
- `collaboration_trigger_contract.notify_channel`（`ops-notification-router`）
- `collaboration_trigger_contract.dedupe_window_hours`
- `collaboration_trigger_contract.state_change_bypass_dedupe`
- `collaboration_trigger_contract.must_emit_receipt_in_chat`

### 3) validator 强校验

新增脚本（命名建议）：

- `scripts/validate_identity_collab_trigger.py`

最小校验项：

1. blocker taxonomy 存在且覆盖上述四类
2. auto-notify 策略存在且为 `immediate`
3. dedupe + state-change bypass 配置存在
4. notification receipt 约束存在（chat/ledger evidence）

### 4) CI required gate

workflow required-gates 增加：

- `python3 scripts/validate_identity_collab_trigger.py`

并在 GitHub branch protection 里设为 required check。

## 验收标准（Definition of Done）

1. 协议文档可读到 Human-Collab 标准条款（taxonomy + contract + immediate notify policy）。
2. `validate_identity_collab_trigger.py` 在正样例通过、反样例失败。
3. CI required-gates 已纳入该校验并可在 PR 触发。
4. 触发 `login_required` 场景时，立即发出通知并输出 receipt（可审计）。

## 交付物清单

- 协议文档更新（spec/runtime）
- 新 validator 脚本
- CI workflow 调整
- 一份审计快照补录（记录本次 P1 落地）

## 风险与备注

- 风险：若仅实例层落地，未来新增 identity 会再次遗漏通知触发。
- 处理：P1 未完成前，禁止将“人协作触发”判定为 fully-closed。
- 本文件作为“待办+验收合同”，用于后续统一复盘与审计。
