# 原生制作检查与专业判断

本说明整理已实际使用的原生制作方法，保留既有文件名以兼容调用。技术核验检查对象、字节、引用和实际观察；知识帮助形成设计判断。两者都不自动证明读者理解或审美效果。专业学习的方向见 [Art 设计工作流](art-design-process.zh-CN.md)，知识包独立存储和标识版本。

## Art 与编码

1. 先通过标题和全文的独立首读，再分析页面比较、包含、机制和限定关系。数值应能在带期间、单位、定义的共同基线上核对。多组同比或现金桥不能因为正文完整就省略关系表达；必要时重新分页，保留全部研究。
2. `packages/layout/semantic_table.py` 负责实际字体测量、语义列、右对齐数字、内边距与合计行；Art明确选择表宽。容量不足必须改结构，不能静默缩小字号。`financial_flow.table_capacity` 计算说明和来源区之外的表格容量。
3. `knowledge_text.load_terms` 实际加载知识包 finance-terms.json；`knowledge_policy.load_policy` 加载 layout-policy.json 并校验字体文件SHA。回执记录参数和文件哈希。当前1.06宽度余量及10.8pt页脚净空仅来自本次STKaiti/LibreOffice观察，不是通用字体或美学模型。
4. 通过 `authoring_text.measure_lines` 与 `text_flow.wrap` 保持数值、日期、英文标识、标点和指定短语。Art可明确指定少量完整数字强调（inline_emphasis）或完整词组不拆行；不能自动把所有数字加粗。标签和金额关系仍需实际观察。
5. `page_capacity.inspect` 检查页面底部annotation区域的净空。页面内未越界不能证明页脚不挤压；几何框相交也不能直接证明字形墨迹遮挡。表上caption不是页脚。
6. 使用 `scripts/render_native_preview.py` 实际重开原生样稿。批准基线必须来自当前原生文件的渲染及绑定记录；PIL草图不能证明原生加粗、字体、链接、换行或容量。
7. 使用 `scripts/audit_native_glyph_bounds.py <PDF> <design-elements.json> --output <report.json>`。它按精确文本和二维空间检查普通文字及表格完整单元格框，明确匹配、表格行、未匹配和超界。完整单元格框不等于内边距检查，也不证明墨迹形状、语义或层级。未匹配不能当通过。

## Output 与审计

- 原生文字/对象、实际字体、PDF文字、文件体积及渲染证据分别验证。`release_evidence.inspect` 在装配正式QA前拒绝失败、缺失或绑定旧PPT/PDF的技术报告。
- `visual_evidence.validate` 要求每页首眼重点、层级、比较、间距、可读性、内容表达六类实际观察，并绑定当前最终PNG和PPTX。fail、unreviewed、缺图、错图或哈希不符阻止放行。比较不适用应说明原因；不能用“内容正确”替代视觉观察。
- 最终读者首次只看真实成品图，冻结理解后才看批准Copy和Art。正面观察放understanding，findings只写问题；有问题用understanding-gaps。第二次对照的art_changes审计实际文案变化，不填写未来修复建议。保留失败和格式修复，不重写旧首读。
- 审计报告区分原审计明确发现、作者首眼发现、独立读者发现、机器几何检查和未观察的应用范围。无发现不是无需改进；发现的归属、影响及处理证据必须可复查。
- 本次目标应用实际观察限LibreOffice；PowerPoint/WPS未执行时明确限定，不能写成全应用通过。Root同上下文执行的Auditor模块必须披露该限制，不能冒称独立审计主体。

具体作品的修法、环境校准、误报与纠正保留在相应实践记录中。知识主干积累可迁移的专业理解；历史案例的效力限于各自情境。报告正文应让读者看见实际制作问题、处理方式及证据范围，不能只在证据文件名中暗示这些历史。
