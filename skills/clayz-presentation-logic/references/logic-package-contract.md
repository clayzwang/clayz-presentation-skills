# PPT v2.3 Logic package contract

`ppt-design-package.json` is the single handoff file shared by Logic, Copy, and Output. Logic writes the root fields and `logic_layer`; Copy appends `copy_layer` to the same file. Never maintain parallel packages.

## Root structure

```json
{
  "contract_version": "2.3",
  "package_id": "example-deck",
  "version": "2.1.0",
  "status": "logic-approved",
  "brief": {},
  "resource_inventory": {},
  "index_evidence": {},
  "logic_layer": {},
  "copy_layer": null,
  "approvals": {
    "logic": {"status": "approved", "approved_by": "user", "notes": ""},
    "copy": null
  }
}
```

`resource_inventory` follows `io.clayz.presentation.resource-inventory/1.0`. Supervisor must finish the seven-scope scan, show the user what was found, selected, unavailable, and which execution route will be used, then lock the ready inventory before Logic starts. Every selected non-host resource carries a content fingerprint; a new resource requires a revised inventory and another visible brief.

`index_evidence` follows `io.clayz.presentation.index-execution-evidence/1.0`. At `logic-approved`, it contains the locked Provider snapshots, completed task-local owner materialization when applicable, and finalized Logic Retrieval Receipts. At `copy-approved`, it additionally contains finalized Copy receipts while preserving the same lock.

Advance `status` only through `draft -> logic-approved -> copy-approved`. After a material Logic change, remove the stale `copy_layer` and return the package to `draft`, or obtain a new `logic-approved` decision.

## `brief`

```json
{
  "purpose": "Review quarterly operations and request the next resource allocation",
  "initiator_stance": "Propose an improvement plan",
  "preflight": {
    "audience": {"primary": "Product and operations decision team"},
    "material_type": "management-report",
    "management_stage": "monitoring-diagnosis",
    "narrative_archetype": "operating-diagnosis",
    "desired_outcome": {"mode": "approve", "target": "Approve pilot resources"},
    "confirmation": {
      "audience": "user-provided",
      "material_type": "user-confirmed",
      "management_stage": "user-confirmed",
      "narrative_archetype": "user-confirmed",
      "desired_outcome": "user-confirmed"
    }
  },
  "usage_context": "Presented in a meeting and circulated afterward",
  "duration_minutes": 20,
  "constraints": []
}
```

`material_type` describes the communication setting: `management-report`, `business-analysis`, `strategy-deployment`, or `sales-training`.

`management_stage` locates the deck in the management loop: `strategic-framing`, `mechanism-design`, `campaign-deployment`, `operating-system`, `monitoring-diagnosis`, `experiment-review`, or `skill-enablement`.

`narrative_archetype` describes the story pattern: `operating-diagnosis`, `policy-reform`, `strategy-map`, `operating-system-design`, `experiment-learning`, `annual-mobilization`, `decision-proposal`, or `training-sop`. These fields form a two-layer route and must not be collapsed into one generic "PPT type." `desired_outcome.mode` is `understand`, `approve`, or `execute`.

## `logic_layer`

Required fields:

- `knowledge_requirements`: questions still requiring research or verification;
- `sources`: source inventory containing at least `source_id`, `resource_id`, `type`, `title`, `locator`, `accessed_at`, and `reliability`; every `resource_id` must reference a resource selected in the pre-Logic inventory;
- `glossary`: terms, definitions, and sources;
- `metric_dictionary`: metric name, definition, formula, unit, period, and source;
- `deck_message_tree`: overall claim, sections, and slide-level claims;
- `narrative`: opening, progression, turning points, closing, and page-order rationale;
- `cross_slide_contract`: cross-slide invariants and semantic series;
- `slides`: slide-level logic;
- `open_items`: unresolved items;
- `lock`: the Logic lock.

### Logic lock

At `logic-approved`, every field below must be `true`:

```json
{
  "slide_order_locked": true,
  "claims_locked": true,
  "numbers_locked": true,
  "metric_definitions_locked": true,
  "semantic_objects_locked": true,
  "semantic_relations_locked": true,
  "page_message_trees_locked": true,
  "sources_locked": true,
  "management_route_locked": true,
  "reasoning_contracts_locked": true,
  "cross_slide_contract_locked": true
}
```

