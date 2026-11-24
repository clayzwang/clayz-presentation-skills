# 连续训练：继承实际改进，并限制本题回退

## 当前文件化材料与迭代目标

以可稳定产出高质量PPT的通用工作流为改进对象。按照stage-file-handoff/1.0保存本次用户目标、实际工具/知识版本、完整研究及过程、Copy讲述与编辑文件、Art设计/渲染、Output文件/QA与Supervisor异常。使用现有stage_documents.py files-collect收集真实文件，而不是只保存最后成品或一份总结。后续模型从这些证据分析工作方法、设计修改，再将实际更新的工具或基础知识字节用于下一轮。案例故事及样本专用修法不升级成通用生产指令。该契约在用户明确要求训练时才执行；普通制作仅保留后续分析所需的材料。


## v0.20.5 current repair policy

The selected `consolidated-once` policy controls all reader return routes: Copy readers together → one Copy repair → both original readers confirm; final reader → one Art/Output repair → same reader confirms. Independent Auditor records only. Residual/new issues are reported, never another repair dispatch. Historical pass-until-clean or repeated returns below apply only to legacy `strict-pass`. See `packages/contracts/reader-cycle.md` from the plugin root.


本补充用于用户明确要求逐题训练、逐轮优化插件及知识包的任务。它不改变
v0.20.4 的作品、读者、审计或发布合同，也不把停止迭代当作验收通过。

每题的产物有三个不同用途：作品用于观察问题；阶段方法与实现用于改善制作；
专业知识用于理解新的情境。只改当前稿、增加工作记录或复制旧文件，均不能
称为已升级插件或知识包。版本名变化也不能证明发生过有效修改。

本题结束或达到回退上限后，沿实际缺陷或改善机会选择小范围更新。已有规则
已经覆盖的问题，先辨认执行为何仍会漏掉，改进相应阅读、编辑或调度动作，
避免再加同义口号。知识补充说明概念、机制、适用条件、替代解释和专业来源；
本页修法及效果观察留在案例中。允许保持其他阶段不变。

下一题开始前，保存本题原版本与优化后版本的字节清单、实际差异及验证结果。
下一题必须从优化后的源目录创建运行快照，校验复制结果，并在真实阶段输入中
绑定该快照。阶段执行者实际读取相关新内容，说明采用、调整或未采用的理由。
知识已写入、方法已采用、作品已变化与读者效果已验证分别陈述。

若没有形成实质更新，不能把同一快照重新命名后宣称递推。保留未完成的升级
状态，按用户的训练要求完成改进后再开始下一题。原版、开发版和正式发布版
分别标识；本地开发源不代表已安装到应用或已向 GitHub 发布。

## 回退预算

Supervisor 在第一次实质回退前读取任务中已说明的预算。用户只要求限制次数时，
执行者可提出有明确来源的数值选择，并写进现有任务约束；不把自选数值说成
用户原话。已有合同中更严格的预算继续适用。

实质回退指负面内容或呈现评价导致较早阶段修改主要成果。同一次派发可合并
相关问题；按原问题家族计数，换编号、换读者或拆成小修改不重置次数。保存
实际问题证据、预期可观察的改善，再用 `scripts/iteration_budget.py reserve`
预占次数。失败尝试也消耗次数。单纯字节绑定或记录格式纠正不会额外触发内容
返工，但不能借此重新编写内容。

达到任务预算、同一问题的修复及复读额度用尽，或剩余收益不足以支持再返工时，
停止本题。冻结当前成果与原始未决发现，用脚本记录 cutoff；后续派发会拒绝
继续修复此题。没有变化的材料不重新抽取读者来争取通过。停止记录与失败原件
允许下一题继续训练，不能补造匹配的成品链、正式审计闭环或验收结果。

脚本检查次数、状态及证据绑定，不能判断解释质量，也不能替代原读者校验器。
用户明确改变预算时，另存修订并保留原历史，不能悄悄重置已有计数。

## 训练操作计数

明确训练的能力扫描、来源收集、作者写入、Office 启动、整稿渲染、技术修复、技术轮次和回退重启默认记录实际次数。新开明确训练可通过 `runtime.training_limits` 明确设置相应上限。确保锁定后端、配对、签入、独立读者、逐轮验收及用户设定的累计轮数继续有效。原生读者退回额度与技术修复次数分别记录。

续接旧冻结轮次时，由原协调者核对实际授权及原始证据，通过 `workflow_cli.py adopt-training-operational-policy` 追加兼容决定。原 run/session、冻结配置及原事件完整保留。该命令复用同一决定的读回结果。受影响的工具从新策略的原生状态读取有效上限和已观察计数。配置中的历史值和本轮过去的启动等记录均可查。

从 `workflow_cli.py status` 查看已记录次数，使用 `observe-training-operation` 绑定实际操作凭证。用 `render_native_preview.py --training-run` 渲染训练稿，并以原稿或终稿精确字节执行复开和导出。该命令记录 Office 启动标识、独立 profile 和完整渲染。技术台账初始化可以使用 `execution_ledger.py init --training-run` 读取兼容生效的策略。
