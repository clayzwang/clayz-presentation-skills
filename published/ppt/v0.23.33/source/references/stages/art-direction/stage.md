# Art：按语义组织空间与关系

## 可选：把原文语义片段落实到多个原生对象

一个Copy正文单元与一个视觉文本框是不同层次。模型可以根据当前角色、条件、
对应或比较关系选择原文的连续片段及各自位置；共享限定仍须能接回完整判断。
连续推理需要整段时保留整段，分开后是否更清楚要看实际页面和读者理解。

`packages.layout.semantic_fragments.add_text_fragments`把一个无控制字符的完整
段落，按作者给出的Unicode半开区间和EMU坐标创建多个可编辑文本框。作者提供
`node_id`、当前配置字体、明确字号/颜色/四边距/对齐及可选强调区间；工具复用
既有`project_emphasis`保留跨框强调，并按原文顺序连续创建对象。它不选择拆分、
重点、视觉阅读方向或布局，不改文字，不自动缩字、保存、导出或启动Office。

当前原生文字诊断按XML顺序连接`a:t`并核对完整文字，未要求一个正文只在一个框。
本原语保持该连续顺序，但当前图中各片段如何共同解释、对应和限定，仍由Art
判断。若作者在这些片段的XML顺序中插入其他标签，或随后改字，原有诊断与实际
读取可能不再对应；不能为通过检查改Copy、删限定或改变评价器。

`fragments`每项只有`start`、`end`、`box_emu=[left,top,width,height]`，区间完整
覆盖原段且不重叠/遗漏；`margins_emu`按left/top/right/bottom提供。返回实际shape、
原node身份、源区间和原生名称/几何，作者仍按当前design接口登记真实映射和分组。
它没有生成新的标题/关系，不能把返回字段当成设计、容量或质量通过。

这是可选制作原语。多段或含控制字符的内容继续使用既有原生制作方法，不为调用
工具重写原文。实际字体、宽高余量、图像、阅读路径和目标应用行为仍在原预算内
观察；内存构造测试不证明专业、生动或更快。现有独立读者与有限返工保持。

## 专业内容阅读与原始依据分别保留

理解当前Copy时，先认清整稿推进、各级标题的统领、正文解释及所有关系的类型、
方向和范围。必要时可用scripts/copy_semantic_view.py --graph 当前graph.json
--output 一个新文件生成可选阅读视图；它保留完整标题正文、表值/轴/单位/期间、
节点层级、事实/计算/解释/预期/未知分类和原选表范围坐标，不自动拆段或决定布局。
原生Copy图仍是唯一内容身份来源；所有核对、锁定、返工及交接继续用原字节，
不得把阅读视图作为新的Copy graph，也不把工具输出当作理解或专业质量通过。

视图不展示来源跨度/编辑理由、选表理由和作者自评。判断研究支持或选择范围
需要这些依据时，仍在当前授权范围内核对原图；正文中的条件、例外和不确定性
必须完整阅读，分类标签不是事实正确的证明。脚本不跟随report或其他来源路径，
不授予额外材料权限、不开放新检索，不改变现有角色或独立读者的输入。

## 从内容关系选择可见表征

以观众在当前页需要认出、比较或解释的关系为设计起点，再理解当前Copy中的
参与者、对象、动作、条件和共同限定。连续文字适合保留推理和必要边界；当
对应、包含、差异、并行或时序主要依赖读者反复在长段中搜索时，可以比较
空间分组、直接对应、图表、机制示意和图文协作是否让这种联系更容易看见。
选用的知识应帮助这个具体取舍，不能只给既成的整段文字容器补一条原则。

图形和连线的含义须由当前有依据的关系承担：位置相邻不自动是流程，箭头
不自动是因果，不把多个并行职责画成串行依赖。主次、阅读路径与必要说明
共同构成设计；大数字、统一配色或没有碰撞各自都不代表整页已经专业生动。
保持原Copy内容和可追溯映射，按实际图形及原读者理解检验；不规定每页必须
用图、固定栏数、图型菜单或新的质量闸门。

## 持续专业能力：专业、精准、生动的设计

本阶段持续有效使用工具包与知识包，把Copy内容及其关系转化为专业、精准、
生动的排版设计。工具支持原生实现，知识支持对当前任务的理解和取舍；设计
质量通过实际作品、阅读路径与读者认识检验。局部标签、碰撞、端点或元数据
修补属于实施证据，不能替代完整设计目标。

在全稿视觉系统和逐页任务中，专业性体现在层级、秩序、排印、节奏与一致的
识别；精准性体现在对象、数据、关系、范围及限定的对应；生动性体现在恰当
的图表、图文和空间组织让重要差异、机制和联系容易把握。实际阅读相关知识
再作采用、调整或放弃，使用合适媒介和原生工具；不以装饰、配图数量、固定
栏数或知识命中数替代这些判断。Copy锁及既有独立读者、预算和未知边界保持。

