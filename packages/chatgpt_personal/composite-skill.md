---
name: {{SKILL_NAME}}
description: Root-orchestrate and audit an editable presentation through the governed Logic, Copy, Art Direction, Output, and Supervisor stages in one self-contained ChatGPT Skill. Use for creating, revising, or auditing PPT, PPTX, slides, presentations, and decks when environment preflight, owner Library routing, evidence-bound handoffs, and paired PPTX plus supervision-report delivery are required.
---

# Clayz Presentation Personal

Operate one presentation workflow with five internally separated stages. This is one publication unit, not one undifferentiated authoring prompt: Logic, Copy, Art Direction, Output, and Supervisor retain their existing ownership and artifacts.

## Root invariants

- Treat the directory containing this `SKILL.md` as the composite Skill root. Paths beginning with `runtime/`, `config/`, `scripts/`, `packages/`, `catalog/`, `docs/`, or `references/` are relative to that root.
- Before authoring or auditing, run `scripts/validate_composite_skill_mount.py --root <skill-root>` and bind its report. Continue only when it returns `status: complete`, exactly one `SKILL.md`, and all five internal stage modules.
- Validate `runtime/personal-extension.json` against both `config/personal-extension-resolved.json` and the external pack lock at `runtime/runtime-lock.json` with `scripts/validate_personal_extension.py`. The external lock must preserve the exact set and snapshots of every `required: true` Provider. In owner-personal mode, a missing or invalid runtime, lock, or required Provider is `composite-skill-runtime-incomplete`; do not fall back to an unbound theme or detached stage.
- Resolve private sources only through the locked `library://` mounts and Provider manifests declared by the Personal Extension Runtime. Never infer a physical path, ingest the whole Library, or expose private source bodies in the audit record.
- Keep one Public Core, one resolved-configuration hash, one fresh script-issued run challenge, one exact task-request SHA-256, one resource-inventory lock, one Provider snapshot lock, and one cumulative stage-evidence chain for the run.
- Do not record private chain-of-thought. Record observable requests, evidence, decisions, conflicts, handoffs, tool results, artifact hashes, and responsibility instead.

## Root control plane

For every `new-build`, `revision`, or `audit` request:

1. Classify the task mode and identify the requested decision outcome. Do not call a presentation authoring tool first.
2. Validate the composite Skill mount and Personal Extension Runtime.
3. Open the supervision lifecycle record before scanning. Save the canonical current user request as immutable task-local bytes, then use `scripts/runtime_preflight.py --issue-challenge --task-request <file> --output <challenge.json>` to generate the run ID, task hash, nonce, bounded validity window, and canonical task-root issuance record. Never accept a caller-chosen run ID or caller-asserted task hash. The same challenge SHA may be consumed only once through the task-root ledger, regardless of the challenge filename. The Supervisor is the initiator, mediator, recorder, and final auditor; these roles must be explicit and chronologically evidenced even when a later hard gate stops the run.
4. Run the required environment and resource preflight exactly once with the same `--task-request` bytes and fresh `--challenge`. In this Personal Skill, `scripts/runtime_preflight.py` must resolve `config/personal-extension-resolved.json`; never substitute `config/default.json`, and treat `--require` as additive only. An available host-capability declaration is challenge-bound but remains `host-declared-unverified`: it must carry the same run/task/nonce/challenge values and structured receipts whose inventory files are hash-checked by the script, yet it may produce only a `provisional`/`attemptable` native route and can never self-authorize `ready`. A runtime-probed route may be ready immediately. A provisional route permits the non-authoring stages and one locked Output attempt, but delivery remains blocked until the actual PPTX, objects, and final render independently pass. Inventory plugin runtime, task inputs, owner Library, public Index, brand assets, host capabilities, font environment, and every configured target application's acceptance capability. Present a concise resource brief stating what was found, selected, unavailable, provisional, and which route will be attempted before Logic or audit work begins. Only absence of both a ready and attemptable authoring/rendering route may block the governed work; unavailable PowerPoint, WPS, or other target-native reopen checks must be recorded as deferred acceptance and must not block Logic.
5. Lock the resource inventory and Provider snapshots once. Every Provider marked `required: true` must bind a non-empty snapshot and be actually selected by at least one finalized receipt in every applicable stage; mere presence in the shared snapshot list is insufficient. A new source, asset, route, or configuration requires return to this root control plane and a revised brief.
6. Read only the internal stage module required for the current transition. Do not load all five stage modules by default.

## Stage router

- New build: read `references/stages/logic/stage.md`, then Copy, Art Direction, Output, and Supervisor in order.
- Revision: identify the earliest responsible stage, read that module, and replay only the necessary downstream stages while preserving approved upstream evidence.
- Audit: after mount and resource preflight, read `references/stages/supervisor/stage.md`; load another stage only when the audit needs its governing contract to assign responsibility.
- Logic: `references/stages/logic/stage.md`
- Copy: `references/stages/copy/stage.md`
- Art Direction: `references/stages/art-direction/stage.md`
- Output: `references/stages/output/stage.md`
- Supervisor: `references/stages/supervisor/stage.md`

Each stage must validate its input, preserve the shared locks, emit its approved artifact and cumulative evidence, and return control to this root router. A later stage may challenge an upstream conflict but may not silently rewrite the upstream artifact.

## Delivery contract

Output may stage an editable PPTX, render evidence, object inventory, deviation log, and QA report, but may not deliver the PPTX alone. Supervisor must independently audit the written PPTX objects and final renders, validate `ppt-supervision-report.json`, and bind the final pair:

1. `<presentation>.pptx`
2. `ppt-supervision-report.json`

The report must use contract v3.3, identify the initiator, mediator, recorder, and final auditor, and preserve the unique canonical action order from preflight-before-Logic through paired delivery. Every governed action has its fixed phase, actor role, and status. External role, lifecycle, and target-application references include actual file SHA-256 values and resolve to non-empty governed artifacts. Any real issue requires a v1.1 checkpoint bound to this run, task request, complete issue-ID set, and mediation timestamp; a clean run must not invent one. Target pass/fail requires a same-run target-application receipt bound to the final PPTX hash and observed inside the challenge window between Output handoff and final audit. The report binds the current run ID, task-request SHA-256, nonce, task-root SHA-256, challenge, canonical issuance and consumption receipt hashes, resolved-config SHA-256, runtime preflight, and resource inventory, embeds `environment_observation` with the exact preflight route plus satisfied/declared-unverified/missing capability results and final target-application dispositions, records the final PPTX filename and SHA-256, and locks `delivery_pair.required_artifacts` to `pptx` and `supervision-report`.

After the report validator passes, run `scripts/publish_supervised_pair.py` with the final PPTX, report, runtime preflight, resolved config, and validation artifacts. Deliver only from the resulting new bundle directory after `delivery-manifest.json` verifies exactly the PPTX and supervision-report hashes. A manual or single-file handoff is not a completed delivery.

## Stop conditions

Fail closed and return the concrete missing evidence when the composite mount is incomplete, the external runtime lock or any required private Provider/asset cannot be validated, materialized, and selected in applicable stage receipts, neither a ready nor provisional route can satisfy every personal resolved-config requirement, a provisional attempt fails to produce independently valid final artifacts, the run challenge lacks its task-root issuance record, is stale/replayed, or has a mismatched task/config binding, an upstream artifact is invalid, or the publisher cannot materialize and revalidate the PPTX/report pair. Do not fail closed merely because a configured target application's native reopen/render capability is unavailable; record that condition as deferred acceptance and limit the compatibility claim. Never repair these conditions by inventing configuration, copying another stage's authority, or silently degrading the user's private identity.
