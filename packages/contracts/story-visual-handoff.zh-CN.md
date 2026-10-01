# 完整故事、页面安排与图片稿交接 — v0.17.2

新任务使用内容包 `3.1`、Art Direction 计划 `2.0`、交接扩展 `1.1`。保留五阶段、校准、Independent Auditor、配置、资源盘点、Index 回执和真实阶段工作记录。

## Logic：完整故事与放置位置

`story` 保存完整实质论述：title、thesis、audience、desired_outcome、opening、conclusion、有序 chapters（chapter_id、title、purpose、blocks，transition 可选）、sources、glossary、metric_dictionary、open_items、invariants。每段包含 story_id、完整 text、claim_status、source_ids、qualifiers、must_preserve。事实和计算绑定选中资源与来源定位，保留口径和不确定性。

`logic_layer.slides` 按页序包含 slide_id、chapter_id、narrative_role、claim、source_story_ids、data。全部 story 段落都有放置位置，不提前剪裁。Logic 决定总论点、章节、逐页主张、页面职责和正文页数；`logic_layer.lock.slide_order_locked` 为 true，copy_layer 为 null。除用户明确省略，默认一页封面、一页尾页；具体文字由 Copy 决定。Art Direction 宜采用贴合内容的形象配图，按实际显示尺寸控制分辨率、裁切、压缩和体积，文字保持原生可编辑；整页图片不算原生生成。

工具不内置分析路线、父子推理合同或兄弟分组配额。方法来自任务、个人配置或选中外部知识。各阶段不主动生成演讲备注或附录；用户要求及历史备注仍可读取，研究与阶段工作记录保留。

## Copy：措辞、剪裁与内容打标

先读完整 story，保留原文和页面安排。logic_artifact 用绝对路径、sha256、bytes 绑定真实原始 Logic 文件。story、logic_layer、brief、acceptance_contract、resource_inventory、包身份原样保留。页数、顺序、页面职责或含义变化回 Logic；每页具体文字、剪裁和内容分组由 Copy 决定。

copy_layer 包含 logic_version、pagination_owner: "logic"、story_sha256、chapter_order、semantic_preservation_review 和有序 slides。每页含 slide_id、title_copy_id、可选 storyline_copy_id、footnote_copy_ids、copy_units。每个可见单元含全稿唯一 copy_id、text、role、text_mode、本页范围内的 source_story_ids、parent_copy_id、sibling_group_id、非负整数 logic_level（Copy 层级）、order、render_separately: true、merge_with_children: false、intentional_line_breaks。父级和组标记可为 null。Copy 自主分组和措辞，不依赖旧 Logic 节点映射；node_copy_map、source_logic_node_ids 仅为可选历史字段，不作为新任务要求。不新增语法或分组配额。必保信息应可见；已有备注须可追溯，不得用来隐藏必要限定条件。用 semantic_preservation_review 记录实际内容保真检查。

3.1 中 Art Direction 的 visual_layers.node_id 使用 Copy ID，page_message_tree_depth 记录 Copy 层级深度，logic_statement 绑定逐页 claim。内容密度、注意力分配由 Art Direction 判断，不再强制 Logic 打旧标签。copy_unit_map 和 semantic_layout_tree 承接 Copy 分组，visual_baseline 继续视觉打标，Output 负责实施。

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
历史内容包 2.4、3.0 按原版本兼容读取；v0.17.2 新任务使用 3.1/2.0，不以兼容替代新交接。校验器证明绑定与覆盖，专业审阅判断论证、措辞、可读性和设计质量。