## Narrative and cross-slide contract

`narrative` must contain at least:

```json
{
  "opening": "Establish the performance facts and management tension",
  "progression": "Move from the overall result to user stages, then from causes to action",
  "turning_points": ["S06 moves from diagnosis to proof of controllability"],
  "closing": "Conclude with the next action that requires approval",
  "management_stage_path": ["monitoring-diagnosis", "campaign-deployment"],
  "audience_state_arc": [
    {"slide_id": "S02", "state_before": "Knows the result is under pressure", "state_after": "Understands where the gap is concentrated", "narrative_move": "locate"}
  ]
}
```

`cross_slide_contract`:

```json
{
  "invariants": [
    {
      "invariant_id": "INV-SEGMENT-ORDER",
      "kind": "object-order",
      "scope_slide_ids": ["S08", "S09", "S10"],
      "locked_values": ["Trial users", "Active users", "Collaborating teams", "Enterprise accounts"],
      "rationale": "Usage, retention, and experiment results must map to the same user-stage order"
    }
  ],
  "series": [
    {
      "series_id": "SER-MAP",
      "purpose": "object-drilldown",
      "slide_ids": ["S08", "S09", "S10"],
      "comparison_key": "User stage",
      "invariant_ids": ["INV-SEGMENT-ORDER"],
      "change_by_slide": [
        {"slide_id": "S08", "new_information": "Usage behavior and gaps", "unchanged_context": "User-stage definitions and order"}
      ],
      "break_rule": "Leave the series only when moving to a cross-stage synthesis"
    }
  ]
}
```

`kind` is `term`, `object-order`, `metric-definition`, `analysis-axis`, `grouping`, or `scope`. `purpose` is `compare`, `progressive-reveal`, `time-evolution`, `object-drilldown`, `policy-family`, or `accumulation`. A series locks semantic constants and each slide's new information; it does not prescribe repeated layouts.

## Slide-level logic

```json
{
  "slide_id": "S03",
  "section_id": "SEC01",
  "narrative_role": "recommendation",
  "audience_state_before": "Accepts the problem but does not know what to change",
  "audience_state_after": "Accepts two improvement routes and their validation approach",
  "analysis_level": "management-action",
  "zoom_transition": "hold",
  "content_load_class": "standard",
  "decision_weight": "high",
  "series_id": null,
  "series_role": "standalone",
  "question_answered": "How should the next stage improve?",
  "claim": "The next stage must improve both onboarding guidance and permission defaults.",
  "transition_from": "The previous slide confirms gaps in activation and collaboration.",
  "transition_to": "The next slide assigns ownership and validation cadence for both improvements.",
  "data": [],
  "logic_map": {
    "statement": "The improvement direction contains two peer actions: onboarding guidance and permission defaults.",
    "objects": [
      {"object_id": "O01", "label": "Improvement", "type": "action", "definition": "Parent class for next-stage actions"},
      {"object_id": "O02", "label": "Improve onboarding guidance", "type": "method", "definition": "Reduce the learning cost of completing the first key task"},
      {"object_id": "O03", "label": "Clarify default permissions", "type": "method", "definition": "Reduce configuration friction after team creation"}
    ]
  },
  "page_message_tree": {
    "root_node_id": "N00",
    "reading_sequence": ["N00", "N01", "N02", "N03"],
    "nodes": [
      {"node_id": "N00", "parent_node_id": null, "level": 0, "semantic_role": "claim", "content_ref": "claim", "sibling_group_id": null, "children": ["N01"]},
      {"node_id": "N01", "parent_node_id": "N00", "level": 1, "semantic_role": "category", "content_ref": "object:O01", "sibling_group_id": "G-ROOT", "children": ["N02", "N03"]},
      {"node_id": "N02", "parent_node_id": "N01", "level": 2, "semantic_role": "action", "content_ref": "object:O02", "sibling_group_id": "G-IMPROVE", "children": []},
      {"node_id": "N03", "parent_node_id": "N01", "level": 2, "semantic_role": "action", "content_ref": "object:O03", "sibling_group_id": "G-IMPROVE", "children": []}
    ]
  },
  "semantic_relations": [
    {"relation_id": "R01", "type": "contains", "source_object_ids": ["O01"], "target_object_ids": ["O02", "O03"], "direction": "forward", "strength": "confirmed", "evidence_source_ids": ["SRC01"]},
    {"relation_id": "R02", "type": "peer", "source_object_ids": ["O02"], "target_object_ids": ["O03"], "direction": "none", "strength": "confirmed", "evidence_source_ids": ["SRC01"]}
  ],
  "source_ids": ["SRC01"],
  "claim_status": "recommendation",
  "confidence": "high",
  "reasoning_contracts": {
    "action_traceability": [
      {
        "action_node_id": "N02",
        "evidence_node_ids": ["N01"],
        "owner_object_ids": ["O01"],
        "timing": "Next operating cycle",
        "metric_refs": [],
        "review_cadence": "Monthly review"
      }
    ],
    "change_mechanism": null,
    "operating_system": null,
    "experiment_learning": null
  },
  "do_not_change": ["Keep the two actions as peers; do not merge them into one explanatory sentence"]
}
```

