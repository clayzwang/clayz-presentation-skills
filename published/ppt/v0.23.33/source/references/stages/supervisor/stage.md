# Supervisor：协调四阶段与旁路审计

本文件适用于workflow_cli创建的fast/normal/train任务。当前输入为professional-input/2.0，交接用stage-interface/1.0；完整操作见 packages/contracts/three-modes.zh-CN.md 与 packages/contracts/three-mode-command-boundaries.zh-CN.md。历史3.x包装、旧读者和旧发布指令仅见 references/legacy/three-modes-interface-r01/，不作为本模式步骤。

## 职责与权力边界

主生产为Logic → Copy → Art → Output；Supervisor协调、保留规则和事实，不是第五位内容作者。normal/train的Auditor为独立新上下文、只记录的旁路角色。不得在Supervisor内补写研究、改文案、替换设计或修改PPTX，不代作者/读者批准，不把形式有效当质量通过。

区分资源检查、讨论确认知识、PPT能力建议和实际制作。只在用户要求制作/修订/审计材料时进入本模式。讨论知识遵循native-library-workflow的真实draft→本人confirm→commit；未确认稿不能进入检索，不能以任务维护替代用户的知识确认。

## 当前运行与专业输入

1. 从当前用户要求判断研究/执行/混合责任和实际读者；不强制报告原型、页数、字数或设计结构，不为日常可逆制作反复请求提纲批准。用户明确要求与未知项如实保留。
2. 使用workflow_cli init选择fast/normal/train并冻结同一task request、task-config、workflow-rules与原生challenge。保留真实版本/快照。离线component_version_guard application只检查本地一致性，不宣称公开最新或全局已安装。
3. 以同run、同task/config/challenge做一次真实runtime_preflight，绑定environment。宿主/model能力和原始收据真实留档；未知写unknown。不得自填pass、伪造更强隔离、修改默认配置/预算或切路来掩盖失败。新三模式不再要求另建旧unified task-selection；真实旧selection仅在实际使用时原生验证。
4. train先绑定独立训练包与实际阶段目标。每个作者用project的professional-input/2.0；只给该阶段当前内容和专业brief/目标，不传旧答案、作者自评或其它阶段的目标。Logic为研究任务；Copy唯一内容为完整report；Art唯一内容权威为原字节graph；Output消费design、真实renders、全部图和具名资源。canonical运行配置和全量技术运行包不混入专业内容。
5. 作者保留真实产物及过程。协调者以角色文件JSON调用commit，工具捕获stage-interface、实际源材料和不可变字节。Logic仍接受validate_research_documents实质校验，Copy仍接受真实生成链/identity接口，Art仍受精确Copy锁，Output仍受对象/数据/七项QA检查。无需旧files-*、3.x技术包装或五阶段record-stage链。

旧stage-input/1.0的前驱handoff模型与当前professional2.0不同。不要改contract名、补空handoff或把旧运行包塞给作者来强行调用files-prepare/files-bind-*；这些只适用于显式历史绑定。完整命令边界见three-mode-command-boundaries。

## 三个读者及原读者复看

normal/train使用content、layout、final三个独立读者，每轮/首次均fresh，直接派发reader-prepare first packet。冻结understanding/assessment/findings之后，由同一读者接收comparison材料。首读前不暴露作者自评、预期答案、旧轮/旧读者结论。保存实际宿主派发/返回、context ID和可得usage；模型身份未知保持unknown，共享文件系统只作真实角色指令隔离披露。

| 读者 | 首读 | 唯一正式回退 |
| --- | --- | --- |
| content | Copy标题与正文 | Logic，随后重做受影响Copy/Art/Output |
| layout | Art全部实际图 | Art，随后重做受影响Output |
| final | Output实际图/PPTX/PDF | Copy，随后重做Art/Output |

调用原生repair保留各自一次预算；多项问题合并。上游变化使下游通过失效，同轮原读者confirmation复看，不换人、不重抽首读、不新编号清零。残留按原规则闭合为closed-with-findings，不再开额外修复。fast跳过这些角色时仅记未调用，不能声称读者通过。

## 专业阅读与实际影响

In the evidence-reconciliation pass, read Logic for substantive completeness, Copy for natural continuous prose,
and the final pages for actual readability. Judge whether the intended reader
can understand without reconstructing the research notes. Data/object/layout
checks do not establish language quality. Prioritize material content repair
over tidying audit records; quote exact text/copy IDs and route missing analysis
to Logic, awkward expression to Copy, and visual loss to the responsible visual
stage. Preserve the existing independent-audit and delivery policy.

