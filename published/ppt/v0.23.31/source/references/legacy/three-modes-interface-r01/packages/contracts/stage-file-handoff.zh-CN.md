# 阶段文件交接与后续方法迭代 — Copy图1.1

新任务使用内容包3.5。本契约定义已有阶段的专业文件接口，不创建额外作者、审批阶段、控制器或训练运行。

## 职责与文件流

用户输入按职责形成文件。Logic接收研究课题、读者、研究要求和资料；Copy接收完整研究及分页、措辞要求；Art接收Copy—Art接口输出的完整语义图、格式要求及选中的基础设计知识；Output接收设计/制作规格、真实渲染图及交付要求。Supervisor掌握完整用户目标、工具/知识版本、运行记录、配置及各阶段结果。

专业输入和handoff文件有固定的职责字段白名单，不接收task_selection、acceptance、全量resource/index、theme/layout或performance_budget等运行快照。必要身份以文件引用及哈希追踪。原生技术运行包由Supervisor/工具另存，服务机器校验和报告，不作为Logic/Copy的专业输入。

每份文件引用包含path、sha256和bytes，使用前核验实际字节。各修订保存新文件，不覆盖前一份。落盘不等于内容充分、设计优秀或实际采用；专业阅读和质量判断继续沿用原有校准、读者与Auditor，不增加审批层级或数量配额。

## Logic：完整研究及过程

主交付是实际展开的research-report.md。完整论述有证据支持的事实、机制、关系、必要比较、分歧、解释和未知，按真实题材形成自然段和层次；结论与摘要只能作为报告中的部分。没有预设发现数量、研究段数或字数配额，不以findings清单代替正文。

research-process.json保存实际可核查events：action是做过的动作，record是实质记录，可附source_ids及实际证据文件artifacts。记录资料检索/阅读、定位摘录、定义核对、计算、反证、问题和论述修订等实际发生的工作，不补写虚构历程。

evidence.json包含sources，各来源有source_id、title、locator；来源实际文件可通过artifacts引用。data.json保存实际数值、期间、单位、定义/计算及出处，无数量研究可以为[]。这些文件支持报告，不代替报告。

## Copy：完整研究到主辅链

唯一内容输入是Logic完成的文字研究报告。按copy-graph/1.0执行 ../../scripts/copy_graph.py：prepare只绑定原报告和Copy专业brief；main登记通读后的全部结论型storyline及有类型相邻连接；逐页heads按层生成子标题，bodies再生成正文和完整页内连接；上一页完成才进入下一页。各标题正文用head_/body_编码，直接引用原报告字符范围；每页恰一个H1，其数量就是正文页数，封面尾页另计。没有中间完整讲述稿或files-account新制作入口。

完整字段、15关系类型、多重连接/超边、多维数组、来源及限制见copy-graph.zh-CN.md。每节点有连接，页内网络连接storyline，整稿连通；不可用局部孤岛满足检查。正文和子标题按需缺省，允许同层两种节点。主链、辅链及实际复核各自落盘，不事后补造。原生标题/正文读者先冻结理解，再对照原报告、实际节点和逻辑关系；保留一次合并返工和原读者复看。

完成后interface命令逐字节无损透传Copy输出，验证/回执单独保存，不是新作者/新阶段。files-copy接收--input原生专业输入、--content图、--generation最后实际生成记录、--interface回执、--process实际过程，保存Copy阶段handoff/1.1。旧handoff/1.0只用于历史读取；新绑定不接受旧account协议。files-bind-copy由工具生成现有3.5技术运行包及只读QA文字位置投影，专业内容权威仍是接口语义图。

## Art与Output

Art从接口原样输出的Copy语义图理解对象、论证和信息关系，结合用户格式要求与基础设计知识选择整体设计、空间、图表、层级、阅读动线、颜色和字体。heading数量不是栏数，文字单元不是视觉块。脚本实现已经选定的内容组织与设计，不替代专业判断。

Art保存设计/制作规格、全部真实渲染页图、渲染清单和过程记录。Art的planning和设计绑定copy_structure_lock；不得增删、改写、调整层级、连接或分页，也不得返回Copy重写。遇到内容问题按节点忠实写入audit_observations，只进入既有审计报告；禁止art_content与新增表达文字。

Output保存实际可编辑PPTX、PDF、全部页图清单、原生QA及过程/异常文件。原生对象、字体、容量、内容、渲染与目标应用等检查保持独立结果。files-output不把失败QA改成通过，也不替代现有原生校验。

## Supervisor与后续模型分析

Supervisor对照用户目标、实际报告/语义图、设计与最终文件，输出真实监督报告，保存异常文件。各阶段专业材料和技术运行记录均落盘但分开组织，不把配置追踪当作研究内容。

files-collect复制本次用户输入、实际工具/知识版本文件、五阶段专业handoff及其引用的材料，生成training-materials.json，保留原路径、保存位置和实际哈希。Supervisor同时通过可重复的--supporting-artifact参数保留实际技术绑定、校准、读者首读/复看、Auditor及报告文件；这些支持材料不回灌给内容作者。未执行的检查保留未执行状态，不补造产物。它只保存材料，不执行训练或下一轮生成。

后续大模型以这些实际材料分析问题、设计可复用的基础方法改进，再更新工具或基础知识；下一轮实际使用更新后的版本。任务案例、公司内容、稿件及读者答案留作本轮诊断，不能作为下一题作者的隐含内容或固定生成方法。单份效果改善不能单独证明通用工作流变好。

## 原生接口

入口均为scripts/stage_documents.py，先用对应命令的--help查看参数：files-prepare、files-research、files-copy、files-art、files-output、files-supervisor、files-check、files-collect、files-check-collection。

files-bind-logic与files-bind-copy只由Supervisor/工具调用，用于将专业文件绑定到原生机器校验/报告协议。它们不生成研究、文案或质量批准，不把运行包交回内容作者。内容包3.0—3.4在本工具默认校验中不作为新制作入口，显式历史回放或原绑定工具才用于读旧稿。

材料收集命令同时要求--tool-snapshot与--knowledge-snapshot；保留实际字节，而不只保留版本名。files-check-collection可在原目录已移动时验证保存字节及嵌套文件引用是否齐全，分析程序可用read_collected_file按原引用读取归档副本。
