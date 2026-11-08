# 三模式工作流 / mode-workflow 1.0

工具0.23.0，修订three-modes.interface.r01，本地候选。生产职责为Logic、Copy、Art、Output；Supervisor旁路审计。接口是生产者输出的抽象文件契约和不可变快照，不改内容，不新增作者。知识包1.3.0+composition.r01.1沿用原字节，未发布、安装或启动连续训练。

## 模式及职责

| 模式 | 生产 | 独立读者及审计 | 训练包 |
| --- | --- | --- | --- |
| fast 快速 | 四阶段及技术检查 | 无 | 无 |
| normal 正常（默认） | 同一主路径 | 内容、排版、成品三读者及Supervisor独立审计 | 无 |
| train 训练 | normal同一路径 | 同normal | 外部训练包，显式阶段目标 |

知识调用属于Art；培训记录不成为生产内容输入。原有Library能力不因新模式改变。训练模式指工具/工作流/知识的有证据迭代，不自动宣称在优化模型权重。训练目标可分别属于Logic、Copy、Art、Output，同一阶段可多目标，也可没有目标。不能把“目标”误写成阶段记忆并将旧稿交给新作者。

## 三个接口 / stage-interface 1.0

| 接口 | 生产者完整留档 | 下一作者内容投影 |
| --- | --- | --- |
| logic-copy | 完整文字研究report、process、evidence、data | 仅report，另给读者/表达brief |
| copy-art | graph、真实顺序generation、interface身份回执、process | 原字节graph，另给专业要求 |
| art-output | design、真实全页renders清单与图、process、知识读取证据knowledge | design、renders及实际全页图；制作资源以具名文件角色一并保存 |

commit接收“角色→实际文件绝对路径”的JSON。所有文件当场保存到任务内objects并计算SHA256/bytes；事件只追加、前后哈希相连。原始路径只作为来历，消费端使用快照。当前外部依赖须真实存在且字节匹配；历史JSON中的旧指针不被当作当前递归采集任务。过程日志不是从终稿倒补的证明：Copy仍用原生copy_graph.py先完整登记main，再按页heads、bodies，最后assemble、interface；commit复核这些原生记录并保存真实记录字节。

Copy节点必须有稳定head_/body_编码、层级、来源范围和关系。关系类型、方向和联合关系完全沿用copy-graph/1.0；字段检查不能代替实际语义审阅。标题须在证据边界内形成清晰命题，正文需要加工成易读论证，不只是按页切原报告。所有节点接入本页storyline及全稿网络。表格保留完整维度/期间/单位或可追溯子集，Art选择适当图文呈现。封面尾页和页数由当前需求与完整研究决定，不在新接口固定容量。

Art保留copy_structure_lock与audit_observations。知识证据包括实际节点/CU、读取正文证据、对当前问题的采用/调整/不采用理由；不能把索引命中数当作设计质量。Art不得改写、删节、重排节点与页面，不得因内容问题退回Copy。正常的成品读者提出回Copy时，由Copy在记录的唯一返工中改内容，后续Art忠实重做新输入。

Output保留原生文字、图表、形状、连接及用户要求的可编辑性。原生表征、自动换行、行距、负号、单位、字体、数据、溢出检查沿用当前工具的方法。实际全页重开渲染与人工读图不可用时须写not-observed/deferred，不能用格式有效或PPTX中存在文字代替视觉通过。新的mode-output-qa观察契约把实际字节检查与人工/环境观察分开；旧output-qa4.1及旧包仍可原生验证，不将旧报告伪装成新版已通过。

## 三读者和一次回退

| 读者 | 初读对象 | 评判职责 | 未通过去向 | 次数 |
| --- | --- | --- | --- | --- |
| content 内容 | Copy全稿可见标题/正文 | storyline论证问题明确、结构完整、逻辑可靠、衔接自然；标题层级/表达；下层事实与解释 | Logic→重做Copy及受影响后续 | 一次 |
| layout 排版 | Art全部实际页图 | 关系/类型的有效呈现、知识的适用判断、空间排布与阅读路径 | Art→受影响后续 | 一次 |
| final 成品 | Output全部实际页图、PPTX、PDF | 认知价值、表达清楚、逻辑正确及实际成品问题 | Copy→Art→Output | 一次 |

每名首读者使用全新上下文，原作者不充当自己的独立读者。内容读者合并原标题和正文读者，须实际覆盖两个层次；排版和成品分别观察相应产物。`reader-prepare --phase first`的工具packet直接作为派发输入；只看首读可见内容/图像，冻结understanding、assessment、findings。之后prepare comparison提供本次完整Logic报告、排除semantic_review的语义证据及适用设计/知识证据；原读者做证据对照。禁止先看作者自评再倒填首读。

首读响应：`{"understanding":["具体独立理解"],"assessment":"判断及范围","findings":[{"id":"F1","observation":"具体问题","impact":"影响","evidence":"节点或页图定位"}]}`。
对照响应：`{"verdict":"pass|repair|deferred","explanation":"实质对照","findings":[],"unobserved_checks":[]}`。同一原对照不可重抽判断覆盖；实际问题和未观察范围均保留。
返工由`repair --reader ...`按表唯一去向打开，生成新版本并保留旧版本；原读者prepare confirmation后响应`resolutions:[{id,status:resolved|remaining,explanation}]`与`new_findings:[]`，逐项包含首读/对照/前次复看已发现项。任何新发现不能消除旧失败。该读者次数用尽后残留闭合为closed-with-findings；不另造一轮或换读者清零。
上游返工使受影响阶段的原通过失效。下游重做后由各自原读者confirmation复看新source，**不计为新的独立读者或额外返工**；若其尚未用过本名读者的一次回退仍可按表打开。原读者丢失/不可用须deferred说明，不能让新读者冒充复看。

