---
name: "ppt"
description: "研究、编写、设计和制作可编辑PPT；快速、正常、训练三种模式，使用分阶段抽象接口和独立训练包。"
---

# PPT制作

这是工具0.23.31 / three-modes.knowledge-use-projection.b02.r15本地候选；没有因此发布或安装。未指定模式时用normal。普通制作不启动训练，不修改工具或知识。训练模式需要独立的ppt-train包和明确阶段目标。

先读取 [三模式与命令](packages/contracts/three-modes.zh-CN.md)。主路径始终是 **Logic → 接口 → Copy → 接口 → Art → 接口 → Output**。Supervisor只在正常/训练模式进行旁路独立审计；接口不作者化，不增加总作者。

- fast：四阶段主路径及实际技术核验，不调用三个独立读者和旁路审计。
- normal：内容、排版、成品三个独立读者及Supervisor审计。
- train：normal的同一生产路径，另外绑定独立训练包，记录阶段目标、真实过程、开销及有范围的效果证据。

按当前阶段读取职责模块：[Logic](references/stages/logic/stage.md)、[Copy](references/stages/copy/stage.md)、[Art](references/stages/art-direction/stage.md)、[Output](references/stages/output/stage.md)、[Supervisor](references/stages/supervisor/stage.md)。这些文件直接说明当前project/commit交接、专业职责和技术检查。新模式命令边界见 [当前命令边界](packages/contracts/three-mode-command-boundaries.zh-CN.md)；完整旧文档存于 references/legacy/three-modes-interface-r01/，仅供显式历史绑定参考。

Copy唯一内容输入是Logic完整文字报告，按 [copy-graph/1.0](packages/contracts/copy-graph.zh-CN.md) 真实顺序登记全部主链，再逐页子标题及正文辅链。接口把Copy语义图逐字节交给Art。Art保留文字、数据、节点、连接、页数及页序；基于元素职责和关系选择表征，问题写入audit_observations。不得将关系一律做成箭头，也不得只把报告切成文字框。Art从当前表达问题出发实际读取绑定知识节点及相关完整CU，并保存采用、调整或不采用的理由。不预设页数、栏数或项目数。默认不用平安母版。

正常/训练的内容读者在Copy后，必要时回Logic一次；排版读者在Art后，回Art一次；成品读者在Output后，回Copy一次。每名读者首读直接使用prepare packet并冻结独立理解，再做不含作者自评的证据对照。返工后由原读者复看；上游变化使受影响的下游通过失效，同轮继续原上下文，原失败永不消失。Supervisor的独立审计只记录，不开启额外返工。

使用 `python -B scripts/workflow_cli.py` 建立独立任务目录并保存同一份task-config与workflow-rules；阶段内容通过project投影，运行配置与作者自评不混入公司内容输入；Art/Output只在technical_files接收当前run冻结配置，作者自评不投影。依赖先查现有运行时。保留真实原始来源、制作脚本、全页图、可编辑PPTX、PDF及完整报告；未执行、失败和无法观察的检查如实记录。哈希/协议/单例通过不证明通用质量提高。

## 传输节流与跨轮上下文隔离

制作与训练派发前读取`config/transport-economy.json`和`references/transport-economy.zh-CN.md`，使用`scripts/transport_economy.py`核对本轮包、登记不继承历史的上下文、准备相同像素的较小编码，记录实际看图及本人证据复用。专业推理、必要细节与独立检查保持；不得把准备体积当作VPN实测。

知识包沿用明确绑定版本，外置挂载，不因本次工具候选升级而声称知识或账号安装已升级。Library讨论与确认入库功能仍使用 [原生知识工作流](packages/contracts/native-library-workflow.md)，不自动启动生产或训练。

本地r03另将Art所需Copy identity回执放入professional-input的technical_files（不增内容输入），并把读者canonical_rules复制到准备包内。图字节、原规则正文、读者标准/回退及失败判定不变；相对源引用作为canonical_rules_origin留档，不授予额外阅读权限。

本地r06把比较包知识证据改为[当前专业白名单](packages/contracts/reader-knowledge-evidence.zh-CN.md)，历史评价完整留史，不投影给比较读者；首读、准则及闭合规则不变。阶段过程用[process.events](packages/contracts/process-evidence.zh-CN.md)保存当时实际记录。原生运行方法的执行权限作用域须一致，详见[UNO方法](references/libreoffice-uno-export.zh-CN.md)。

