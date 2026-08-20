# PPT v2.1逻辑层合同

`ppt-design-package.json` 是 Logic、Copy、Output 共用的唯一交接文件。Logic 只写根信息和 `logic_layer`；Copy 在同一文件追加 `copy_layer`。不得维护两个平行包。

## 根结构

```json
{
  "contract_version": "2.1",
  "package_id": "example-deck",
  "version": "2.1.0",
  "status": "logic-approved",
  "brief": {},
  "logic_layer": {},
  "copy_layer": null,
  "approvals": {
    "logic": {"status": "approved", "approved_by": "user", "notes": ""},
    "copy": null
  }
}
```

`status` 只能沿 `draft → logic-approved → copy-approved` 前进。逻辑发生实质变化时，必须删除旧 `copy_layer`，把状态退回 `draft` 或重新审批为 `logic-approved`。

## brief

```json
{
  "purpose": "季度经营复盘并申请下一阶段资源",
  "initiator_stance": "提出改进方案",
  "preflight": {
    "audience": {"primary": "产品与运营决策团队"},
    "material_type": "management-report",
    "management_stage": "monitoring-diagnosis",
    "narrative_archetype": "operating-diagnosis",
    "desired_outcome": {"mode": "approve", "target": "批准试点资源"},
    "confirmation": {
      "audience": "user-provided",
      "material_type": "user-confirmed",
      "management_stage": "user-confirmed",
      "narrative_archetype": "user-confirmed",
      "desired_outcome": "user-confirmed"
    }
  },
  "usage_context": "会议投屏并会后流转",
  "duration_minutes": 20,
  "constraints": []
}
```

`material_type` 是沟通场景：`management-report`、`business-analysis`、`strategy-deployment`、`sales-training`。

`management_stage` 是管理闭环位置：`strategic-framing`、`mechanism-design`、`campaign-deployment`、`operating-system`、`monitoring-diagnosis`、`experiment-review`、`skill-enablement`。

`narrative_archetype` 是叙事原型：`operating-diagnosis`、`policy-reform`、`strategy-map`、`operating-system-design`、`experiment-learning`、`annual-mobilization`、`decision-proposal`、`training-sop`。三者共同构成双层路由，不能用单一“PPT类型”代替。`mode`：`understand`、`approve`、`execute`。

## logic_layer

必备字段：

- `knowledge_requirements`：仍需学习或核实的问题；
- `sources`：来源清单，至少含 `source_id`、`type`、`title`、`locator`、`accessed_at`、`reliability`；
- `glossary`：术语、定义和来源；
- `metric_dictionary`：指标名、定义、公式、单位、期间和来源；
- `deck_message_tree`：总论点、章节和逐页主张；
- `narrative`：开场、递进、转折、收束和页序理由；
- `cross_slide_contract`：跨页不变量和系列页语义；
- `slides`：逐页逻辑；
- `open_items`：未解决事项；
- `lock`：逻辑锁。

### 逻辑锁

`logic-approved` 时以下字段必须全部为 `true`：

```json
{
  "slide_order_locked": true,
  "claims_locked": true,
  "numbers_locked": true,
  "metric_definitions_locked": true,
  "semantic_objects_locked": true,
  "semantic_relations_locked": true,
  "page_message_trees_locked": true,
  "sources_locked": true,
  "management_route_locked": true,
  "reasoning_contracts_locked": true,
  "cross_slide_contract_locked": true
}
```

## narrative 与跨页合同

`narrative` 至少包含：

```json
{
  "opening": "先建立业绩事实与管理张力",
  "progression": "由总体下钻用户阶段，再由原因进入行动",
  "turning_points": ["S06从诊断转入可控性证明"],
  "closing": "形成需批准的下一阶段动作",
  "management_stage_path": ["monitoring-diagnosis", "campaign-deployment"],
  "audience_state_arc": [
    {"slide_id": "S02", "state_before": "只知道结果承压", "state_after": "理解差距集中处", "narrative_move": "定位"}
  ]
}
```

