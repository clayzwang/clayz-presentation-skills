# PPT监督报告合同 v3.6

v3.5 和 v3.4 报告仅作为 legacy 读取；下面的 JSON 示例仍是 legacy v3.4
结构。新运行使用 report3.6，并从阶段记录和实际主要产物汇总完整工作报告。

`ppt-supervision-report.json` 是 Supervisor 的协调、对账、完整工作报告和放行记录。新 report3.6 运行在顶层附加权威 `work_report` 对象及规范的 `work_report_sha256`。实际文件／渲染的独立审计由共享的 `io.clayz.presentation.independent-audit/1.0` 产物完成，并以 `auditor_artifact` 绑定；该产物不批准返工，也不得写回任何上游产物。Supervisor 必须保留其中的发现，不能改写结论。

正式 JSON 是可读 Markdown 报告的确定性来源；Markdown 与同一已验证目录一起发布。Markdown 可以比 PPTX 更丰富，因为它记录任务、证据、决策和审计，但不是另一个自行撰写的事实源。完整报告应让未读过对话的读者理解任务要求；验收要求；证据、来源和反证；假设与不确定性；故事线和有意义的排除；最终 copy；逐页设计意图；三轮 Supervisor 校准及下游吸收；实际 PPTX 统计、页面文字和备注；Independent Auditor 观察；放行、局限和改进。缺失的 notes 或未观察的检查必须明确标为 `not-recorded`、`deferred` 或 `uncertain`，不得凭记忆补写。

历史 v3.4 报告中由 Supervisor 承担 `final_auditor` 的旧结构只用于读取
legacy 记录。新运行必须使用 Independent Auditor 产物，并披露真实审计上下文。
当前交付政策先保证绑定和证据完整：质量问题可以随 `issues-found` 交付；绑定、
身份、格式或必需证据缺失仍阻止已验证的成对交付。用户明确的“不满足就不交付”
条件写入 `acceptance.release_conditions`；默认是空数组，硬分类或 legacy
`blocking=true` 不会自动生成放行条件。

过程监督使用独立的 `ppt-supervision-checkpoint.json`，不改变本文件的最终报告合同。Checkpoint只用于诊断和沟通，不是闸门、批准单或拒绝推进凭证。

下面的 JSON 仅保留用于读取使用旧 `final_auditor` 角色的 legacy v3.4 报告；新运行
遵循示例之后的 `auditor_artifact` 与生命周期规则。

```json
{
  "checkpoint_version": "1.1",
  "checkpoint_id": "CP-01",
  "run_id": "run-0123456789ab4def8123456789abcdef",
  "task_request_sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
  "recorded_at": "2026-08-12T22:10:00+08:00",
  "stage": "copy-to-art-direction",
  "status": "recommend-user-input",
  "related_issue_ids": ["SUP-006"],
  "conflicts": [{"conflict_id": "CF-01", "issue_ids": ["SUP-006"], "severity": "major", "cause": "后续5个月只有月均值，没有逐月明细", "decision_impact": "不能绘制逐月趋势或判断压力分布", "evidence": ["ppt-design-package.json"], "approved_baseline": "只展示月均", "downstream_challenge": "逐月趋势任务与月均基准冲突", "alternatives": ["补充逐月值", "改为月均与缺口表达"], "user_decision": "pending"}],
  "questions_for_user": ["请补充8—12月逐月目标或预测值；若暂无，是否接受只展示月均并明确缺数？"],
  "assumptions_if_continue": ["不虚构逐月数，仅展示已知月均和缺口"],
  "same_conflict_previously_escalated": false,
  "control_returned_to": "main-process-or-user"
}
```

`status` 只能为 `continue`、`recommend-user-input`、`proceed-with-assumptions`。不得出现 `blocked`、`rejected`、`vetoed`。同一冲突没有新证据时只升级一次；问题合并后通常不超过3个。用户选择继续时，记录可逆假设并交还控制。

批准产物是当前执行基准，不是不可挑战的永久锁。任一层提出挑战时，Checkpoint必须保留 `approved_baseline`、`downstream_challenge`、证据、替代方案、可逆性和 `user_decision`；用户裁决前不得把替代方案静默写回上游。

## 根结构

