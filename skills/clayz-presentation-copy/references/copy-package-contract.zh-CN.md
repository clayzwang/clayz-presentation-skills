# PPT v2.1文案层合同

Copy 在状态为 `logic-approved` 的同一 `ppt-design-package.json` 中追加 `copy_layer`。完成后根状态为 `copy-approved`；`logic_layer` 不得发生任何变化。

## copy_layer

```json
{
  "logic_version": "2.1.0",
  "cross_slide_copy_contract": {
    "invariant_renderings": [
      {
        "invariant_id": "INV-SEGMENT-ORDER",
        "visible_terms": ["试用用户", "活跃用户", "协作团队", "企业账户"],
        "order_locked": true,
        "aliases_forbidden": ["A类", "B类", "C类", "D类"]
      }
    ],
    "series_copy_strategies": [
      {
        "series_id": "SER-MAP",
        "stable_language": "固定用户阶段名称和顺序",
        "progression_language": "每页标题明确新增的分析层和判断",
        "repetition_rule": "重复只服务横向映射，不复制空泛句式"
      }
    ]
  },
  "slides": [],
  "lock": {
    "titles_locked": true,
    "storylines_locked": true,
    "visible_copy_locked": true,
    "copy_hierarchy_locked": true,
    "numbers_locked": true,
    "punctuation_locked": true,
    "intentional_line_breaks_locked": true,
    "speaker_notes_locked": true,
    "title_modes_locked": true,
    "narrative_functions_locked": true,
    "cross_slide_copy_locked": true
  }
}
```

`logic_version` 必须与根 `version` 一致。若 Logic 更新版本，旧 `copy_layer` 自动失效。

## 逐页文案

```json
{
  "slide_id": "S03",
  "title_mode": "action-directive",
  "storyline_function": "action-bridge",
  "audience_transition_copy_strategy": "先重申已确认差距，再说明两项动作如何被检验",
  "title_copy_id": "C-S03-01",
  "storyline_copy_id": "C-S03-02",
  "copy_units": [
    {
      "copy_id": "C-S03-01",
      "text": "下一阶段改进：同步优化上手引导与权限设置",
      "role": "title",
      "text_mode": "sentence",
      "source_logic_node_ids": ["N00"],
      "logic_level": 0,
      "parent_copy_id": null,
      "sibling_group_id": null,
      "grammar_signature": "judgment-sentence",
      "order": 1,
      "render_separately": true,
      "merge_with_children": false,
      "intentional_line_breaks": []
    },
    {
      "copy_id": "C-S03-02",
      "text": "围绕上手引导和权限设置两条并列路径推进改进。",
      "role": "storyline",
      "text_mode": "sentence",
      "source_logic_node_ids": ["N00"],
      "logic_level": 0,
      "parent_copy_id": null,
      "sibling_group_id": null,
      "grammar_signature": "storyline-sentence",
      "order": 2,
      "render_separately": true,
      "merge_with_children": false,
      "intentional_line_breaks": []
    },
    {
      "copy_id": "C-S03-03",
      "text": "改进",
      "role": "group-label",
      "text_mode": "label",
      "source_logic_node_ids": ["N01"],
      "logic_level": 1,
      "parent_copy_id": "C-S03-01",
      "sibling_group_id": "G-ROOT",
      "grammar_signature": "action-category",
      "order": 3,
      "render_separately": true,
      "merge_with_children": false,
      "intentional_line_breaks": []
    },
    {
      "copy_id": "C-S03-04",
      "text": "优化上手引导",
      "role": "item",
      "text_mode": "list-item",
      "source_logic_node_ids": ["N02"],
      "logic_level": 2,
      "parent_copy_id": "C-S03-03",
      "sibling_group_id": "G-IMPROVE",
      "grammar_signature": "verb-object",
      "order": 4,
      "render_separately": true,
      "merge_with_children": false,
      "intentional_line_breaks": []
    },
    {
      "copy_id": "C-S03-05",
      "text": "明确权限默认值",
      "role": "item",
      "text_mode": "list-item",
      "source_logic_node_ids": ["N03"],
      "logic_level": 2,
      "parent_copy_id": "C-S03-03",
      "sibling_group_id": "G-IMPROVE",
      "grammar_signature": "verb-object",
      "order": 5,
      "render_separately": true,
      "merge_with_children": false,
      "intentional_line_breaks": []
    }
  ],
  "node_copy_map": [
    {"logic_node_id": "N00", "primary_copy_id": "C-S03-01", "supplemental_copy_ids": ["C-S03-02"]},
    {"logic_node_id": "N01", "primary_copy_id": "C-S03-03", "supplemental_copy_ids": []},
    {"logic_node_id": "N02", "primary_copy_id": "C-S03-04", "supplemental_copy_ids": []},
    {"logic_node_id": "N03", "primary_copy_id": "C-S03-05", "supplemental_copy_ids": []}
  ],
  "footnote_copy_ids": [],
  "speaker_notes": [
    {"note_id": "NOTE-S03-01", "text": "先讲总类，再分别解释两项行动。", "source_ids": []}
  ],
  "series_copy_review": {
    "series_id": null,
    "invariant_terms_preserved": true,
    "object_order_preserved": true,
    "new_information_explicit": true
  }
}
```

