# 独立审计模块

`io.clayz.presentation.independent-audit/1.0` 是 Output 之后的共享审计合同。
它是 Supervisor 发布单元使用的内部模块，不是第六个制作阶段、第二个
Public Core 或第二套检索引擎。

## 目的与权限

Output 将完成的 PPTX、对象证据和实际可用的渲染证据同时送给 Supervisor 与本模块。
Auditor 直接读取不可变的用户原始要求，以及 Supervisor 当前的承诺和变更，
检查实际写盘文件及可用渲染，并向 Supervisor 返回不可变审计产物。Auditor 只报告
事实、发现和不确定性，不改写成品，不授予放行权，也不改变阶段结论。

Supervisor 仍负责协调和最终放行。用户交付政策允许时，Supervisor 可以把发现
退回责任阶段，或带着已披露的质量问题交付可用成品；必须原样保留 Auditor 的
发现和状态。实物质量缺陷不等于产物绑定、身份、格式或证据完整性失败。

## 必需证据与接口

审计产物使用上述合同名，并通过实际路径、字节数和必要时的 SHA-256 绑定：

- `task_request`：不可变的用户原始请求；
- `acceptance_rules`：规范化任务验收合同，含用户明确的硬/软要求及优先级；
- `supervisor_rules`：Supervisor 的启动承诺、校准发现，以及记录过的任务范围或
  要求变更；
- 最终 PPTX、对象清单以及完成检查时实际可用的最终渲染证据；
- `run_id`、任务请求哈希、配置/验收绑定和 `audited_at`。

当前校准 report3.6 交付中的 Auditor 产物与五份真实阶段记录、可选且已绑定的
`work-notes`、三个 `calibration_artifacts` 和 `supervisor_release` 一起装配，
派生的 `core_sequence` 承载核心生命周期。正式监督 JSON 从这些记录和实际主要
产物汇总完整工作报告，再从 JSON 确定性派生可读 Markdown。v3.5 和旧生命周期、
Index、检索及性能字段仍可作为 legacy 或可选补充证据，只有实际提供时才校验。

Auditor 为实际写盘 PPTX、对象、渲染以及可用时的页面文字／备注提供独立观察，
并披露覆盖局限。它不补写缺失的阶段 notes，也不凭记忆还原工作历史；报告应将
这类证据标为 `not-recorded`、`deferred` 或 `uncertain`。它也不替代阶段负责的
专业判断；Supervisor 保留产物并决定放行。

产物记录 `findings`、`audit_status` 和 `coverage`。每条发现说明观察证据、预期
状态、实际状态、影响、严重度、置信度，以及已知的要求或页面 ID。未检查项目记为
`deferred` 并写明覆盖限制，不得虚构为 `pass`。没有渲染路线时，Auditor 可以检查写盘
PPTX 和对象证据，把渲染覆盖记为 deferred/not-run，并返回绑定完整的产物；不能仅因没有
像素而阻断写盘 PPTX 交付。

`independent_context` 是必需的上下文披露，记录 `execution_mode`、`context_id`、
`model_identity_disclosure` 和 `limitations`。宿主有独立模型或进程时可以使用；
若宿主无法提供隔离的执行器或上下文，就在可用审计上下文中完成并明确说明隔离不可用，
不能冒充独立模型、进程或人员，也不能声称证据不支持的独立性。这个限制本身不阻断制作
或交付。

汇总监督报告通过 `auditor_artifact` 绑定该产物的路径、SHA-256 与 `audited_at`。
新任务只有在绑定有效且放行时间不早于审计时间时才可发布。report3.6 或 v3.5 报告保留兼容字段
`supervisor_roles.final_auditor` 时只能为 `not-needed` 或 `incomplete`；第五份阶段记录
使用 `auditor` 角色。包含 Supervisor 完整 `final_auditor` 角色的历史报告仍可作为
legacy 证据读取。

## 规则优先级与交付政策

Auditor 遵循既有优先级：用户原始要求、已保存的个人层、默认值。Supervisor 负责解析并
记录目标、承诺和用户授权的变更，可以说明如何检查要求，但不是可以覆盖用户或个人层的
新权威。Supervisor 不能在交付时把用户硬要求降为软要求。硬要求未满足时，Auditor 用
证据记录 `fail`，不得改写为 `pass`。

只有用户明确的“不满足就不交付”条件才写入 `acceptance.release_conditions`；默认值为
`[]`。硬分类或 legacy `blocking=true` 不会自动生成该条件。

默认情况下，只要产物绑定完整，即使有质量问题也仍是可交付候选，并带着发现交付
（通常为 `run_status=issues-found`）。可选知识库无法读取、目标应用验收未执行、
以及已披露的质量不足，本身不拒绝生成或交付，只记录为限制或延期检查。用户明确写出
“某要求未满足就不交付”时才增加相应放行条件；否则无需逐条询问，也不启动重复的无限
返工循环。

绑定、身份、格式、必需产物缺失或审计证据完整性失败，会阻止已验证的成对发布，
因为无法建立可信结果。这是证据失败，不是质量判断。

## 共享知识边界

Auditor 如需知识支持的检查，可以读取本次运行锁定的同一 CompositeIndex、已选回执和
来源正文。它不建立第五个学习库、私有替代索引或自动晋升路径。可复用观察仍保持
observation 状态，经现有反馈路径返回 Logic、Copy、Art Direction 或 Output。

## 工作顺序

1. 接收 Output 交接，以及用户任务、验收合同和 Supervisor 规则的不可变绑定。
2. 建立审计上下文，披露是否为独立执行器、隔离上下文或可用的同一 Agent 上下文，不能
   声称宿主没有提供的隔离等级。
3. 直接检查写盘 PPTX 和对象证据，渲染可用时再检查最终画面。对证据覆盖的硬/软要求
   逐项检查；不可用或未执行的项目保持清晰的 deferred 状态。
4. 输出带具体发现、覆盖范围和限制的不可变审计产物。即使成品可交付，也保留失败发现。
5. 将产物返回 Supervisor。Supervisor 按用户政策与阶段证据决定放行状态，可以路由修复，
   但不能编辑审计结果。