```json
{
  "contract_version": "3.4",
  "origin_namespace": "io.clayz.presentation",
  "status": "supervised",
  "run_id": "run-0123456789ab4def8123456789abcdef",
  "task_request_sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
  "package_id": "example-deck",
  "package_version": "2.1.0",
  "art_direction_plan_contract_version": "1.7",
  "output_qa_contract_version": "4.0",
  "supervised_at": "2026-08-12T22:30:00+08:00",
  "run_status": "complete-with-deferred-acceptance",
  "acceptance_contract": {},
  "stage_snapshots": {},
  "requirement_traceability": [],
  "retrieval_quality": {},
  "generation_efficiency": {},
  "index_evidence": {},
  "resource_usage": {},
  "environment_observation": {
    "preflight": {"artifact": "runtime-preflight.json", "scan_id": "runtime-example", "sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", "run_id": "run-0123456789ab4def8123456789abcdef", "task_request_sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd", "nonce": "1111111111111111111111111111111111111111111111111111111111111111", "challenge_sha256": "2222222222222222222222222222222222222222222222222222222222222222", "task_root_sha256": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff", "issued_at": "2026-08-12T20:45:00+08:00", "expires_at": "2026-08-13T20:45:00+08:00", "issuance_receipt_sha256": "4444444444444444444444444444444444444444444444444444444444444444", "consumption_receipt_sha256": "3333333333333333333333333333333333333333333333333333333333333333", "config_sha256": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"},
    "route": {"route_id": "native-presentation-tool+libreoffice", "authoring_backend": "native-presentation-tool", "render_backend": "libreoffice", "status": "provisional"},
    "required_capabilities": {"configured": ["editable-text", "render-preview"], "satisfied": [], "declared_unverified": ["editable-text", "render-preview"], "missing": []},
    "target_applications": [
      {"application": "powerpoint", "capability": "powerpoint-reopen-render", "availability": "unavailable", "final_status": "deferred", "authoring_gate": false, "evidence_refs": ["runtime-preflight.json#target_application_checks.powerpoint sha256=cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"]},
      {"application": "wps", "capability": "wps-reopen-render", "availability": "unavailable", "final_status": "deferred", "authoring_gate": false, "evidence_refs": ["runtime-preflight.json#target_application_checks.wps sha256=cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"]},
      {"application": "libreoffice", "capability": "libreoffice-reopen-render", "availability": "available", "final_status": "pass", "authoring_gate": false, "evidence_refs": ["output/final-reopen-render/libreoffice/target-application-check.json sha256=9999999999999999999999999999999999999999999999999999999999999999"]}
    ],
    "compatibility_scope": "partial",
    "attribution_summary": "LibreOffice重开渲染已通过；PowerPoint与WPS原生验收因宿主不可用而延期，不阻断制作。"
  },
  "supervisor_roles": {
    "initiator": {"status": "complete", "summary": "发起治理运行并在结束时交还控制", "evidence_refs": ["ppt-resource-inventory.json sha256=8888888888888888888888888888888888888888888888888888888888888888", "ppt-supervision-report.json"]},
    "mediator": {"status": "not-needed", "summary": "记录本轮没有发现需要调解的问题", "evidence_refs": ["ppt-supervision-report.json#issues"]},
    "recorder": {"status": "complete", "summary": "记录预检、阶段交接、终审和交付", "evidence_refs": ["ppt-supervision-report.json#lifecycle_events"]},
    "final_auditor": {"status": "complete", "summary": "重跑最终校验并完成独立审计", "evidence_refs": ["ppt-output-qa.json sha256=7777777777777777777777777777777777777777777777777777777777777777", "ppt-supervision-report.json#slides"]}
  },
  "lifecycle_events": [
    {"event_id": "SUP-E01", "occurred_at": "2026-08-12T21:00:00+08:00", "phase": "root", "actor_role": "initiator", "action": "supervision-started", "status": "completed", "summary": "分类并发起受治理的PPT运行", "evidence_refs": ["ppt-resource-inventory.json sha256=8888888888888888888888888888888888888888888888888888888888888888"]},
    {"event_id": "SUP-E02", "occurred_at": "2026-08-12T21:01:00+08:00", "phase": "preflight", "actor_role": "recorder", "action": "runtime-preflight-completed", "status": "completed", "summary": "检测宿主能力并锁定制作与渲染路线", "evidence_refs": ["runtime-preflight.json sha256=cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"]},
    {"event_id": "SUP-E03", "occurred_at": "2026-08-12T21:02:00+08:00", "phase": "preflight", "actor_role": "recorder", "action": "resource-brief-presented", "status": "completed", "summary": "在Logic前向用户展示已选、不可用和未选资源", "evidence_refs": ["ppt-resource-inventory.json#user_brief sha256=8888888888888888888888888888888888888888888888888888888888888888 content_sha256=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"]},
    {"event_id": "SUP-E04", "occurred_at": "2026-08-12T21:10:00+08:00", "phase": "logic", "actor_role": "recorder", "action": "logic-handoff-recorded", "status": "completed", "summary": "记录Logic批准和证据锁", "evidence_refs": ["ppt-design-package.json sha256=6666666666666666666666666666666666666666666666666666666666666666"]},
    {"event_id": "SUP-E05", "occurred_at": "2026-08-12T21:20:00+08:00", "phase": "copy", "actor_role": "recorder", "action": "copy-handoff-recorded", "status": "completed", "summary": "记录Copy批准和证据锁", "evidence_refs": ["ppt-design-package.json#copy_layer sha256=6666666666666666666666666666666666666666666666666666666666666666"]},
    {"event_id": "SUP-E06", "occurred_at": "2026-08-12T21:30:00+08:00", "phase": "art-direction", "actor_role": "recorder", "action": "art-direction-handoff-recorded", "status": "completed", "summary": "记录Art Direction批准和证据锁", "evidence_refs": ["ppt-art-direction-plan.json sha256=5555555555555555555555555555555555555555555555555555555555555555"]},
    {"event_id": "SUP-E07", "occurred_at": "2026-08-12T22:00:00+08:00", "phase": "output", "actor_role": "recorder", "action": "output-handoff-recorded", "status": "completed", "summary": "记录PPTX写入和Output QA交接", "evidence_refs": ["final.pptx sha256=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", "ppt-output-qa.json sha256=7777777777777777777777777777777777777777777777777777777777777777"]},
    {"event_id": "SUP-E09", "occurred_at": "2026-08-12T22:20:00+08:00", "phase": "supervision", "actor_role": "final_auditor", "action": "final-audit-completed", "status": "completed", "summary": "完成对象和渲染的独立终审", "evidence_refs": ["ppt-output-qa.json sha256=7777777777777777777777777777777777777777777777777777777777777777", "ppt-supervision-report.json#slides"]},
    {"event_id": "SUP-E10", "occurred_at": "2026-08-12T22:25:00+08:00", "phase": "delivery", "actor_role": "recorder", "action": "delivery-pair-locked", "status": "completed", "summary": "将最终PPTX和审计报告锁定为同一次交付", "evidence_refs": ["final.pptx sha256=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", "ppt-supervision-report.json"]},
    {"event_id": "SUP-E11", "occurred_at": "2026-08-12T22:30:00+08:00", "phase": "delivery", "actor_role": "initiator", "action": "control-returned", "status": "returned", "summary": "携带联合产物和审计结论交还控制权", "evidence_refs": ["ppt-supervision-report.json#control_returned_to"]}
  ],
  "artifact_paths": {
    "runtime_preflight": "runtime-preflight.json",
    "resource_inventory": "ppt-resource-inventory.json",
    "package": "ppt-design-package.json",
    "art_direction_plan": "ppt-art-direction-plan.json",
    "pptx": "final.pptx",
    "render_root": "output/rendered",
    "output_qa": "ppt-output-qa.json",
    "object_inventory": "ppt-object-inventory.json",
    "build_deviation_log": "ppt-build-deviation-log.json",
    "font_environment_report": "font-environment-report.json",
    "font_name_audit_report": "pptx-font-name-audit.json",
    "cjk_render_report": "cjk-render-report.json",
    "size_audit_report": "ppt-size-audit.json",
    "final_reopen_render_root": "output/final-reopen-render"
  },
  "delivery_efficiency": {
    "status": "pass",
    "profile": "lightweight",
    "total_bytes": 1460000,
    "media_share_of_file": 0.82,
    "blocker_count": 0,
    "warning_count": 0,
    "exception_reason": null,
    "evidence": "体积报告与最终PPTX哈希一致；对象清单独立复核未发现重复媒体、意外字体或附件。"
  },
  "delivery_pair": {
    "status": "ready",
    "required_artifacts": ["pptx", "supervision-report"],
    "pptx": {"path": "final.pptx", "sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"},
    "supervision_report": {"path": "ppt-supervision-report.json"},
    "delivery_manifest": {"path": "delivery-manifest.json"},
    "publisher": "scripts/publish_supervised_pair.py",
    "evidence": "最终PPTX哈希和审计报告路径已锁定为同一次用户交付"
  },
  "slides": [],
  "issues": [],
  "deck_findings": [],
  "responsibility_attribution": {},
  "recommendations": [],
  "asset_observations": [],
  "control_returned_to": "main-process-or-user"
}
```

