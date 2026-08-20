# Art Direction Plan Contract v1.3

`ppt-art-direction-plan.json` is the sole visual-decision handoff between a `copy-approved` script package and Output. It may not introduce new business content. Set its status to `art-direction-approved` only after every visual decision is locked.

## Root structure

```json
{
  "contract_version": "1.3",
  "status": "art-direction-approved",
  "package_contract_version": "2.1",
  "package_id": "example-deck",
  "package_version": "2.1.0",
  "communication_contract": {},
  "art_direction": {},
  "reference_budget": {},
  "ab_review": {},
  "decision_log": {},
  "typography_contract": {},
  "deck_rhythm": {},
  "slides": []
}
```

`communication_contract` must reproduce `brief.preflight` from the script package exactly. `typography_contract`, `deck_rhythm`, and each slide's `copy_unit_map`, `visual_hierarchy`, and `medium_execution_contract` retain the machine-checkable fields defined by expression plan v2.1, while Art Direction owns every visual choice.

`typography_contract` inherits all type, grid, and exception policies from central configuration:

- `body_min_pt`, `audience_detail_min_pt`, and `chart_text_min_pt` must not be lower than their corresponding `theme.typography` limits.
- `even_point_sizes_required` equals `theme.typography.prefer_even_point_sizes`.
- `fractional_point_sizes_allowed` equals `theme.typography.allow_fractional_point_sizes`.
- `minimum_exception_policy` equals `theme.typography.minimum_exception_policy`.
- `grid_system` is derived from `layout.column_count`, for example `12-column`.

When content does not fit, enlarge the dominant medium, remove nonessential ticks, facet, split the slide, or send the issue back to Copy. Never silently reduce configured minimums.

## `art_direction`

Required fields:

- `visual_thesis`: the deck-wide visual proposition.
- `material_route`: one of the four material routes.
- `first_impression`: the intended first audience impression.
- `composition_principles` and `forbidden_defaults`.
- `silhouette_sequence`, `density_sequence`, `dominant_media_sequence`, and `motif_sequence`.
- `brand_constraints_repeated`.
- `approval={status, approved_by, notes}`.

The four sequences must cover the complete deck in slide order. `density_sequence` describes visual density only; content load and decision weight are inherited slide by slide from Logic. Output may start only when `approval.status=approved`. `approved_by` must record the real approval basis, not a self-declaration such as “complete.”

## `reference_budget`

```json
{
  "max_total_loaded": 24,
  "max_per_archetype": 6,
  "max_sequences_loaded": 4,
  "loaded_record_ids": ["REF-DEMO-015", "REF-DEMO-299"],
  "loaded_sequence_ids": ["SEQ-DEMO-QUARTERS"],
  "query_log": [],
  "sequence_query_log": [],
  "budget_respected": true
}
```

Reuse of one case across multiple slides counts once. `query_log` records search conditions and adoption outcomes; “reviewed references” is not sufficient.

## `decision_log`

```json
{
  "conflicts": [
    {
      "conflict_id": "CF-01",
      "layers": ["copy", "art-direction"],
      "rules": ["preserve all locked copy", "single-slide capacity is insufficient at target type size"],
      "owner": "copy",
      "resolution": "return to Copy and split into two slides; Art Direction does not delete copy",
      "backflow": true,
      "approval_basis": "user approved the split"
    }
  ],
  "deviations": [],
  "unresolved": []
}
```

An approved plan must have an empty `unresolved` array. Resolve conflicts in this authority order: user and facts, Logic, Copy, Art Direction, Output. A downstream layer may not override an upstream layer.

## Additional per-slide fields

In addition to the expression-plan fields, every slide includes:

- `design_intent`: communication task, first impression, first visual, attention order, composition rationale, and prohibited fallbacks.
- `area_plan`: regions, responsibilities, area percentages, included `copy_id` values, and 12-column grid spans.
- `semantic_layout_tree`: grouping, containment, relations, reading order, and shape intent.
- `reference_selection`, plus `reference_exception` when no reference is used.
- `ab_review`: candidates, selection, rejection reasons, and gray-box status.
- `art_direction_lock`.
- `handoff_status=ready-for-output`.
- `content_load_class_repeated` and `decision_weight_repeated`.
- `series_visual_contract`: series identity, backbone behavior, persistent elements, progressive change, allowed variation, and exit reason.
- `motif_id`, or `null`.
- `semantic_whitespace`: type, regions, narrative responsibility, and protection status.
- `persistent_context_rail`: enablement, purpose, scope, current marker, and maximum area.
- `medium_execution_contract.data_chart_contract`: chart type, type size, direct labels, point-connection policy, semantic lines, and collision avoidance; `null` for non-data slides.

The percentages in `area_plan` total 90–110 percent, allowing approximation for the title zone, safety margins, and local overlap. Every visible `copy_id` must be covered.

## Semantic layout tree

```json
{
  "tree_id": "SLT-S03-B",
  "mode": "hierarchical",
  "root_node_id": "N0",
  "nodes": [
    {"node_id": "N0", "parent_node_id": null, "node_type": "canvas", "semantic_role": "slide canvas", "region_id": null, "copy_ids": [], "shape_family": "none", "reading_order": 0},
    {"node_id": "N1", "parent_node_id": "N0", "node_type": "intent-zone", "semantic_role": "primary evidence", "region_id": "R-MAIN", "copy_ids": ["S03-C01"], "shape_family": "chart", "reading_order": 1}
  ],
  "relations": [],
  "checks": {
    "single_root": true,
    "all_copy_ids_covered_once": true,
    "hierarchy_explains_grouping": true,
    "reading_order_explicit": true,
    "shape_choices_semantic": true,
    "no_flat_card_default": true
  }
}
```