`cross_slide_contract`：

```json
{
  "invariants": [
    {
      "invariant_id": "INV-SEGMENT-ORDER",
      "kind": "object-order",
      "scope_slide_ids": ["S08", "S09", "S10"],
      "locked_values": ["试用用户", "活跃用户", "协作团队", "企业账户"],
      "rationale": "使用行为、留存变化和实验结果必须按同一用户阶段顺序映射"
    }
  ],
  "series": [
    {
      "series_id": "SER-MAP",
      "purpose": "object-drilldown",
      "slide_ids": ["S08", "S09", "S10"],
      "comparison_key": "用户阶段",
      "invariant_ids": ["INV-SEGMENT-ORDER"],
      "change_by_slide": [
        {"slide_id": "S08", "new_information": "使用行为与差距", "unchanged_context": "用户阶段定义与顺序"}
      ],
      "break_rule": "只有进入跨阶段综合判断时才允许退出该系列"
    }
  ]
}
```

`kind`：`term`、`object-order`、`metric-definition`、`analysis-axis`、`grouping`、`scope`。`purpose`：`compare`、`progressive-reveal`、`time-evolution`、`object-drilldown`、`policy-family`、`accumulation`。系列只锁语义恒定项和每页新增认识，不提前指定同构版式。

## 逐页逻辑

```json
{
  "slide_id": "S03",
  "section_id": "SEC01",
  "narrative_role": "recommendation",
  "audience_state_before": "认同问题存在，但不清楚怎么改",
  "audience_state_after": "接受两条改进路径及其验证方式",
  "analysis_level": "management-action",
  "zoom_transition": "hold",
  "content_load_class": "standard",
  "decision_weight": "high",
  "series_id": null,
  "series_role": "standalone",
  "question_answered": "下一阶段如何改进？",
  "claim": "下一阶段需要同时优化上手引导与权限设置。",
  "transition_from": "前页确认当前激活与协作存在缺口。",
  "transition_to": "后页展开两项改进的责任与验证节奏。",
  "data": [],
  "logic_map": {
    "statement": "改进方向包含上手引导和权限设置两项并列行动。",
    "objects": [
      {"object_id": "O01", "label": "改进", "type": "action", "definition": "下一阶段行动总类"},
      {"object_id": "O02", "label": "优化上手引导", "type": "method", "definition": "降低首次完成关键任务的学习成本"},
      {"object_id": "O03", "label": "明确权限默认值", "type": "method", "definition": "减少团队创建后的配置摩擦"}
    ]
  },
  "page_message_tree": {
    "root_node_id": "N00",
    "reading_sequence": ["N00", "N01", "N02", "N03"],
    "nodes": [
      {"node_id": "N00", "parent_node_id": null, "level": 0, "semantic_role": "claim", "content_ref": "claim", "sibling_group_id": null, "children": ["N01"]},
      {"node_id": "N01", "parent_node_id": "N00", "level": 1, "semantic_role": "category", "content_ref": "object:O01", "sibling_group_id": "G-ROOT", "children": ["N02", "N03"]},
      {"node_id": "N02", "parent_node_id": "N01", "level": 2, "semantic_role": "action", "content_ref": "object:O02", "sibling_group_id": "G-IMPROVE", "children": []},
      {"node_id": "N03", "parent_node_id": "N01", "level": 2, "semantic_role": "action", "content_ref": "object:O03", "sibling_group_id": "G-IMPROVE", "children": []}
    ]
  },
  "semantic_relations": [
    {"relation_id": "R01", "type": "contains", "source_object_ids": ["O01"], "target_object_ids": ["O02", "O03"], "direction": "forward", "strength": "confirmed", "evidence_source_ids": ["SRC01"]},
    {"relation_id": "R02", "type": "peer", "source_object_ids": ["O02"], "target_object_ids": ["O03"], "direction": "none", "strength": "confirmed", "evidence_source_ids": ["SRC01"]}
  ],
  "source_ids": ["SRC01"],
  "claim_status": "recommendation",
  "confidence": "high",
  "reasoning_contracts": {
    "action_traceability": [
      {
        "action_node_id": "N02",
        "evidence_node_ids": ["N01"],
        "owner_object_ids": ["O01"],
        "timing": "下一经营周期",
        "metric_refs": [],
        "review_cadence": "月度复盘"
      }
    ],
    "change_mechanism": null,
    "operating_system": null,
    "experiment_learning": null
  },
  "do_not_change": ["两项行动为并列关系，不得合并成一句说明"]
}
```