`resource_usage` 在出现时遵循 `io.clayz.presentation.resource-usage/1.0`：必须把用户在 Logic 前看过的全部已选资源逐项对账为“实际使用”或“明确未用”，将已用资源映射到五个治理阶段及具体证据，并提供最终用户可见摘要。它是 report3.6 的补充证据；出现时缺失或锁不一致应记录为证据问题。

`stage_snapshots` 必须嵌入 Logic（`brief` 与 `logic_layer`）、Copy（`copy_layer`）和 Art Direction（沟通合同、视觉命题、决策日志、字体、节奏和逐页计划）的不可变决策快照。每份快照同时绑定原文件 SHA-256 和规范化快照 SHA-256，并与实际验证过的上游产物逐字一致。`requirement_traceability` 恰好覆盖每条任务验收要求，并把它映射到 Logic、Copy、Art Direction、Output 和 Supervisor 证据。

`calibration_artifacts` 记录 Logic→Copy、Copy→Art Direction 和 Art Direction→Output
之间由 Supervisor 返回并汇总的哈希绑定评价。每份产物使用
`io.clayz.presentation.supervisor-calibration/1.0`，绑定 run、任务请求、验收合同和
来源产物映射，并记录具体发现。消费方阶段记录通过 `calibration_bindings` 写入回执
SHA，以及 `accepted`、`partially-accepted` 或 `declined` 和理由。来源哈希陈旧时，下游
绑定失效。

