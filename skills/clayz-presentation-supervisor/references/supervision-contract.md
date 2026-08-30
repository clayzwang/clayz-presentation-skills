# Presentation Supervision Report Contract v3.3

`ppt-supervision-report.json` is an independent post-production audit. It does not approve rework and may not write back to upstream artifacts.

Process supervision uses `ppt-supervision-checkpoint.json`; a checkpoint is diagnostic communication, not a gate, approval form, or veto.

```json
{
  "checkpoint_version": "1.1",
  "checkpoint_id": "CP-01",
  "run_id": "run-0123456789ab4def8123456789abcdef",
  "task_request_sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
  "recorded_at": "2026-08-12T22:10:00+08:00",
  "stage": "copy-to-art-direction",
  "status": "recommend-user-input",
  "related_issue_ids": ["SUP-006"],
  "conflicts": [{
    "conflict_id": "CF-01",
    "issue_ids": ["SUP-006"],
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
  "contract_version": "3.3",
  "origin_namespace": "io.clayz.presentation",
  "status": "supervised",
  "run_id": "run-0123456789ab4def8123456789abcdef",
  "task_request_sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
  "package_id": "example-deck",
  "package_version": "2.1.0",
  "art_direction_plan_contract_version": "1.6",
  "output_qa_contract_version": "3.9",
  "supervised_at": "2026-08-12T22:30:00+08:00",
  "run_status": "complete-with-deferred-acceptance",
  "index_evidence": {},
  "resource_usage": {},
  "environment_observation": {
    "preflight": {"artifact": "runtime-preflight.json", "scan_id": "runtime-example", "sha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc", "run_id": "run-0123456789ab4def8123456789abcdef", "task_request_sha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd", "nonce": "1111111111111111111111111111111111111111111111111111111111111111", "challenge_sha256": "2222222222222222222222222222222222222222222222222222222222222222", "task_root_sha256": "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff", "issued_at": "2026-08-12T20:45:00+08:00", "expires_at": "2026-08-13T20:45:00+08:00", "issuance_receipt_sha256": "4444444444444444444444444444444444444444444444444444444444444444", "consumption_receipt_sha256": "3333333333333333333333333333333333333333333333333333333333333333", "config_sha256": "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"},
    "route": {"route_id": "native-presentation-tool+libreoffice", "authoring_backend": "native-presentation-tool", "render_backend": "libreoffice", "status": "provisional"},
    "required_capabilities": {"configured": ["editable-text", "render-preview"], "satisfied": [], "declared_unverified": ["editable-text", "render-preview"], "missing": []},
    "target_applications": [
      {"application": "powerpoint", "capability": "powerpoint-reopen-render", "availability": "unavailable", "final_status": "deferred", "authoring_gate": false, "evidence_refs": ["runtime-preflight.json#target_application_checks.powerpoint sha256=cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"]},
      {"application": "wps", "capability": "wps-reopen-render", "availability": "unavailable", "final_status": "deferred", "authoring_gate": false, "evidence_refs": ["runtime-preflight.json#target_application_checks.wps sha256=cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"]},
      {"application": "libreoffice", "capability": "libreoffice-reopen-render", "availability": "available", "final_status": "pass", "authoring_gate": false, "evidence_refs": ["output/final-reopen-render/libreoffice/target-application-check.json sha256=9999999999999999999999999999999999999999999999999999999999999999"]}
    ],
    "compatibility_scope": "partial",
    "attribution_summary": "LibreOffice reopen/render passed; native PowerPoint and WPS acceptance is deferred because the host lacks those applications, without blocking authoring."
  },
  "supervisor_roles": {
    "initiator": {"status": "complete", "summary": "started the governed run and returned control", "evidence_refs": ["ppt-resource-inventory.json sha256=8888888888888888888888888888888888888888888888888888888888888888", "ppt-supervision-report.json"]},
    "mediator": {"status": "not-needed", "summary": "recorded that no finding required mediation", "evidence_refs": ["ppt-supervision-report.json#issues"]},
    "recorder": {"status": "complete", "summary": "recorded preflight, stage handoffs, audit, and delivery", "evidence_refs": ["ppt-supervision-report.json#lifecycle_events"]},
    "final_auditor": {"status": "complete", "summary": "reran final validators and completed independent audit", "evidence_refs": ["ppt-output-qa.json sha256=7777777777777777777777777777777777777777777777777777777777777777", "ppt-supervision-report.json#slides"]}
  },
  "lifecycle_events": [
    {"event_id": "SUP-E01", "occurred_at": "2026-08-12T21:00:00+08:00", "phase": "root", "actor_role": "initiator", "action": "supervision-started", "status": "completed", "summary": "classified and initiated the governed presentation run", "evidence_refs": ["ppt-resource-inventory.json sha256=8888888888888888888888888888888888888888888888888888888888888888"]},
    {"event_id": "SUP-E02", "occurred_at": "2026-08-12T21:01:00+08:00", "phase": "preflight", "actor_role": "recorder", "action": "runtime-preflight-completed", "status": "completed", "summary": "inspected host capabilities and locked authoring and render routes", "evidence_refs": ["runtime-preflight.json sha256=cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc"]},
    {"event_id": "SUP-E03", "occurred_at": "2026-08-12T21:02:00+08:00", "phase": "preflight", "actor_role": "recorder", "action": "resource-brief-presented", "status": "completed", "summary": "presented the selected, unavailable, and unused resources before Logic", "evidence_refs": ["ppt-resource-inventory.json#user_brief sha256=8888888888888888888888888888888888888888888888888888888888888888 content_sha256=aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"]},
    {"event_id": "SUP-E04", "occurred_at": "2026-08-12T21:10:00+08:00", "phase": "logic", "actor_role": "recorder", "action": "logic-handoff-recorded", "status": "completed", "summary": "recorded the Logic approval and evidence lock", "evidence_refs": ["ppt-design-package.json sha256=6666666666666666666666666666666666666666666666666666666666666666"]},
    {"event_id": "SUP-E05", "occurred_at": "2026-08-12T21:20:00+08:00", "phase": "copy", "actor_role": "recorder", "action": "copy-handoff-recorded", "status": "completed", "summary": "recorded the Copy approval and evidence lock", "evidence_refs": ["ppt-design-package.json#copy_layer sha256=6666666666666666666666666666666666666666666666666666666666666666"]},
    {"event_id": "SUP-E06", "occurred_at": "2026-08-12T21:30:00+08:00", "phase": "art-direction", "actor_role": "recorder", "action": "art-direction-handoff-recorded", "status": "completed", "summary": "recorded the Art Direction approval and evidence lock", "evidence_refs": ["ppt-art-direction-plan.json sha256=5555555555555555555555555555555555555555555555555555555555555555"]},
    {"event_id": "SUP-E07", "occurred_at": "2026-08-12T22:00:00+08:00", "phase": "output", "actor_role": "recorder", "action": "output-handoff-recorded", "status": "completed", "summary": "recorded the written PPTX and Output QA handoff", "evidence_refs": ["final.pptx sha256=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", "ppt-output-qa.json sha256=7777777777777777777777777777777777777777777777777777777777777777"]},
    {"event_id": "SUP-E09", "occurred_at": "2026-08-12T22:20:00+08:00", "phase": "supervision", "actor_role": "final_auditor", "action": "final-audit-completed", "status": "completed", "summary": "completed the independent object and render audit", "evidence_refs": ["ppt-output-qa.json sha256=7777777777777777777777777777777777777777777777777777777777777777", "ppt-supervision-report.json#slides"]},
    {"event_id": "SUP-E10", "occurred_at": "2026-08-12T22:25:00+08:00", "phase": "delivery", "actor_role": "recorder", "action": "delivery-pair-locked", "status": "completed", "summary": "locked the final PPTX and supervision report as one handoff", "evidence_refs": ["final.pptx sha256=bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", "ppt-supervision-report.json"]},
    {"event_id": "SUP-E11", "occurred_at": "2026-08-12T22:30:00+08:00", "phase": "delivery", "actor_role": "initiator", "action": "control-returned", "status": "returned", "summary": "returned control with the paired artifacts and audit outcome", "evidence_refs": ["ppt-supervision-report.json#control_returned_to"]}
  ],
  "artifact_paths": {
    "runtime_preflight": "runtime-preflight.json",
    "resource_inventory": "ppt-resource-inventory.json",
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
  "delivery_pair": {
    "status": "ready",
    "required_artifacts": ["pptx", "supervision-report"],
    "pptx": {"path": "final.pptx", "sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"},
    "supervision_report": {"path": "ppt-supervision-report.json"},
    "delivery_manifest": {"path": "delivery-manifest.json"},
    "publisher": "scripts/publish_supervised_pair.py",
    "evidence": "the final PPTX hash and supervision report path are locked for the same user handoff"
  },
  "slides": [],
  "issues": [],
  "deck_findings": [],
  "responsibility_attribution": {},
  "recommendations": [],
  "asset_observations": [],
  "control_returned_to": "main-process-or-user"
}
```

