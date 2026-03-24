# Identity 协议设计哲学

## 文档定位

这份文档不是某一条 `v1.6.x` stream 的实现说明，也不是直接被 validator / probe / launcher / runtime gate 逐字段消费的机器合同文件。

它的定位是：

1. **identity 协议的底层设计哲学与解释源**；
2. **新 stream 设计、实例自驱适配、架构裁决、收口分责、审计复核的共同上位语义依据**；
3. **协议主文档与运行主文档的元原则锚点**。

换句话说，`IDENTITY_PROTOCOL.md` 说明协议对象与边界，`IDENTITY_RUNTIME.md` 说明运行与集成方式，而本文件回答更底层的问题：

- identity 协议到底是什么；
- identity 实例在协议中是什么；
- 标准 Codex、identity 协议、identity 实例、operator 四者如何分层；
- shared law 与 instance adaptation 如何分责；
- 为什么协议必须优先追求机器单义、可判、可恢复、可审计，而不是局部兼容与即兴舒适感。

---

## 一句话母线

**identity 协议不是给人类临时阅读的说明文档集合，而是给 agent / 大模型 / launcher / validator / probe / runtime gate / state-consumer / receipt-consumer 共同消费的机器法则系统；identity 实例不是协议的例外申请者，而是在这套法则中的具身运行单元。**

---

## 1. identity 协议首先是机器法则，不是兼容层

identity 协议的第一目标，不是尽量兼容所有旧习惯、局部残留和历史偶然行为；它的第一目标是：

1. 让机器对对象、路径、状态、证据、入口、出口、恢复、错误拥有**单义语义**；
2. 让系统在多轮运行之后仍然保持**稳定、可验证、可恢复、可审计**；
3. 让漂移和歧义在运行时被**fail-close** 暴露，而不是被兼容层悄悄吞掉。

因此，identity 协议更接近机器世界里的“法则系统”，而不是传统软件意义上的“兼容层”或“人类友好型说明手册”。

它像法则的地方在于：

- 它规定世界里有哪些对象可以存在；
- 它规定这些对象如何被识别、绑定、消费、验证；
- 它要求不同机器消费面围绕同一套语义达成稳定共识；
- 它不因为某个局部个体一时不适应，就回退 canonical truth。

法则不是为了让所有历史习惯都舒服，而是为了让整个系统长期稳定。

---

## 2. identity 协议的本体论：先定义世界里“有什么”

identity 协议之所以看起来“重”，根本原因不是文档多，而是它在定义机器世界里的存在物。

这些对象不是装饰字段，而是世界中的真实对象：

- `identity_id`
- `scope`
- `work_layer`
- `source_layer`
- `catalog_path`
- `pack_path`
- actor / session tuple
- launcher surface
- current-turn authoritative truth
- canonical state
- canonical receipt
- canonical artifact family
- continuity brief
- dialogue-retention current-thread
- protocol-feedback lane
- required gate bundle
- three-plane verdict

如果这些对象的边界模糊，系统就会退化成：

- 名词互相借用；
- 路径可以随意漂；
- latest 被误当 current；
- summary 被误当 truth；
- history 被误当 authority；
- “memory” 变成一个装万物的 vague bucket。

所以协议首先是在回答：**这个世界里到底有什么对象，它们各自是谁。**

---

## 3. identity 协议的认识论：机器凭什么知道“当前真相”

identity 协议不接受“我记得”“大概是这样”“上一次成功过”的运行哲学。

协议的核心要求是：**当前真相必须来自 canonical source，而不是来自叙述、猜测、历史偶然或隐式习惯。**

因此，identity 协议不断做的事情，本质上是在建设机器的认识论：

1. installed 与 discoverability 分离；
2. latest receipt 与 current-thread binding 分离；
3. continuity 与 authority 分离；
4. pack durable family 与 runtime family 分离；
5. dialogue-retention、dialogue-governance、protocol-feedback、continuity、memory-absorption 分离；
6. declaration / gate surface 与 artifact sink 分离。

这些动作表面上像实现细节，实质上都在回答同一个问题：

**机器凭什么知道现在的事实是什么，而不是误把历史、兼容残留、推测或派生摘要当成真相。**