`retrieval_quality` 与 `generation_efficiency` 仅在提供 Index／运行对账字段时校验。它们在 report3.6 交付中仍是可选字段；保留真实值，不创建占位回执、耗时或预算声明。文件体积效率不能替代运行时间效率。

新运行的 `supervisor_roles` 记录 Supervisor 的 `initiator`、`mediator` 和
`recorder` 职责。兼容字段 `final_auditor` 保持 `not-needed` 或 `incomplete`，不能
暗示 Supervisor 编写了审计。第五份阶段记录使用 `auditor` 角色；Independent Auditor
单独以 `auditor_artifact` 绑定，包含路径、SHA-256、`audited_at` 和
`independent_context`。质量问题不要求用户 Checkpoint 或调解；只有
实质业务选择、范围变更或用户明确的“不满足就不交付”条件才创建 v1.1
`ppt-supervision-checkpoint.json`，并绑定同一 run、任务请求和受影响问题 ID。所有
外部角色及生命周期证据引用必须带 `sha256=<实际文件哈希>`，解析到任务根内非空、
合同有效的受治理产物；报告内部自引用则与当前内存报告核对。每个角色记录简明结果
与证据引用，不记录私有思维链。

`core_sequence` 是 report3.6 必需的生命周期摘要，由五份阶段记录、三个
`calibration_artifacts`、Auditor 产物和 Supervisor 放行派生，顺序为：
`supervision-started` → `logic-to-copy-calibrated` →
`copy-to-art-direction-calibrated` → `art-direction-to-output-calibrated` →
`independent-audit-completed` → `supervisor-release`。旧的 `lifecycle_events` 列表在
此分支是可选补充证据；若提供，每个事件必须真实且有绑定，不为满足 legacy 读取器
虚构预检／资源简报／调解序列。只有实质决策、范围变更或明确“不满足就不交付”条件
才记录调解。

`environment_observation` 必须逐字绑定 `runtime-preflight.json` 的扫描 ID、文件 SHA-256、运行 ID、规范化任务请求 SHA-256、任务根 SHA-256、规范签发/消费台账哈希、实际 resolved config SHA-256、锁定路线、路线必需能力状态和全部目标应用。报告根与预检的运行/任务绑定必须一致，且预检不得遗漏已校验 resolved config 声明的任何必需能力；宿主提供的“可用”能力还必须具有同一运行的实测来源，但仍保持 `host-declared-unverified`：这些能力写入 `declared_unverified` 而不是 `satisfied`，路线保持 `provisional`。不可用目标只能记为 `deferred`，可用但未执行记为 `not-selected`，实际执行后才可记为 `pass` 或 `fail`；所有目标固定 `authoring_gate=false`。`deferred`/`not-selected` 必须绑定经哈希校验的预检记录；`pass`/`fail` 必须提供 `io.clayz.presentation.target-application-check/1.0` 回执，绑定同一 run、任务请求、目标应用和最终 PPTX SHA-256，且 `observed_at` 必须同时落在 challenge 有效窗口内以及 Output 交接至最终审计之间。`compatibility_scope` 根据最终状态计算为 `full`、`partial` 或 `none`，用于约束兼容性声明和问题归因。

