# Presentation Supervision Report Contract v2.6

`ppt-supervision-report.json` is an independent post-production audit. It does not approve rework and may not write back to upstream artifacts.

Process supervision uses `ppt-supervision-checkpoint.json`; a checkpoint is diagnostic communication, not a gate, approval form, or veto.

```json
{
  "checkpoint_version": "1.0",
  "checkpoint_id": "CP-01",
  "stage": "copy-to-art-direction",
  "status": "recommend-user-input",
  "conflicts": [{
    "conflict_id": "CF-01",
    "severity": "major",
    "cause": "the next five months provide only a monthly average, not monthly detail",
    "decision_impact": "a monthly trend or pressure distribution cannot be drawn",
    "evidence": ["ppt-design-package.json"],
    "approved_baseline": "show monthly average only",
    "downstream_challenge": "the monthly-trend task conflicts with the average-only baseline",
    "alternatives": ["supply monthly values", "express average and gap instead"],
    "user_decision": "pending"
  }],
  "questions_for_user": ["Provide monthly target or forecast values, or confirm an average-and-gap view with the missing detail disclosed."],
  "assumptions_if_continue": ["do not fabricate monthly values; show only the known average and gap"],
  "same_conflict_previously_escalated": false,
  "control_returned_to": "main-process-or-user"
}
```

`status` is `continue`, `recommend-user-input`, or `proceed-with-assumptions`; never `blocked`, `rejected`, or `vetoed`. Escalate the same conflict once without new evidence and normally consolidate to at most three user questions. If the user proceeds, record reversible assumptions and return control.

An approved artifact is the current execution baseline, not an unchallengeable permanent lock. A checkpoint preserves `approved_baseline`, `downstream_challenge`, evidence, alternatives, reversibility, and `user_decision`. Do not write an alternative upstream before user adjudication.

## Root structure

```json
{
  "contract_version": "2.6",
  "package_id": "example-deck",
  "package_version": "2.1.0",
  "art_direction_plan_contract_version": "1.3",
  "output_qa_contract_version": "3.6",
  "supervised_at": "2026-08-12T22:30:00+08:00",
  "run_status": "issues-found",
  "artifact_paths": {
    "package": "ppt-design-package.json",
    "art_direction_plan": "ppt-art-direction-plan.json",
    "pptx": "final.pptx",
    "render_root": "output/rendered",
    "output_qa": "ppt-output-qa.json",
    "object_inventory": "ppt-object-inventory.json",
    "build_deviation_log": "ppt-build-deviation-log.json",
    "font_environment_report": "font-environment-report.json",
    "cjk_render_report": "cjk-render-report.json",
    "size_audit_report": "ppt-size-audit.json",
    "final_reopen_render_root": "output/final-reopen-render"
  },
  "delivery_efficiency": {
    "status": "pass",
    "profile": "lightweight",
    "total_bytes": 1460000,
    "media_share_of_file": 0.82,
    "blocker_count": 0,
    "warning_count": 0,
    "exception_reason": null,
    "evidence": "the size report binds the final hash; an independent object inventory finds no duplicate media, accidental fonts, or attachments"
  },
  "slides": [],
  "issues": [],
  "deck_findings": [],
  "responsibility_attribution": {},
  "recommendations": [],
  "asset_observations": []
}
```

`run_status` is `clean`, `issues-found`, or `incomplete-evidence`. Missing Art Direction, PPTX, final renders, or build-deviation evidence requires `incomplete-evidence`.

`delivery_efficiency.status` is `pass`, `fail`, or `uncertain`; `uncertain` requires root `incomplete-evidence`. Unless the user specified otherwise, `profile` is `lightweight`. The size audit binds the final PPTX hash and reconciles file size, media counts, duplicates, fonts, and attachments with `ppt-object-inventory.json.package_media`. A deck over its total soft budget may pass when item-level efficiency passes and `exception_reason` states the business need. Duplicate, unused, over-resolution, or accidentally embedded content cannot be excepted.

