# Output：忠实、可编辑且可验证的实现

本文件适用于workflow_cli创建的fast/normal/train任务。当前输入为professional-input/2.0，交接用stage-interface/1.0；完整操作见 packages/contracts/three-modes.zh-CN.md 与 packages/contracts/three-mode-command-boundaries.zh-CN.md。历史3.x包装、旧读者和旧发布指令仅见 references/legacy/three-modes-interface-r01/，不作为本模式步骤。

## 当前Art内容锁

只实现当前project中的design、renders、全页图和具名资源。保留Copy文字、数据、节点、关系、页数页序及Art原生对象/空间设计；没有Art改论点、改文案或改页数的分支。Art内容问题作为audit_observations保留。只在对应原生读者正式repair后重做受影响内容，Output不自行退回或改上游。

## 当前读者与返工

normal/train在Art的layout读者闭合后准备Output，成品final读者的唯一repair回Copy并重做Art/Output。confirmation使用原读者，旧失败、消耗和残留不重置。Auditor只记录，不开启新返工；fast只有实际技术核验，不声称独立读者通过。

## Production reliability (v0.17.6)

Read `packages/contracts/production-reliability.md` (or its `.zh-CN.md` peer). It supersedes older automatic font-size and consecutive-composition gates and inline report transport. Art owns rendered legibility and repetition; Output and Supervisor own editable delivery and PPTX size.

For v0.17.6, implement every tabular presentation as an integrated native table; return a medium change to Art when that is unavailable. Verify fonts inside native tables and charts, including Latin text and digits, using the current font audit and actual renders. Reserve approximately 10% internal usable capacity in text boxes and shapes under `layout.internal_content_reserve_ratio`; check internal overflow and object collisions as well as slide bounds and record PowerPoint/WPS coverage separately. See the production-reliability contract for the capacity definition.

## Reader understanding (v0.17.1)

Read `packages/contracts/reader-quality.md` or its `.zh-CN.md` peer
according to the task locale. Necessary explanation and evidence fidelity take
priority over shortness; use existing records for review observations.

Preserve the complete approved wording, including causal/comparison links
and qualifiers. Do not silently abbreviate, shrink illegibly or move necessary
body explanation into notes to solve overflow. Realize only changes authorized by the current native reader route; otherwise retain the specific capacity problem with evidence for the reader/audit record, without opening an extra return.

## 当前专业交接

读取当前stage-file-handoff及three-mode-command-boundaries。Output的必交角色为pptx、pdf、renders、qa、inventory、process，脚本和资源用额外具名角色保存。协调者用workflow_cli commit --stage output提交；不调用files-output或构造3.x内容包。完整report、Copy图、Art图及原生读者/审计记录由当前run保存，后续报告从真实快照派生。

## Page planning consumption — v0.19.0

Read the actual Art planning under locale-matched
`packages/contracts/page-planning.md` together with complete images and
object specifications. It explains content grouping, hierarchy, meaningful
shape/line/type functions and grounded additions. Implement the locked objects
and native editing boundaries; unresolved meaning/composition is recorded for the existing reader/audit route; Output cannot open an extra return or change locked upstream work. Preserve the planning source rather than
inventing a design rationale during implementation.

## Boundaries

### Local r08.1 — choose implementation from the locked native prototype

When Art supplies a hash-bound, editable native prototype, inspect that file
and its actual object properties before choosing to regenerate it. Check the
writer's coverage of the current specifications, including paragraph spacing,
text/table vertical anchors and connector endpoints when those are present.
A helper that handles only some fields cannot establish fidelity for the rest.
Adopt the verified native objects when that preserves the complete locked
design, or implement the missing properties explicitly. This choice does not
waive Output's final write, reopen, native comparison and actual rendering.

Keep native-object fidelity, visible clipping and text-metric capacity results
separate in the existing QA. A PDF font metric box is not a pixel-ink measure;
an uncut glyph in an image does not erase a recorded usable-capacity failure.
Retain the known result and the task's bounded repair policy rather than
regenerating unchanged pages to obtain a clean check. This is an implementation
action, not a new gate, font substitution or change to the approved content.

Own native object creation and technical coordinate realization within Art Direction tolerances, groups, charts, tables, SVG, media preparation, theme application, compatibility repair, package optimization, artifact metadata, and final write/reopen/render QA when the locked render route is available. Record deferred/not-run coverage when it is not.

Do not change approved text, data, relationships, page sequence, composition, or visual intent. Record material conflicts with evidence for the existing bounded reader/audit route; Output does not open an ad-hoc upstream return.


