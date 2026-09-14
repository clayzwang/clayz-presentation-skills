---
name: {{SKILL_NAME}}
description: Root-orchestrate presentation Library inspection, discussion-based confirmed knowledge, PPT enablement, and editable presentation work through Logic, Copy, Art Direction, Output, and Supervisor in one self-contained Skill. Use from ordinary Chat or Work for presentation-related Library inspection, reusable presentation knowledge, PPT capability advice, or creating, revising, and auditing PPT, PPTX, slides, presentations, and decks. No ChatGPT Project is required.
---

# Clayz Presentation Personal

Operate one presentation workflow with five internally separated production
stages and one shared post-Output audit module. This is one publication unit,
not one undifferentiated authoring prompt: Logic, Copy, Art Direction, Output,
and Supervisor retain their existing ownership and artifacts; the Independent
Auditor returns an audit artifact to Supervisor and is not a sixth production
stage.

The stages are an enablement system: they give the model better evidence, authority, tools, and feedback. They do not replace professional judgment. Logic receives the deepest reasoning responsibility; context economy compresses transport and repeated execution, never the thought needed to understand and explain the subject.

This same-name Skill is callable from ordinary Chat and Work and is not tied to a
ChatGPT Project. Keep implicit invocation and explicit mentions supported.
Read `packages/contracts/stage-enablement.md` and
`packages/contracts/native-library-workflow.md` for the one production path, and
read `packages/contracts/independent-audit.md` when the post-Output audit is
required.

Classify only the work requested: inspection, discussion/learning, capability
advice, or production. Production uses execution/research/mixed content
responsibilities according to material maturity, not separate product editions.
Inspection and discussion do not require a presentation renderer.

Before production, run `configure-task` to merge defaults, available saved
personal configuration and this task's requirements. Use its v2 selection and
merged config throughout. The historical mode fields have one new-run value,
`unified`; do not offer or select public/private runtime branches. An installed
Personal Extension is an integrity-checked initial settings source, not a
trigger for loading every private Provider or a different workflow.

Library knowledge is optional. Its address can be supplied later, and its
availability does not reset a loaded master or preferences. Resolve actual
native file references and bytes; addresses, catalog entries and free-text
permission results do not prove access. Use explicit current-task attachments
when available. Skip unavailable optional sources, record the limitation, and
continue; preserve specific user-required sources and quality requirements.
Never silently claim that an unavailable source was used. Do not redirect to a
new project, invented Library plugin installation or repeated authorization.

For a calibrated production run, a real PPTX writer may remain `attemptable`
while preflight keeps fidelity, font, render, or other unobserved configured
capabilities in `missing_capabilities`. This is pending evidence, not proof
that the writer is absent. Continue the locked Output attempt, use the supplied
master when configured, and let Output/Auditor record observed load, object,
font, render, or failure evidence. `spec-only` never represents a writable
PPTX route; invalid bindings or absence of a real writer's minimum
editable-content capability still stop the affected work.

Personal configuration may be read from the user's saved Library document;
if unavailable, retain an already loaded layer, or use defaults when none was
ever loaded. Keep one-time overrides separate from saved defaults. Existing
discussion confirmation and actual host write/readback govern persistent
knowledge/configuration changes; no local mirror is a native Library commit.
Do not invent a writer or mark unconfirmed discussion as reusable knowledge.

Use the same selected master for comparisons with and without Library content.
Fresh creation changes task content and artifacts, not the user's visual
identity. The final report3.6 JSON is assembled from five real stage records,
the actual primary artifacts and the bound `independent-audit/1.0` artifact;
its readable Markdown companion is derived from that JSON in the same run and
may be delivered alongside it. Neither a hand-written summary nor a Word
document is a substitute.


## 内容、布局、生成的连续改进

按「内容（Logic、Copy）→ 排版与布局（Art Direction）→ 生成 PPT（Output）」
连续推进；五个模块隔离职责，不要求五个独立代理，也不是只能向前的流水线。
每个制作模块在当前草案上执行「具体问题 → 对应 Library/索引检索 → 阅读相关
正文或案例 → 判断采用、调整或不采用 → 修改本阶段成果 → 验证效果」。适用的
事实定义和品牌硬要求先读；初稿可被推翻，不为既定答案寻找装饰性引用。

索引命中、哈希核验和读过技能不等于改善作品。用已有阶段备注或检索回执简短
记录问题、修改前状态、来源位置、适用性、修改后状态和实际检查结果；没有匹配
或不需修改时如实说明。视觉案例应查看实际图像，不能只凭元数据声称比较过。
从已锁定来源池中检索更多适用记录不需重做整轮盘点；新增来源池或快照按现有
契约修订绑定。遵守累计检索预算，已解决的问题不重复查询。