`run_status`：`clean`、`complete-with-deferred-acceptance`、`issues-found`、`incomplete-evidence`。没有其他问题但至少一个目标应用为 `deferred` 或 `not-selected` 时使用 `complete-with-deferred-acceptance`，PPTX、正式报告和派生 Markdown 仍可一起交付。质量缺陷、未满足要求或渲染覆盖不可用／未选用时，在用户政策允许时使用 `issues-found` 并如实交付。report3.6 中，五份记录装配、三个校准产物、Auditor 产物、`supervisor_release`、`core_sequence`、`work_report`／`work_report_sha256` 或必需绑定／证据完整性缺失时使用 `incomplete-evidence` 并阻止已验证成对单元。派生 Markdown／manifest 格式错误或不匹配属于发布证据失败，不新增 `delivery_pair` 成员。旧生命周期、Index／检索、性能、Library 和渲染证据可以缺失；缺失时记录限制，不得虚构。可选阶段 notes 缺失记为 `not-recorded`，不单独阻止绑定完整的成对单元。

`origin_namespace` 必须为 `io.clayz.presentation`，`status` 必须为 `supervised`，`control_returned_to` 记录终审后接收控制权的用户或责任流程。`artifact_paths` 必须把环境预检和 Logic 前资源盘点作为一等证据，而不是只记录下游制作文件。

`delivery_efficiency.status` 只能为 `pass`、`fail` 或 `uncertain`。用户未提前指定时 `profile` 必须为 `lightweight`；`uncertain` 时根状态必须为 `incomplete-evidence`。`ppt-size-audit.json` 必须绑定最终PPTX哈希，并与 `ppt-object-inventory.json.package_media` 的文件大小、媒体数量、重复项、字体和附件事实相互印证。超出总体软预算但单项效率已通过时，可以 `pass`，但 `exception_reason` 必须写出具体业务必要性；重复、未使用、超分辨率或意外嵌入内容不能用例外理由放行。

`delivery_pair` 将 PPTX 和正式审计报告保持为已验证的主要成对单元。发布器写出确定性的 `work-report.md`，并将它放入 manifest 的 `derived_files` 集合；它从同一已验证目录随正式成对单元交付，但不加入 `delivery_pair.required_artifacts`。`required_artifacts` 仍必须恰好为 `["pptx", "supervision-report"]`；PPTX 项记录文件名和已核验 SHA-256，报告项记录本报告文件名，`delivery_manifest.path` 必须为 `delivery-manifest.json`，`publisher` 必须为 `scripts/publish_supervised_pair.py`。新运行必须有有效的 `auditor_artifact` 绑定且 `audited_at <= released_at` 才能为 `ready`。由必需绑定／证据缺失造成的 `incomplete-evidence` 必须 `blocked`；带延期渲染覆盖的绑定完整 `issues-found` 报告在默认政策下仍可 `ready`。Output 只能暂存文件；只有发布器可以物化新的已验证交付目录，且 Supervisor 只能从该目录同时交付 PPTX、正式报告与 `work-report.md`。manifest 的 `derived_files` 条目把 Markdown 路径、字节和哈希绑定到正式 JSON，且不形成循环报告哈希。人工复制或单文件交付不算完成。

`asset_observations` 只记录本次实际使用资产的软反馈，可含 `asset_id`、`task_fit`、`execution_effect`、`conflict_signal`、`neighbor_value`、`reuse_note` 和证据。1—5分只代表本任务情境，不得解释为全局质量分，不得自动改变参考准入、分类、检索权重或把生成物升级为参考。

## 完整工作报告指引

report3.6 JSON 是本任务的完整工作记录。它从阶段主要产物、简短阶段
记录、可选且已绑定的 `work-notes`、三份 Supervisor 校准产物、独立
Auditor 产物和最终 PPTX 的实际检查汇总而来，并在顶层附加 `work_report`
及 `work_report_sha256`。核心的 `render_work_report_markdown` 路径从同一
JSON 确定性派生 `work-report.md`，并将它写入 `manifest.derived_files`；
不能再单独编辑一份叙事来充当事实源。

汇总记录应让未读过对话的读者理解任务和验收要求、证据和来源、反证及其
处理、假设和不确定性、故事线、决策、取舍与有意义的排除、最终可见 copy
和备注、逐页设计意图及内容到视觉的关系、三轮 Supervisor 评价及 Logic、
Copy、Art Direction 或 Output 各自吸收的内容、实际 PPTX 页数／对象／
媒体统计、页面文字和 speaker notes、实际偏差、Independent Auditor 的
观察与审计局限、放行决定、问题、局限和改进。可以使用 `task`、
`evidence`、`story`、`copy`、`design`、`calibration`、`actual`、`audit`、
`release` 等标题帮助阅读，但它们不是固定故事类型或版式配额。Markdown 应围绕
已保存的研究、观点、排除、视觉意图和实际结果组织可读叙述，不能只是键名清单、
原始 JSON dump 或旧的泛化摘要。没有对应证据时省略空断言，并写明 `not-recorded`
或具体限制。