`asset_observations` records soft feedback only for assets used in this task, such as `asset_id`, `task_fit`, `execution_effect`, `conflict_signal`, `neighbor_value`, `reuse_note`, and evidence. A 1–5 task score is not global quality and may not alter admission, classification, retrieval weight, or promote output to a reference automatically.

## Per-slide structure

Each slide records:

- `slide_id` and `render_file`;
- `planned`: first visual, area signature, silhouette, density, dominant medium, structure signature/type, series and motif, whitespace, context rail, semantic tree, visual-self-correction requirement, required object types/counts, target-type counts, typography minima, and data-chart contract;
- `actual_objects`: shapes, text shapes, connectors, pictures, graphic frames, tables, charts, and diagrams;
- `rendered`: observed medium, first visual, area, series backbone, motif, whitespace, context rail, semantic tree, self-correction evidence, minimum type size, token violations, scatter evidence, recognizability, and concrete evidence; and
- `checks`: independent fidelity checks from Logic/Copy through target-application compatibility.

Required checks include:

- `logic_copy_fidelity`
- `copy_art_direction_fidelity`
- `art_direction_build_fidelity`
- `art_direction_first_visual_fidelity`
- `art_direction_area_plan_fidelity`
- `plan_object_fidelity`
- `object_render_fidelity`
- `art_direction_rhythm_fidelity`
- `purposeful_series_fidelity`
- `cross_slide_invariant_fidelity`
- `semantic_whitespace_fidelity`
- `motif_fidelity`
- `context_rail_fidelity`
- `semantic_layout_tree_fidelity`
- `visual_self_correction_integrity`
- `deviation_authorization`
- `qa_truthfulness`
- `anti_cardification`
- `target_app_compatibility`
- `inherited_chrome_fidelity`
- `typography_legibility`
- `scatter_semantics_and_labels`

Check status is `pass`, `fail`, `not-applicable`, or `uncertain`. `uncertain` requires root `incomplete-evidence`. `not-applicable` still needs specific evidence.

`planned.audience_detail_min_pt`, `chart_text_min_pt`, and `data_chart_contract` reproduce the Art Direction plan exactly. On body slides, record `rendered.minimum_audience_text_pt_observed` and every central type-token violation in `nonconforming_point_sizes_observed`. Below-minimum text or a nonempty violation list fails `typography_legibility` and creates an issue.

On scatterplots, inspect `scatter_label_evidence` and `scatter_line_evidence`. Use `SCATTER_ENTITY_LABEL_MISSING_OR_UNREADABLE` for missing, overlapping, or unreadable names and `SCATTER_UNJUSTIFIED_POINT_CONNECTIONS` for semantically unsupported entity connections. Non-scatter slides mark the check `not-applicable`; scatter slides may not.

Allowed `medium_label` values are `typography`, `data-chart`, `table`, `timeline`, `swimlane`, `matrix`, `relationship-diagram`, `process`, `photo-or-screenshot`, `scenario-illustration`, `cards`, `columns`, `mixed`, `other`, and `not-reviewed`.

## Issue structure

```json
{
  "issue_id": "SUP-006",
  "finding_code": "ART_DIRECTION_FIRST_VISUAL_DRIFT",
  "slide_id": "S06",
  "severity": "major",
  "owner_layer": "output-build",
  "confidence": "high",
  "failed_checks": ["art_direction_build_fidelity", "art_direction_first_visual_fidelity"],
  "source_artifacts": ["ppt-art-direction-plan.json", "final.pptx", "output/rendered/6.png"],
  "evidence": "the plan's first visual is the four-stage axis; four light boxes occupy the actual dominant area",
  "expected": "nodes, stages, and progression form the first visual",
  "actual": "the slide reads first as four ordinary columns",
  "impact": "stage and progression meaning is lost",
  "recommended_change": "restore the axis and node area and hierarchy",
  "regression_rule": "a timeline slide must be recognizable as a timeline within three seconds at thumbnail size"
}
```