`resource_usage` follows `io.clayz.presentation.resource-usage/1.0`. It reconciles every resource selected in the user-visible pre-Logic inventory as actually used or intentionally unused, maps used resources to all five governed stages with concrete evidence, and carries a final user-visible summary. A missing or mismatched reconciliation requires `incomplete-evidence`.

`supervisor_roles` is mandatory and contains exactly `initiator`, `mediator`, `recorder`, and `final_auditor`. Initiator, recorder, and final auditor must be `complete`. Mediator may be `not-needed` only when the report has no issues; any issue requires completed mediation, a v1.1 `ppt-supervision-checkpoint.json`, and one `mediation-recorded` lifecycle event. The checkpoint binds the same run ID, task-request SHA-256, exact report issue IDs, and mediation timestamp. Every external role and lifecycle evidence reference includes `sha256=<actual-file-sha256>` and resolves to a non-empty, contract-valid task-local artifact; report self-references are verified against the report in memory. Each role records a concise outcome and evidence references, never private chain-of-thought.

`lifecycle_events` is a chronological, task-local record. Each governed action is unique and uses its fixed phase, Supervisor role, and status. The canonical order is `supervision-started` → `runtime-preflight-completed` → `resource-brief-presented` → Logic → Copy → Art Direction → Output → optional `mediation-recorded` → `final-audit-completed` → `delivery-pair-locked` → `control-returned`. This makes environment preflight and the resource brief provably precede Logic. The resource-brief event timestamp must match the pre-Logic inventory and its evidence binds both the inventory file SHA-256 and `user_brief.content_sha256`. Mediation exists only for real issues and is never invented for a clean run.