`zoom_transition`：`hold`、`zoom-in`、`zoom-out`、`shift`、`none`。`content_load_class`：`light`、`standard`、`dense`、`detail-dense`。`decision_weight`：`low`、`medium`、`high`、`critical`。`series_role`：`establish`、`continue`、`advance`、`culminate`、`break`、`standalone`。

## 高级推理合同

- `action_traceability`：行动节点必须追溯证据节点，并写责任对象、时间、指标和复盘节奏；指标使用本页 `data_id`。
- `change_mechanism`：页面使用 `transforms-to` 时必填，至少包含 `old_constraint_object_ids`、`rule_change_object_ids`、`behavior_change_object_ids`、`result_object_ids`、`scope_object_ids`、`exception_object_ids`。From／To只有同时说明旧约束、规则改变、行为变化和结果才成立。
- `operating_system`：`narrative_role=operating-system` 时必填，包含 `input_object_ids`、`decision_rules`、`output_object_ids`、`user_object_ids`、`cadence`、`feedback_relation_ids`、`exception_object_ids`。缺少输入、规则、输出、使用者、更新节奏或反馈时，只能称为分类框架，不能称为经营系统。
- `experiment_learning`：`narrative_role=experiment-learning` 时必填，包含 `hypothesis`、`intervention_object_ids`、`observation_refs`、`disconfirmed_belief`、`new_learning`、`next_test`。`observation_refs` 使用本页节点或数据引用。

`condition` 关系必须额外包含 `combination`：`all-of`、`any-of` 或 `one-of`，分别表示全部成立、任一成立和互斥选择。其他关系不得设置该字段。`peer` 的 `direction` 必须为 `none`；`sequence` 与 `transforms-to` 必须有方向。共同条件不得借阅读顺序暗示为先后步骤。

## 节点与引用规则

- `content_ref` 只能为 `claim`、`object:<object_id>`、`data:<data_id>` 或 `relation:<relation_id>`。
- 每页恰有一个根节点；非根节点必须有存在的父节点，且 `level = parent.level + 1`。
- `children` 与 `parent_node_id` 双向一致；`reading_sequence` 恰好覆盖全部节点一次。
- 同一父节点的多个子节点必须有非空且一致的 `sibling_group_id`；单子节点也建议保留稳定组ID。
- `semantic_role` 描述逻辑职责，不是视觉角色。禁止 `left-card`、`accent-box`、`arrow-step` 等视觉词。
- `logic_map.statement` 只写对象和关系，不写左右、上下、圆圈、卡片、颜色或字号。

## 数据与证据

每个 `data` 项至少含：`data_id`、`metric_name`、`display_value`、`raw_value`、`unit`、`period`、`definition_ref`、`source_ids`、`evidence_status`。允许 `raw_value` 为 `null`，但此时状态必须说明缺数，不得展示伪造数值。

`claim_status`：`source-fact`、`direct-calculation`、`interpretation`、`causal-claim`、`forecast`、`recommendation`、`target`、`hypothesis`、`missing-data`。因果关系只有在证据支持时才使用 `cause`；否则使用 `supports`、`maps-to` 或假设强度。

## Logic禁止字段

`logic_layer` 内不得出现 `copy_id`、`visible_copy`、`speaker_notes`、`font`、`font_size`、`color`、`layout`、`position`、`shape`、`text_box`、`line_break`。这些属于 Copy 或 Output。
