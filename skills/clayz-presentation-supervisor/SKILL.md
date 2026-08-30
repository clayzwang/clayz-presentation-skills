---
name: clayz-presentation-supervisor
description: Root-orchestrate and independently audit every presentation task across resource inventory, Personal Extension resolution, Provider locking, Logic, Copy, Art Direction, Output, written PPTX objects, and final renders. Use for any request to create, revise, generate, or audit slides, PPT, PPTX, presentations, or decks. Prevent direct tool bypass; show what is available and selected before authoring, dispatch the five governed stages, detect drift and evidence failures, and return control without silently rewriting or redesigning.
---

# Clayz Presentation Supervisor

Act as the presentation task control plane, then produce an evidence-backed supervision report that identifies the earliest layer able to prevent each problem.

## Root orchestration contract

Supervisor is the required entry point for presentation intent and the final independent auditor. This does not add a sixth workflow stage: the governed stage list remains `Logic -> Copy -> Art Direction -> Output -> Supervisor`. The root control-plane work happens before Logic and binds the evidence reused by all five stages.

For a new or revised presentation:

1. Classify the request as `new-build`, `revision`, or `audit`. Do not call a presentation authoring tool before this classification.
2. Run `../../scripts/validate_plugin_mount.py` and bind its report. All five Skills and every required `runtime/`, `config/`, `packages/`, and `scripts/` path must come from one mounted plugin root. Missing shared files are `plugin-runtime-incomplete`; do not continue with detached Skills or reinterpret them as a complete plugin.
3. Resolve and validate the Personal Extension Runtime, resolved config, and external `runtime/runtime-lock.json` before Logic. The pack lock must preserve the exact binding set for every runtime Provider marked `required: true`. In an owner-personal task, absence, invalidity, hash drift, or a shrunken required-Provider set is `personal-extension-not-loaded`; do not silently fall back to the public theme unless the user explicitly requests public-core mode.
4. Resolve every declared Provider manifest through the runtime mount, validate its identity and locked snapshot, and record one task Provider lock. Every runtime Provider marked `required: true` must bind a non-empty snapshot and be actually selected by at least one finalized receipt in every applicable stage; mere presence in the shared snapshot list is insufficient. Required Provider or brand-asset failure is fail-closed. Optional Provider failure must be recorded as an explicit public-core fallback.
5. Read the locale-matched `references/resource-inventory-gate.md` and `references/first-class-index-gate.md`. Scan the complete plugin, task inputs, owner Library, public Index, brand assets, fonts, and host capabilities. During this scan, materialize every required owner Library source into `task-private-learning`, merge it into the CompositeIndex, and bind the resulting snapshot. Inventory locators do not satisfy either gate.
6. Save the canonical current user request as immutable task-local bytes. Use `../../scripts/runtime_preflight.py --issue-challenge --task-request <file> --output <challenge.json>` to generate the run ID, request hash, nonce, validity window, and canonical task-root issuance record; do not accept caller-chosen equivalents. The consumption ledger is keyed by challenge SHA inside that task root, so copying or renaming the challenge cannot permit replay. Then run one host capability preflight against the exact same task bytes, fresh challenge, and resolved configuration. `--require` may add stricter requirements but may never remove a configured one. Any available host-tool declaration must bind the same run/task/nonce/challenge values and provide structured, hash-checked host-inventory receipts, but it remains `host-declared-unverified`: it may make a route `provisional`/`attemptable`, never `ready`. A provisional route permits Logic, Copy, Art Direction, and one locked Output attempt; only independently validated final PPTX/object/render evidence can complete delivery. Lock the route, finalize `ppt-resource-inventory.json`, and send its concise user-facing brief in commentary. State what was found, what this task will use, what is unavailable, provisional, or not selected, and the locked route. Scan and record every configured target application whether present or absent. Treat route requirements and target-application acceptance as separate classes: absence of both a ready and attemptable route may block governed work; unavailable PowerPoint, WPS, or other target-native reopen checks are deferred acceptance and never a pre-Logic gate. If ready or provisional, continue automatically; no governed stage may begin before this message.
7. Dispatch Logic, Copy, Art Direction, and Output in order. Require each handoff to carry the same plugin-mount report, Personal Extension digest, resolved-config digest, resource-inventory lock, Provider snapshots, route lock, and cumulative full Retrieval Receipts. A stage without its Index receipt or inventory lock never ran.
8. After Output, resume the independent audit workflow below. Delivery is not authorized until a supervision report exists, upstream validators are rerun against the final PPTX, selected resources are reconciled to actual use, and all blocking findings are resolved or explicitly accepted by the user. Mirror the run ID, task-request hash, nonce, task-root hash, challenge hash, canonical issuance and consumption receipt hashes, resolved-config hash, preflight scan ID and raw hash, locked route, satisfied/declared-unverified/missing route requirements, and every target application's available/unavailable result into `environment_observation`; after Output, record each target as `pass`, `fail`, `deferred`, or `not-selected` with evidence. Use `scripts/publish_supervised_pair.py` as the only final publication path and hand off the PPTX plus `ppt-supervision-report.json` only from its validated bundle.

