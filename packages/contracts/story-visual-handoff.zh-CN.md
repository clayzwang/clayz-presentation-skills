# 研究、干净文字与视觉交接 — v0.19.0

本版同时遵循[内容关系与逐页艺术规划](page-planning.zh-CN.md)：Copy 明确正文归属与标题关系，Art 在对象规格前保存逐页统筹规划，审计检查规划及实际呈现。


新任务使用内容包 3.4、Art 计划 2.3、Output QA 4.1、交接扩展 1.3。
五阶段、配置、真实证据、校准、工作记录和独立审计保持现有流程。
旧合同仅用于相应历史材料回读，不能改版本标签后当作新合同。

## Logic 与 Copy

Logic 交完整研究，不预分配页面。保留来源、发现、数据、事实强度、限定条件、
必要内容和跨页业务不变量。原有研究字段及来源规则保持有效；
Logic 批准时 logic_layer 与 copy_layer 均为空。

Copy 阅读完整故事，可改写、调整、拆分、合并、重组和排序。
负责内容编排、分页、页面顺序与结论措辞，保留真实含义。
绑定原始 Logic 文件与研究、任务、配置和证据。
copy_layer 包含 logic_version、pagination_owner:"copy"、research_sha256、
实际语义复核说明与 slides；每页有 slide_id、copy_units。
章节、页面职责 narrative_role、数据引用 data_ids、用户要求或历史备注按需保留。
logic_layer 仍为空，不再制作另一份 Logic 页面投影。
遵守用户明确要求及实际封面、结束页要求。

干净文字只分为：

- 标题 title：主 Storyline；
- 副标题 subtitle：次级 Storyline；
- 各级标题 heading：附正整数 heading_level；
- 正文 body；
- 注释 annotation：说明、限定条件、来源等。

每类都可以没有，层级可以跳级，标题下面不必有次级标题或正文。
每段只有 copy_id、text、role，各级标题另有 heading_level；
保留自然段落换行。数组顺序是文字编排，不能直接绑定视觉阅读顺序。
根级 copy_provenance 单独记录各 copy_id 的来源发现 ID；
保留必要内容的可追溯性，不向 Art 传递视觉指令。
语义保真需要实际阅读，来源链接或校验通过不能代替判断。

Copy 先组织问题、判断、证据与段落关系，再分配文字角色。逐句检查 Storyline
与证据是否对应，分清实体、期间和会计口径，避免重复报数。独立判断按需写局部
标题，连续解释可以不加；没有 heading 本身不是缺陷。按
[内容与自然表达](reader-quality.zh-CN.md)完成实际审读并使用已有语义复核记录。

Copy 不输出 columns/table/ladder/rows/flow、父子或同级分组树、
强制单独渲染、禁止合并、同级同样式、视觉阅读序号、强制换行、
句式签名或媒介请求。旧字段在 3.4 新任务中不适用。

## Art 与参考来源

Art 决定呈现结构、媒介、构图、分组、合并、视觉层级、字级、动线、空间与节奏。
columns/table/ladder 等仍然可以作为 Art 自主选择的设计。
多个文字段落可以放入一个可编辑对象；同级文字可以有不同样式和注意力权重。
保持真实业务顺序和含义，Copy 数组顺序不是视觉阅读命令。

轻量包不携带 Art 版式库、设计索引或布局索引。
有学习包时，优先查其相关索引、正文和视觉材料；覆盖不足可补充网络参考。
没有学习包时，优先依靠大模型设计能力主动从网上找适用布局与设计参考。
按当前内容和受众选择空间、平面、编辑排版、广告等领域的参考。
实际参考的借鉴结果记入现有工作记录；查到名称或写了回执不代表已经学习。

无匹配、浏览不可用或参考不足时可以自主设计，记录真实情况。
原创构图无需注册；不可编造来源、索引记录或声称借用了不存在的命名模式。
学习包如何编写、组织和包装不属于本次引擎版本范围。
看参考与复制素材的权限分开；在线参考查询不逐次审批，也不重启未变化的预检。

## Art 计划 2.3 与图片稿

