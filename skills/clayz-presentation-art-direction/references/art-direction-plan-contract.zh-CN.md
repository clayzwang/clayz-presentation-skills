# 艺术指导计划合同 v1.6

`ppt-art-direction-plan.json` 是 `copy-approved` 脚本包与Output之间唯一视觉决策文件。它不新增业务内容，状态只能在全部视觉决策锁定后设为 `art-direction-approved`。

## 根结构

```json
{
  "contract_version": "1.6",
  "status": "art-direction-approved",
  "package_contract_version": "2.3",
  "package_id": "example-deck",
  "package_version": "2.1.0",
  "resource_inventory_lock": {},
  "index_evidence": {},
  "communication_contract": {},
  "art_direction": {},
  "reference_budget": {},
  "ab_review": {},
  "decision_log": {},
  "typography_contract": {},
  "deck_rhythm": {},
  "slides": []
}
```

`resource_inventory_lock` 必须与脚本包中 Logic 启动前的资源盘点签名完全一致。Art Direction 只能选用盘点内的主题、模板、视觉参考、资产、字体和 Provider；若发现新资源，必须交还 Supervisor 修订盘点并向用户重新简报。

`communication_contract` 必须逐字继承脚本包 `brief.preflight`。`typography_contract`、`deck_rhythm`、逐页 `copy_unit_map`、`visual_hierarchy` 和 `medium_execution_contract` 延续原表达计划v2.1的机器可校验字段，但其所有选择权移交给Art Direction。

`typography_contract` 的字号、网格和例外政策都必须继承中央配置：

- `body_min_pt`、`audience_detail_min_pt`、`chart_text_min_pt`：分别不低于 `theme.typography` 中对应下限；
- `even_point_sizes_required`：等于 `theme.typography.prefer_even_point_sizes`；
- `fractional_point_sizes_allowed`：等于 `theme.typography.allow_fractional_point_sizes`；
- `minimum_exception_policy`：等于 `theme.typography.minimum_exception_policy`；
- `grid_system`：由 `layout.column_count` 生成，例如 `12-column`。

容量不足时通过扩大主媒介、删减非必要刻度、分面、拆页或回流Copy解决，不得静默降低配置下限。

## art_direction

必备字段：

- `visual_thesis`：整稿视觉命题；
- `material_route`：四类材料路线之一；
- `first_impression`：受众第一感受；
- `composition_principles`、`forbidden_defaults`；
- `silhouette_sequence`、`density_sequence`、`dominant_media_sequence`、`motif_sequence`；
- `brand_constraints_repeated`；
- `approval={status, approved_by, notes}`。

四个序列必须按页序覆盖全稿。`density_sequence`只表示视觉密度；内容负载与决策重量逐页继承Logic。`approval.status=approved` 才能交给Output；`approved_by` 写真实批准依据，不写“已完成”之类自我声明。

## reference_budget

```json
{
  "max_total_loaded": 24,
  "max_per_archetype": 6,
  "max_sequences_loaded": 4,
  "loaded_record_ids": ["REF-DEMO-015", "REF-DEMO-299"],
  "loaded_sequence_ids": ["SEQ-DEMO-QUARTERS"],
  "query_log": [{
    "request_id": "request-art-direction-reference",
    "receipt_id": "receipt-registered-selection",
    "query": "银行规模与增长证据的比较页",
    "selected_record_ids": ["REF-DEMO-015"],
    "adoption_outcome": "只采用层级和比较语法；禁止复制源文案和像素"
  }],
  "sequence_query_log": [],
  "budget_respected": true
}
```

同一案例跨页复用只计一次。`query_log` 必须非空，把每个已加载记录绑定到 Art Direction 检索回执，并记录检索条件和采用结果；不能只写“参考过样本”。

## decision_log