外部来源和上游 snapshot 的身份、定位、权利及哈希 trace 保留在任务本地证据中。
任务事实和 work notes 归任务本地记录及派生报告所有；不能写入插件公共源，也不能
把公共源当作任务报告。

Art Direction 必须说明内容关系如何变成视觉关系，媒介为何适合证据和受众，
以及在文字主导时为何文字比图表、图片、表格或图示更清楚。报告记录模型
负责的专业视觉判断，包括入选和排除路径；脚本只负责绑定字节、统计、从
实际 PPTX 提取可观察的文字／备注并汇总，不能代替艺术判断。每页不要求
必须有图表、图片、表格或轮廓变化。

相关 notes 或观察没有被记录时，使用 `not-recorded` 并说明由此产生的
限制。不能从主要产物完整、后续阶段记忆、填充的 JSON 字段或 PPTX 存在，
推断完整历史。只有摘要的 legacy 报告属于证据不完整；这不证明此前阶段没有
执行。`deferred`、`uncertain` 和质量 `fail` 都要保持真实；在绑定证据完整且
现有政策允许时可以交付。

## 逐页结构

```json
{
  "slide_id": "S06",
  "render_file": "6.png",
  "planned": {
    "first_visual": "贯穿四阶段的推进主轴",
    "area_signature": "title:12; timeline:58; evidence:30",
    "silhouette_family": "horizontal-stage-axis",
    "density_class": "balanced",
    "dominant_medium": "relationship-diagram",
    "structure_signature": "four-stage-timeline",
    "structure_type": "timeline",
    "series_id": "SER-Q",
    "series_behavior": "locked-backbone",
    "motif_id": "MOTIF-QUARTER-AXIS",
    "semantic_whitespace_mode": "future-space",
    "context_rail_enabled": true,
    "semantic_tree_id": "SLT-S06-B",
    "semantic_tree_mode": "hierarchical",
    "visual_self_correction_required": true,
    "required_object_types": ["shape", "connector"],
    "minimum_object_counts": {"shape": 8, "connector": 1},
    "target_type_counts": {"shape": 8, "table-cell": 0, "chart-label": 0},
    "audience_detail_min_pt": 12,
    "chart_text_min_pt": 12,
    "data_chart_contract": null
  },
  "actual_objects": {
    "shapes": 12, "text_shapes": 8, "connectors": 1, "pictures": 0,
    "graphic_frames": 0, "tables": 0, "charts": 0, "diagrams": 0
  },
  "rendered": {
    "medium_label": "timeline",
    "first_visual_observed": "四个等宽浅色卡片",
    "area_plan_observed": "卡片约占内容区72%，主轴不足8%",
    "series_backbone_observed": "季度轴位置漂移，已出现季度未保持稳定。",
    "motif_observed": "季度轴仍存在，但新增季度没有形成唯一焦点。",
    "semantic_whitespace_observed": "未来季度空间被浅色说明框填满。",
    "context_rail_observed": "章节轨道面积正常，但当前标记顺序错误。",
    "semantic_tree_observed": "计划中的主轴父组被拆成四个同级卡片，层级树在渲染中被压平。",
    "visual_self_correction_evidence_observed": "A/B原型与两轮观察记录齐全，但Output未忠实执行入选树。",
    "minimum_audience_text_pt_observed": 12,
    "nonconforming_point_sizes_observed": [],
    "scatter_label_evidence": "本页不是散点图。",
    "scatter_line_evidence": "本页不是散点图。",
    "recognizability": "fail",
    "evidence": "主轴权重过低，阶段推进不能在缩略图中被快速识别。"
  },
  "checks": {
    "logic_copy_fidelity": {"status": "pass", "evidence": "四阶段名称和顺序一致。"},
    "copy_art_direction_fidelity": {"status": "pass", "evidence": "全部原子文案和语义关系被承接。"},
    "art_direction_build_fidelity": {"status": "fail", "evidence": "制作把主轴退化为卡片背景。"},
    "art_direction_first_visual_fidelity": {"status": "fail", "evidence": "第一视觉由主轴漂移为卡片。"},
    "art_direction_area_plan_fidelity": {"status": "fail", "evidence": "辅助卡片占比超过计划。"},
    "plan_object_fidelity": {"status": "pass", "evidence": "存在连接线和四个节点。"},
    "object_render_fidelity": {"status": "fail", "evidence": "对象存在但时间轴语法不可辨认。"},
    "art_direction_rhythm_fidelity": {"status": "pass", "evidence": "本页轮廓与全稿序列一致。"},
    "purposeful_series_fidelity": {"status": "fail", "evidence": "系列持久元素漂移，新增信息不再是唯一变化。"},
    "cross_slide_invariant_fidelity": {"status": "fail", "evidence": "Q1与Q2位置在本页互换。"},
    "semantic_whitespace_fidelity": {"status": "fail", "evidence": "未来空间被装饰性说明填充。"},
    "motif_fidelity": {"status": "fail", "evidence": "母题存在但推进规则未执行。"},
    "context_rail_fidelity": {"status": "fail", "evidence": "当前章节标记与页序不一致。"},
    "semantic_layout_tree_fidelity": {"status": "fail", "evidence": "主轴父子分组被压平成四个同级卡片。"},
    "visual_self_correction_integrity": {"status": "pass", "evidence": "原型、分维观察、定向修改与停止理由齐全，未按自动总分选版。"},
    "deviation_authorization": {"status": "fail", "evidence": "主轴降权没有Art Direction重新批准。"},
    "qa_truthfulness": {"status": "fail", "evidence": "Output QA错误判艺术指导保真为pass。"},
    "anti_cardification": {"status": "fail", "evidence": "时间节点被制作成同权重卡片。"},
    "target_app_compatibility": {"status": "pass", "evidence": "目标软件实机或确定性静态检查未发现字体、首尾页或对象可见性漂移。"},
    "inherited_chrome_fidelity": {"status": "pass", "evidence": "正文仅有版式继承的一条标题分隔线，页码仅来自母版动态字段，页面层候选为0。"},
    "typography_legibility": {"status": "pass", "evidence": "受众最小字号满足中央配置，且未发现不合规字号。"},
    "scatter_semantics_and_labels": {"status": "not-applicable", "evidence": "本页不是散点图。"}
  }
}
```