保留包身份、acceptance_contract、resource_inventory_lock、
communication_contract、Provider 锁与真实来源证据。
reference_research 记录 learning_package_available、source_strategy、
实际 references 与 notes；策略为 learning-first、web-first 或 autonomous。
学习包可用时优先查学习包；没有参考、匹配或无法联网不会阻断原创设计。
不要求参考条数、命名版式或检索匹配。

每页有 slide_id、Art 自主定义的 reading_sequence、copy_unit_map、
medium_execution_contract。structure_type 自由描述，minimum_object_counts
记录实际对象要求；art_direction.approval 保留现有批准基准。
设计意图、面积、层级、布局树、母题、原型按设计需要记录，不设表单配额。

copy_unit_map 每项包含 copy_id、render_target_id、target_type、
native_location。原生对象类型只用于验证可编辑性，不限制版式。
多个 copy_id 可以共用一个目标；native_location 标识 shape_name，
表格单元格另有从零开始的 row/column，图表标识具体原生标签。
共用文本通过不相交的 text_range:[start,end) 字符区间定位；
文本体中的多个段落用换行连接。视觉顺序和样式由 Art 独立决定。
不再根据 Copy 检查父子目标相同关系、单独对象或同级样式一致。

每页制作并检查使用真实批准文字的可读 PNG/JPEG 图片稿。
全稿图片与视觉规格一致后才能交给 Output；
visual_baseline 保留锁定时间、Copy 与规格哈希、全部页面图片与实际观察。
每个 element 标识 element_id、kind/purpose、copy_ids、native_type、归一化坐标、
分组、对齐、实际字体字级、锁定属性及允许技术调整。
一个 element 可以对应多段文字；混合样式可用 text_styles 按文案 ID 说明。
图表绑定批准研究数据；图片和图标绑定真实且有权限的素材。
用 scripts/stage_documents.py lock-design 锁定，不能事后由最终 PPTX 补图片稿。

Art 同时决定原生编辑边界。每个 element 是一个独立原生对象，声明唯一
native_name 和 render_separately:true；该标志属于 Art 对象，不属于 Copy ID。
自然连续的正文仍可共用一个明确声明的文本框。需要独立选择、移动、宽度或
格式调整的内容，分别成为对象；需要一起移动时，用 native_group_path 从外到内
声明原生组名，并保留独立可编辑的子对象。省略路径表示不分组。
映射 shape_name 与 element.native_name 一致。编辑选择使用既有 purpose 和
work-notes 说明；旧 Art 2.1 保留按原版本回读。

## Output、Supervisor 与独立审计

Output 按 Art 的图片与规格制作可编辑对象，按原生位置与字符区间核对文案。
允许 Art 明确选择的文段共框、同级不同样式和自主阅读路径。
QA 4.1 去掉 atomic_copy_separation、parent_child_hierarchy、peer_parallelism、
storyline_single_line、list_alignment 等继承 Copy 的规则；
脚本、QA 与 Supervisor 均不得重新引入。

保留文字、标点、大小写、数字、必要限定条件和用户明确要求。
选用表格时仍须完整原生表格；图表、字体、内部容量、最终回读渲染、
可编辑性及交付大小保持已有可靠性要求。

Output 必须保留 Art 声明的对象和准确分组，不得擅自合并、拆分、改组或拍平。
对象边界变化回 Art。最终 PPTX 比对和 QA 检查真实名称、原生类型与分组路径；
文字齐全不能单独证明编辑保真。

Supervisor 与 Auditor 检查遗漏、变义、不实关系、可读性失败与执行偏差，
不负责设计，不继承被删除的排版要求。
产出正确但平庸可以同时存在；提升设计仍是 Art 的责任。
不增加审美配额、挑战要求或额外审批。

Art 检查内容关系能否从实际页面理解；媒介造成的重复或原文分组含混交回 Copy。
Supervisor 同时审读文字与页面，不能只检查字号、文字完整或图片稿保真。
工具运行、记录完整性和实际质量按[验证结果解释](verification-outcomes.zh-CN.md)
分别判断，保留原始结果与后续核验。

保留真实三份交接文档、图片稿、最终 PPTX 对象证据与 design_comparison。
实际最终渲染、哈希和覆盖范围必须如实记录，缺少原生检查保留 deferred。
assemble-report 从真实材料生成完整报告和便携对照；
PPTX／报告发布对与 stage-handoff.zip 保持现有机制。