上下文披露JSON须有context_id、execution_mode、model_identity_disclosure、limitations数组、host_receipt实际宿主返回文件路径。首读允许same-model-new-context、isolated-context或isolated-executor；模型信息不可观察时明确写unknown。不伪造更强隔离；共享文件系统仅靠角色指令隔离时写清。新上下文ID不能复用另一名读者。上下文能力不具备时交付状态保留未完成，不能作者自填读者通过。

Supervisor以新的独立Auditor上下文执行旁路审计：先成品独立理解，再对照原始要求、规则、完整阶段、三个读者原记录。审计pass/deferred，只记录问题，不增加生产阶段、不改稿、不开启额外返工；报告保留实际问题、方法改进与所有未观察检查。旧审计专业方法仍适用。三读者和审计不是结果保证。

## 真实运行命令

下文`TOOL`是当前包根，`RUN`是包外新任务目录，所有CLI用已有可用Python运行时，无需重装。`--help`列出具体参数。

```sh
python -B TOOL/scripts/workflow_cli.py init --directory RUN --task /absolute/request.txt --mode normal --knowledge-manifest /absolute/knowledge/manifest.json
python -B TOOL/scripts/workflow_cli.py project --run RUN --stage logic --output /absolute/logic-input
python -B TOOL/scripts/workflow_cli.py commit --run RUN --stage logic --files /absolute/logic-role-files.json
python -B TOOL/scripts/workflow_cli.py project --run RUN --stage copy --output /absolute/copy-input --brief /absolute/copy-brief.json
```

Logic直接落盘完整报告/证据/数据/过程；Copy在project的report上用原生copy_graph.py执行prepare、record main/heads/bodies、assemble、interface，再commit copy。Art project后读知识、设计、制作真实可编辑PPTX并渲染、保存design/knowledge/renders/process，commit art。Output生成最终PPTX/PDF、全页图、原生对象检查及观察QA后commit output。每阶段的资源（含制作脚本）用额外角色传入commit，不能只在聊天说明。

```sh
python -B TOOL/scripts/workflow_cli.py reader-prepare --run RUN --role content --phase first --output /absolute/content-first
python -B TOOL/scripts/workflow_cli.py reader-record --run RUN --packet /absolute/content-first/reader-input.json --response /absolute/first.json --context /absolute/context.json
```

首读冻结后同样prepare/record comparison；需要返工才repair。新阶段提交后prepare/record原读者confirmation。layout、final、audit类同。fast中这些命令拒绝执行，不能将跳过描述成通过。

预检沿用当前runtime_preflight：init已发出真实challenge；先component_version_guard --mode application，再按runtime_preflight.py --help提供实际host/model能力文件、当前task-config、challenge、原task-request及component-version-report。新三模式已使用单一明确配置，不再要求旧unified task-selection；若显式使用旧selection则仍原生验证。environment命令只绑定本run、同task哈希、同配置哈希的真实预检回执。预检不能用自写pass代替。运行中不悄悄切路；失败保留，确需重启按原规则新建任务。

```sh
python -B TOOL/scripts/workflow_cli.py environment --run RUN --receipt /absolute/runtime-preflight.json
python -B TOOL/scripts/workflow_cli.py status --run RUN
python -B TOOL/scripts/workflow_cli.py publish --run RUN --output /absolute/new-delivery --tool-snapshot /absolute/tool.zip --knowledge-snapshot /absolute/knowledge.zip
python -B TOOL/scripts/workflow_cli.py verify-handoff --bundle /absolute/new-delivery
```

交付采用显式新契约mode-delivery/1.0、mode-supervision-report/1.0，完整保存PPTX、PDF、全页ZIP/清单、Logic正文、主辅链/生成记录、接口、Art设计和知识证据、实际脚本/资源、读者原记录及审计。提交QA有失败/未观察时报告issues-found；不能写通用效果提升。环境能力ready和观察质量分开；实际硬失败/用户硬门槛须解决或保留未完成，不能用发布器掩盖。旧report3.6发布器只用于历史读取，新路径不会借旧验证通过为新版背书。

NAS按项目当前共享说明和实时health执行files.archive，business/automatic直接status验收，pending仅在后台确实要求本人时提供实际链接。核对completed、真实目标及全部哈希；不创建本地假NAS目录。

## train绑定外部训练包

先读取单独ppt-train/SKILL.md；该包通过training-package/1.0、training-session/1.0契约与当前run.json连接，不导入生产Python模块。目标来自本次明确JSON或Gitea Issue；包记录基线真实字节、阶段开始/完成/中断、工具调用收据、使用量、效果证据。随后`bind-training --package /absolute/ppt-train/manifest.json --session /absolute/session/session.json`。project只传当前阶段的本次目标，不传旧案例稿件、读者答案或作者自评。普通fast/normal不会自动载入训练包。

返工重放时若另一名尚未用过回退的原读者发现问题，可以打开其独立的一次回退；外层回退保持待复看状态，不能因此重置任一预算。多项待复看均有原记录，只有对应原读者复看当前产物才逐项关闭。

Output QA JSON的contract为io.clayz.presentation.mode-output-qa/1.0，checks须逐项包含all_page_images、reading_path、data_signs_units、native_editability、fonts_native_reopen、overflow、relationship_expression；每项status为pass/fail/not-observed/deferred，explanation注明实际观察范围，evidence为真实path/sha256/bytes数组，pass/fail必须有证据。交接自动读取最终PPTX的原生对象文本/表格/图表及页序，复核Copy文字和表格标签/值/单位/期间保留；机器检查的范围和人工/环境判断分别存档。