```json
{
  "conflicts": [
    {
      "conflict_id": "CF-01",
      "layers": ["copy", "art-direction"],
      "rules": ["全部锁定文字必须保留", "目标字号下单页容量不足"],
      "owner": "copy",
      "resolution": "回流Copy拆为两页，不由Art Direction删字",
      "backflow": true,
      "approval_basis": "用户确认拆页"
    }
  ],
  "deviations": [],
  "unresolved": []
}
```

批准计划的 `unresolved` 必须为空。冲突裁决按用户／事实→Logic→Copy→Art Direction→Output顺序；后层不能覆盖上层。

## 逐页新增字段

除原表达计划字段外，每页必须包含：

- `design_intent`：沟通任务、第一印象、第一视觉、注意顺序、构图理由、禁用回退；
- `area_plan`：区域、职责、面积比例、包含copy_id和12列网格跨度；
- `semantic_layout_tree`：页面分组、包含、关系、阅读顺序和形状意图；
- `composition_pattern_decision`：请求 ID、解析 ID、已选 Pattern ID 或显式 `unresolved`、任务约束、预期视觉效果、采用与拒绝原因、关联 Failure Pattern ID，以及 Retrieval Receipt ID；不得包含坐标、Theme、Visual Variant、Layout Contract、Renderer、模板、资产或隐藏推理；
- `layout_contract_decision`：请求 ID、解析 ID、已选 Layout Contract ID 或显式 `unresolved`、Slot 绑定及 Retrieval Receipt ID；它与 Composition Pattern、Visual Variant 保持独立；
- `reference_selection` 与无参考时的 `reference_exception`；
- `ab_review`：候选、选择、淘汰理由和灰度状态；
- `art_direction_lock`；
- `handoff_status=ready-for-output`。
- `content_load_class_repeated` 与 `decision_weight_repeated`；
- `series_visual_contract`：系列身份、骨架行为、持久元素、递进变化、允许变化和退出理由；
- `motif_id`：视觉母题，无则为 `null`；
- `semantic_whitespace`：留白类型、区域、叙事职责和保护状态；
- `persistent_context_rail`：是否启用轻量导航、目的、范围、当前标记和面积上限。
- `medium_execution_contract.data_chart_contract`：数据图表的类型、字号、直接标注、点间连线、语义线与标签避让合同；非数据图表页为 `null`。
- `medium_execution_contract.quantitative_execution_contract`：逐项登记 Logic 数据 ID、编码方式、比较任务、尺度/基准/单位理由，以及经用户明确批准的形状编码例外。三个及以上可比值必须以原生图表或表格作为主媒介。
- `content_aware_canvas`：基于证据记录主体保护、候选放置区、裁切、对比度、视觉方向和覆盖策略；
- `asset_strategy`：模板只推导不克隆、资产语义角色、候选与选择、家族判断、许可记录和 `never_copy` 边界。

`area_plan` 的比例合计为90%至110%，允许标题区、安全区和局部重叠造成近似值；全部可见copy_id必须被覆盖。

## 内容感知画布

图像主导页必须使用 `content_aware_canvas.enabled=true`；混合媒介页只要图片影响文字放置或裁切，也应启用。非图像页使用明确的关闭哨兵值。

```json
{
  "enabled": true,
  "canvas_type": "photo",
  "subject_protection_zones": [
    {"zone_id": "SUBJECT-01", "role": "产品与视线", "protection": "hard", "reason": "主证据不得遮挡"}
  ],
  "candidate_placement_zones": [
    {"zone_id": "PLACE-01", "suitability": "primary", "anchor_edges": ["left", "top"], "supports_copy_ids": ["S03-C01"], "reason": "对比稳定且顺应视线"}
  ],
  "crop_strategy": "focal-crop",
  "contrast_strategy": "native",
  "directional_flow": "主体视线从产品指向主张",
  "overlay_policy": "none",
  "evidence_basis": "按整页尺寸和真实文字占地观察源图"
}
```

主体区与放置区的ID全局唯一；可用放置区必须覆盖全部可见copy_id，`avoid` 区可以不承载文案。`overlay_policy` 只能是 `none|local-scrim|local-support-surface`，不得暗示整页卡片。字段记录专业观察，不能只由自动分数生成。