`severity` is `critical`, `major`, `moderate`, or `minor`. `owner_layer` is `logic`, `copy`, `art-direction`, `output-build`, `output-qa`, `interface`, or `system`. `confidence` is `high`, `medium`, or `low`.

Stable finding codes include at least:

```text
LOGIC_RELATION_UNDERSPECIFIED
COPY_RELATION_DRIFT
COPY_ATOMIZATION_PRESSURE
ART_DIRECTION_PLAN_CONTRADICTION
ART_DIRECTION_NOT_EXECUTED
ART_DIRECTION_FIRST_VISUAL_DRIFT
ART_DIRECTION_ATTENTION_HIERARCHY_MISMATCH
ART_DIRECTION_AREA_PLAN_DRIFT
ART_DIRECTION_RHYTHM_DRIFT
PURPOSEFUL_SERIES_BROKEN
UNJUSTIFIED_SILHOUETTE_REPETITION
CROSS_SLIDE_INVARIANT_DRIFT
SEMANTIC_WHITESPACE_FILLED
ART_DIRECTION_FALSE_SEMANTIC_WHITESPACE
MOTIF_SEQUENCE_DRIFT
CONTEXT_RAIL_UI_DRIFT
SEMANTIC_LAYOUT_TREE_FLATTENED
VISUAL_SELF_CORRECTION_EVIDENCE_MISSING
CANDIDATE_DIVERSITY_COLLAPSED
AUTOMATIC_SCORE_SELECTED_LAYOUT
BUILD_UNAPPROVED_DEVIATION
PLAN_TABLE_WITHOUT_TABLE_CELL
PLAN_OBJECT_GRAMMAR_MISMATCH
BUILD_TABLE_MISSING
BUILD_CHART_MISSING
BUILD_STRUCTURE_COLLAPSED_TO_CARDS
BUILD_REQUIRED_OBJECT_MISSING
RENDERED_MEDIUM_UNCLEAR
DECK_SILHOUETTE_REPETITION
QA_FALSE_PASS
MASTER_PAGE_NUMBER_DUPLICATED
TITLE_CHROME_DUPLICATED
FONT_SIZE_BELOW_MINIMUM
FONT_SIZE_NONCONFORMING_TOKEN
CJK_GLYPH_RENDER_MISSING
PPTX_LIGHTWEIGHT_PROFILE_MISSING
PPTX_DUPLICATE_OR_UNUSED_MEDIA
PPTX_RASTER_OVERSIZED
PPTX_UNEXPECTED_EMBEDDED_PAYLOAD
SCATTER_ENTITY_LABEL_MISSING_OR_UNREADABLE
SCATTER_UNJUSTIFIED_POINT_CONNECTIONS
EVIDENCE_INCOMPLETE
CONTENT_NOT_READY_BEFORE_DESIGN
AGGREGATE_WITHOUT_UNDERLYING_DETAIL
NARRATIVE_CHAIN_SPLIT
PREMATURE_DECLARATION_BEFORE_DILEMMA
PUNCTUATION_DEPENDENT_LAYOUT
RELATED_DATA_CARDIFICATION
PLAN_QUALITY_FALSE_PASS
```

Every failed per-slide check must be referenced by at least one issue on that slide.

## Deck findings, recommendations, and attribution

`deck_findings` is a string array containing cross-slide patterns and evidence. Each `recommendations` item includes `priority`, `target_layer`, `change`, `verification`, and `scope`.

Use integer responsibility weights summing to 100 only with sufficient evidence. Otherwise use qualitative attribution:

```json
{
  "mode": "qualitative",
  "confidence": "low",
  "primary": ["output-build", "output-qa"],
  "secondary": ["interface"],
  "rationale": "generation-process records are incomplete, so no false-precision percentages are used"
}
```