Supervisor 在阶段交接时接收每个产物的副本并返回哈希绑定校准；下一阶段在锁定
成果前记录 `calibration_bindings` 的接受、部分接受或拒绝及理由。Output 完成后，
实际 PPTX、对象和渲染证据同时送 Supervisor 与 Independent Auditor。Auditor 直接
读取用户原始要求、验收规则和 Supervisor 承诺，回传独立审计产物。发现问题交回
最早负责的模块：改含义找 Logic，改表达找 Copy，改构图找 Art Direction，改实现
找 Output。更新相应成果并仅重验受影响部分；一般可逆修订继续执行，不把阶段批准
变成逐次向用户请示。保留真实失败或待验状态，不让阶段记录或完整索引代替内容、
视觉和成品质量。

审计报告是完整工作记录，可以比 PPTX 更丰富，但所有事实都必须来自任务内已保存的
阶段主要产物、work records、可选的 `work-notes`、校准／Auditor 产物和实际 PPTX。
报告应能单独说明任务要求、研究证据与反证、假设和不确定性、故事线与排除、copy、
逐页设计意图、三轮 Supervisor 评价及下游吸收、实际生成物、Auditor 观察、放行和局限。
缺失 notes 或未观察检查写为 `not-recorded`／`deferred`／`uncertain`，不凭记忆补齐。
Art Direction 要记录内容关系如何转成视觉关系、媒介选择及文字呈现的理由和实际偏差；
脚本只统计、绑定、提取和汇总，艺术判断仍由模型负责。可读 Markdown 由 report JSON
确定性派生，不能另写事实源，也不要求每页图表、图片或轮廓变化。

## Root invariants

- 日常 PPT 制作使用 `scripts/component_version_guard.py --mode application --output <component-version-report.json>`，离线核对当前安装包自身的一致性，状态 `installed` 即可进入制作和交付。GitHub、Codex、ChatGPT 发布版本不同、GitHub 不可达或开发候选验收日期过期都不阻止制作。不要要求用户声明“候选验收模式”。完整性、内部兼容性和私人 Provider 绑定仍须有效。`--mode release-check` 仅用于明确要求的开发发布核验。本规则优先于旧参考文件中的 latest-only 制作门禁。

- Treat the directory containing this `SKILL.md` as the composite Skill root. Paths beginning with `runtime/`, `config/`, `scripts/`, `packages/`, `catalog/`, `docs/`, or `references/` are relative to that root.
- Before authoring, auditing, or running bundled code that stages a native Library write, run `scripts/validate_composite_skill_mount.py --root <skill-root> --mode installed` and bind its report. Continue only when it returns `status: complete`, exactly one `SKILL.md`, all five internal stage modules, and the shared Independent Auditor module. This is package-integrity validation, not presentation rendering or production preflight; learning does not require a renderer. `host_observations` about regenerated UI metadata or additional files are non-blocking and are not runtime authority. Do not rerun the publisher-only `--mode archive` against a host-managed installation; immutable instructions, code, contracts, dependency files, configuration and Provider locks remain strictly checked.
- Validate installed package integrity and any bundled Personal Extension metadata with the existing validators. This does not activate private knowledge or require its remote source files. Resolve the effective task configuration only through the unified layer merger.
- Resolve actual selected sources through observed references and preserve their identity, rights and hashes. Never ingest the whole Library blindly. The optional confirmed-knowledge store keeps its existing publication/readback policy; do not redirect it merely because a reference locator changes.
- Keep one Public Core, one resolved-configuration hash, one fresh script-issued run challenge, one exact task-request SHA-256, one resource-inventory lock, one Provider snapshot lock, one cumulative stage-evidence chain, and one bound Independent Auditor artifact for the run.
- Do not record private chain-of-thought. Record observable requests, evidence, decisions, conflicts, handoffs, tool results, artifact hashes, and responsibility instead.
- Record stage work while it happens. When richer context is useful, attach an observed `work-notes` JSON or Markdown artifact through the existing stage-record path; missing notes stay `not-recorded` and are never reconstructed at final delivery.
- Assemble the full work report from primary stage artifacts, work records, bound calibration/Auditor evidence and the actual PPTX. Record actual PPTX statistics plus extracted page text and speaker notes when available. Professional judgment stays in model-authored stage/Supervisor records; scripts only bind, count, extract and aggregate.
- Supervisor records the user's objective, hard and soft requirements, requirement
  precedence and delivery policy before Logic. The user request remains higher
  authority than saved personal settings and defaults; Supervisor clarifies and
  records but does not override it. An unmet hard requirement is a truthful
  finding, not an automatic refusal to generate or deliver a binding-complete
  artifact unless the user explicitly made it a no-delivery condition.

