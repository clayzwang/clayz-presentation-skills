# 研究成果、内容结构与呈现结构交接 — v0.17.4

新任务使用内容包 `3.2`、Art Direction 计划 `2.0`、交接扩展 `1.2`。历史 2.4/3.0/3.1 按原版本和职责兼容读取，不可只改版本号。五阶段、校准、Independent Auditor、配置、资源盘点、Index 与真实工作记录继续保留。

## Logic：研究与研究成果

Logic 调查研究对象，交付不依赖页数或版式的完整研究报告。先回答证据支持什么、依据是什么、有哪些反证或其他解释、意味着什么、哪些仍未知。研究结论归 Logic；演示文稿结论的措辞与位置归 Copy。研究成果不能只是待办清单，也不提前写成幻灯片标题、固定章节和页序。保留理解与复核所需的细节。

根字段 `research` 包含 research_question、scope、summary、findings、data、sources、glossary、metric_dictionary、open_items、invariants。每项 finding 含 finding_id、question、完整 text、claim_status、source_ids、qualifiers、must_preserve、data_ids。可按研究主题整理，但数组顺序不规定演示顺序。sources 绑定 source_id、已选 resource_id 和 locator；事实、计算须有来源。data 保留 data_id、metric_name、display_value、raw_value（缺失时 null）、unit、period、definition_ref、source_ids、evidence_status，计算与限制可复核。

Logic 批准时 logic_layer、copy_layer 均为 null，story 缺省或 null。Logic 不分页、不写上屏标题、不规定演示章节、封尾页或结论页。用户已有的页数与演示要求保留在 brief/acceptance 中供 Copy 执行；研究主题名称和实质研究结论仍允许，禁止的是把页面组织字段塞进研究报告。

## Copy：内容结构与适合 PPT 的文字

Copy 先读完整研究，写出可独立理解的自然中文，再决定演示章节、页面职责、页数、页序、标题、开场、结尾与上屏结论。交付物是文字和内容结构，尚不是 PPT 成品或视觉设计。Copy 可合并、拆分、重排研究内容，改写措辞和分组，须守住事实、判断强度、限定条件、必要信息与用户约束。不得为排版删掉关键解释或加强结论。

logic_artifact 以绝对路径、sha256、bytes 绑定真实 Logic 文件。research、brief、acceptance、inventory、包身份/版本、配置与运行绑定原样保留。copy_layer 使用 pagination_owner: "copy"、research_sha256、logic_version、自行组织的 chapters（chapter_id/title/purpose）、chapter_order、semantic_preservation_review 和有序 slides。为兼容现有渲染器保留 logic_layer 字段，但它现在是 **Copy 创建的页面投影**，必须标记 owner: "copy"，Logic 交接中不得存在。投影 slides 含 slide_id、chapter_id、narrative_role、完整页面主张 claim、source_finding_ids 和从 research 原样引用的 data；lock.slide_order_locked 锁定 Copy 批准的页序。

每个 Copy 页面含 slide_id、title_copy_id、可选 storyline_copy_id、footnote_copy_ids、copy_units。可见单元含唯一 copy_id、text、role、text_mode、source_finding_ids、parent_copy_id、sibling_group_id、非负 logic_level、order、render_separately:true、merge_with_children:false、intentional_line_breaks。它们表示内容关系，不规定视觉排布。自然完整句可作为一个单元，不强迫对仗口号，不切碎因果解释。必保研究成果应进入正文，不能只放备注。semantic_preservation_review 应记录具体句子与覆盖/限定的实际判断，不能只写“字段已齐全”。

Copy 可按页发出 presentation_requests：request_id、kind（table/chart/logo/ordinal/image/diagram/other）、语义 purpose、相关 copy_ids/data_ids。允许指令添加表格、图表、Logo、序号等，说明表达目的；最终坐标、图表编码、具体素材与视觉形状仍由 Art 决定。Art 对请求记录 accepted/adapted/declined 与理由，用户明确要求仍须遵守。

封面与尾页默认要求由 Copy 执行。分页、章节顺序、标题、结论措辞、分组调整回 Copy，含义不变无需重做研究；新增事实、计算、研究判断或证据缺口回 Logic。不主动生成演讲备注/附录。Storyline 仅在用户所选母版明确要求时为必需。

## Art Direction：呈现结构

Art 决定内容用段落、表格、图表、结构图等怎样呈现，以及分组、阅读路径、视觉层级、配图、Logo 和序号。即使 Copy 未发指令，Art 也可依据已批准数据与受治理素材主动选择。内容关系须保真，但不等于一个内容组必须画成一个框，文字列成行列也不强制最终画成表格。每页以 presentation_request_resolutions（request_id/status/reason）回应 Copy 的请求。

新增 Logo、装饰序号属于呈现决策；序号不得暗示无依据排名或步骤，Logo 不得暗示无依据合作关系。图表刻度、单位和图例应由已批准数据与定义推导。新增解释文字回 Copy；新增事实、计算和判断回 Logic；重新分页回 Copy。Art 不自行改写文案或生成最终 PPTX。

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

3.2 包不必提供 `storyline_single_line` QA 检查；已有检查仍按其状态与证据规则读取，2.4／3.0 校验保持不变。仅承接用户所选母版的明确 Storyline 约束。

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
历史内容包 2.4、3.0、3.1 按原版本兼容读取；v0.17.4 新任务使用 3.2/2.0，不以兼容替代新交接。校验器证明绑定与覆盖，专业审阅判断论证、措辞、可读性和设计质量。