`environment_observation` exactly binds the `runtime-preflight.json` scan ID, raw-file SHA-256, run ID, normalized task-request SHA-256, task-root SHA-256, canonical issuance- and consumption-ledger hashes, exact resolved-config SHA-256, locked route, route-requirement status, and every target application. The report root and preflight run/task bindings must match, and preflight may not omit any capability required by the validated resolved config. Available host-provided capabilities require same-run inspection provenance but remain `host-declared-unverified`: their capabilities appear under `declared_unverified`, not `satisfied`, and their route stays `provisional`. An unavailable target is `deferred`, an available but unexecuted target is `not-selected`, and only an executed check may be `pass` or `fail`; every item fixes `authoring_gate=false`. Deferred and not-selected outcomes bind the hash-checked preflight record. Pass/fail outcomes require a hash-bound `io.clayz.presentation.target-application-check/1.0` receipt tied to the same run, task request, target application, and final PPTX SHA-256; its `observed_at` must be inside the challenge window and between Output handoff and final audit. `compatibility_scope` is derived as `full`, `partial`, or `none` and bounds compatibility claims and attribution.

`run_status` is `clean`, `complete-with-deferred-acceptance`, `issues-found`, or `incomplete-evidence`. Use `complete-with-deferred-acceptance` when there are no other issues but at least one target is `deferred` or `not-selected`; the PPTX and report may still be delivered together. Missing Art Direction, PPTX, the locked-route render, build-deviation evidence, first-class Index materialization, resource-use reconciliation, or any stage receipt requires `incomplete-evidence` and prevents normal delivery.

`origin_namespace` is exactly `io.clayz.presentation`, `status` is exactly `supervised`, and `control_returned_to` names the user or responsible process that received control after audit. `artifact_paths` includes the runtime-preflight and pre-Logic resource-inventory records as first-class evidence, not only downstream build artifacts.

`delivery_efficiency.status` is `pass`, `fail`, or `uncertain`; `uncertain` requires root `incomplete-evidence`. Unless the user specified otherwise, `profile` is `lightweight`. The size audit binds the final PPTX hash and reconciles file size, media counts, duplicates, fonts, and attachments with `ppt-object-inventory.json.package_media`. A deck over its total soft budget may pass when item-level efficiency passes and `exception_reason` states the business need. Duplicate, unused, over-resolution, or accidentally embedded content cannot be excepted.

`delivery_pair` makes the PPTX and supervision report one delivery unit. `required_artifacts` is exactly `["pptx", "supervision-report"]`; the PPTX record contains the filename and verified SHA-256, the report record names this report, `delivery_manifest.path` is exactly `delivery-manifest.json`, and `publisher` is exactly `scripts/publish_supervised_pair.py`. `incomplete-evidence` requires `blocked`; otherwise the validated pair is `ready`. Output stages may stage files, but only the publisher may materialize a new verified bundle and only Supervisor may hand off the two validated artifacts from it. A manually copied or single-file handoff is not a completed delivery.

`asset_observations` records soft feedback only for assets used in this task, such as `asset_id`, `task_fit`, `execution_effect`, `conflict_signal`, `neighbor_value`, `reuse_note`, and evidence. A 1–5 task score is not global quality and may not alter admission, classification, retrieval weight, or promote output to a reference automatically.

## Per-slide structure

Each slide records:

- `slide_id` and `render_file`;
- `planned`: first visual, area signature, silhouette, density, dominant medium, structure signature/type, series and motif, whitespace, context rail, semantic tree, visual-self-correction requirement, required object types/counts, target-type counts, typography minima, data-chart contract, and quantitative-execution contract;
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

Every check evidence string cites the stable slide ID and is unique to that slide and check. Reusing one sentence across checks or pages is invalid. Supervisor reruns the complete Output QA validator against the final PPTX; a self-authored “consistent” statement cannot replace object or render evidence.

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
