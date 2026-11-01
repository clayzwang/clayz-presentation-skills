---
name: clayz-presentation-copy
description: Read the complete research, develop an independent reader-facing account, then edit and paginate it without fixed content-group or heading defaults.
---
# Copy：从完整讲述编辑出PPT文字结构

## 当前职责与输入

当前内容协议为3.5，专业交接为stage-files/1.0。阅读`../../packages/contracts/stage-file-handoff.zh-CN.md`与本语言的`references/copy-package-contract.zh-CN.md`、`references/atomic-copy-and-hierarchy.zh-CN.md`。

Copy从Logic的专业handoff文件读取完整研究报告、过程和证据；接收用户与本阶段相关的读者、用途、分页和措辞要求。技术运行包、字体/布局快照和渲染预算不作为写作内容。依据文件引用取得必要材料，不重复携带全套运行状态。

Copy负责实质编辑判断。先理解研究，再建立读者可以连续理解的讲述；分页、标题和细分文字服务这一讲述。禁止先以页面、栏目、卡片或标题正文槽位作为首次写作入口，再把分页结果串接为前置讲述。重新串接的页面文字只能用于后验连读，必须标为这种用途。

## 实际写作顺序

阅读完整报告及必要的过程和来源，确认研究能够支撑用户需要理解的内容。研究不足返回Logic补研究；不能靠文案填补事实、机制或关系。

面向读者写完整讲述，保存`copy/complete-account.md`，用`scripts/stage_documents.py files-account`登记。该操作发生在创建分页文档之前，并将真实讲述文件及输入绑定到account记录。不得从已写出的页面表生成这一前置文件。

在已保存的讲述上进行编辑、归纳与分页，依据真实的承接、对照、条件、包含、证据和解释关系决定边界。用户给出的页数或分段要求在本阶段处理；没有要求时依据内容选择，不能先定每页项目数再填充。研究本来互相依赖的内容应保持联系，不能为了条目整齐压成同级判断。

在内容组织成立后分配title、subtitle、heading、body、annotation等文字角色。所有类别按需使用；可以没有局部标题。heading使用实际的正整数层级，工具不默认一级，也不从二元组、列表长度或模板自动创造标题与层次。不要把所有主题做成相同数量的标题正文组，也不以换成另一个数量纠正内容关系。

正文细分以完整意思和依赖关系为依据。一个自然段可以跨多个body，也可以保持为一个body；文字单元不是视觉块。既有`content_relationships`中写本页实际关系和正文作用；不得用一条通用声明批量替代逐页关系判断。

## 文件化编辑成果

保存`copy/content.json`，包含：已登记的account_record文件引用、slides、unit_sources和实际semantic_review。每个可见文字单元以讲述稿的实际字符范围追溯；直接引用须完全一致，改写或派生说明实际理由。页内单位只含copy_id、text、role和必要的heading_level，不带栏数、几何、媒介或视觉分组指令。

保存`copy/edit-process.json`记录实际编辑取舍、保留和删改、关系变化与剩余问题。使用`files-copy`保存专业handoff；交给Art和Supervisor的是讲述、文案与过程文件的引用。

主产物不再是由页面内容反向生成的“连续稿”。索引和来源覆盖支持追溯；实际讲述及其编辑派生关系支持内容复核。工具不自动写任何段落或决定分组数量。

## 复核与读者

实际对照完整研究、完整讲述和分页文字。核对必要信息、论证关系、作用范围和不确定性是否保存；检查分组本身是否成立，而不只检查每句话可否找到来源。能复述单条文字不能单独证明整体组织合理。保真、理解、组织质量分别按真实观察记录。

按原生`../../packages/contracts/reader-cycle.zh-CN.md`和`../../packages/contracts/reader-review.zh-CN.md`使用全新上下文标题/正文读者。先冻结独立理解，再对照研究、讲述和实际文案；保持原来的合并返工及原读者复看次数。原始首读及剩余问题保留，不增加读者层级、审批或数量门槛。

Supervisor/工具用`files-bind-copy`保存技术绑定，沿用原生校验、校准和报告；这些配置与控制记录不回灌为Copy正文。Art根据真实内容关系独立设计，不按heading数量直接决定视觉分组。

## 复用边界

为后续模型分析保存本次完整输入、研究、讲述、文案、过程、读者观察和版本引用。迭代对象是可复用的基础方法、工具与交接能力。不能把本次公司的故事、这次修法或某种版式当成下一题的默认内容。