## Context and visibility guard

- Send a short user-visible start update before the first long scan or tool run. Do not wait until all five stages finish before showing any useful status. After preflight and each substantive handoff, briefly state what the current work establishes, what the Library changed or left unchanged, and the next unresolved check. Do not substitute gate names for progress or paste full contracts, receipts, source bodies, logs, or JSON into chat.
- Use governed files as working memory. Keep exact packages, receipts, reports, and hashes in task artifacts. In model context retain only the root rules, the current stage module, the locale-matched references required for the current decision, and a compact pointer summary of already approved artifacts. Carry earlier stages by path plus SHA-256 and reopen only the fields needed for the current validation; do not restate cumulative artifacts in prompts or messages.
- Read long task inputs and Library records by relevant excerpt or chunk. Start a stage with one focused receipt and add another only for an unresolved material question, while treating candidate and selection budgets cumulatively. Never load an entire long source merely because it was selected. Discard raw excerpts after their claim, adoption target, source pointer, and hash are recorded in the governed artifact.
- After preflight and every governed stage, write or refresh `run-context-checkpoint.json` in the task root. This is a derived resume index, not a new source of truth. Keep it small and include only `run_id`, `task_request_sha256`, completed and next phase, authoritative artifact paths and SHA-256 values, unresolved blockers or deferred checks, and a concise user-requirement summary. Do not include private source text or chain-of-thought.
- When the current conversation already contains a failed full-deck attempt, repeated large generations, or a host context/compaction warning, validate the newest checkpoint and resume from its `next_phase`; do not restart completed stages. If there is not enough safe context to load the next required module and evidence, stop at the durable checkpoint before starting that stage and ask the user to continue in a new chat with the checkpoint and authoritative artifacts. Treat this as a resumable context boundary, not a failed presentation run.
- Once the verified delivery bundle exists, run the current `verify-handoff` against that new bundle; answer delivery-first in a compact message using only its returned exact PPTX, `ppt-supervision-report.json`, and `work-report.md` paths, hashes, task/run identity and actual PPTX summary. State validation status and only material deferred checks, then stop. The report carries the full audit; duplicating it in chat is prohibited, and a task-directory glob must never select an older report.

## Root control plane

For every PPT artifact `new-build`, `revision`, or `audit` request:

