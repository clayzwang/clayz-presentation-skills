# Copy语义图与Copy—Art接口 1.0

载荷`io.clayz.presentation.copy-graph/1.0`根字段仅为contract、research_report（path/sha256/bytes）、pages、nodes、connections、main_chain、semantic_review。不含字体、几何、栏数或画法。

pages为有序数组，每项`{id,role,storyline_id,node_ids}`；role为content/cover/closing。content恰有一个head level=1，storyline_id就是它；封面尾页storyline_id=null，有自己的framing标题且位于边界。main_chain按正文页序列出所有storyline编码。

页面编码与现有原生渲染器一致：ASCII字母或数字开头，后续为ASCII字母、数字、下划线或连字符（例如page_01）；不把标题正文或路径当编码。head_/body_编码同样使用字母、数字、下划线或连字符后缀。编码限制用于稳定引用和文件身份，不限制中文可见内容。

语义节点编码不使用双下划线`__`，该分隔符留给工具派生的原生表格位置，防止另一个body编码与数组技术位置冲突。技术位置不是新增Copy元素。

标题节点：`{id:"head_...",kind:"head",level:1,page_id:"...",text:"明确结论",source_spans:[...],claim_status:"fact"}`。正文节点：`{id:"body_...",kind:"body",level:2,page_id:"...",content:{type:"text",text:"完整正文"},source_spans:[...],claim_status:"interpretation"}`。两种节点同层可并存。body在storyline下从level=2开始。claim_status枚举fact/calculation/interpretation/guidance/uncertainty；单一节点若混合性质，文字须明确区分，必要时拆节点。

source_spans以原报告解码后的Unicode字符计数，半开区间`{start,end,operation,reason?}`。verbatim必须与原文完全一致；edited/derived/table-selection必须有具体reason。由研究段落中的明确数列生成数组用derived并说明转写、口径和限制，不能谎称原文存在表格；由原表选取用table-selection。每节点至少一个范围；不能凭引用范围宣称语义已保全。

计算范围使用原文件`read_bytes().decode("utf-8")`，不转换CRLF、不先改写原报告。`source-index --input INPUT --output INDEX`可返回原报告逐段文字及实际范围，供作者定位；它不编辑、分组或生成文案。

表格正文content：`{type:"table",values:[[...]],axes:[{name:"指标",labels:[...]},{name:"报告期",labels:[...]}],unit:"...",period:"..."}`。维数任意，标签对应每维。选取子集添加`selection:{original_shape:[...],axis_indices:[[...],...],reason:"..."}`。null保留为未提供，不能作零。表是一个Copy元素，技术文字位置不改变元素身份。

连接：`{id:"edge_...",sources:["head_a"],targets:["body_b"],types:["包含"],direction:"directed",scope:"page",meaning:"本结论包含以下机制及其必要条件"}`。direction=directed/symmetric；scope=main/page/cross-page/framing。15类型见Copy Skill。多源多目标是一个联合关系，不自动解释为每对端点独立成立；多条边用独立ID表达多个连接。main只连接相邻一级标题并保持顺序；额外跨页关系使用cross-page。

类型描述的是**源节点与目标节点之间**成立的关系，不能因为一个正文段落内部讲了流程，就把标题到该正文的连接标作流程。先读两端完整意思，写明联合/逐项作用，再选择类型。标题可能概括正文，也可能作为另一判断的证据，不能按head/body身份自动套边。meaning必须与端点、方向和每个类型一致。

有向类型采用明确语义：包含=源包含目标；因果=源因、目标果；递进=从源所述进一步到目标；时序=源先目标后；流程=源步骤到目标步骤；条件=源条件限制目标成立；分支=源分岔到目标分支；循环=源到目标为所述循环的一段；反馈=源结果返回并影响目标上游；依赖=源依赖目标前提；论证=源论据论证目标判断；支撑=源证据或解释支持目标判断。并列、对比、关联可为symmetric；若有向，meaning说明该方向的具体含义，不推导未证明的因果。多类型必须在同一方向上各自成立；反向关系另建边，不能以增加“关联”掩盖误标。类型语义和关系成立与否由实际阅读复核，结构校验不替作者裁定。

主链的线性顺序不自动构成递进、时序或因果。相邻标题是换观察角度、补充条件、比较、从事实到推断，还是同一判断的进一步展开，须分别核准两端主张；不能把“翻到下一页”的过程当作业务对象的流程，也不能用叙述推进批量标递进。确为关联时说明具体关联，而不把它当作掩盖其他误标的通用附加类型。

semantic_review包含storylines、information_preservation、selection_and_omissions、uncertainty、relations的实质复核。与process、原生读者及Auditor保存。字符范围、连通性、包含无环、标题层级和页数检查是结构检查，不是论证及设计质量结论。

## 实际登记命令

BRIEF仅含purpose（必填文字）、audience、pagination_requirements、wording_requirements；各项是文字或文字数组，不含研究、设计或运行配置。比如`{"purpose":"向非行业商业读者完整介绍公司","audience":"非行业商业读者","pagination_requirements":[],"wording_requirements":["保留期间、单位及必要限定"]}`。报告全文是唯一内容来源，其他专业要求归入这四个字段。

```text
python scripts/copy_graph.py prepare --report REPORT --brief BRIEF --output INPUT
python scripts/copy_graph.py main --input INPUT --payload MAIN --output MAIN_RECORD
python scripts/copy_graph.py heads --input INPUT --payload HEADS --previous MAIN_RECORD --output HEAD_RECORD
python scripts/copy_graph.py bodies --input INPUT --payload BODIES --previous HEAD_RECORD --output BODY_RECORD
# 下一页heads消费上一页BODY_RECORD；每页完整结束后再推进
python scripts/copy_graph.py assemble --last-record LAST --review REVIEW [--framing FRAMING] --output GRAPH
python scripts/copy_graph.py interface --copy-output GRAPH --output ART_INPUT --receipt RECEIPT
```

MAIN仅含pages、nodes（全部H1）、connections（全部相邻主链关系）、reading_review（非空文字，展开通读的范围、读者路径、标题判断和不确定性，不是布尔值或对象）。MAIN中的pages.node_ids暂时只列本页H1。HEADS为page_id/nodes（全部子标题按层）；BODIES为page_id/nodes/connections（本页所有具体逻辑关系）。FRAMING为pages/nodes/connections，只添加封面/尾页。最终REVIEW为五字段对象，每项均非空文字。所有记录使用真实时间及前置记录哈希，不覆盖历史。

接口`io.clayz.presentation.copy-art-interface/1.0`首版mode=identity，逐字节相等，不在载荷附加字段。回执绑定两文件和copy-graph/1.0。未来Copy内部可改，稳定载荷不能静默变更；不兼容显式升版及适配，不把适配判断交给Art。

Art设计文件`copy_structure_lock={interface:RECEIPT_FILEREF,graph_sha256:CANONICAL_GRAPH_HASH,authority:"presentation-only"}`；必须有`audit_observations:[]`或实际问题，每项node_ids/observation/impact/disposition="audit-only"。Art不得使用art_content、修改图、增删页、改文案、层级及连接或发起上游重写。呈现可调整空间、媒介、字体、视觉组合和阅读动线，不能凭空间暗示改变逻辑。真实不可满足的页面忠实记入报告。

真实原生预览CLI使用`render_native_preview.py PPTX --copy-graph ART_INPUT --directory OUT --font-file FONT --font-family FAMILY [--fontconfig CONFIG]`，从接口图取得固定页面编码，不再把当前载荷作为旧art_content传入；缺省页码只适用于没有当前图的历史/独立技术预览。