## 资产策略

```json
{
  "template_mode": "derive-not-clone",
  "icon_policy": "semantic-only",
  "required_roles": ["渠道", "动作"],
  "candidate_asset_ids": ["ICON-PUBLIC-042"],
  "selected_asset_ids": ["ICON-PUBLIC-042"],
  "selection_rationale": "Icon比重复标签更快区分渠道",
  "family_consistency": "single-family",
  "license_records": [
    {"asset_id": "ICON-PUBLIC-042", "source": "配置的资产注册表", "license": "MIT", "attribution_required": true}
  ],
  "never_copy": ["参考文案", "参考品牌身份", "参考Master或Layout坐标"]
}
```

已选资产必须是已审阅候选的子集，并且每项恰有一条来源与许可记录。`family_consistency` 为 `single-family|intentional-mix|not-applicable`。权利不明的资产不能入选；若字体、原生形状、图表或表格更清楚，空选择也是有效结论。

## 语义布局树

```json
{
  "tree_id": "SLT-S03-B",
  "mode": "hierarchical",
  "root_node_id": "N0",
  "nodes": [
    {"node_id": "N0", "parent_node_id": null, "node_type": "canvas", "semantic_role": "页面画布", "region_id": null, "copy_ids": [], "shape_family": "none", "reading_order": 0},
    {"node_id": "N1", "parent_node_id": "N0", "node_type": "intent-zone", "semantic_role": "主证据", "region_id": "R-MAIN", "copy_ids": ["S03-C01"], "shape_family": "chart", "reading_order": 1}
  ],
  "relations": [],
  "checks": {
    "single_root": true,
    "all_copy_ids_covered_once": true,
    "hierarchy_explains_grouping": true,
    "reading_order_explicit": true,
    "shape_choices_semantic": true,
    "no_flat_card_default": true
  }
}
```

`mode` 只能为 `flat|hierarchical`。根节点之外的 `region_id` 引用 `area_plan`；节点中的copy_id按Copy顺序恰好覆盖一次。关系类型只可为 `contains|peer|sequence|cause|condition|supports|compares|feedback|anchors`。树不得重复原文或精确坐标：原文与渲染目标仍以 `copy_unit_map` 为唯一真值，区域几何仍以 `area_plan` 为唯一真值。形状家族可为 `none|rectangle|rounded-rectangle|ellipse|path|line|table|chart|image|text|mixed`，不得把矩形当默认容器。

## 系列、母题和留白

`series_visual_contract`：

```json
{
  "series_id": "SER-Q",
  "behavior": "locked-backbone",
  "persistent_elements": ["Q1-Q4时间底板", "短期战役底座"],
  "logic_change_repeated": "新增第三阶段及本周期分析判断",
  "progressive_change": "显影Q3节点并高亮当前季度，其余季度保持原位",
  "allowed_variation": ["当前季度强调", "新增数据和注释"],
  "sequence_reference_ids": ["SEQ-DEMO-QUARTERS"],
  "break_reason": ""
}
```

`behavior`：`standalone`、`locked-backbone`、`controlled-variation`、`series-break`。Logic无 `series_id` 时只能用 `standalone`；有系列时必须使用后3种。`series-break` 只用于Logic的 `series_role=break`，必须说明退出理由。

`semantic_whitespace.mode`：`none`、`future-space`、`unknown-space`、`pause`。非`none`时必须有至少一个区域、具体叙事职责，且 `protected_from_filling=true`。空白只是排不满时使用 `none`，并在面积计划中重新分配。

`persistent_context_rail.enabled=true` 时只允许长稿或连续系列，`max_area_percent` 必须在1至8之间；关闭时为0。导航不得成为第一视觉或UI面板。

## 数据图表合同

数据图表页的 `medium_execution_contract.data_chart_contract` 至少包含：