1. Classify the requested work and content responsibility. For production, run the unified configure-task flow once; no public/private runtime choice exists. Inspection and discussion do not trigger production.
2. Validate the installed composite mount and available packaged metadata for integrity. Bind the merged task-config and v2 task selection; profile availability only affects input layers.
3. Open the supervision lifecycle record before scanning. Save the canonical current user request as immutable task-local bytes, then use `scripts/runtime_preflight.py --issue-challenge --task-request <file> --output <challenge.json>` to generate the run ID, task hash, nonce, bounded validity window, and canonical task-root issuance record. Never accept a caller-chosen run ID or caller-asserted task hash. The same challenge SHA may be consumed only once through the task-root ledger, regardless of the challenge filename. Supervisor records the objective, hard/soft requirements and delivery policy as initiator, coordinator/calibrator and recorder. The Independent Auditor is a separate shared post-Output module; do not use a Supervisor `final_auditor` role as its substitute in a new run.
4. Run one environment/resource preflight with the exact task request, fresh challenge, `--config <task-config.json>` and `--task-selection <task-selection.json>` from the unified merger. Treat `--require` as additive only. An available host-capability declaration is challenge-bound but remains `host-declared-unverified`: it must carry the same run/task/nonce/challenge values and structured receipts whose inventory files are hash-checked by the script, yet it may produce only a `provisional`/`attemptable` native route and can never self-authorize `ready`. A runtime-probed route may be ready immediately. A provisional route permits the non-authoring stages and one locked Output attempt; after that attempt, a valid Independent Auditor artifact with actual evidence is required for release. Inventory plugin runtime, task inputs, the selected owner/public Library scope, public Index, brand assets, host capabilities, font environment, and every configured target application's acceptance capability. Record `unified` in both mode fields. Use actual Library availability and selected sources; no installed-profile quota or blanket bootstrap requirement applies. Present a concise resource brief before Logic that keeps required external resources, task-generated artifacts (including source materialization only when used), the optional confirmed snapshot, deferred environment acceptance, and research evidence to collect in separate categories. State what was found, selected, unavailable, provisional, and which route will be attempted. A missing topic attachment is a deferred task input rather than a blocker when the task authorizes research and an allowed research source is actually available; record the evidence to collect and its limits. Research may supplement the topic but never replace a required private Provider, and web/public search must never substitute for private-provider bytes. For authoring/rendering capability checks, only absence of both a ready and attemptable route may block the governed work; this does not waive selected private Provider or asset gates. Unavailable PowerPoint, WPS, or other target-native reopen checks must be recorded as deferred acceptance and must not block Logic.
5. Lock one inventory and Index snapshot set: bundled methods plus actually selected sources. Materialize task sources only when needed, otherwise use not-applicable owner materialization. Every explicitly required source still needs real evidence. Retrieve for the current question; a no-match result is valid. Do not select records just to satisfy a Provider quota. A new source, asset, route, or configuration requires return to this root control plane and a revised brief. Finalize the acceptance draft with `scripts/finalize_task_acceptance.py <draft> <task-acceptance.json> --config <task-config.json> --brief-output <task-commitments-brief.json>` so the merged config, personal layer and task overrides are actually used. Pass `--origin-map <origin-map.json>` only when that real file exists. Store explicit user no-delivery conditions in `acceptance.release_conditions`; default `[]` remains unchanged, and hard classification or legacy `blocking` does not create release gates. Ordinary requirements receive a nearby classification when absent. Unless the user explicitly omits the respective role, the acceptance contract and Logic sequence include one opening cover and one closing synthesis/action page; a short body-page budget never silently removes them. Quality limitations discovered after authoring remain audit findings and do not reopen the inventory gate.
6. Read only the internal stage module required for the current transition. Do not load all five stage modules by default. Refresh the context checkpoint before switching modules, then carry the previous stage only by its validated artifact pointer and hash.

## Stage router

- New build: start with `references/stages/logic/stage.md`, then Copy, Art Direction, Output, and Supervisor. Run each stage's selected public or personal Library/Index iteration before handoff, review the three production boundaries above, and return to the earliest owner when evidence requires a revision.
- Revision: identify the earliest responsible stage, read that module, and replay only the necessary downstream stages while preserving approved upstream evidence.
- Audit: after mount and resource preflight, read `references/stages/supervisor/stage.md` and `packages/contracts/independent-audit.md`; load another stage only when the audit needs its governing contract to assign responsibility.
- Logic: `references/stages/logic/stage.md`
- Copy: `references/stages/copy/stage.md`
- Art Direction: `references/stages/art-direction/stage.md`
- Output: `references/stages/output/stage.md`
- Supervisor: `references/stages/supervisor/stage.md` plus the shared Independent Auditor module after Output

Each stage must validate its input, preserve the shared locks, emit its approved
artifact and cumulative evidence, send that artifact to its next owner and
Supervisor, and consume the returned calibration before locking the next
revision. A later stage may challenge an upstream conflict but may not silently
rewrite the upstream artifact. Output additionally sends the actual PPTX,
objects and renders to the Independent Auditor.

## Delivery contract

Enforce the stage-work-record contract in `packages/contracts/stage-enablement.md`.
At each handoff save and verify that stage's real work record through
`scripts/publish_supervised_pair.py record-stage` and `check-records`.
Supervisor adds its coordination/calibration record after the four production
records and consumes the Independent Auditor's immutable artifact;
`assemble-report` collects all five records plus that artifact, optional bound
`work-notes`, and actual final-deck evidence. It validates the complete current
report3.6 JSON and derives its readable Markdown before the existing final
publisher can deliver it.
Never substitute a hand-written success summary or modify the installed
checks to turn a failure into a pass. Preserve existing valid stage work and
re-execute only missing or invalidated work.

Output may stage an editable PPTX, render evidence, object inventory, deviation log, and QA report, but may not deliver the PPTX alone. Output sends the written PPTX objects and final renders to Supervisor and the Independent Auditor. Supervisor consumes the Auditor artifact, validates `ppt-supervision-report.json`, derives its readable Markdown, and binds the final delivery bundle:

1. `<presentation>.pptx`
2. `ppt-supervision-report.json`
3. the deterministically derived Markdown report