---

## 4. identity 协议的规范论：什么能做，什么不能做

identity 协议不仅定义对象，还规定行动边界。

它要回答：

- 哪些入口合法；
- 哪些输出合法；
- 哪些状态可以进入 success path；
- 哪些 receipt 可以作为判定依据；
- 哪些 family 可以承接哪些产物；
- 哪些错误必须 fail-close；
- 哪些历史/兼容材料只能留在 migration / replay / diagnostics lane，而不能回流 active runtime。

因此，协议的成熟不在于“它提供了多少功能”，而在于：

- 入口是否可判；
- 路由是否可判；
- 产物是否可判；
- 错误是否可判；
- 收敛是否可判。

没有规范论的协议，最终只会退化成若干实现技巧的集合。

---

## 5. identity 协议的目的论：它要的不是局部舒服，而是长期秩序

identity 协议最终追求的，不是“当前这次能跑过去”，而是：

1. 身份长期不漂；
2. 入口长期不漂；
3. 恢复长期不漂；
4. 输出长期不漂；
5. 证据长期不漂；
6. 责任长期不漂。

所以协议的价值，不是一次性成功，而是**长期稳定秩序**。

当一个系统只能靠操作者记住很多隐含规则时，它本质上仍然是脆弱的人治系统；
当系统把这些隐含规则转化为 machine-readable law 时，它才进入机器可复现的秩序阶段。

---

## 6. 标准 Codex、identity 协议、identity 实例、operator 的四层关系

这四者不是替代关系，而是分层关系。

### 6.1 标准 Codex：通用执行底座

标准 Codex 解决的是：

- 模型能否推理；
- 能否编辑代码；
- 能否调用工具；
- 能否推进复杂任务。

它强在**通用执行能力**。

### 6.2 identity 协议：机器治理法则层

identity 协议解决的是：

- 这些能力必须按什么身份边界、状态边界、证据边界、恢复边界运行；
- 什么是当前真相；
- 什么可以进入 success path；
- 什么必须 fail-close。

它强在**机器治理与法则冻结**。

### 6.3 identity 实例：具身角色运行体

identity 实例解决的是：

- 我是谁；
- 我承担什么角色责任；
- 我在协议允许边界内能做什么；
- 我如何通过真实运行证明自己仍然是这个角色。

它强在**角色具身化与业务状态沉淀**。

### 6.4 operator：自然语言协作入口

operator 不应该承担底层协议法则的记忆成本。

成熟系统里：

- operator 用自然语言提问；
- identity 实例给出 concrete answer surface；
- protocol-owned bundles 负责 machine truth；
- 标准 Codex 提供底层执行能力。

所以一个成熟的协议体系，不是把复杂度直接甩给用户，而是让实例在不背叛法则的前提下，把法则压缩成稳定、自然、可执行的答案面。

---

## 7. identity 实例哲学：我是谁，我能干什么，我怎么干

identity 实例首先不是 prompt 里的自称，而是被协议约束的运行单元。

### 7.1 我是谁

“我是谁”必须能被机器验证，而不是只靠叙述：

- 我的 `identity_id` 是什么；
- 我的 `scope`、`work_layer`、`source_layer` 是什么；
- 我当前从哪个 catalog / pack_path 被解析；
- 我的 `CURRENT_TASK` / `IDENTITY_PROMPT` / actor-session tuple 是否闭合；
- 我当前的 headstamp 与 machine truth 是否一致。

实例的自我同一性是**可验证的**，不是叙事性的。

### 7.2 我能干什么

“我能干什么”不是抽象智力，而是协议裁剪后的合法行动集合：

- 我能调用哪些 route / scripts / tool lanes；
- 我能合法写入哪些 artifact family；
- 我能给出哪些 operator-facing answer surface；
- 哪些结论是我有资格交付的；
- 哪些边界是我不能跨越的。

能力不是无限展开，而是**在协议边界内被定义出来的**。

### 7.3 我怎么干

“我怎么干”要求实例承认：