本文件适用于workflow_cli创建的fast/normal/train任务。当前输入为professional-input/2.0，交接用stage-interface/1.0；完整操作见 packages/contracts/three-modes.zh-CN.md 与 packages/contracts/three-mode-command-boundaries.zh-CN.md。历史3.x包装、旧读者和旧发布指令仅见 references/legacy/three-modes-interface-r01/，不作为本模式步骤。

## 当前Copy—Art接口与职责

先读 packages/contracts/copy-graph.zh-CN.md。专业内容输入只能是接口无损输出的Copy语义图；其载荷与Copy输出相同。理解全稿主链和逐页辅链，再选择符合节点职责、层级和连接的呈现。一级标题恰为本页storyline。逻辑连接不一定画出来，视觉形式不能制造或替换关系。

Art无权修改文字、标题、正文、数据、层级、页序、页数及任何逻辑连接，也无权退回Copy重写。问题按具体节点和影响写入audit_observations（disposition=audit-only），忠实保留进原生审计报告。禁止art_content及文字expression_additions。设计与planning均绑定copy_structure_lock，工具检查精确接口和页序；Output比较原Copy技术位置，不能用Art改文案解决容量问题。

保持原有A01—A11、知识学习、真实图片稿、原生对象、读者和Auditor流程。Art根据内容决定空间、字体、媒介、视觉组合与阅读动线，不能把一个文字元素等同一个框；多维数组可用表、图等忠实表达。工具生成的QA位置投影不是Copy的新增切分或设计要求。

先理解当前页storyline、head/body职责和有向/对称/联合关系，再以当前表达问题进入所选知识包。可以从domain-map.json或节点的composition_readings选择相关CU，实际读取完整正文再判断适用性；不遍读全部条目或按命中数量证明设计质量。迁移元素职责、组合、阅读路径和图文协作，不复制参考的元素数、方向、空间比例或容量。现有Art过程和art_cognition中保留实际节点码、CU编码、实际读取的文件/工具记录，以及采用、调整或不采用的具体理由。知识建议不能授权改写Copy结构；冲突进入audit_observations。

## 先建立整稿系统，再落实局部布局

在现有 A01—A03 与 planning 中，从完整 Copy 的 cover/content/closing 角色、主链和反复出现的对象形成这份稿件的视觉系统，再做各页 A04—A09。说明首页如何建立身份与进入正文，同级标题如何保持可识别的层级，以及字体、字重、颜色职责、对齐与定位线索中哪些规则持续、哪些能随页面任务改变。记录当前系统的允许变化边界和理由，不只列一组字号或逐页布局名称；A10/A11 再用真实页面序列检查是否兑现。使用已有 art_cognition、planning 与过程，不新增表单、作者或审批步骤。

从本次问题进入已绑定知识：系列规则可查 K.SYS、P.SYS.FAMILY、P.SYS.SEMANTIC_GRAMMAR；标题、段落、主次和留白可查 P.LANG.TEXT_ORGANIZATION、P.PER.HIERARCHY、P.COMP.SPACE，并按需要阅读全文 CU。这些入口已有原则，不复制其正文为另一套知识；调用与采用仍须记录真实读取和当前适用理由。字体环境以实际资产与重开观察为准，缺失保留未知。

局部自适应是在该系统内响应语义关系与容量，不是每页随机改变同级标题的字色、位置或断行语法，也不是把所有页写死为统一 y 坐标、高度或固定模板。封面和正文职责不同可以有不同构图，同类比较为便于核对可以同构；变化不能让同级身份难以追踪。先按完整意义单元检查实际标题断点、标题与正文的层级及归属，再在 Copy 原字节内调整空间和排印；禁止保护所有词的机械禁断清单或用技术容纳通过代替实际读图。无法忠实容纳时保留 audit-only 问题，不能替 Copy 改文案。

保存前先完成实际写入所需的元数据与绑定；若保存已实际写盘、随后退出码为 1，仍计入已有写盘次数。保留原始返回、文件与哈希，依据实际阶段区分写盘、导出和退出失败；元数据前置不构成新增一次免费保存，也不改变每次导出或持久 Office 的预算。执行接口只记录真实结果，不替上述专业判断。

## 可选的首次保存前元数据写入原语

采用python-pptx创建新演示文稿时，可以在既有首次save之前调用
`packages.pptx_attribution.apply_configured_custom_properties(prs, canonical_config)`。
canonical_config须由本轮technical_files.canonical_task_config的精确JSON读取，
不得取安装默认配置或手写版本。函数按当前metadata模式写入配置的custom_properties，
用XML转义保存名称和值，建立OPC属性部件及关系；不会把keywords当作custom属性。
已有所需属性完全相符时保持原部件，冲突或缺项时报错留给作者明确处理，不静默覆盖。
它只操作内存中的既有演示，不保存、不导出、不启动Office、不改可见内容。
使用者仍在原预算内执行已有首次保存，并实际读取ZIP属性及关系确认结果。
返回created/retained只说明写入动作，不证明成品、字体、容量或目标应用通过。
这是落实已有配置的可选制作原语，没有新增元数据要求、读者或免费保存。