For an audit-only request, start from the available approved packages and artifacts, record every missing prerequisite, and run the audit workflow without inventing prior approvals.

## Cloud font acceptance

Read `theme.typography.font_validation` from the resolved configuration. When its mode is `preserve-name-defer-native` and a listed deferred font such as `华文楷体` or `STKaiti` is unavailable in the cloud renderer:

- require the written PPTX and its East Asian font fields to preserve the requested family name;
- forbid silent replacement and record any observed cloud-render substitution;
- treat cloud PNG/PDF output as diagnostic-only and do not require cloud PDF pixel equivalence;
- emit `font-validation-pending` for native reopen/render on a machine with the complete font; and
- allow PPTX delivery with that explicit pending state, but never claim final font-pixel acceptance.

`fail_on_missing_primary_font` still blocks substitution and authoritative render claims. It does not block writing a semantically correct PPTX for a font explicitly covered by the deferred-native policy. A missing non-deferred font, a changed PPTX font name, or a claimed authoritative render without the font remains blocking.

## Authority

Classify and dispatch work, bind configuration and evidence locks, inspect, compare, diagnose, classify severity, record uncertainty, challenge upstream assumptions, and return control to the responsible layer or user.

Do not perform Logic, Copy, Art Direction, or Output work inside Supervisor; dispatch those responsibilities to their governed skills. Do not silently rewrite Logic or Copy, select a replacement composition, modify the PPTX, approve on the user's behalf, force an endless exit loop, or treat an automatic score as truth.

## Required context

1. Validate `../../runtime/plugin-mount-contract.json` with `../../scripts/validate_plugin_mount.py`, then resolve the central configuration in one order only: use an explicit task configuration when supplied; otherwise, when `../../runtime/personal-extension.json` exists, treat it as the generated **Personal Extension Runtime**, validate its self-lock, resolved config hash, external `../../runtime/runtime-lock.json`, and exact required-Provider binding set with `../../scripts/validate_personal_extension.py`, and use the config path named there; otherwise use `../../config/default.json`. In owner-personal mode, a missing or invalid generated runtime/pack lock is a blocking integration failure rather than an implicit default-theme fallback, and preflight may not be run against the public default. Bind the mount report and extension digest without creating a separate private supervision authority.
2. Resolve the task locale from the explicit request or `locale.default`. For `en-US`, read the base English references; for `zh-CN`, read the matching `.zh-CN.md` files. Read only one language unless translation comparison is explicitly requested.
3. Read `references/supervision-contract.md` and `references/failure-pattern-routing.md`. These authority and routing contracts are mandatory and never search-dependent; the existence of a matching Failure Pattern is search-dependent.
4. Read `../../packages/contracts/knowledge-learning.md` and the locale-matched `references/feedback-index-routing.md` before routing reusable observations. These governance contracts are mandatory and never search-dependent.
5. Read the locale-matched `references/resource-inventory-gate.md` and `references/first-class-index-gate.md`. Supervisor must select the reviewed counterexamples from `task-private-learning`, bind its own finalized receipts, and prove the user saw the resource brief before Logic.
6. Verify that every stage used the same resource-inventory lock, runtime lock, and task Provider snapshots, including the bundled public Provider and task-private-learning. Never treat a private record as stronger evidence merely because it is private.
7. Classify optional audit signals and resolve them through the built-in Capability Index. Typical signals include `plan-object-render`, `medium-fidelity`, `runtime-conflict`, `environment-observation`, `interaction-failure`, `retry-loop`, `execution-ledger`, and `failure-recovery`.
8. Load only optional `knowledge_refs` returned by selected capability records. Resolve an optional Failure Pattern only from observed evidence and keep its retrieval receipt ID. Unresolved signals stay explicit and never authorize invented diagnoses, repair methods, or silent intervention.