检查状态：`pass`、`fail`、`not-applicable`、`uncertain`。`uncertain` 只用于证据不足，根状态必须为 `incomplete-evidence`。`not-applicable` 也要写具体证据。每条检查证据必须包含稳定的 slide ID，并且对该页、该检查唯一；跨检查或跨页重复同一句话判无效。Independent Auditor 针对最终 PPTX 执行完整文件／对象／渲染审计；Supervisor 校验报告与绑定，不能用自己写的“一致”代替对象和渲染证据。

`planned.audience_detail_min_pt`、`chart_text_min_pt`、`data_chart_contract` 与 `quantitative_execution_contract` 必须逐字继承艺术指导计划。正文页 `rendered.minimum_audience_text_pt_observed` 必须记录实际最小受众字号，`nonconforming_point_sizes_observed` 记录所有违反中央字号令牌政策的值；低于配置下限或列表非空时 `typography_legibility` 必须失败并生成对应问题。

散点图页必须审查 `scatter_label_evidence` 与 `scatter_line_evidence`：实体标签缺失、重叠或不可读时使用 `SCATTER_ENTITY_LABEL_MISSING_OR_UNREADABLE`；不同实体点被无语义连接时使用 `SCATTER_UNJUSTIFIED_POINT_CONNECTIONS`。非散点图页该检查为 `not-applicable`，散点图页不得标为不适用。

`medium_label` 可使用：`typography`、`data-chart`、`table`、`timeline`、`swimlane`、`matrix`、`relationship-diagram`、`process`、`photo-or-screenshot`、`scenario-illustration`、`cards`、`columns`、`mixed`、`other`、`not-reviewed`。

## 问题结构

```json
{
  "issue_id": "SUP-006",
  "finding_code": "ART_DIRECTION_FIRST_VISUAL_DRIFT",
  "slide_id": "S06",
  "severity": "major",
  "owner_layer": "output-build",
  "confidence": "high",
  "failed_checks": ["art_direction_build_fidelity", "art_direction_first_visual_fidelity"],
  "source_artifacts": ["ppt-art-direction-plan.json", "final.pptx", "output/rendered/6.png"],
  "evidence": "计划第一视觉为四阶段主轴；实际四个浅色框占据主要面积。",
  "expected": "节点、阶段和推进方向构成第一视觉。",
  "actual": "页面首先被识别为普通四栏。",
  "impact": "阶段感和推进感丢失。",
  "recommended_change": "恢复主轴与节点的面积和层级权重。",
  "regression_rule": "时间轴页须在缩略图中3秒内被辨认为时间轴。"
}
```