## 当前读者与返工

normal/train的layout读者检查实际全页图，唯一repair回Art；final读者唯一repair回Copy后，Art忠实重做新输入。受影响下游旧通过失效，由原读者confirmation复看；不新增title/content门禁、读者或返工预算。Art自身发现内容问题仅记录audit-only，不自行改文案。

Art owns presentation structure and design. Read the whole Copy document and
the complete story it communicates, then decide how the audience should see
and understand it. Textual headings are meaning cues, not geometry or styling
commands. Copy's editorial order does not prescribe the visual reading path.

Fine body units expose semantic contributions, not a required number of boxes.
Read them together, their relationship purposes and the actual Copy explanation
when available. Decide which should share a paragraph, object or visual group,
which merit emphasis, and which can be separated without breaking the account.
Keep qualifications and referents intelligible when changing visual order.
If a dependency is unclear, faithfully present the supplied connection and record the concern and uncertainty for audit. Do not change wording or connections.

Check that the actual page makes the argument and distinct judgments readable.
Font-size differences or faithful text alone are insufficient. Art chooses faithful spatial grouping and presentation. Content or structure objections remain audit-only. No mandatory heading count or layout is introduced.

## 当前输入与设计边界

只使用project投影的精确Copy graph、Art专业格式brief、当轮目标及已绑定知识。先前作者自评、读者答案、旧公司稿与旧3.x技术内容包不作为设计内容输入。运行配置由协调者单独保留；专业格式/字体约束通过brief传入，技术检查引用同run的canonical task-config，不另建或切换配置。

## Eleven concrete design results and knowledge codes — v0.20.2

Read [the Art design process](packages/contracts/art-design-process.md)
or its [Chinese peer](packages/contracts/art-design-process.zh-CN.md).
Execute the dependencies: whole-deck Copy preparation → whole-page semantic
preparation → attention decisions → expression/composition/element language →
draft observation and targeted revision. A04/A05 identify actual content
responsibilities and ownership; A06 consumes them to assign visual responsibility;
A07–A09 realize that intention. Text role, argument responsibility, category
ownership and visual responsibility are distinct, compatible dimensions.
Use applicable knowledge when making each choice, and explain the consequential
Copy objects/groups and reasons in existing planning. Generic deck statements
or code receipts alone do not complete these decisions.

Read [Art cognition and external learning](packages/contracts/art-cognition.md). Cover A01 task, A02 direction, A03 narrative, A04 page proposition, A05 roles/relations, A06 perception, A07 concept, A08 composition, A09 visual language, A10 integration, A11 critique. For each, state a scoped conclusion, actionable operations and checks/uncertainty in `art_cognition`; reuse unaffected work and revisit local choices. These are eleven thinking concerns, not eleven agents or approval steps.

When the user selects the foundations learning pack, validate it and use `scripts/art_learning.py lookup --pack <path> --code <Axx-or-principle>`. Read the principle, applicability, action, limitation and optional examples; cite exact consulted nodes and explain their effect on the choice. Do not merely append codes. Every code has a principle; cases are synthetic teaching examples, not university work or tested outcomes. Keep the package external to Light. The package is optional; concrete conclusions and actions are required for new Art work even without it.

Record art_cognition, copy_structure_lock and audit_observations in immutable planning and the actual Art plan. Preserve the Copy interface output exactly. The final reader assesses actual faithful presentation; content objections remain in the native audit report.

For problem-led learning, use the domain guidance in the Art design process.
An optional pack's `domains` reading map can connect a symptom to relevant
professional concepts without classifying it automatically. Learn the underlying
judgment before prescribing a page repair; keep study, application and observed
effect separate in existing notes. Let code follow the design decision.

## Composition guidance

Read [Reader-centered composition](../../../skills/clayz-presentation-art-direction/references/reader-centered-composition.md)
or its [Chinese peer](../../../skills/clayz-presentation-art-direction/references/reader-centered-composition.zh-CN.md) before
designing. Layout should help the reader perceive importance, relationships
and a useful reading path, with a comfortable rhythm across the whole deck.
Neat alignment, text containment and an explanation of the chosen layout do
not establish that result. Use the guidance to make and revise actual design
choices; it introduces no layout catalog, aesthetic score or approval form.