本地r07补明锁稿前的[Copy整稿角色与标题语言](references/stages/copy/stage.md)责任，以及[Art先建立整稿视觉系统](references/stages/art-direction/stage.md)再局部布局的入口。既有知识原字节保留；专业规划写入已有 reading_review / semantic_review / art_cognition / planning，不改接口、读者规则或次数。尚未验证视觉、语义或成本改善。

本地r08只收窄Output的production_resources：四个已定义知识读取proof角色留在原Art及审计快照，不复制成制作输入。design、renders、editable-source、全页图和其他具名制作资源保持；不按文件扩展名或knowledge前缀删资源。这不是任意自由文本净化或强文件系统隔离，不改变读者、预算、闭合和失败规则。

本地r09增加可选页码字段/PDF诊断：只读当前PPTX、PDF与精确renders绑定，不启动Office、不做新渲染或改变门禁。缓存匹配不等于canonical页码正确，歧义保留unobserved。方法见references/page-number-field-diagnostic.zh-CN.md；既有准则、代码、预算、字体和失败规则保持。

## 本地r10 规范技术配置

Art和Output的professional-input.technical_files.canonical_task_config为当前run已经冻结的task-config精确字节，含路径、SHA256和字节数。它是技术约束，不增加公司内容输入；Art仍只消费原字节Copy图，Output仍消费design/renders及真实制作资源。以此核对当前identity、字体、颜色及制作配置，不能取安装包默认配置、历史稿或作者自评作替代。缺失或身份不符时保留实际错误，不静默派生默认值。该投影不证明配置已落实到原生对象/元数据，也不证明字体、编辑、容量或渲染检查通过。Office运行身份/累计计数仍须实际运行证据，不能由冻结配置推断。既有四类Kproof边界、读者清洁输入、判定、预算与失败规则不变。

本地b02.r01深化Copy的正文语义重构与标题归属方法，保留真实main→heads/bodies→assemble顺序、报告唯一内容输入、完整保真及原读者/预算。仅为后续未初始化训练的本地候选；没有安装发布或已证实的通用效果。

本地b02.r02另提供首次保存前配置元数据的可选内存写入原语，保留Copy语义方法与外部K1.3.2原字节；仍属未来未初始化轮的本地候选。

本地b02.r03落实用户修订：Logic结论型完整分析、Copy层级及关系、Art专业精准生动设计为持续目标；各轮问题只作真实迭代证据。保留原契约与当前已准备知识原字节，尚无专业效果结论。

本地b02.r04深化观众内容、关系表征与追溯/过程职责的区分；知识专业字段与旧训练历史分开。仅为后续未初始化轮次的候选；固定目标、评价、Python、读者及预算不变，无专业效果或全局发布结论。

本地b02.r05新增可选专业内容阅读工具，保留当前内容、关系、主张分类与选表范围，制作理由及自评另供原图核对；不改变原生投影、内容身份、评价、目标、预算或当前运行。它不是独立阅读或专业提升证明，尚未全局安装/发布。

本地b02.r06新增可选原文字片段原生制作原语及Art用法。模型选择分段与空间，工具保留原文、强调、原生对象顺序及明确样式；既有内容、投影、评价、目标、预算和已运行任务不变。知识仍为原1.3.4字节；没有专业效果、全局安装或发布结论。


图片历史生命周期须遵守`references/history-lifecycle.zh-CN.md`：图像检查结束退役；后续用fresh无历史上下文，原读者判断通过完整哈希绑定接续，不重抽首次判断。不能将新图压缩或缓存命中视为清除旧图。


确定性技术步骤优先使用`references/technical-batch.zh-CN.md`与`scripts/technical_batch.py`：先准备当前case/hash绑定的有限计划，一次执行、失败即停，完整输出留本地、模型只收机械摘要。专业研究/设计原文仍完整读取，任何模型token/VPN节省必须另行观测。


批处理API返回数据与标准CLI实际stdout必须分开记账；两者均不自动等同模型输入或VPN。直接API包装器的真正输出另核，不能将名义CLI序列化大小写成实际对话节省。

当前读者知识投影支持actual_adoption的专业数组记录，详见references/reader-knowledge-use.zh-CN.md；保持独立首读、原专业标准、未知和固定返工/阶段规则，不能把采用声明当通过。