`severity`：`critical`、`major`、`moderate`、`minor`。`owner_layer`：`logic`、`copy`、`art-direction`、`output-build`、`output-qa`、`interface`、`system`。`confidence`：`high`、`medium`、`low`。

稳定 `finding_code` 至少包括：

- `LOGIC_RELATION_UNDERSPECIFIED`
- `COPY_RELATION_DRIFT`
- `COPY_ATOMIZATION_PRESSURE`
- `ART_DIRECTION_PLAN_CONTRADICTION`
- `ART_DIRECTION_NOT_EXECUTED`
- `ART_DIRECTION_FIRST_VISUAL_DRIFT`
- `ART_DIRECTION_ATTENTION_HIERARCHY_MISMATCH`
- `ART_DIRECTION_AREA_PLAN_DRIFT`
- `ART_DIRECTION_RHYTHM_DRIFT`
- `PURPOSEFUL_SERIES_BROKEN`
- `UNJUSTIFIED_SILHOUETTE_REPETITION`
- `CROSS_SLIDE_INVARIANT_DRIFT`
- `SEMANTIC_WHITESPACE_FILLED`
- `ART_DIRECTION_FALSE_SEMANTIC_WHITESPACE`
- `MOTIF_SEQUENCE_DRIFT`
- `CONTEXT_RAIL_UI_DRIFT`
- `SEMANTIC_LAYOUT_TREE_FLATTENED`
- `VISUAL_SELF_CORRECTION_EVIDENCE_MISSING`
- `CANDIDATE_DIVERSITY_COLLAPSED`
- `AUTOMATIC_SCORE_SELECTED_LAYOUT`
- `BUILD_UNAPPROVED_DEVIATION`
- `PLAN_TABLE_WITHOUT_TABLE_CELL`
- `PLAN_OBJECT_GRAMMAR_MISMATCH`
- `BUILD_TABLE_MISSING`
- `BUILD_CHART_MISSING`
- `BUILD_STRUCTURE_COLLAPSED_TO_CARDS`
- `BUILD_REQUIRED_OBJECT_MISSING`
- `RENDERED_MEDIUM_UNCLEAR`
- `DECK_SILHOUETTE_REPETITION`
- `QA_FALSE_PASS`
- `MASTER_PAGE_NUMBER_DUPLICATED`
- `TITLE_CHROME_DUPLICATED`
- `FONT_SIZE_BELOW_MINIMUM`
- `FONT_SIZE_NONCONFORMING_TOKEN`
- `CJK_GLYPH_RENDER_MISSING`
- `CJK_FONT_FAMILY_MISMATCH`
- `ACCEPTANCE_REQUIREMENT_FAILED`
- `RETRIEVAL_RELEVANCE_OR_BUDGET_FAILURE`
- `GENERATION_PERFORMANCE_BUDGET_EXCEEDED`
- `PPTX_LIGHTWEIGHT_PROFILE_MISSING`
- `PPTX_DUPLICATE_OR_UNUSED_MEDIA`
- `PPTX_RASTER_OVERSIZED`
- `PPTX_UNEXPECTED_EMBEDDED_PAYLOAD`
- `SCATTER_ENTITY_LABEL_MISSING_OR_UNREADABLE`
- `SCATTER_UNJUSTIFIED_POINT_CONNECTIONS`
- `EVIDENCE_INCOMPLETE`
- `CONTENT_NOT_READY_BEFORE_DESIGN`
- `AGGREGATE_WITHOUT_UNDERLYING_DETAIL`
- `NARRATIVE_CHAIN_SPLIT`
- `PREMATURE_DECLARATION_BEFORE_DILEMMA`
- `PUNCTUATION_DEPENDENT_LAYOUT`
- `RELATED_DATA_CARDIFICATION`
- `PLAN_QUALITY_FALSE_PASS`

每个逐页 `fail` 检查必须被同页至少一个问题引用。

## 整稿发现、建议与归因

`deck_findings` 为字符串数组，写跨页规律与证据。`recommendations` 每项包含 `priority`、`target_layer`、`change`、`verification`、`scope`。

证据充分时使用整数权重且合计100；否则使用定性归因：

```json
{
  "mode": "qualitative",
  "confidence": "low",
  "primary": ["output-build", "output-qa"],
  "secondary": ["interface"],
  "rationale": "缺少生成过程记录，不使用伪精确比例。"
}
```