Judge page balance from the actual combined weight of color, filled area,
position, grouping and text density. Check that the strongest visible region
serves the intended hierarchy, including purposeful asymmetry. Revise a
secondary saturated panel or dense region that overwhelms the main evidence;
inspect the color drafts and sequence again before locking the baseline.

### Local r08.1 — preserve reading hierarchy during fit repairs

When repairing clipping, crowded sources or narrow columns, compare the actual
revised page with the understanding task again. A wider line or an uncut
paragraph can still flatten the distinction between the main result, its
business owner and the explanation. Trace the title's judgment to its visible
support, including any subject change within a paragraph. Inspect whether the
reader must reconstruct those pairings sentence by sentence after the repair.
If that relation has become harder to see, revise the affected typography,
grouping or spatial correspondence and inspect the page in its real sequence.
Retain continuous prose when it serves the relationship. This adds no required
labels, argument count, layout, score or approval gate; containment and reading
hierarchy remain separate observations in the existing Art critique.

Distinguish source locators from evidence needed to make the current judgment.
A comparison value or counterfactual may be factually retained in a source line
yet be absent from the main reading path. When its magnitude changes the
reader's interpretation, compare a visible placement near the relevant result
with the current footnote treatment; choose from the actual page and preserve
the comparison basis. This is a contextual hierarchy decision, not a rule to
promote every qualification or source number.


### Local r10.1 — measure native usable capacity before lock

Before locking, use the actual font and reopened native prototype to compare
text metrics against each text object's usable box and every native table cell.
Subtract the written native margins first; apply the configured internal reserve
to that usable width and height, including normal padding, vertical anchors and
paragraph spacing. A width scale or estimated line advance is only a design
estimate. Distinguish line advance, PDF font-metric boxes and visible ink; none
is interchangeable with the other two. Inspect the complete matched object/cell
set, and retain unmatched or unmeasured targets as unknown rather than pass.
Use the existing draft render and capacity evidence; this does not require a
second full-deck render or a new approval gate. Reconcile the result with the
locked object specifications. If the existing route cannot measure an item,
state that coverage limit instead of estimating a verified reserve.

Resolve a measured shortfall through Art's content relationships and available
space, preserving necessary explanation, font hierarchy and native editing
boundaries. Review the affected whole page again: a title's wrap should preserve
readable meaning units, and a narrow closing panel may repeat the nearby claim
and consume attention without adding a useful conclusion. Decide whether that
repetition aids recall or adds reading work from the actual sequence; no fixed
column count, wrap dictionary or mandatory deletion follows. Bounds and capacity
pass do not establish these reading qualities. The observed STKaiti metric
height of about 1.30 times the size in the AIA/LibreOffice run is not a universal
font, renderer, line-height or design constant.

## 当前交接

Art当前packet在technical_files.copy_art_identity_receipt提供实际identity回执副本及准确SHA256/bytes，供绑定presentation-only锁；content_files仍只有原字节graph。技术回执不引入报告、过程或额外作者自评。graph文件字节哈希与model.digest(graph)的规范化图摘要职责不同，不假定两者相同；精确interface锁按原生要求绑定回执文件哈希。



保存design、真实全页renders manifest与图、process、knowledge读取/应用证据，以及制作脚本和具名资源。协调者调用workflow_cli commit --stage art；工具检查精确Copy图/identity回执、页数页序、真实图及presentation-only结构锁。新模式不生成旧3.x包来调用record-planning或lock-design。Light不含固定布局目录，设计不受命名模式、容器形状或布局白名单约束。

## Page planning before object specifications — v0.19.0

Read `packages/contracts/page-planning.md` or its Chinese peer. First
understand the page message, content groups, ownership, passage functions and
supported relationships. Save readable page planning before refining object
specifications: overall arrangement and reasons, attention and reading path,
important element treatments, and whether ordinals, labels, emphasis or a slogan
help. Record actual presentation choices and revisions with purpose, Copy basis, evidence and impact. Preserve Copy wording, data, relationships, hierarchy, page order and pagination exactly; no art_content or added expression text. Content objections are audit-only. Visual grouping and the reading path may change only while preserving those meanings and identities.

Let one element or coherent combination serve mutually supporting functions.
A process block's own direction-bearing shape may replace a separate arrow
when the relation and readable text space remain clear. Shape, line and type
are freely chosen means; no compulsory silhouette, equal group sizes, object
count or arrow prohibition applies. Explain semantic containment and native
editing groups separately.

Save actual immutable planning as a named design/process artifact, then build and inspect images and matching specifications. Save real revisions when the draft reveals a better choice. Bind planning, full-deck images and specifications through current design/renders/process roles and workflow_cli commit; do not create an old package wrapper for this task. Generic purpose
labels, technical coordinates and retrospective explanations do not establish
reader-centered planning. Audit actual realization and retain missing evidence
or ineffective choices as findings.

## References and original design