## Workflow

1. Verify the root orchestration checkpoint and bind the run ID, task-request SHA-256, plugin-mount report, and exact hashes of the runtime preflight, pre-Logic resource inventory, Logic package, Copy package, Art Direction plan, PPTX, render root, object inventory, deviation log, QA report, resolved configuration, Personal Extension Runtime, Provider lock, route lock, and available retrieval receipts. The preflight run/config binding, raw hash, and complete target-application observation set must be represented inside the final report, not merely referenced by filename.
2. Audit business relationships and content readiness before visual quality.
3. Compare approved importance with actual visual attention, and approved medium with actual object types and rendered appearance; use the resolved medium-fidelity capability when applicable.
4. Check cross-slide invariants, series behavior, semantic whitespace, motif, reading order, typography, data labels, connectors, and target-application compatibility.
5. Treat written PPTX objects and final renders as stronger evidence than in-memory success messages; use environment-grounded observation only when that capability was resolved.
6. For every issue, record evidence, expected state, actual state, impact, severity, confidence, earliest responsible layer, and recommended return target. A registered Failure Pattern may support this classification only when selected in a receipt and matched to actual rendered evidence.
7. Distinguish deterministic failures from professional judgment and from unresolved uncertainty. Interaction and retry-loop diagnoses require their corresponding resolved capabilities; optional Failure Pattern gaps remain `unresolved` rather than becoming invented codes.
8. Return reusable learning candidates to Logic, Copy, Art Direction, or Output with evidence and limits; never create a Supervisor learning silo, issue the separate human admission, update a benchmark baseline, or promote a candidate automatically.
9. Reconcile every initially selected resource as used or unused with a reason, cover all five stages with evidence, and present the user with a concise actual-use summary. Late unlisted resources are invalid; new material requires a revised pre-Logic inventory and another brief before use.
10. Emit one v3.3 report with `origin_namespace: io.clayz.presentation`, status `supervised`, the same challenge-bound run/task/config values as preflight, cumulative root `index_evidence`, and validated `resource_usage`. Record Supervisor explicitly as initiator, mediator, recorder, and final auditor. Use the unique canonical lifecycle order: root initiation, runtime preflight, user-visible pre-Logic resource brief, Logic, Copy, Art Direction, Output, optional real mediation, final audit, paired-delivery lock, and control return. Each governed action uses its fixed phase, role, and status. Every external role, lifecycle, and target-application evidence reference includes the actual file SHA-256 and resolves to a non-empty governed artifact. A real issue requires a v1.1 checkpoint bound to this run, task request, full issue-ID set, and mediation timestamp; a clean run must not invent one. A target pass/fail requires a same-run `target-application-check/1.0` receipt bound to the final PPTX hash and observed inside the challenge window between Output handoff and final audit. Do not record private chain-of-thought; record actions, decisions, evidence references, and outcomes.
11. Bind `delivery_pair` to the final PPTX filename and SHA-256, this supervision-report filename, `delivery-manifest.json`, and `scripts/publish_supervised_pair.py`. `incomplete-evidence` requires a blocked pair. Otherwise run the publisher only after report validation, then deliver exactly the PPTX and report from its new verified bundle. A missing report, missing lifecycle event, mismatched binding or hash, absent manifest, publisher bypass, or single-artifact handoff proves Supervisor completion was not established and blocks normal delivery.

## Validation

Run:

```bash
python ../../packages/validators/validate_supervision_report.py \
  <copy-package.json> <art-direction-plan.json> <output-qa.json> \
  <object-inventory.json> <supervision-report.json> \
  --pptx <final.pptx> --render-root <final-render-root> \
  --runtime-preflight <runtime-preflight.json> \
  --config <resolved-config.json>

python ../../scripts/publish_supervised_pair.py \
  <copy-package.json> <art-direction-plan.json> <output-qa.json> \
  <object-inventory.json> <supervision-report.json> \
  --pptx <final.pptx> --render-root <final-render-root> \
  --runtime-preflight <runtime-preflight.json> \
  --config <resolved-config.json> --output-dir <new-delivery-directory>
```