### Local r10.1 — revision-safe evidence and truthful handoff

Before running a revision script, enumerate its new writable outputs, including
command receipts, glyph/size/rhythm evidence, failure logs and manifests. Assign
the current revision to each and refuse any existing path; a filename left in a
reused script can destroy history even if the main deck is versioned. Use
`scripts/output_evidence_io.py`'s `ensure_new_paths` before invoking tools and
`write_new_json` for author-owned receipts, or equivalent exclusive-create
semantics. Inputs may be reused; previously written evidence is never an output
slot. Preserve original failures and save record corrections under a new path.
If an overwrite happens, restore only from a real hash-bound copy, record the
incident and distinguish unrecoverable bytes; never regenerate plausible history.

Before writing the stage execution declaration and formal work record, consume
the actual current original-validator result and process return code. Explicitly
check completed execution, record validity and the quality status being claimed.
A present JSON file, zero wrapper return, completed record chain or an intended
pass does not establish successful quality verification. Use `verification_observation`
and `require_verification` from the same helper to bind those observations; they
do not replace or change an original validator. A valid fail/unverified result
may be handed off accurately as such; a tool error cannot be recorded as pass.
For record-only validators, require completed/valid but preserve quality=unverified.
A formatting or import-path correction needs a new result and corrected handoff,
not another PPTX write or deck render. Keep the actual task render total, including
Art previews where counted, visible alongside the current Output count.

## Required context

1. Read the current professional packet’s design, renders, all actual page images, editable source and named resources. Inspect the exact Art revision; do not replace it with an older glob match. Technical authoring/rendering uses the same task-config and locked environment retained by root; no second preflight, legacy task-selection creation or alternate config.
2. Preserve selected master/layout, font identities, colors, native object names/groups, Copy ranges and resources. Use only real supplied assets with rights and hashes. Missing capabilities or required bytes are observations, not authority to silently substitute.
3. Read relevant native expression, layout and implementation methods when their object types are present. Optional layout trees/patterns/contracts are used only when Art supplied them; absence does not create a gate. Old package validators and calibration/report envelopes are not additional current-mode inputs.
4. A native-presentation-tool declaration is usable only under the actual bound preflight; declared capability is not final readiness. A real writer may be attemptable while quality checks remain pending. Keep every missing/unknown capability and actual failure; no spec-only or picture-only substitute for the required editable PPTX.
5. Reuse actual task knowledge/resources only as selected and documented. No prior-company answer, unconfirmed discussion draft, invented Library receipt or automatic knowledge commit enters production. Task attachments remain usable under their actual rights and context.

## Consume the visual baseline

Inspect all locked drafts together with the specification before building.
Record `output_started_at` and `visual_baseline_sha256` in QA. Do not start
without a complete valid baseline or replace native pages with preview images.
Preserve editable text, data-bound charts/tables and editable diagram objects;
photographs remain image assets. Log permitted micro-adjustments; record content, hierarchy or composition problems for the current bounded reader/audit route; do not modify locked upstream work or open another return.

For a later correction to observation prose, it can be useful to keep a dated
supplement linked to the original record. Distinguish when the visual baseline
was actually formed from when its description was corrected. An unchanged
design need not be rebuilt to repair a receipt; preserve its real baseline and
the later correction rather than treating the correction as a new design event.

## Workflow

Apply the shared artifact-led Library loop to the implementation plan: approved
visual intent -> concrete object/font/connector/capacity question -> Output
Library method -> revised implementation -> written-object and render check.
Inspect relevant implementation details, not only index metadata. Use a targeted
prototype when it resolves a material technical uncertainty before the full
build. Record which object behavior or rendered defect the reference improved.
The full deck follows the current approved Art Direction revision; do not reduce
it to familiar layout shells because they are easier to script. Record hierarchy, text and page-scope concerns against their earliest responsible stage. Rebuild only after the current native reader route changes the responsible artifact and dependent bindings; do not invent another return.