Use the model's design ability to develop the composition from this story and
audience. Seek relevant design references online when they help resolve a
specific design question. Choose useful references
from spatial design, graphic design, editorial composition, advertising or
other appropriate disciplines. Search and inspect them according to the
page's communication problem; there is no required number or finite menu.

Use the actual knowledge package bound for this task. Before design/script writing, follow the current expression problem to the relevant index nodes and full CU text, including visual material when present. Do not substitute another package, invent an installation or read every record by default.
Connect the useful principles to this story and audience. An index entry,
method name or receipt alone is not learning adoption.

No match, unavailable browsing or insufficient references permits original
design. Record what was actually available and consulted and the limitation.
Never fabricate a source, named registered pattern, retrieval or attribution.
Original composition does not require registration or a source receipt.

Use existing work notes and `reference_research` to preserve the actual source
approach and consequential uses. The optional external Art foundations package ships as a separate release asset; it is not a layout catalog or owner-admitted knowledge. Online design research is authorized by
this workflow; it does not require approval for every reference. Keep asset
reuse rights distinct from looking at a composition for inspiration. Record a
new asset in the normal resource evidence without silently changing user
requirements or resetting an unchanged preflight.

## Context and authority

Consume the exact current professional packet and Copy graph. Preserve the Copy identity, source locators, node relationships and current-stage goal. Use professional formatting requirements supplied by root; technical scripts use the same run task-config and locked environment separately. Read current stage-enablement and relevant reader-quality/production-reliability methods; do not import their historical package envelopes or old gates.

Preserve actual source provenance and asset rights. Retrieve selected learning through available tools; a required bound knowledge item must be read or its limitation disclosed. Original design does not require a registered pattern. No invented reference, rights, host read receipt or adoption claim is permitted.

## Design

1. Prepare the entire Copy story, then each whole page under the
   [design process](packages/contracts/art-design-process.md). Distinguish
   text roles, argument responsibilities, category ownership and dependencies
   before assigning visual responsibility. Bind consequential A04/A05 judgments
   to identifiable content; use them to decide A06's intended attention and
   reading order. Preserve shared qualifications and complete comparison sets.
2. Choose composition, hierarchy, grouping, medium, spacing and reading paths
   from that content. Make the important relationship perceptible in the
   spatial arrangement; a heading/body pair does not imply its own equal
   rectangle. Columns, tables, ladders and other arrangements remain available
   Art choices, without Copy prescribing them. Shared drawing code implements
   these choices rather than supplying their default geometry.
   Let the whole composition communicate alongside the words. Choose spatial,
   pictorial or typographic means freely for the content; frames, blocks and
   background depth are examples, never required objects or a layout recipe.
   Inspect whether the actual arrangement expresses the intended relationships
   and emphasis, and preserve useful contrast when correcting balance.
3. Decide native editing boundaries as part of the design. Content that needs
   independent selection, movement, width or format changes becomes a separate
   object. Natural continuous paragraphs may share one text box. Use native
   groups when separate editable children should move together. Equal textual levels may have different styles
   or visual weight. Preserve actual meaning; visual sequence must not invent a
   business sequence, rank, cause or relationship.
4. Use approved data for charts and tables. If choosing tabular presentation,
   specify an integrated native table. Govern images, logos and symbols by
   purpose and rights; decorative ordinals must not imply unsupported rank.
   When native reopening wraps a cell differently from measurement, consider
   a small target/font-specific `semantic_table.plan(native_width_scale=...)`
   calibration, then inspect the reflow and available height. Its default is 1;
   a previous case's value is not a universal preset. For source links, choosing
   the actual annotation object or Copy range can avoid linking a product name
   that happens to equal a source code .
   When an explicit source-link scope is selected, check whether an older
   whole-heading fallback still adds unrelated clickable text. Inspect the
   actual clickable objects as well as the correctly linked source codes.
5. Produce readable PNG/JPEG drafts of every page using the actual approved
   text from the Copy interface, preserving differences. Inspect thumbnails, full-size pages and the actual page sequence.
   Judge attention, relationships, reading effort, visual fatigue, purposeful
   repetition, whitespace and the combined weight of color and text. Check
   whether filled areas and dense passages pull attention to the intended
   evidence and conditions. If consecutive pages flatten different tasks
   into the same reading experience, revise the affected designs and inspect
   the sequence again. Retain repetition when its comparison or progression
   benefit remains visible. No fixed card count, area ratio, font-level parity
   or random variation establishes quality.
6. Refine a matching visual specification with coordinates, typography,
   native targets and bounded technical adjustments. Bind each Copy ID once
   for traceability; several IDs may bind one object through disjoint text
   ranges. Art's `reading_sequence` is independent of Copy's array order.
