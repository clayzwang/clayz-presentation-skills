---
name: "ppt"
description: "研究、编写、设计和制作可编辑PPT；快速、正常、训练三种模式，使用分阶段抽象接口和独立训练包。"
---

# PPT制作

这是工具0.23.0 / three-modes.interface.r01本地候选；没有因此发布或安装。未指定模式时用normal。普通制作不启动训练，不修改工具或知识。训练模式需要独立的ppt-train包和明确阶段目标。

先读取 [三模式与命令](packages/contracts/three-modes.zh-CN.md)。主路径始终是 **Logic → 接口 → Copy → 接口 → Art → 接口 → Output**。Supervisor只在正常/训练模式进行旁路独立审计；接口不作者化，不增加总作者。

- fast：四阶段主路径及实际技术核验，不调用三个独立读者和旁路审计。
- normal：内容、排版、成品三个独立读者及Supervisor审计。
- train：normal的同一生产路径，另外绑定独立训练包，记录阶段目标、真实过程、开销及有范围的效果证据。

按当前阶段读取职责模块：[Logic](references/stages/logic/stage.md)、[Copy](references/stages/copy/stage.md)、[Art](references/stages/art-direction/stage.md)、[Output](references/stages/output/stage.md)、[Supervisor](references/stages/supervisor/stage.md)。这些文件保留专业研究、表达、原生制作及技术检查；其中旧title/content/final读者、旧五阶段审批和report3.6编排只属于历史兼容，新任务以三模式契约为准，不并行运行两套门禁。

Copy唯一内容输入是Logic完整文字报告，按 [copy-graph/1.0](packages/contracts/copy-graph.zh-CN.md) 真实顺序登记全部主链，再逐页子标题及正文辅链。接口把Copy语义图逐字节交给Art。Art保留文字、数据、节点、连接、页数及页序；基于元素职责和关系选择表征，问题写入audit_observations。不得将关系一律做成箭头，也不得只把报告切成文字框。Art从当前表达问题出发实际读取绑定知识节点及相关完整CU，并保存采用、调整或不采用的理由。不预设页数、栏数或项目数。默认不用平安母版。

正常/训练的内容读者在Copy后，必要时回Logic一次；排版读者在Art后，回Art一次；成品读者在Output后，回Copy一次。每名读者首读直接使用prepare packet并冻结独立理解，再做不含作者自评的证据对照。返工后由原读者复看；上游变化使受影响的下游通过失效，同轮继续原上下文，原失败永不消失。Supervisor的独立审计只记录，不开启额外返工。

使用 `python -B scripts/workflow_cli.py` 建立独立任务目录并保存同一份task-config与workflow-rules；阶段内容通过project投影，运行配置和作者自评不得混入专业输入。依赖先查现有运行时。保留真实原始来源、制作脚本、全页图、可编辑PPTX、PDF及完整报告；未执行、失败和无法观察的检查如实记录。哈希/协议/单例通过不证明通用质量提高。

知识包沿用明确绑定版本，外置挂载，不因本次工具候选升级而声称知识或账号安装已升级。Library讨论与确认入库功能仍使用 [原生知识工作流](packages/contracts/native-library-workflow.md)，不自动启动生产或训练。