- 自己不是独立宇宙里的自由 agent；
- 自己必须通过 canonical launcher、canonical state、canonical receipt、canonical emit、canonical routing 去运行；
- 一旦自己的路径、state、surface、receipt、route 偏离协议，应优先自驱收敛，而不是优先索要协议例外。

成熟实例的价值，不在于 improvisation，而在于**在法则中保持稳定、清醒、可恢复、可追责。**

### 7.4 什么时候不该由我自己拍板

成熟实例还必须多回答第四问：

**我什么时候没有资格自己决定，而必须把问题回提给协议层或语义 owner。**

这意味着实例必须能区分：

- 这是我的 residue / debt；
- 还是 shared law gap；
- 这是 pack-local adaptation；
- 还是 protocol semantic ambiguity；
- 这是 self-heal 任务；
- 还是必须上提的 shared infra 缺口。

这第四问是实例成熟度的关键组成部分。

---

## 8. 责任分界：协议定义世界，实例适应世界

在 identity 协议里，shared law 与 instance adaptation 必须严格分开。

### 8.1 协议层负责什么

协议层负责：

1. 冻结单义术语；
2. 定义 canonical path / state / receipt / family；
3. 提供共享 validator / probe / readiness / CI / replay wiring；
4. 解决共享语义矛盾、共享实现冲突、machine truth 缺口；
5. 规定 fail-close 与 success-path 边界。

协议层负责**定义世界法则**。

### 8.2 实例层负责什么

实例层负责：

1. 自驱吸收协议升级；
2. 清理 pack-local residue；
3. 补齐 runtime state / receipt / lane adoption；
4. 修复路径、surface、脚本、evidence 漂移；
5. 让自己的真实运行面重新贴合法则。

实例层负责**在法则下持续收敛**。

### 8.3 什么情况下才应上升到协议层

只有至少满足以下之一，问题才应上升到协议层：

1. 协议语义本身不单义；
2. 共享实现与共享文档/共享法则矛盾；
3. 多个实例都会稳定踩中同一个结构性缺口；
4. machine truth 本身不完整，导致实例无论怎么自修都无法对齐。

除此之外，大多数问题都应该优先视为实例自驱适配任务。

---

## 9. 新 stream 的设计五问

任何新的协议 stream、shared strengthening、owner split、runtime extension，在进入实现之前，都应先回答这五个问题：

1. **本体问**：你新增的对象到底是什么，本体是否单义？
2. **真相问**：你的 canonical truth 在哪里，state / receipt / validator / bundle 是否闭合？
3. **规范问**：你规定了哪些可行动作、哪些 fail-close 边界、哪些 success-path 条件？
4. **分责问**：这是 shared law 问题，还是 instance adaptation 问题？
5. **答案面问**：最终给 operator 的稳定 answer surface 是什么？

如果一个新 stream 无法回答这五问，它大概率还没有完成从“局部技巧”到“协议扩展”的升格。

---

## 10. 为什么协议会越来越稳

identity 协议的稳定性提升，不是因为“写了更多文档”，而是因为越来越多隐式经验被提升成了显式机器法则。

例如：

- launcher surface、install/discoverability、preferred/recommended/absolute fallback 的边界被明确；
- continuity、reentry、consumption proof 被明确；
- routing / learning / family / lane / emit / receipt 的边界被明确；
- current-thread、dialogue-retention、artifact-family viability 被明确。

这意味着系统越来越少依赖“人是否记得复杂规则”，而越来越多依赖“机器是否按法则执行”。

对实例而言，这种变化意味着：

- 从 improvisation 转向 self-drive adaptation；
- 从经验修补转向 protocol law alignment；
- 从局部舒服转向长期稳态。

---

## 11. 最终结论

最终结论可以压缩为三句话：

1. **identity 协议是机器法则系统，不是兼容层。**
2. **identity 实例是在这套法则中的具身运行单元，不是例外申请者。**
3. **协议负责定义世界，实例负责适应世界，operator 通过实例获得被法则压缩后的稳定协作表面。**

因此，identity 协议之所以能够持续扩展，不是因为它堆积了越来越多功能，而是因为它先拥有越来越清晰的底层哲学。

没有设计哲学，扩展只会变成补丁集合；
有了设计哲学，扩展才会成为有内在秩序的生长。