7. Retain the exact Copy interface graph and lock. Record actual concerns in audit_observations with audit-only disposition. Output implements the locked faithful presentation; no Art content projection or upstream rewriting is allowed.
8. Reconcile all page images with specifications before current-mode commit. Save the real baseline revision and its hashes. The coordinator commits design/renders/process/knowledge and named resources through workflow_cli; the exact graph, lock and page identities remain subject to the existing core checks. Old package3.x plan validators are used only for an explicitly supplied historical binding, not manufactured as another gate for this packet.

Each baseline element is one independently retained native object. Declare a
unique `native_name` and `render_separately:true` on that Art element; several
Copy IDs may belong to it. For native grouping, add `native_group_path` with
group names outermost first. An omitted path means an ungrouped object.
Use the existing purpose and work notes to explain consequential editing choices.
Output must preserve these object boundaries and groups. It cannot merge, split,
regroup or flatten them for convenience; a boundary change returns to Art.
Text ranges prove content coverage, while native object structure proves the
declared editing behavior. Neither alone proves comfortable editing.

A semantic layout tree, A/B prototype, relative-layout solver or external
learning pattern may help a particular design. Use them when useful; none is a
required style, creativity gate or substitute for inspecting the drafts.
Avoid overloading a page or shortening necessary Copy to satisfy symmetry.
Technical text capacity and approximately 10% internal reserve support editable
delivery; they are not whole-slide whitespace quotas.

## Work record at handoff

Save actual planning/design decisions, knowledge read evidence and concrete adoption/adjustment/non-adoption reasons, native source, full-page images, scripts/resources and unresolved audit observations under new revision paths. Include them in process/knowledge or extra named file roles; current commit snapshots exact bytes and event order. Do not reconstruct planning from the later Output file. Output consumes project design/renders/images and named resources, including the native source when supplied.

## Native production checks

Apply actual native preview, inspectable knowledge reads, table-cell/footer checks, bound visual evidence and stale-record rejection within the current route and budget. Read the bound external knowledge’s philosophy and relevant full methods before design. Preserve failed readings and disclose actual reader/Auditor context and unobserved applications. These are professional checks, not the old five-stage or extra development gates.


### Local r11.1 — choose the relationship before its visual form

Use the mounted knowledge's existing relationship, grouping and text-organization
chapters to decide what the audience must connect. Trace a consequential reader
operation through the actual draft: finding a business, locating its value,
retaining a sign or scope, and connecting an explanation. Identify the operation
that the current arrangement still leaves to memory or search. Compare a
suitable alternative for that relationship before settling the existing page
plan; a small sketch or native fragment within the current budget can reveal
this without another full-deck production cycle. A sequence, shared semantic
region, aligned values or continuous paragraphs may serve the relation. Rejecting
an unsupported complete causal bridge does not require retaining every partial
comparison as a paragraph. Keep attribution and quantified causation distinct. Distinguish sequence from elapsed time/causality, proximity
from ownership, and an equation row from a single economic cause. Retain labels,
units and the scope/purpose of mixed components when changing representation.
No diagram quota, fixed column count, or company-specific layout is implied.

During actual native reading distinguish the font-metric box, visible ink,
container inner bounds and total remaining space. A total reserve pass does not
prove the box stays inside each padding edge; no visible clipping does not clear
that geometric finding. An unmatched line remains unmatched in the original
report even when spatially bound PDF-word evidence supports its full text.
Keep unresolved results instead of deriving a new tolerance from one renderer.
Read numeric ranges and their units as meaning units alongside words; preserve
continuous reading where the current geometry allows, without a universal ban
on breaks or shrinking the font. This extends existing native/semantic reading,
not another review stage. See the mounted r11 production observation for limits.

### Local r12.1 — keep the scope of a typography repair explicit

A native measurement can reveal a capacity problem without invalidating every
existing line break. Identify the actual objects and properties to change;
preserve unaffected authored lines and compare the affected paragraph before
and after. A global width recalibration can alter previously readable units,
so use it only when the evidence concerns those objects too. This is not a
requirement to retain an ineffective layout or a new approval gate.

Read resolved typography minima before constructing the first draft, including
annotations. `scripts/native_text_revision.py` offers configured_size and a
line-only revision helper that leaves other objects unchanged. Art still
chooses the lines. Its line_capacity helper describes candidate widths with
measurement provenance; assess manual lines as well as automatic candidates.
Joining a range or amount-unit phrase can exceed native capacity. Consider the
surrounding clause and available region together; do not silently shrink or
reflow the whole deck. The helper neither wraps text nor supplies a quality pass.

For python-pptx native tables, write padding on the cell itself (tcPr); setting
cell.text_frame margins addresses bodyPr and does not establish effective cell
padding. The same helper accepts either a native cell or a TextFrame explicitly.
Reopen the saved object and inspect the actual properties, then retain native
metric and visible-ink observations separately. Keep the existing bounded
repair policy: unsuccessful rereading is a retained failure, not permission to
start another loop under a new label.

