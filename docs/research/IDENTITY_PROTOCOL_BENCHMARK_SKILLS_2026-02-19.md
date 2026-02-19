# Identity Protocol 对标评审（Skills 协议深钻）

- 日期：2026-02-19
- 评审对象：
  - OpenAI Codex Skills 官方文档（含子页面）
  - Agent Skills 标准站点（含子页面）
- 目的：将当前 identity 协议从“可用”升级为“类 skills 协议级别 + 可扩展生态能力”。

## 1. 深钻来源与关键结论

### 1.1 OpenAI Codex Skills（官方）

核心页面：
- https://developers.openai.com/codex/skills/

下钻页面：
- https://developers.openai.com/codex/app/features/#skills-support
- https://developers.openai.com/codex/app-server/#skills
- OpenAPI 端点（Skills）：https://api.openai.com/v1/skills（由 OpenAI OpenAPI 工具核验）

提炼出的关键机制：
1) **Progressive Disclosure**：先加载 metadata，再按需加载完整 SKILL.md。
2) **显式 + 隐式触发并存**：`$skill-name` 和 description 匹配双通道。
3) **多作用域发现机制**：repo / user / admin / system。
4) **可选元数据层**：`agents/openai.yaml` 提供 UI、策略、依赖声明。
5) **技能可管理性**：支持启用/禁用、列表扫描、服务器侧技能注入（app-server）。
6) **API 化趋势**：Skills 资源已有 API（create/list 等）。

### 1.2 Agent Skills（标准站点）

核心页面：
- https://agentskills.io/home

下钻页面：
- https://agentskills.io/specification
- https://agentskills.io/integrate-skills
- https://agentskills.io/what-are-skills

提炼出的关键机制：
1) **技能即“目录协议”**：最小单元是目录 + `SKILL.md`。
2) **协议字段最小化**：`name`、`description` 是触发与发现核心。
3) **轻量可移植**：强调跨系统复用、渐进增强（可加 scripts/references/assets）。
4) **生态兼容导向**：以“可发现、可组合、可执行”为重点，而不是绑定单一产品。

## 2. 当前 identity 协议与 skills 协议对照

| 维度 | Skills 协议实践 | 当前 identity 协议现状 | 结论 |
|---|---|---|---|
| 最小协议单元 | `SKILL.md` + frontmatter | `identities.yaml` + `IDENTITY_PROMPT.md` + `CURRENT_TASK.json` | ✅ 已有更强结构化 |
| 触发机制 | 显式 + 隐式 | 目前以运行时装配为主，缺 identity 触发策略字段 | ⚠️ 需补齐 |
| 发现与作用域 | repo/user/admin/system | 已有 catalog，但缺标准 discover contract | ⚠️ 需补齐 |
| 元数据层 | `agents/openai.yaml` | 有 catalog 元数据，但 UI/依赖声明不统一 | ⚠️ 需补齐 |
| 依赖声明 | tools/env/mcp 可声明 | 部分写在 prompt，缺 schema 级字段 | ⚠️ 需补齐 |
| 生命周期管理 | enable/disable/list + API | 有 pin + validation + compile，但缺 list/config API 约定 | ⚠️ 需补齐 |
| 可测试性 | 官方强调可触发/可验证 | 已有 validate + smoke test | ✅ 良好 |

## 3. 升级到“新高度”的协议增量（建议 v1.1）

### 3.1 新增 Identity Manifest（类 openai.yaml 的 identity 版本）
建议每个 identity 目录支持可选：`agents/identity.yaml`

建议字段：
- `interface`: `display_name`, `short_description`, `default_prompt`
- `policy`: `allow_implicit_activation`, `activation_priority`, `conflict_resolution`
- `dependencies`: `mcp`, `env_var`, `network`, `filesystem_scope`
- `observability`: `event_topics`, `required_artifacts`

### 3.2 新增 Discover Contract（类 skills/list）
定义 `identity/list` 协议（先文档后实现）：
- 输入：`cwd`, `extraRoots`, `forceReload`
- 输出：identity 清单、启用状态、依赖、错误信息

### 3.3 新增 Activation Contract（类 `$skill-name`）
定义 identity 激活优先级：
- `explicit`（显式指定 identity）优先
- `policy match`（任务匹配）次之
- 冲突时按 `activation_priority` + `objective` 决策

### 3.4 新增治理闭环
- 必须产出：`runtime compile artifact` + `validation report` + `change audit`
- 版本治理：继续 pin 到 tag+commit（已落地），并增加 compatibility matrix。

## 4. 对 weixinstore 的直接收益

1) **减少上下文漂移**：identity 的激活和切换可解释。
2) **减少“技能会用但角色失焦”**：role policy 与 skill policy 解耦后可独立治理。
3) **更强协作能力**：后续新增采集/督导/审核等 identity 时可标准化接入。
4) **可运营审计**：每次角色切换和关键动作有据可查。

## 5. 当前是否已“构建类似文档”

已具备：
- `identity/protocol/IDENTITY_PROTOCOL.md`
- `identity/protocol/IDENTITY_RUNTIME.md`
- `identity/catalog/identities.yaml`
- `identity/catalog/schema/identities.schema.json`
- `skills/identity-creator/SKILL.md`

本文件是新增的“**对标评审与升级方案文档**”，用于把协议从 v1.0 的“可用”推进到 v1.1 的“对标 skills 生态化”。

## 6. 下一步落地清单（可直接执行）

1) 在 `identity/catalog/schema/identities.schema.json` 增加 manifest 相关可选字段。
2) 新增 `identity/protocol/IDENTITY_DISCOVERY.md`（定义 identity/list 合同）。
3) 在 `skills/identity-creator` 增加“生成 agents/identity.yaml”的脚手架能力。
4) 新增 `scripts/identity/validate_identity_manifest.py`。
5) 更新 CI：增加 manifest lint + discovery contract test。

