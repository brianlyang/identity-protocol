# P0 底层协议治理计划：Compiled Brief Directory Taxonomy（2026-03-18）

## 实施状态

- Status: **Architectural ruling absorbed / taxonomy governance stream pending landing**
- Scope: directory taxonomy governance only
- Current execution rule: **do not create any new canonical directory family before approval**
- Registry status: **not canonical until stream/taxonomy governance is approved**

## 背景

当前 `identity/runtime/IDENTITY_COMPILED.md` 在协议仓内承担的是：

- Codex `model_instructions_file` 默认 runtime brief
- compile/activate 后的受管生成物
- review/checklist/consumer integration 的对齐目标

但它所在的 `identity/runtime/` 目录语义上又容易被误读成：

- 普通 runtime evidence/log artifact
- 应被 release cleanliness 当作污染物看待
- 不应被 tracked 的运行期产物

这两个事实同时存在，说明**文件本身不是错的，目录归类值得重审**。

## 当前已确认事实

1. `identity/runtime/IDENTITY_COMPILED.md` 当前是 tracked file，不是临时未跟踪产物。
2. `scripts/compile_identity_runtime.py` 当前默认写入该路径。
3. `scripts/identity_creator.py activate/compile` 当前也显式指向该路径。
4. consumer/docs/checklist 已把该路径当作 canonical compatibility path 使用。
5. `runtime-artifact-isolation-root-cause-and-remediation-v1.4.12.md` 已明确它是
   “governance artifact, not runtime test artifact, and remains intentionally tracked”。

## 当前冻结口径（在 taxonomy 批准前有效）

在目录 taxonomy 治理完成前，统一按以下口径解释：

1. `identity/runtime/IDENTITY_COMPILED.md` **继续保留现路径**。
2. 它的当前身份定义为：
   - `tracked compiled brief`
   - `legacy canonical compatibility path`
   - `not ordinary runtime evidence/log artifact`
3. 在 taxonomy 批准前，`identity/runtime/IDENTITY_COMPILED.md` 禁止手工语义编辑；只能通过 `docs/template/script -> compile` 的 source-first 路径生成更新。
4. 任何人不得据此直接新建 `identity/compiled/`、`identity/brief/` 等新 canonical family。
5. 任何路径迁移必须在目录治理批准后单独执行，不得夹带在功能修复中顺手完成。

## 核心问题

需要先回答 3 个问题，才能进入迁移：

1. `IDENTITY_COMPILED.md` 的正式 artifact class 是什么？
2. 现有冻结目录家族中，是否已经存在可合法承载 compiled brief 的 family？
3. 当前 `identity/runtime/IDENTITY_COMPILED.md` 是否冻结为 `legacy canonical compatibility path`？

只有在问题 2 的答案为“没有现成 family 可承载”时，才允许进入“新增目录家族”议题。

## 架构师需要拍板的最小决策

### 1) Artifact class 冻结

请在协议层为 `IDENTITY_COMPILED.md` 冻结正式语义分类，至少回答：

- 它是否属于 `runtime artifact`
- 它是否属于 `protocol controlled mirror`
- 它是否应被定义为新的 `compiled brief governed artifact` 类

### 2) 目录 family 判断

请先判断：

- 现有 `identity/runtime/` 是否允许存在“tracked compiled brief”这一特例
- 若不允许，现有顶层 family 中是否已有合法替代位置
- 若都不成立，是否批准新增 directory family

### 3) Canonical vs compatibility 路径冻结

请明确：

- 当前 `identity/runtime/IDENTITY_COMPILED.md` 是否冻结为 `legacy canonical compatibility path`
- 若未来迁移，compatibility mirror 是否为强制阶段

## 我方建议的治理顺序

### Phase 1：语义治理（先做）

目标：

- 不改路径
- 先冻结 artifact class
- 先消除“runtime 污染物”误读

交付：

- governance wording
- semantic registry row or equivalent semantic freeze
- validator wording alignment

### Phase 2：taxonomy 审计（再做）

目标：

- 审计现有 family 是否能承载 compiled brief
- 若不能，给出新增 family 的必要性证明

交付：

- family inventory
- canonical path impact list
- compatibility constraints

### Phase 3：taxonomy 批准（架构师拍板）

目标：

- 决定是否新增目录家族
- 决定新 canonical path 是否成立

交付：

- governance doc
- mapping/registry update
- validator acceptance conditions

### Phase 4：path migration（最后做）

目标：

- 只在 taxonomy 批准后迁移

最小迁移要求：

1. new canonical path
2. old path compatibility mirror
3. compile/creator/docs/consumer/config/validator 全量切换
4. deprecation window 明确
5. mirror retirement gate 明确

## 禁止事项

1. 禁止先建新目录再补文档。
2. 禁止把 taxonomy 批准与 path migration 混成一次普通改动。
3. 禁止把 `IDENTITY_COMPILED.md` 误报为普通 runtime log/report pollution。
4. 禁止在未批准前擅自把 consumer path 改到新 family。
5. 禁止在 taxonomy 批准前手工编辑 `identity/runtime/IDENTITY_COMPILED.md` 的语义内容。

## Definition of Done

本治理议题完成必须同时满足：

1. `IDENTITY_COMPILED.md` artifact class 已冻结。
2. 当前路径的 compatibility 身份已冻结。
3. 若需新增 family，目录 taxonomy 已通过治理批准。
4. path migration plan 已列明：
   - canonical path
   - compatibility mirror
   - validator/CI/doc/config impact
   - rollback and retirement conditions

## 给架构师的协作请求（最小版本）

请只先拍板以下 3 件事：

1. `IDENTITY_COMPILED.md` 的正式 artifact class
2. 当前 `identity/runtime/IDENTITY_COMPILED.md` 是否冻结为 legacy canonical compatibility path
3. 是否需要开启“新增 compiled brief directory family”的 taxonomy governance stream

在这 3 件事未拍板前，本提案不授权任何新目录落地。