### Local r13.1 — carry the chosen font into the actual native process

Use the existing native renderer with the task's explicit font identity:
`render(pptx, directory, slide_ids, font_file=resolved_font_path,
font_family=resolved_family, fontconfig=existing_fontconfig_path)`.
The equivalent CLI requires `--font-file` and `--font-family`; supply
`--fontconfig` for the already configured runtime font environment. These are
paths/values from this task's runtime setup, not a new font search or route.
The old three-argument call now stops before conversion rather than rendering
with an unbound font. With no fontconfig argument, inherited resolution must
still match the requested file hash. The renderer forwards the environment to
LibreOffice/Poppler, saves `font-environment.json`, and stops before PDF
conversion on a mismatch. This precheck does not replace PDF font or glyph
inspection and does not make another full render available under the budget.

For fixed-size native paragraphs, `set_paragraph_edge_space(cell_or_text_frame,
left_pt, right_pt)` writes real paragraph space inside native padding. Choose
its value and affected paragraphs deliberately; it replaces existing paragraph
marL/marR and can affect indentation or bullets. It leaves font and shape size
unchanged. `native_capacity` reads actual cell/TextFrame margins plus those
paragraph edges, reports both axes and consumes the extra space. Supply actual
candidate run metrics and dimensions; use it before save and after reopening.
Before fitting candidate lines, derive usable width from the actual object
margins and paragraph edges, then apply the reserve to that usable width.
Construct the candidate emphasis runs before assessing their width: the ordinary
font estimate used by measure_lines does not measure mixed bold/native runs.
Keep that estimate distinct from reopened native metrics; a previously observed
width_scale is not a guarantee. Inspect the actual longest styled lines in the
existing native draft review, and compare both object capacity and its clearance
from the actual adjacent footer. Do not infer footer clearance from a fixed
body-bottom coordinate or infer inner-edge containment from total reserve.
If the measurements differ, preserve the concrete dimensions and unresolved
factors rather than increasing a global coefficient until the check passes.

Before spending the allowed local repair, calculate what the observed deficit
requires. For unchanged styled line span L and reserve r, usable width must be
at least L/(1-r); add actual object margins and paragraph-edge allowances only
once. scripts/plan_text_capacity.py calculates this lower bound from explicit
measurements; it is not an acceptance checker. Compare the result with available
page space, then choose a wider frame or a different line/group arrangement.
If the text, runs or wrapping change, the old span is only a diagnostic bound,
not a prediction. Reopen and measure within the existing render budget. Do not
round near-threshold failures up, add global shrinkage, or alter the threshold.
A font size is not measured text height. Auto-fit, hanging indents, bullets,
vertical text and renderer transformations need their own geometry observation;
the fixed-box estimate does not cover them. A positive reserve does not prove
inner-edge containment, visible ink or readable relationships. Keep the
original glyph/capacity checks and bounded visual reading unchanged.


### Local r15.1 — read beyond the entry point

After identifying the title and the first emphasized element, follow the body
in the actual requested font: can the audience distinguish the current claim,
its necessary explanation and relevant qualification at their point of use?
A whole paragraph in an accent color or a large tinted box may give an entry
without expressing the relationships inside it. Choose emphasis spans, paragraph
boundaries, alignment and space around those relationships; do not treat every
Copy unit or sentence as requiring equal visual weight or a separate card.
When a native writer breaks a logical paragraph into manual visual lines,
represent authored emphasis as half-open Unicode character intervals in the
original paragraph. Use `packages/layout/text_emphasis.py:project_emphasis`
to project those ranges into each line's runs; concatenated lines must preserve
the exact original text. Do not search each already-broken line for a whole
phrase: a cross-line phrase would silently lose its styling, and repeated text
could select the wrong occurrence. Art chooses the ranges and line breaks;
the helper chooses neither. Inspect the actual runs and rendered fragments,
including both members of a comparison when both were meant to be emphasized.
This is a faithful implementation aid, not proof of a useful visual hierarchy.
Keep long prose where continuous reasoning needs it. Across the sequence, check
whether a familiar-looking value still refers to the same metric and scope.
Record what the real prototype makes visible in existing Art observations;
capacity, object counts and unchanged text do not establish this result.
No fixed argument count, layout quota, font replacement or additional reader
gate is introduced. Preserve the original final reader and repair budgets.


### Local r17.1 — judge Chinese line breaks in their reading context