1. Use Art’s design/format requirements and the same run canonical task-config for technical colors, typography, layout roles, selected master, renderer, target applications, delivery profile and checks. Do not manufacture old acceptance/resource envelopes to satisfy another wrapper.
2. Bind the acceptance typography and performance budgets before creating objects. Consume the one `runtime-preflight.json` created by root Supervisor before Logic; Output must not run a second preflight. Verify that its run ID, task-request SHA-256, task-root SHA-256, canonical issuance/consumption receipt hashes, and resolved-config SHA-256 match this run, then consume its locked authoring and render route without rediscovering tools or switching routes. Preserve `target_application_checks` as observations separate from the route gate: an unavailable target-native reopen check is deferred evidence, not a reason to stop Logic or authoring. If a hard route failure requires a fallback, return control to Supervisor so it can close the run and restart from a fresh bound preflight within the configured restart budget.
3. Read the complete locked route capabilities, including available/attemptable and pending checks. Record unavailable capabilities rather than pretending support. Never add target-native acceptance capabilities to the required route merely because an application appears in target_applications; optional implementation guidance is used only when actually relevant and available.
4. Implement Art's locked visual specification directly. An externally supplied Pattern, Layout Contract or Layout Tree is optional; use its compilation tools only when actually selected by Art. An absent pattern or tree does not require a fallback. Preserve Art's native mappings, shared text ranges and independently chosen styles and reading paths.
5. Preserve exact locked copy and `copy_id` traceability in object names or the build inventory. Preserve Art's selected emphasis ranges across manual visual lines. If constructing runs from an approved logical paragraph, use `packages/layout/text_emphasis.py:project_emphasis` with its exact text, lines and selected source intervals; never infer ranges with per-line whole-phrase matching. Compare actual run styles and final pixels to the locked Art. A discovered omission already present in the locked design remains an upstream finding; Output cannot silently add emphasis.
6. Apply the configured theme. Never import a reference deck's master, font, or object styling unless the user supplied it as the active theme and redistribution is not involved. When a user master is configured, attempt that actual master and preserve its layout/theme mapping; do not silently replace it with a generated blank theme because inheritance is not yet verified.
7. Collect source material in one bounded round and cache it task-locally. Before the first write, verify the complete slide-role sequence including cover and closing, master/layout dependencies, any Storyline-to-placeholder binding explicitly required by a user-selected master, exact font names, copy-to-region capacity, intentional breaks, and internal object-collision risks. Never synthesize a smaller line beneath the Storyline merely because the master leaves room for one. Write the PPTX once. When the locked render capability is available and selected, reopen through that route, inspect package objects, run `packages/validators/audit_ppt_font_names.py` before rendering, render the selected final slide set and perform thumbnail plus full-size review. When rendering is unavailable or deliberately unselected, record `deferred` or `not-run` evidence and continue with the written PPTX; never claim render pass or invent pixels. Send the actual file, object and available render artifacts to Supervisor and the Independent Auditor; do not describe Output's own QA as an independent audit. Use `scripts/task_runtime.py check` to measure deterministic operations and reuse outputs only when their declared inputs and outputs still match. After a local repair, rerender affected pages when the route is available; master or global theme changes invalidate all affected pages. Final evidence must cover the final slide set when rendering is available, or state the exact coverage gap. For each configured target application, run native reopen/render only when that capability is available and selected within the bounded run; record available but unused targets as `not-selected`, unavailable targets as `deferred`, and executed targets as `pass` or `fail`. These states must flow into Supervisor's `environment_observation`. Resolve a deferred font identity against its canonical family plus aliases; one match satisfies the identity, and aliases never become fallback positions. Write the identity's exact `pptx_family` into both Latin and East Asian PPTX fields. `font-validation-pending` covers only native pixel acceptance and can never hide a wrong written family. When Office is selected, keep one process alive for the run instead of reopening the application per slide or check.
8. Keep technical fixes within this run’s canonical write/render/repair limits and the actual reader return state. Do not infer an extra repair from a helper or reset any used budget. Never let implementation repair rewrite locked content or design. Record actual writes, conversions, failures, reuse, elapsed times and reasons; an overrun is retained and the current enforced limit controls further work.
9. Stamp documented, removable clayz provenance into custom document properties:

```bash
python scripts/stamp_pptx_metadata.py <deck.pptx> --config <resolved-config.json>
```

10. Record bounded tool calls, artifacts, hashes, failures, capability resolutions, runtime preflight, and retrieval receipt IDs with task-local execution evidence; never record private chain-of-thought.
11. Save final PPTX/PDF, full-page renders, object inventory, process/deviations, font-name audit and explicit mode-output-qa/1.0 observations. Root keeps run/config/environment identity separately; these are not old package3.x envelope fields required on the author’s handoff. Verify each quantitative encoding against actual native chart/table/shape objects; a plan-object mismatch cannot be described away. Capture the written PPTX's actual slide count, object/media statistics, and per-slide visible text and speaker notes from the file when the runtime exposes them; distinguish extracted facts from planned intent and mark unavailable extraction as `not-recorded`. When deferred-native validation applies, include each identity's requested canonical family, matched installed name or `unavailable`, written-PPTX family counts, observed cloud renderer, diagnostic-only render status, and `font-validation-pending` acceptance state.
12. Emit task-local learning candidates only after final write, reopen, render, and inspection; persist them through the configured Output learning route and never auto-promote them. Candidates remain observation-only; discussion confirmation and immutable commit belong to the root facade and require the actual user's decision.