`zoom_transition` is `hold`, `zoom-in`, `zoom-out`, `shift`, or `none`. `content_load_class` is `light`, `standard`, `dense`, or `detail-dense`. `decision_weight` is `low`, `medium`, `high`, or `critical`. `series_role` is `establish`, `continue`, `advance`, `culminate`, `break`, or `standalone`.

## Advanced reasoning contracts

- `action_traceability`: trace each action node to evidence nodes and record owner, time, metric, and review cadence. Metric references use slide-local `data_id` values.
- `change_mechanism`: required when a slide uses `transforms-to`. Include `old_constraint_object_ids`, `rule_change_object_ids`, `behavior_change_object_ids`, `result_object_ids`, `scope_object_ids`, and `exception_object_ids`. A From/To claim is valid only when it explains the old constraint, rule change, behavior change, and result.
- `operating_system`: required for `narrative_role=operating-system`. Include `input_object_ids`, `decision_rules`, `output_object_ids`, `user_object_ids`, `cadence`, `feedback_relation_ids`, and `exception_object_ids`. Without inputs, rules, outputs, users, cadence, or feedback, call the construct a classification framework, not an operating system.
- `experiment_learning`: required for `narrative_role=experiment-learning`. Include `hypothesis`, `intervention_object_ids`, `observation_refs`, `disconfirmed_belief`, `new_learning`, and `next_test`. `observation_refs` uses slide-local nodes or data references.

A `condition` relation must also contain `combination`: `all-of`, `any-of`, or `one-of`. Other relations must not carry that field. `peer.direction` must be `none`; `sequence` and `transforms-to` must be directed. Never imply sequence merely through reading order.

## Node and reference rules

- `content_ref` is only `claim`, `object:<object_id>`, `data:<data_id>`, or `relation:<relation_id>`.
- Each slide has exactly one root. Every non-root node has an existing parent and `level = parent.level + 1`.
- `children` and `parent_node_id` are reciprocal. `reading_sequence` covers every node exactly once.
- Multiple children of one parent share a non-empty `sibling_group_id`; retain a stable group ID for a single child when useful.
- `semantic_role` describes logical responsibility, never a visual role. Reject labels such as `left-card`, `accent-box`, or `arrow-step`.
- `logic_map.statement` describes objects and relationships, never coordinates, shapes, colors, or typography.

## Data and evidence

Every `data` item contains at least `data_id`, `metric_name`, `display_value`, `raw_value`, `unit`, `period`, `definition_ref`, `source_ids`, and `evidence_status`. `raw_value` may be `null` only when the status explicitly records missing data; never display an invented value.

`claim_status` is `source-fact`, `direct-calculation`, `interpretation`, `causal-claim`, `forecast`, `recommendation`, `target`, `hypothesis`, or `missing-data`. Use `cause` only when evidence supports causality; otherwise use `supports`, `maps-to`, or hypothesis strength.

## Forbidden Logic fields

Do not place `copy_id`, `visible_copy`, `speaker_notes`, `font`, `font_size`, `color`, `layout`, `position`, `shape`, `text_box`, or `line_break` inside `logic_layer`. They belong to Copy or Output.