```json
{
  "chart_type": "scatter",
  "audience_text_min_pt": 12,
  "even_point_sizes_only": false,
  "direct_label_policy": "all-entities",
  "entity_label_field": "entity_name",
  "point_connection_policy": "markers-only",
  "semantic_lines": [],
  "label_collision_strategy": ["offset", "leader-lines", "facet-or-split"],
  "unlabeled_point_exception": null
}
```

- 散点图 `direct_label_policy` 必须为 `all-entities`，实体名称直接贴点或用标签—点引导线，不得只靠图例、编号或颜色反查。
- 散点图 `point_connection_policy` 只能为 `markers-only` 或 `semantic-lines-only`。不同实体默认不连线；点的输入顺序不构成业务关系。
- `semantic-lines-only` 时，每条线必须记录 `line_id`、`meaning` 与 `visible_label`。目标线、100%线、中位数线、统计拟合线、等值线、同一对象时间轨迹等可以使用；装饰线和默认折线不可使用。
- 标签碰撞优先通过错位、标签—点引导线、扩大图域、分面或拆页解决。引导线只连接标签与对应点，不得被误作实体间关系。
- `unlabeled_point_exception` 默认必须为 `null`。确需不显示个别实体名时必须回流并取得用户明确批准，不能由Output自行决定。
- 非散点图仍须满足12pt图表文字下限和偶数字号规则；`direct_label_policy` 可根据比较任务使用 `key-values` 或 `as-needed`。

`deck_rhythm` 额外包含：

- `series_groups`：逐项重复Logic系列身份、页面和行为；
- `motif_sequence`：按页记录母题ID或`null`；
- `motif_contracts`：每个母题的目的、建立页、复现页、局部变化规则、打破页和打破理由；
- `semantic_whitespace_slide_ids`；
- `purposeful_repetition_review`：确认系列重复有业务目的、非系列同构有打破策略。

验证器会实际核验轮廓和密度连续重复上限、主媒介多样性、底部结论带占比、内容特定首要视觉以及非系列结构复用。“主图”“主表”“结论结构”等只是占位词，不能作为首要视觉决策。

## A/B候选

每个候选至少记录：

```json
{
  "candidate_id": "B",
  "silhouette_family": "full-width-evidence",
  "first_visual": "主趋势图",
  "main_backbone": "趋势→驱动→动作",
  "reading_path": "left-to-right",
  "area_plan": [],
  "reference_ids": ["REF-DEMO-015"],
  "risk_notes": [],
  "semantic_tree_signature": "主趋势图包含两层驱动，动作锚定右下",
  "prototype_file": "greybox/S03-B.png"
}
```

高风险页必须恰有两个候选；普通页至少保留一个已锁定候选。选择结果必须与页级轮廓、第一视觉和面积计划一致。

高风险页的 `ab_review.visual_self_correction` 必须记录：`required=true`、`max_rounds=2`、1—2轮原型渲染、五维观察、`preserve`、`change`、候选差异状态、自动信号的 `diagnostic-only` 角色、以 `professional-visual-judgment` 为最终选择依据和明确停止理由。五维为制作完整性、文字可读性、注意层级、结构语义、构图任务适配。若两者均不足，可在前一轮标为 `both-insufficient-rebuild`，但最终轮必须形成可批准选择；不得按融合总分自动选版，不得让两个候选收敛成同一壳，不得超过两轮。

## 锁

`art_direction_lock` 的以下字段全部为 `true`：

- `composition_locked`；
- `silhouette_locked`；
- `dominant_medium_locked`；
- `density_locked`；
- `reading_path_locked`；
- `copy_mapping_locked`。
- `series_behavior_locked`；
- `motif_locked`；
- `semantic_whitespace_locked`；
- `context_rail_locked`。
- `semantic_layout_tree_locked`。
- `content_aware_canvas_locked`；
- `asset_strategy_locked`。

Art Direction更新后，旧PPTX、Output QA和Supervisor报告全部失效。