## Validation and current handoff

Audit written font names using the exact canonical config. For a deferred identity with font_asset, verify the actual supplied file hash/length/version; missing bytes remain deferred, mismatched bytes fail. When the exact font is available, carry its file/family and process fontconfig into rendering. Preserve exact Latin and East Asian PPTX font fields. Missing native font acceptance is font-validation-pending, not permission to rename the requested identity.

Under an existing preserve-name-defer-native policy, a locked LibreOffice conversion may produce diagnostic PDF/all-page images with actual fallback observations retained; save fc-match, renderer logs, pdffonts and page images. Do not claim exact-font or PowerPoint/WPS acceptance. render_native_preview.py’s exact file/family check remains unchanged; it is not evidence of exact-font success when the canonical file is missing.

Perform applicable native object, data, typography, capacity, bounds and actual render checks. Use validators only with the input contract they actually accept; old3.x package/plan/QA wrappers are historical-bound tools, not another required gate. Save raw return codes and original result files. Exceptions, import/help success or wrapper completion never become quality pass.

mode-output-qa/1.0 contains all_page_images, reading_path, data_signs_units, native_editability, fonts_native_reopen, overflow and relationship_expression. Each has pass/fail/not-observed/deferred, a concrete scope/explanation and true evidence; pass/fail require actual evidence. Interactive move/edit/data-label behavior requires actual application observation; object existence does not establish it. Keep unobserved checks pending.

Coordinator commits pptx/pdf/renders/qa/inventory/process and actual scripts/resources through workflow_cli. Only after the three current readers and record-only audit does root use workflow_cli publish and verify-handoff. The mode-delivery/mode-supervision-report paths are current; do not invoke publish_supervised_pair/assemble-report/record-stage or relabel legacy QA as new QA for this run.

## Work record at handoff

Use process and named evidence roles to retain actual design consumption, file/object checks, conversions, cache reuse, failures and limitations under new revision paths. Current commit captures immutable bytes and events. No five-stage record chain or historical calibration wrapper is required; do not backfill work or overwrite earlier evidence.

## v0.18.2 implementation boundary

In the current mode, implement Art's
locked drafts/specifications without inheriting old Copy atomicity, parent-target,
sibling-style or reading-order rules. Several Copy IDs may occupy one editable
text object or native cell through disjoint native_location.text_range bindings.
Verify each approved text range and actual complete coverage. Art chooses styles
and visual reading_sequence independently of textual heading levels and Copy array
order. No registered Pattern, Layout Contract or semantic tree is required.
Use such tools only when Art actually supplied them; optional absence is valid.
Current professional fields and mode-output-qa govern this run; old package field examples remain historical.

Preserve Art's editing boundaries: each baseline element's native_name,
render_separately:true, native type and optional native_group_path. Create
separate native children inside declared groups. Do not merge, split, regroup
or flatten objects for convenience; return boundary changes to Art. Inspect
real final PPTX objects as well as text ranges. Use package-specific comparison helpers only if their required historical package was genuinely supplied; otherwise preserve current-mode inventory/QA evidence without fabricating an envelope.

Read `packages/contracts/verification-outcomes.md` or its `.zh-CN.md` peer.
Use `--result-json <path>` on native comparison, Output QA and deviation-log
validation to retain automatic execution/integrity/quality diagnostics with the
existing command evidence. Do not interpret an exception as a quality finding,
or rewrite declared fail/deferred/uncertain results as pass to satisfy a record.
Fix affected tool/input causes, rerun affected checks and preserve earlier output.
The deviation-log validator's record pass is not a PPTX quality verdict.


## Native production checks

Apply actual native preview, table-cell/footer checks, bound visual evidence and stale-record rejection within current mode, route and budgets. Preserve failed readings, actual knowledge use, Auditor context limits and unobserved target applications; do not introduce historical development gates.


### Local r11.1 — preserve destination identity when restoring page fields

When a targeted prototype returns to full-deck order, restore the approved
slide-number text body into its existing destination shape; do not clone the
whole source shape with its slide-local cNvPr ID. `scripts/native_slide_number.py`
provides a narrow `restore_slide_number_field(target, source)` helper: it keeps
the destination ID/name/geometry, requires an automatic slidenum source and
matching geometry/style, and refuses relationship-bearing text. Other cloning
cases still need their own relationship and identity handling. Inspect actual
written IDs and reopen the exact final PPTX; unchanged parts or a mixed PDF do
not replace a required full-file reopen.

