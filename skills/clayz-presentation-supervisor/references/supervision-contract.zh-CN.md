# PPT监督报告合同 v2.6

`ppt-supervision-report.json` 是独立事后审计记录，不表示用户批准返工，也不得写回任何上游产物。

过程监督使用独立的 `ppt-supervision-checkpoint.json`，不改变本文件的最终报告合同。Checkpoint只用于诊断和沟通，不是闸门、批准单或拒绝推进凭证。

```json
{
  "checkpoint_version": "1.0",
  "checkpoint_id": "CP-01",
  "stage": "copy-to-art-direction",
  "status": "recommend-user-input",
  "conflicts": [{"conflict_id": "CF-01", "severity": "major", "cause": "后续5个月只有月均值，没有逐月明细", "decision_impact": "不能绘制逐月趋势或判断压力分布", "evidence": ["ppt-design-package.json"], "approved_baseline": "只展示月均", "downstream_challenge": "逐月趋势任务与月均基准冲突", "alternatives": ["补充逐月值", "改为月均与缺口表达"], "user_decision": "pending"}],
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
  "contract_version": "2.6",
  "package_id": "example-deck",
  "package_version": "2.1.0",
  "art_direction_plan_contract_version": "1.3",
  "output_qa_contract_version": "3.6",
  "supervised_at": "2026-08-12T22:30:00+08:00",
  "run_status": "issues-found",
  "artifact_paths": {
    "package": "ppt-design-package.json",
    "art_direction_plan": "ppt-art-direction-plan.json",
    "pptx": "final.pptx",
    "render_root": "output/rendered",
    "output_qa": "ppt-output-qa.json",
    "object_inventory": "ppt-object-inventory.json",
    "build_deviation_log": "ppt-build-deviation-log.json",
    "font_environment_report": "font-environment-report.json",
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
  "slides": [],
  "issues": [],
  "deck_findings": [],
  "responsibility_attribution": {},
  "recommendations": [],
  "asset_observations": []
}
```

`run_status`：`clean`、`issues-found`、`incomplete-evidence`。缺少艺术指导、PPTX、最终渲染或制作偏差证据时使用 `incomplete-evidence`。

`delivery_efficiency.status` 只能为 `pass`、`fail` 或 `uncertain`。用户未提前指定时 `profile` 必须为 `lightweight`；`uncertain` 时根状态必须为 `incomplete-evidence`。`ppt-size-audit.json` 必须绑定最终PPTX哈希，并与 `ppt-object-inventory.json.package_media` 的文件大小、媒体数量、重复项、字体和附件事实相互印证。超出总体软预算但单项效率已通过时，可以 `pass`，但 `exception_reason` 必须写出具体业务必要性；重复、未使用、超分辨率或意外嵌入内容不能用例外理由放行。

`asset_observations` 只记录本次实际使用资产的软反馈，可含 `asset_id`、`task_fit`、`execution_effect`、`conflict_signal`、`neighbor_value`、`reuse_note` 和证据。1—5分只代表本任务情境，不得解释为全局质量分，不得自动改变参考准入、分类、检索权重或把生成物升级为参考。

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

检查状态：`pass`、`fail`、`not-applicable`、`uncertain`。`uncertain` 只用于证据不足，根状态必须为 `incomplete-evidence`。`not-applicable` 也要写具体证据。

`planned.audience_detail_min_pt`、`chart_text_min_pt` 与 `data_chart_contract` 必须逐字继承艺术指导计划。正文页 `rendered.minimum_audience_text_pt_observed` 必须记录实际最小受众字号，`nonconforming_point_sizes_observed` 记录所有违反中央字号令牌政策的值；低于配置下限或列表非空时 `typography_legibility` 必须失败并生成对应问题。

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