`title_mode`：`cover`、`factual-status`、`analytical-judgment`、`mechanism-rule`、`action-directive`、`transition-assertion`、`instructional-action`、`closing`。

`storyline_function`：`none`、`evidence-bridge`、`mechanism-explanation`、`action-bridge`、`audience-transition`、`instruction-bridge`、`scope-qualification`。封面与尾页使用 `none`；普通正文不得使用 `none`。

`series_copy_review.series_id` 必须与Logic一致。非系列页使用 `null`，但三个检查仍写 `true`，表示没有制造跨页漂移；系列页必须能从标题、Storyline或正文识别本页新增认识。

## 原子单元规则

- `copy_id` 在整稿唯一；`text` 非空且是最终锁定文字。
- `source_logic_node_ids` 非空，只引用本页逻辑节点。
- `logic_level` 与所映射主节点层级一致；补充文案可映射同一节点，但不能冒充新层级。
- `role`：`title`、`subtitle`、`storyline`、`group-label`、`item`、`evidence`、`data-label`、`data-value`、`data-unit`、`annotation`、`footnote`、`closing`。
- `text_mode`：`sentence`、`label`、`list-item`、`label-value`、`dialogue`、`quote`、`note`。
- `render_separately` 必须为 `true`；`merge_with_children` 必须为 `false`。这里的“分别渲染”指每个 `copy_id` 有独立、可追踪的子目标，不预设独立文本框、矩形或卡片；多个目标可以属于同一表格、时间节点、泳道、图表或组合容器。
- `intentional_line_breaks` 是字符索引数组；没有主动断句时为空。不得在 `text` 中直接混入换行符。
- 禁止 `|`、`｜` 或连续三个以上空格模拟分栏。

## 节点映射规则

- `node_copy_map` 恰好覆盖本页全部逻辑节点一次。
- 每个节点有且只有一个 `primary_copy_id`；不同节点不得共享主文案。
- `primary_copy_id` 的 `source_logic_node_ids` 必须只包含对应节点。
- 父节点主文案不得包含任一子节点主文案的完整文本。
- 子节点主文案的 `parent_copy_id` 必须等于父节点的 `primary_copy_id`。
- 同一逻辑兄弟组的主文案必须保持相同 `sibling_group_id`、`grammar_signature`、`role` 和 `text_mode`；确有语义差异时应先在 Logic 中拆组。

## 页面特例

- 封面允许 `title_copy_id` 和可选 `subtitle`，`storyline_copy_id` 可为 `null`。
- 尾页使用 `closing`；具体文字由本次任务的用户要求或批准文案决定，不得由框架、主题或历史案例预设。
- 正文页必须有标题和单句Storyline；Storyline不得含主动换行。
- 低内容负载、高决策重量的转场页允许没有常规正文清单，但必须用 `transition-assertion` 与 `audience-transition` 真实推动受众状态。
- 高密度分析页标题允许两段式表达和主动断句，不得为了单行缩小字号；断点仍通过字符索引锁定。
- 系列页不得改写 `invariant_renderings.visible_terms` 的名称与顺序；如业务确需别名，必须回流Logic修改不变量。
- KPI的标签、显示值和单位使用三个独立 `copy_id`，由 Art Direction 映射到同一组合容器的不同子对象，再由Output执行。
- 演讲者备注不进入 `copy_units`，不得被Art Direction或Output显示到页面。
