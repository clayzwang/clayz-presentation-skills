# 完整故事与图片稿交接 — v0.17.0

所有新任务读取本契约。使用内容包 `3.0`、Art Direction 计划 `2.0`、交接扩展 `1.0`。
五阶段、Supervisor 三次校准、Independent Auditor、任务要求、Library/Index、配置与发布权保持原有机制。

v0.17.1 同时遵循[内容充分与自然表达](reader-quality.zh-CN.md)：先把分析展开，再改写为读者能理解的文字；必要解释可以较长，由排版妥善容纳。使用已有阶段观察和发现记录，不新增字段、字数门槛或审批环节。

## Logic：先把完整论述写成立

产出可脱离 PPT 阅读的完整论述：主旨、开篇、各章节的实际段落、证据、机制、限定条件、过渡和结论。
可以按历史、诊断、比较、提案等适合任务的方式组织，不强制时间线，也不能以目录、标题列表或字段标签代替故事。

Logic JSON 保留包身份、版本、状态、acceptance_contract、brief、resource_inventory、approvals 和 index_evidence。
`contract_version` 为 `3.0`；`logic_layer`、`copy_layer` 均为 null。权威内容放入 `story`：

- `title`、`thesis`、`audience`、`desired_outcome`、`opening`、`conclusion`；
- `sources` 沿用来源 ID、选中资源 ID 和 locator；保留 `glossary`、`metric_dictionary`、`open_items`、`invariants`；
- 有序 `chapters`：各章包含 `chapter_id`、`title`、`purpose`、完整 `blocks` 和 `transition`；
- 每段包含稳定 `story_id`、完整 `text`、`claim_status`、`source_ids`、明确 `qualifiers` 及布尔 `must_preserve`。

数字、计算及证据沿用原有口径与证据机制。Logic 决定论证和章节顺序，不锁死分页。
用户明确的页数等约束交由 Copy 落实。Copy 开始前保存并记录真实 Logic 修订，不能事后从成品补写。

## Copy：分页并转化为演示文字

阅读全文，决定分页、单页职责、标题和正文层级、精简和语言节奏。对仗、平仄、口号是可选手段，准确清楚优先。
文字的平行结构归 Copy，空间对齐归 Art Direction。可以拆页、合并展示单元，但不能改变事实、结论强度、限定条件、章节顺序和论证关系。
实质内容变化回传 Logic。

Copy 保留原始 `story`、`brief`、任务要求、来源盘点及包身份。`logic_artifact` 使用任务内绝对路径及 `{path, sha256, bytes}` 指向真实 Logic 文件。
`copy_layer` 增加 `pagination_owner: "copy"`、规范 JSON 的 `story_sha256`、`chapter_order`、实质 `semantic_preservation_review`。
每个文字单元及备注都添加非空 `source_story_ids`。必保段落必须映射到可见文字或明确备注；不能为了字段通过把必要的可见限定条件藏进备注。

兼容既有渲染器时，Copy 在分页后填充旧名 `logic_layer`，其含义是 **Copy 负责的派生页面语义投影**：页面 ID、单页观点、数据与关系、message tree、页序和跨页约束等。
其中 sources、glossary、metric_dictionary、open_items 与 story 完全一致。页面锁从 Copy 批准时开始。
该字段绝不是原始 Logic 交接文档，不转移事实与推理责任；具体字段沿用旧 v2.4 参考。

## Art Direction：整套图片稿与一致的视觉规格

根据真实 Copy 先形成整套逐页图片稿，展示第一视觉、分组、层级、关系、阅读顺序、媒介和跨页节奏，再据此细化规格并反复核对。
封面、正文、尾页均要有真实可读 PNG/JPEG，文字、数字、关系必须正确。不要求原生对象或最终交付分辨率，但不能用空白、缩略示意图或近似文案冒充设计基准。
逐页检查可读性，固定像素尺寸和相似度分数不能代替判断。

可用绘制、渲染或生图工具；使用生图时必须纠正文案和图表错误。事实和文字继承上游，不从像素重新猜测。
全套图片稿是必交内容，不依赖可选 A/B 能力。工具无法生成时如实报告缺口，不改走旧文字稿路线。

计划 `2.0` 保留原有语义设计字段，增加 `visual_baseline`：

- `status: "locked"`、带时区 `locked_at`、`copy_package_sha256`、`spec_sha256`（整个计划去掉 visual_baseline 后的规范 JSON 摘要）；
- 按 Copy 页序排列的 `slides`：`slide_id`、实际 `image` 文件引用、`first_visual`、`reading_path`、`legibility_review`、`copy_and_data_review`、`spec_consistency_review`、`elements`；
- 每个元素有 `element_id`、`kind`、用途 `purpose`、`copy_ids`、归一化 `[x,y,w,h]` 的 `box`、`native_type`、`group_id`、`alignment`、`locked_properties`、有界 `allowed_adjustments`；
- 文字的 `typography` 必含已解析字体 `font_family`、`size_pt`，并记录必要的颜色、字重和间距；图表绑定 `chart_type`、批准的 `data_ids`；图片与 icon 有真实受治理 `asset_ref`，需要时补充裁切；新增符号、装饰同样有 ID；
- 每个可见 copy_id 精确映射一次，图表内文字也不能遗漏。

可复用构图模式保持语义描述；**本次任务的规格**由 Art Direction 决定目标坐标、字号与微调范围，沿用当前主题和母版。
新增文字回传 Copy，新增计算或结论回传 Logic。使用 `scripts/stage_documents.py lock-design` 生成新锁定文件，再通过既有校验和工作记录交接。
Output 开始前锁定图片稿与规格。设计变化生成新修订并使受影响的 Output/审计证据失效，禁止拿成品反改图片稿消除偏差。

## Output：忠实实现原生 PPT

先读图片稿和规格，在 QA 记录 `output_started_at` 与 `visual_baseline_sha256`。
按既定设计制作可编辑文字、数据图表、表格及结构图对象；照片仍可作为图片。整页截图不是原生实现。
记录允许范围内的技术微调，超出范围的层级、构图或内容变化回传上游。实际重新打开最终文件并渲染；不可用时保留明确延后状态。

## Supervisor：设计稿与成品逐页审计

保持原有校准、独立审计及发布交接。报告草稿的 `design_comparison` 绑定基准摘要、实际最终 `pptx_sha256` 和有序 slides。
每页绑定 `slide_id`、`preview_sha256`，并记录：

- 已审阅：`status: "reviewed"`、真实 `final_render` 引用、`rendered_from_pptx_sha256`，以及 content、visual_fidelity、native_editability、design_quality 四类检查；每类含结果和实际观察，失败或不确定项关联报告 issue_ids 与 earliest_owner；
- 最终渲染不可用：`status: "deferred"` 与明确 reason；不能据此免除 Art Direction 图片稿，也不能声称 clean 或视觉通过。

原生性必须检查真实对象。忠实复现坏设计仍是 Art Direction 问题；原始责任与下游漏检分开记录，不改写独立审计结论。
相似度不能替代内容、设计和实现质量判断。

`assemble-report` 自动从真实原始 Logic、最终 Copy、Art Direction 计划生成 `stage_documents`，同时嵌入完整数据、同源可读 Markdown 和锁定图片字节；最终渲染字节随对照记录保存。
既有原子发布器继续交付 PPTX/报告，并导出 `stage-handoff.zip`：三份文档、图片和可离线查看的并排对照 HTML。
旧版 2.4/1.7 可读，不允许新任务借兼容绕过 3.0/2.0 必交内容。校验器证明绑定与覆盖，专业审阅判断论证、措辞、可读性和设计质量。