`mode` is `flat` or `hierarchical`. Every non-root `region_id` refers to `area_plan`; node `copy_ids` cover the Copy sequence exactly once. Allowed relation types are `contains`, `peer`, `sequence`, `cause`, `condition`, `supports`, `compares`, `feedback`, and `anchors`.

The tree must not duplicate exact copy or coordinates. `copy_unit_map` remains the single source of truth for text and rendering targets; `area_plan` remains the single source of truth for region geometry. Allowed shape families are `none`, `rectangle`, `rounded-rectangle`, `ellipse`, `path`, `line`, `table`, `chart`, `image`, `text`, and `mixed`. A rectangle is never the default container.

## Series, motifs, and whitespace

Example `series_visual_contract`:

```json
{
  "series_id": "SER-Q",
  "behavior": "locked-backbone",
  "persistent_elements": ["Q1–Q4 time base", "short-cycle campaign base"],
  "logic_change_repeated": "add phase three and the current-period analytical judgment",
  "progressive_change": "reveal Q3 and highlight the current quarter while keeping other quarters fixed",
  "allowed_variation": ["current-quarter emphasis", "new data and annotations"],
  "sequence_reference_ids": ["SEQ-DEMO-QUARTERS"],
  "break_reason": ""
}
```

`behavior` is `standalone`, `locked-backbone`, `controlled-variation`, or `series-break`. Without a Logic `series_id`, use only `standalone`. With a series, use one of the other three. `series-break` is valid only when Logic has `series_role=break`, and it requires an exit reason.

`semantic_whitespace.mode` is `none`, `future-space`, `unknown-space`, or `pause`. Any non-`none` mode needs at least one region, a concrete narrative responsibility, and `protected_from_filling=true`. If a slide is merely underfilled, use `none` and rebalance `area_plan`.

When `persistent_context_rail.enabled=true`, the deck must be long or continuously serialized, and `max_area_percent` must be between 1 and 8. When disabled, it is 0. The rail must not become the first visual or an application-style panel.

## Data-chart contract

A data slide's `medium_execution_contract.data_chart_contract` includes at least:

```json
{
  "chart_type": "scatter",
  "audience_text_min_pt": 12,
  "even_point_sizes_only": false,
  "direct_label_policy": "all-entities",
  "entity_label_field": "entity_name",
  "point_connection_policy": "markers-only",
  "semantic_lines": [],
  "label_collision_strategy": ["offset", "leader-lines", "facet-or-split"],
  "unlabeled_point_exception": null
}
```

- Scatterplots use `direct_label_policy=all-entities`. Place entity names next to points or connect each label to its point; do not require lookup through a legend, number, or color.
- Scatterplot `point_connection_policy` is `markers-only` or `semantic-lines-only`. Different entities are not connected by default, and input order is not a business relation.
- With `semantic-lines-only`, every line records `line_id`, `meaning`, and `visible_label`. Target, 100-percent, median, statistical-fit, iso-value, and same-entity time-path lines are acceptable. Decorative or default connecting lines are not.
- Resolve collisions through offsets, label-to-point leaders, a larger plot region, facets, or a slide split. Leaders connect labels to their own points and must not imply entity-to-entity relationships.
- `unlabeled_point_exception` is normally `null`. Omitting an entity name requires backflow and explicit user approval; Output may not decide this independently.
- Non-scatter charts still obey the configured chart-text minimum and point-size parity policy. Depending on the comparison task, `direct_label_policy` may be `key-values` or `as-needed`.

Additional `deck_rhythm` fields:

- `series_groups`: repeat Logic series identities, pages, and behaviors.
- `motif_sequence`: record a motif ID or `null` for every slide.
- `motif_contracts`: purpose, establishment slide, recurrence slides, local-variation rule, break slide, and break reason for each motif.
- `semantic_whitespace_slide_ids`.
- `purposeful_repetition_review`: confirm that series repetition has a business purpose and that non-series isomorphism has a break strategy.

## A/B candidates

Each candidate records at least:

```json
{
  "candidate_id": "B",
  "silhouette_family": "full-width-evidence",
  "first_visual": "primary trend chart",
  "main_backbone": "trend → drivers → action",
  "reading_path": "left-to-right",
  "area_plan": [],
  "reference_ids": ["REF-DEMO-015"],
  "risk_notes": [],
  "semantic_tree_signature": "primary trend contains two driver levels; action anchors at lower right",
  "prototype_file": "greybox/S03-B.png"
}
```

A high-risk slide has exactly two candidates; an ordinary slide retains at least one locked candidate. The result must agree with the slide silhouette, first visual, and area plan.

For high-risk slides, `ab_review.visual_self_correction` records `required=true`, `max_rounds=2`, one or two prototype-render rounds, five-dimensional observations, `preserve`, `change`, candidate-difference status, automated signals as `diagnostic-only`, `professional-visual-judgment` as the final basis, and an explicit stop reason. The five dimensions are production integrity, text readability, attention hierarchy, structural semantics, and composition-to-task fit.

If both candidates are insufficient, a pre-final round may use `both-insufficient-rebuild`, but the final round must yield an approvable choice. Never select automatically from an aggregate score, let both candidates converge to one shell, or exceed two rounds.

## Locks

Every following `art_direction_lock` field is `true`:

- `composition_locked`
- `silhouette_locked`
- `dominant_medium_locked`
- `density_locked`
- `reading_path_locked`
- `copy_mapping_locked`
- `series_behavior_locked`
- `motif_locked`
- `semantic_whitespace_locked`
- `context_rail_locked`
- `semantic_layout_tree_locked`

After Art Direction changes, any previous PPTX, Output QA, and Supervisor report is invalid.
