# Art cognition and external learning (v0.20.2)

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

## Art changes: record, then independently audit

Art may change conclusion expression, argument, order and pagination without requesting front-loaded approval. Retain the original approved Logic and Copy unchanged. When the actual presentation differs, put an `art_content` extension in planning (or pass `--art-content`) using contract `io.clayz.presentation.art-content/1.0`, `copy_package_sha256`, complete actual `slides`, and `changes`. Slides use the existing visible `copy_units` and `content_relationships` format with distinct IDs. Original data/requirements/source locks remain intact.

Generate exact structural differences with `art_learning.py diff --package /task/copy.json --presentation /task/actual-slides.json` (the presentation file is a slides array). Add `reason`, `evidence` (including explicit uncertainty when evidence is missing), and `impact` to each generated change. This records whole-page content/argument differences and sequence/pagination changes without making a machine claim about their semantic correctness. Do not mutate originals or label Art's new text Copy-approved. Lock binds both actual content and original baseline. Output matches actual Art content; blank or omitted differences are invalid.

For the final reader use `reader_review.py prepare --phase final ... --plan /task/art-plan.json`. Its isolated first read receives only actual rendered pages and neutral brief. The plan and original Copy remain with the auditor until the second pass. Include both as bound `--evidence`; comparison still uses original approved Copy and additionally contains `art_changes`, one observation per change: `change_id`, `assessment` (`justified`, `unsupported`, `uncertain`), `explanation`, `evidence`. A justified difference can pass. Unsupported/uncertain differences remain findings and prevent an unqualified pass. Repairs go to Art; this introduces no upstream preapproval. Original first-read observations remain immutable.