When inspecting Chinese text, distinguish an allowed inter-character break
from a broken numeric/symbol combination and from an observed loss of meaning
or correspondence. Read P.LANG.TEXT_ORGANIZATION and its scoped W3C sources
for that distinction. A dictionary word crossing a line is not by itself a
defect. In a short heading or comparison label, a phrase boundary may still
help the current reading task; compare it on the actual page rather than
extending it to a deck-wide protected-word list. Identify the affected subject,
unit, qualifier or reading path before requesting a repair. Preserve ordinary
flow when a change would merely exchange one acceptable break for another.
Inspect hierarchy separately: a brightly emphasized exception can overshadow
the main result even if every line break is acceptable. These judgments do not
waive clipping, capacity, content, final-reader or bounded-return checks.

## 当前r03的身份技术文件

professional-input.json的content_files仍只含原字节graph；technical_files.copy_art_identity_receipt指向原生project复制的实际identity回执。只用该回执的准确身份绑定copy_structure_lock.interface，图规范化model.digest与原JSON文件字节SHA256分别核验。该技术文件不提供Logic正文、作者自评或读者结论，不以原始路径扩展阅读权限。

## 当前过程记录格式

交接process使用包根 packages/contracts/process-evidence.zh-CN.md 的顶层process.events，每项action / record / artifacts记录真实当时行为。actual_actions或commands原始日志需按实际事项适配，不能代替该字段；保留原件，不把格式示例当执行证据。

当前知识理由与历史评审须分列。knowledge及具名knowledge-node-return / knowledge-cu-return / knowledge-read-command / knowledge-manifest保存本run实际读取快照；比较读者仅收到 packages/contracts/reader-knowledge-evidence.zh-CN.md 的专业白名单。正文缺失或原包身份未验证如实记录，不把CU ID、作者理解或新复制的正文当作设计前已读证明。

## 本地r10 规范技术配置

Art和Output的professional-input.technical_files.canonical_task_config为当前run已经冻结的task-config精确字节，含路径、SHA256和字节数。它是技术约束，不增加公司内容输入；Art仍只消费原字节Copy图，Output仍消费design/renders及真实制作资源。以此核对当前identity、字体、颜色及制作配置，不能取安装包默认配置、历史稿或作者自评作替代。缺失或身份不符时保留实际错误，不静默派生默认值。该投影不证明配置已落实到原生对象/元数据，也不证明字体、编辑、容量或渲染检查通过。Office运行身份/累计计数仍须实际运行证据，不能由冻结配置推断。既有四类Kproof边界、读者清洁输入、判定、预算与失败规则不变。

## 可选原生文字策略工具


`packages.layout.native_text`提供`configure_frame(frame, fit="fixed", wrap=True)`与
`configure_paragraph(paragraph, align="left")`。Art按当前文字角色选择fixed/shrink/grow/inherit、
wrap及left/center/right/justify/inherit，不由模板推断。对每个新建段落分别设置所选对齐，
避免无意沿用主题或对象中的旧属性。工具不清空文字，不改字体/边距/行距/几何/数据/字段。
fixed仅阻止自动缩字和扩框，仍可能溢出；必要留白、断行、容量、真实像素和目标应用行为
继续实际观察。它是可选制作原语，不是必选版式、全稿批改命令、质量门禁或自动通过依据。

## 当前知识与锁稿证据格式

实际交接前读取[Art知识证据与原生锁](../../art-knowledge-evidence.zh-CN.md)。该页只解释现有knowledge/proof/process/Copy锁/真实renders格式，不新增门禁、不改知识正文、不把哈希或作者自评当阅读或效果证明。

## 当前来源与原生关系交接

实际交接前读取[来源定位与原生关系](../../source-native-relations.zh-CN.md)。该页只解释现有knowledge/proof/process/Copy锁/真实renders格式，不新增门禁、不改知识正文、不把哈希或作者自评当阅读或效果证明。

## 可选原生固定页脚字段

`packages.layout.footer_fields.set_fixed_footer_number(shape, value)`仅转换已创建的专用页码/页脚placeholder与slidenum/footer字段，保留字体、几何及field身份。调用者明确提供语义页号，自行排除封面并维护序列；它不计算页角色、不加静态覆盖、不承诺移动/重排自动编号。未知字段、普通文字对象或非法值在写入前拒绝。固定缓存与实际应用显示分别记录，仍须看全页图；这是可选制作原语，不是默认版式、新门禁或质量通过依据。

## 可选提前原生保真诊断

`scripts/native_copy_diagnostic.py --graph 当前原字节Copy图 --pptx 已保存当前源 --output 新诊断.json`只读复用既有Native capture规则核当前页数/原生文字与图表缓存，可在消耗下一次导出或最后保存前发现遗漏。必要实现修订须按原内容/设计与剩余额度合并，不改源语义图或门禁来通过。诊断只临时复制输入字节，不启动run/Office、不制作PPTX、不渲染；旧文件不改。全部七项专业/视觉QA明确not-observed，缓存值存在不证明自动标签可见，仍须实看全页图/实际原生编辑并记录字体、容量与未测范围。这是可选早期诊断，未取代正式Output提交或新增质量门槛。
