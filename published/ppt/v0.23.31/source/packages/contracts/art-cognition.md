# Art cognition and external learning (v0.20.2)

## v0.20.5 current repair policy

The selected `consolidated-once` policy controls all reader return routes: Copy readers together → one Copy repair → both original readers confirm; final reader → one Art/Output repair → same reader confirms. Independent Auditor records only. Residual/new issues are reported, never another repair dispatch. Historical pass-until-clean or repeated returns below apply only to legacy `strict-pass`. See `packages/contracts/reader-cycle.md` from the plugin root.


Execute the [Art design process](art-design-process.md) (also
[中文](art-design-process.zh-CN.md)): prepare the whole Copy story and each
page's semantics, derive attention from content responsibilities, then realize
it through expression, composition and element language. Consult knowledge at
the affected decision and inspect actual drafts before recording outcomes.
Use existing cognition and page-planning records; the external learning pack
and record schemas remain unchanged.

New Art work records eleven cognitive results: A01 communication task, A02 art direction, A03 visual narrative, A04 page proposition, A05 content roles/relations, A06 perception, A07 expressive concept, A08 composition, A09 visual language, A10 integration, A11 critique. Each result names a scope, a concrete conclusion, executable actions, and checks or uncertainty. They may recur, share actions or reuse unaffected page groups; they are not agents, approvals, or mandatory exhaustive essays. A11 before rendering records planned checks; actual observations require actual rendered images and may update a subsequent planning revision. Never assert a reader test that did not occur.

The external `art-design-foundations` v1.0.0 package contains 66 principle-bearing codes, eight official curriculum sources, 33 paired synthetic teaching examples, and an eleven-step hypothetical worked example. The repository authors synthesized the principles and examples; the universities did not author or endorse this package. Historical and supporting HCI/visualization sources are distinguished. It is an authored reference, not private human-admitted knowledge. The separate release archive is intentionally absent from both Light payloads.

Use a user-selected package path. In the plugin root:

```sh
python scripts/art_learning.py validate --pack /path/to/art-design-foundations-v1
python scripts/art_learning.py lookup --pack /path/to/art-design-foundations-v1 --code A06
python scripts/art_learning.py lookup --pack /path/to/art-design-foundations-v1 --code P.PER.HIERARCHY
```

Read the returned principle, actions, applicability, limits and examples. FLOW lookup includes its relevant principle leaves; leaf lookup stays narrow. Record actual influence, not only the ID. A missing package permits original design with a disclosed limitation; do not fabricate a lookup or fetch every package by default. The user's selection persists for that task. Each category, FLOW, principle and action code must contain a principle description; future classification children retain stable parent codes. Cases are optional and contextual.

## Decision artifact

`art_cognition` uses contract `io.clayz.presentation.art-cognition/1.0` with `steps`. Every step has `flow_code`, `scope` (deck, page or group), `conclusion`, nonempty `actions`, `check_or_uncertainty`, and `knowledge_refs`. Each reference contains `code`, `how_applied`, and the full `receipt` returned by lookup. Without external knowledge, use `knowledge_refs: []` and explain `knowledge_not_used_reason`. All A01—A11 must be represented; repeated scopes are allowed. No field or hash proves quality or private thought. Historical Art 2.3 records without this extension remain replayable.

```sh
python scripts/art_learning.py validate-cognition --record /task/art-cognition.json
python scripts/stage_documents.py record-planning --package /task/copy.json --plan /task/planning-draft.json --cognition /task/art-cognition.json --learning-pack /path/to/art-design-foundations-v1 --title-review /task/title-review.json --content-review /task/content-review.json --output /task/planning.json
python scripts/stage_documents.py lock-design --package /task/copy.json --plan /task/art-draft.json --planning /task/planning.json --title-review /task/title-review.json --content-review /task/content-review.json --output /task/art-plan.json
```

When references are present, record-planning reopens each `--learning-pack` and checks exact selected node bytes, refusing invented hits.

The cognition travels in both immutable planning and Art plan, then the readable Art handoff and supervision work report. Revisions preserve old records. Do not recreate research, Copy, all pages or all renders because a receipt or one composition changed.

## Current Copy structure authority

Art consumes the exact Copy—Art identity interface output (copy-graph/1.0). Bind copy_structure_lock and audit_observations in planning and plan. Art cannot change wording, nodes, levels, argument, relationships, page count or sequence, and cannot request upstream rewriting. Record concerns, affected node IDs and impact with disposition=audit-only. The native report retains every observation; unresolved concerns cannot be reported clean. art_content and textual expression_additions are rejected for current graph authoring.

A01—A11, actual knowledge reading, planning, native drafts, original readers and Auditor remain. Read copy-graph.zh-CN.md for the stable boundary. Presentation choices make supplied relationships understandable; they do not authorize new relationships. Historical Art projections remain readable with their frozen tool semantics, never a new-run fallback.
