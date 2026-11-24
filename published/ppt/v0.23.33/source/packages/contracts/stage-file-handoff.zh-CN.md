# 当前三模式专业文件交接

适用于workflow_cli创建的fast/normal/train run，与three-modes.zh-CN.md及three-mode-command-boundaries.zh-CN.md共同使用。专业packet为professional-input/2.0，产物捕获为stage-interface/1.0。本文不要求旧stage-input/1.0、stage-files包装或3.x技术包。

## 职责投影与真实产物

| 作者 | 唯一当前内容与专业要求 | 提交角色 |
| --- | --- | --- |
| Logic | 研究课题、读者、研究要求和实际资料；该阶段当前目标 | report、process、evidence、data |
| Copy | Logic完整文字report；读者/表达brief及该阶段目标 | graph、generation、interface、process |
| Art | identity接口的原字节Copy graph；格式brief、绑定知识及阶段目标 | design、renders、process；绑定知识时knowledge；实际脚本/资源具名 |
| Output | Art design、renders与所有真实图、原生source及具名资源；交付brief/目标 | pptx、pdf、renders、qa、inventory、process；实际脚本/资源具名 |

作者保存真实文件。协调者构造角色→文件绝对路径JSON调用workflow_cli commit；原生capture复制快照、计算SHA256/bytes并追加事件。源路径只是来历，下游消费快照。每个修订新建文件；历史引用保留为历史，不伪装当前源文件。运行配置、完整监督包、旧自评和读者答案不进入专业内容。

## Logic与Copy

Logic完整report展开事实、机制、必要比较、论证、反证和边界；摘要/findings/来源清单不能代替正文。process记录实际action/record与真实证据引用；evidence保留source_id/title/locator、实际原文或not-obtained限制；data保留数值、期间、单位、口径、公式和出处，无计算可以[]。核心commit继续调用原validate_research_documents，不放宽材料要求。

Copy通读report后用copy_graph.py prepare绑定report和单独专业brief；main实际登记全部storyline及相邻有类型连接，再按页heads→bodies，前页完成才下页，最后assemble与interface。保留字符范围、操作理由、15关系语义、多重/联合连接和数组维度/期间/单位。没有中间讲述稿。graph/generation/interface/process均来自真实生成链，不从终稿倒补。identity接口输出逐字节不变，回执另存。

## Art与Output

Art保留节点、文字、数据、层级、逻辑连接、页数页序；仅选择忠实空间/媒介/对象组合。planning/design保留copy_structure_lock和audit_observations，不用art_content或新增表达文字改Copy。先从当前表达问题实际读取相关知识节点及完整CU，再设计/写脚本，保存宿主原始读回、字节/节点/CU与具体采用、调整或不采用的理由。真正全页图与design页序一致。

Output忠实实现设计并保留原生文字、图表、表格、形状、连接及对象编辑边界。最终PPTX/PDF/全页图绑定同一精确文件版本；真实重开、字体、容量、数据、单位/负号和互动编辑行为分别观察。mode-output-qa/1.0七项完整记录pass/fail/not-observed/deferred和实际证据，文件存在或对象数不替代观察。缺字体按既有deferred-native policy，不静默换identity。

## 协调、读者与训练记录

root保留task-config/workflow-rules、同run预检和独立训练session。normal/train三个读者是content/layout/final，分别唯一回Logic/Art/Copy；原读者复看，Auditor只记录。执行原生prepare/record/repair而非旧title/content门禁。当前发布用workflow_cli publish/verify-handoff；训练capture-production/report/repo-export属于绑定独立训练包。不存在额外的五阶段files-collect必经门槛。

## 历史协议范围

stage_documents.py files-*和3.x package/plan/QA/report工具保留原实现，只服务实际明确绑定的旧输入/历史工件；它们不接受当前packet，本文不制造兼容转换。旧协议完整原文字节见../../references/legacy/three-modes-interface-r01/。字段/输入不匹配应保留真实错误及限制，不能改contract、自填批准或降低校验来取得通过。