`write_new_json` in `scripts/output_evidence_io.py` serializes Path values as
paths but still rejects unknown objects before opening the output. Keep actual
process exit/status assertions; this helper is transport, not a validator.

### Local r12.1 — consume actual native text properties

When consuming Art's native text or table objects, distinguish cell tcPr padding
from TextFrame bodyPr margins. Inspect the written effective properties rather
than assuming a shared text helper set both. `scripts/native_text_revision.py`
provides an explicit cell/TextFrame margin operation and config-bound size
resolution for authoring; it does not waive approved-Art entry, permit Output
to reflow Art's text, or replace original validators and native checks.

### Local r13.1 — preserve the approved font and paragraph space

The Art-preview helper now requires explicit `font_file` and `font_family`;
when it is used for a permitted native probe, also pass the existing
`fontconfig` path (CLI: `--font-file … --font-family … --fontconfig …`).
Do not use the old positional-only call. Reuse the approved runtime's file and
family; its fontconfig must reach the actual child process, not only a parent
shell. A pre-conversion identity receipt and the resulting PDF font/glyph
inspection answer different questions. Final Output still follows the locked
route and its original evidence requirements; a preview cannot replace them.

Read approved paragraph marL/marR as well as effective cell/TextFrame padding.
`native_capacity` can describe a fixed object from its actual native properties
and supplied measured run widths/height, without shrinking text or declaring
quality. Existing paragraph edge space consumes capacity and must survive
implementation. Output cannot add or remove it to redesign unapproved Art;
return an implementation discrepancy through the existing stage boundaries.


### Local r17.1 — separate line-break fidelity from design preference

Preserve the locked Art line breaks and emphasis. When checking Chinese text,
distinguish missing characters, clipping, broken numeric/symbol combinations
and implementation deviations from an ordinary inter-character line break.
The latter alone does not establish a defect. A concrete ambiguity or hard-to-
track relation is a design observation to route to Art within the existing
return budget, not permission to silently reflow the deck. Keep actual
observations and unresolved findings even when the reader understands the page.

## 当前过程记录格式

交接process使用包根 packages/contracts/process-evidence.zh-CN.md 的顶层process.events，每项action / record / artifacts记录真实当时行为。actual_actions或commands原始日志需按实际事项适配，不能代替该字段；保留原件，不把格式示例当执行证据。

## 可选的页码字段诊断

实际PDF页码可能与源属性或缓存不同。可按[诊断说明](../../page-number-field-diagnostic.zh-CN.md)使用包根scripts/inspect_slide_number_fields.py，保留当前精确PPTX/PDF/renders身份、实际命令和几何证据。匹配不等于canonical政策通过，不一致也不自动归因某一侧；不支持或歧义保持未观察并回看实际页图。此助手不改变七项QA、读者、返工、预算、闭合、发布或失败规则，不解决导出器差异本身。

## 本地r10 规范技术配置

Art和Output的professional-input.technical_files.canonical_task_config为当前run已经冻结的task-config精确字节，含路径、SHA256和字节数。它是技术约束，不增加公司内容输入；Art仍只消费原字节Copy图，Output仍消费design/renders及真实制作资源。以此核对当前identity、字体、颜色及制作配置，不能取安装包默认配置、历史稿或作者自评作替代。缺失或身份不符时保留实际错误，不静默派生默认值。该投影不证明配置已落实到原生对象/元数据，也不证明字体、编辑、容量或渲染检查通过。Office运行身份/累计计数仍须实际运行证据，不能由冻结配置推断。既有四类Kproof边界、读者清洁输入、判定、预算与失败规则不变。

## 可选提前原生保真诊断

`scripts/native_copy_diagnostic.py --graph 当前原字节Copy图 --pptx 已保存当前源 --output 新诊断.json`只读复用既有Native capture规则核当前页数/原生文字与图表缓存，可在消耗下一次导出或最后保存前发现遗漏。必要实现修订须按原内容/设计与剩余额度合并，不改源语义图或门禁来通过。诊断只临时复制输入字节，不启动run/Office、不制作PPTX、不渲染；旧文件不改。全部七项专业/视觉QA明确not-observed，缓存值存在不证明自动标签可见，仍须实看全页图/实际原生编辑并记录字体、容量与未测范围。这是可选早期诊断，未取代正式Output提交或新增质量门槛。