For v0.18.2, inspect claim/evidence correspondence, local argument organization,
entity/accounting scope and avoidable repetition in Copy, then their visible
expression in Art and the final render. A missing heading alone is not a defect.
Record concrete affected copy IDs/pages in current reader or audit findings.
Compare the complete Logic report and evidence with the actual Copy explanation and then with
its fine body units. Inspect retained mechanisms and discriminating facts, real
omissions/moves, and continuous grammar and logic after splitting. Missing draft
or reading evidence remains a gap. Do not infer a content pass from provenance
coverage, a generic schema-check pass or an empty issue list. Check that Art's
combination/separation preserves the dependencies and qualifications; use the
existing notes/findings and attribute findings to their earliest responsible owner. Art content objections remain audit-only. Formal content repair follows the current content/final reader’s own bounded route; the Auditor cannot open another repair.
Read `packages/contracts/verification-outcomes.md` or its `.zh-CN.md` peer:
preserve raw tool execution results, record-integrity findings and actual quality
findings separately. Exceptions do not prove content failure or authorize a pass.
An honest failed check is not itself a malformed QA record. Retain independent
assessments and repair results without overwriting the earlier evidence.


## 独立Auditor与问题归属

三个当前读者闭合后，用新的独立Auditor先读成品冻结理解，再对照原要求、阶段证据和完整读者历史。Auditor记录pass/deferred及实际发现，不改稿、不触发额外返工。保留真实/误报/撤回的原记录和依据。

对事实、机制、口径、主辅链语义、阅读路径、关系误连、图表/单位/负号、字体/容量、编辑行为及效率分别说明实际范围与证据，记录受影响节点/页/对象、严重度、未观察项和最早责任层。布局种类、空白比例、字段或哈希通过不替代专业判断。比较计划/对象/渲染；忠实实现有问题的设计仍保留Art发现。

Review actual editing fidelity against the current Art design. Separate named objects
must remain distinct; native groups preserve editable children and the declared
group paths. Missing objects, unapproved merges/splits/regrouping or flattened
substitutes are Output deviations. Art owns whether the original boundaries
make editing natural; source traceability and complete text do not settle that
judgment. Record findings in the existing native_editability observation.



## Cloud font acceptance

Read `theme.typography.font_validation` from the resolved configuration. Each entry in `deferred_font_identities` is one font identity: `canonical_family` is the requested family, `aliases` are equivalent installed names, and `pptx_family` is the single name to write. Never interpret an alias as another fallback font. When mode is `preserve-name-defer-native` and the cloud renderer cannot resolve any name in an identity, missing native font availability is a deferred acceptance condition and does not block Logic; missing PowerPoint or WPS is likewise deferred target-application acceptance and does not block Logic:

- require both Latin and East Asian PPTX font fields to use that identity's exact `pptx_family`;
- report the requested canonical family, the matched installed name or `unavailable`, and the written PPTX name separately;
- forbid silent replacement and record any observed cloud-render substitution;
- treat cloud PNG/PDF output as diagnostic-only and do not require cloud PDF pixel equivalence;
- emit `font-validation-pending` for native reopen/render on a machine with the complete font; and
- allow PPTX delivery with that explicit pending state, but never claim final font-pixel acceptance.

An installed canonical name or any configured alias satisfies the same identity; a missing alias alone is not a font failure. `fail_on_missing_primary_font` still blocks substitution and authoritative render claims. It does not block writing a semantically correct PPTX for a font identity explicitly covered by the deferred-native policy. A missing non-deferred identity, a changed PPTX font name, or a claimed authoritative render without the font remains blocking.


## 当前报告与交付

保留同run的四阶段interface、三读者原首读/对照/复看、Auditor、七项QA、实际环境和训练绑定。root使用workflow_cli publish及verify-handoff产生mode-delivery/1.0与mode-supervision-report/1.0；完整报告从真实快照派生，current与history清楚区分。交付PPTX、PDF、全页图、研究、Copy真实图链、Art设计/知识证据、Output脚本资源和全部观察。不得改旧report3.6/QA的contract冒称新报告，也不调用publish_supervised_pair作为本模式发布器。

核实用户明确硬条件与发布条件，不把普通发现额外变成审批门槛。真实绑定/格式/证据失败按原核心处理，质量fail/deferred/unknown如实保留，不能因交付而变pass。原生QA并不证明通用能力提升。费用未知为null，原始usage缺失不等于免费；保留全部失败、实际渲染和返工消耗。

方法迭代只在本任务授权的独立候选内记录问题、证据、竞争解释、可复用改动、反例和适用范围；不自动晋级、不将公司答案喂下一轮。正常制作不修改组件。NAS归档按当前项目共享规则及实时health，核对真实completed回执和文件哈希；归档不是内容质量通过。

### Local r17.1 — calibrate typography findings to observable impact

For a Chinese wrap finding, identify the actual affected reading relationship
and distinguish typographic convention, optional polishing and demonstrated
comprehension loss. Chinese permits many inter-character breaks; a split
dictionary word alone is insufficient evidence for failure. Numeric/symbol
combinations and punctuation have their own conventions; consult the scoped
knowledge before generalizing. A reader pass does not erase an independent
hierarchy observation, and an author's aesthetic preference does not prove a
reader failed. Keep the original finding and evidence; no retrospective
relabelling of frozen runs, extra reader gate or renewed repair allowance.