The report must use report3.6 and its full-work-report envelope: the real five stage records, any bound `work-notes`, three `calibration_artifacts`, `auditor_artifact`, `supervisor_release` and derived `core_sequence`. The collector attaches the authoritative `work_report` and `work_report_sha256`. It assembles the task requirements, evidence and source trace, contrary evidence, assumptions and uncertainty, storyline and meaningful exclusions, final copy, page-level design intent, calibration responses and downstream absorption, actual PPTX statistics/page text/notes, Auditor observations, release, limitations and improvements from existing artifacts. Missing notes or unobserved checks are `not-recorded`, `deferred`, or `uncertain`; they are never backfilled. Identify Supervisor's initiator, coordinator/calibrator and recorder responsibilities, retain the compatibility `supervisor_roles.final_auditor` entry only as `not-needed` or `incomplete`, and bind the actual Auditor artifact with its hash and `audited_at`. The stage-five work record uses role `auditor`; it is not a Supervisor self-audit. The derived core sequence is `supervision-started`, `logic-to-copy-calibrated`, `copy-to-art-direction-calibrated`, `art-direction-to-output-calibrated`, `independent-audit-completed`, `supervisor-release`. Historical lifecycle events, Index/retrieval accounting and performance fields are optional supporting evidence; preserve them when real, but never fabricate them. Every governed action has its fixed phase, actor role, and status when supplied. A quality issue does not require a v1.1 checkpoint; create one only for a material business choice, scope change or explicit no-delivery condition, and bind it to this run, task request and affected issue IDs. Target pass/fail requires a same-run target-application receipt bound to the final PPTX hash and observed inside the challenge window between Output handoff and final audit. The report binds the current run ID, task-request SHA-256, nonce, task-root SHA-256, challenge, canonical issuance and consumption receipt hashes, the selected config SHA-256, runtime preflight, and resource inventory when those artifacts are part of the run, embeds `environment_observation` with the exact preflight route plus satisfied/declared-unverified/missing capability results and final target-application dispositions, records the final PPTX filename and SHA-256, and retains the validated formal PPTX/report pair. Quality findings and deferred checks may be delivered when these bindings are complete; a missing or mismatched binding blocks the verified pair.

Record the selected mode in the existing `resource_inventory.runtime_mode` and `index_evidence.mode`, and the configuration path/hash in preflight `config_binding`. Preserve their existing report references; do not add unsupported top-level report fields. The derived Markdown is deterministic output of the report JSON, not a separately edited artifact.

After the report validator passes, run `scripts/publish_supervised_pair.py` with the final PPTX, formal report, derived Markdown and the runtime/config/validation artifacts supported by the current core. Every config-taking preflight, font validator/audit, stage validator, final report validator, and publisher invocation must receive `--config <selected-config.json>` explicitly. Deliver only from the resulting new bundle directory after `delivery-manifest.json` verifies the PPTX and formal report and records the derived Markdown path/hash in its derived-files collection. A manual or single-file handoff is not a completed delivery.

When the resolved configuration places a font identity under the existing
`preserve-name-defer-native` policy, missing native font availability is a
deferred acceptance condition and does not block Logic. Preserve that
identity's exact `pptx_family` in both Latin and East Asian PPTX fields; never
substitute silently. Missing PowerPoint or WPS is likewise deferred
target-application acceptance and is not a pre-Logic blocker. Limit final
font-pixel and target-application claims until the deferred checks run.

## Stop conditions

Before the final answer, run `verify-handoff` on the exact newly published
bundle and use its returned paths. Confirm the formal report contains all five
`work_records` and `assembly`, binds the Independent Auditor artifact, matches
the PPTX hash, and the manifest's `derived_files` entry names the exact
`work-report.md` path and hash. It states the actual checks and deferred/quality
findings. Do not glob the task root, link an old
artifact, or substitute a separately rewritten summary or claimed pass for the
validated bundle.
If a required binding or result is missing, correct the affected work through
the existing workflow. The objective is reliable content and a usable deck;
record only evidence and decisions that support those results, without adding a
new form, approval step, or ceremony.

Stop on invalid package/config integrity, missing explicitly required task inputs or master, failed actual authoring/render route, invalid/replayed task binding, invalid stage artifacts, missing Independent Auditor binding, or failed full report/PPTX/Markdown validation. A quality defect, unavailable optional Library, absent personal preference document, missing optional work notes, or deferred native target check alone is not a stop; disclose the missing evidence as `not-recorded` or `deferred` and continue when the binding-complete policy permits. Keep already loaded settings, record the limitation and continue with actual usable inputs. Never invent a pass, alter installed checks, or substitute a summary for the assembled report.
