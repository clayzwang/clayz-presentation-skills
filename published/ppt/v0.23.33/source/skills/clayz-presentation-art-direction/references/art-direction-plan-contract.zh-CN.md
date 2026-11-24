# Art Direction 计划 2.3

本版同时遵循[内容关系与逐页艺术规划](../../../packages/contracts/page-planning.zh-CN.md)：Copy 明确正文归属与标题关系，Art 在对象规格前保存逐页统筹规划，审计检查规划及实际呈现。


新任务遵循[研究与视觉交接](../../../packages/contracts/story-visual-handoff.zh-CN.md)。
绑定合同版本 2.3、内容包版本 3.4、任务身份、批准状态、验收合同、
资源签名、communication_contract 和真实索引证据。
art_direction.approval 保留 status 与 approved_by。

reference_research 记录学习包是否可用、learning-first／web-first／autonomous 策略、
实际来源 locator/use 与说明。学习包可用时优先查它；
没有匹配或无法联网可以原创设计，轻量包不带 Art 设计索引或版式库。

slides 保留 Copy 页面顺序；reading_sequence 是 Art 自主定义的视觉阅读顺序，
完整覆盖文案 ID。medium_execution_contract 自由描述结构与实际对象要求。
设计意图、面积、母题、布局树等按当前设计需要记录。
不再有 atomicity_review、父子目标匹配或同级同样式要求。

copy_unit_map 每项标识 copy_id、render_target_id、target_type、native_location。
同一个原生对象可以接收多个文案 ID，使用不相交的 text_range:[start,end) 字符区间。
shape_name 标識实际对象；表格单元格另有从零开始的 row/column，
图表另有 label_kind 与需要的 series_index/point_index。
目标对应 visual_baseline 的 element_id 和 copy_ids。
样式与阅读顺序不机械继承文字级别或数组位置。

使用真实文字制作并检查全部可读图片稿，与坐标、字体、对象、数据、
素材及技术容差一起锁进 visual_baseline，再交 Output。
用 stage_documents.py lock-design 锁定，最终 PPTX 制作仍属于 Output。

每个 visual_baseline 元素表示一个原生编辑对象，声明唯一 native_name 和
render_separately:true；映射里的 shape_name 与该名称一致。
一个 Art 对象仍可以承载多个 Copy ID。按独立选择、移动、宽度或格式调整的
实际需要划分对象；需要整体移动时，用原生分组保留可分别编辑的子对象。
可选 native_group_path 按从外到内列出原生组名，省略表示不分组。
Output 必须保留对象、原生类型和准确分组，不得擅自合并、拆分、改组或拍平。
这些要求属于 Art 对象，不属于 Copy 段落。旧 2.1 仅按原合同回读。
