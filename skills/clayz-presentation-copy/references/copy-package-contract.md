# PPT v2.1 Copy-layer contract

Copy appends `copy_layer` to the same `ppt-design-package.json` while its status is `logic-approved`. On completion, root status becomes `copy-approved`; `logic_layer` remains byte-for-byte unchanged.

## `copy_layer`

```json
{
  "logic_version": "2.1.0",
  "cross_slide_copy_contract": {
    "invariant_renderings": [
      {
        "invariant_id": "INV-SEGMENT-ORDER",
        "visible_terms": ["Trial users", "Active users", "Collaborating teams", "Enterprise accounts"],
        "order_locked": true,
        "aliases_forbidden": ["Class A", "Class B", "Class C", "Class D"]
      }
    ],
    "series_copy_strategies": [
      {
        "series_id": "SER-MAP",
        "stable_language": "Keep user-stage names and order fixed",
        "progression_language": "Each title states the new analytical layer and judgment",
        "repetition_rule": "Repeat only to support mapping; do not duplicate generic phrasing"
      }
    ]
  },
  "slides": [],
  "lock": {
    "titles_locked": true,
    "storylines_locked": true,
    "visible_copy_locked": true,
    "copy_hierarchy_locked": true,
    "numbers_locked": true,
    "punctuation_locked": true,
    "intentional_line_breaks_locked": true,
    "speaker_notes_locked": true,
    "title_modes_locked": true,
    "narrative_functions_locked": true,
    "cross_slide_copy_locked": true
  }
}
```

`logic_version` equals root `version`. A new Logic version invalidates the previous `copy_layer`.

## Slide-level copy

```json
{
  "slide_id": "S03",
  "title_mode": "action-directive",
  "storyline_function": "action-bridge",
  "audience_transition_copy_strategy": "Restate the confirmed gap, then explain how the two actions will be tested",
  "title_copy_id": "C-S03-01",
  "storyline_copy_id": "C-S03-02",
  "copy_units": [
    {
      "copy_id": "C-S03-01",
      "text": "Next-stage improvement: optimize onboarding and permission settings together",
      "role": "title",
      "text_mode": "sentence",
      "source_logic_node_ids": ["N00"],
      "logic_level": 0,
      "parent_copy_id": null,
      "sibling_group_id": null,
      "grammar_signature": "judgment-sentence",
      "order": 1,
      "render_separately": true,
      "merge_with_children": false,
      "intentional_line_breaks": []
    },
    {
      "copy_id": "C-S03-02",
      "text": "Advance improvement through two peer routes: onboarding guidance and permission defaults.",
      "role": "storyline",
      "text_mode": "sentence",
      "source_logic_node_ids": ["N00"],
      "logic_level": 0,
      "parent_copy_id": null,
      "sibling_group_id": null,
      "grammar_signature": "storyline-sentence",
      "order": 2,
      "render_separately": true,
      "merge_with_children": false,
      "intentional_line_breaks": []
    },
    {
      "copy_id": "C-S03-03",
      "text": "Improvement",
      "role": "group-label",
      "text_mode": "label",
      "source_logic_node_ids": ["N01"],
      "logic_level": 1,
      "parent_copy_id": "C-S03-01",
      "sibling_group_id": "G-ROOT",
      "grammar_signature": "action-category",
      "order": 3,
      "render_separately": true,
      "merge_with_children": false,
      "intentional_line_breaks": []
    },
    {
      "copy_id": "C-S03-04",
      "text": "Improve onboarding guidance",
      "role": "item",
      "text_mode": "list-item",
      "source_logic_node_ids": ["N02"],
      "logic_level": 2,
      "parent_copy_id": "C-S03-03",
      "sibling_group_id": "G-IMPROVE",
      "grammar_signature": "verb-object",
      "order": 4,
      "render_separately": true,
      "merge_with_children": false,
      "intentional_line_breaks": []
    },
    {
      "copy_id": "C-S03-05",
      "text": "Clarify permission defaults",
      "role": "item",
      "text_mode": "list-item",
      "source_logic_node_ids": ["N03"],
      "logic_level": 2,
      "parent_copy_id": "C-S03-03",
      "sibling_group_id": "G-IMPROVE",
      "grammar_signature": "verb-object",
      "order": 5,
      "render_separately": true,
      "merge_with_children": false,
      "intentional_line_breaks": []
    }
  ],
  "node_copy_map": [
    {"logic_node_id": "N00", "primary_copy_id": "C-S03-01", "supplemental_copy_ids": ["C-S03-02"]},
    {"logic_node_id": "N01", "primary_copy_id": "C-S03-03", "supplemental_copy_ids": []},
    {"logic_node_id": "N02", "primary_copy_id": "C-S03-04", "supplemental_copy_ids": []},
    {"logic_node_id": "N03", "primary_copy_id": "C-S03-05", "supplemental_copy_ids": []}
  ],
  "footnote_copy_ids": [],
  "speaker_notes": [
    {"note_id": "NOTE-S03-01", "text": "Introduce the parent class, then explain each action.", "source_ids": []}
  ],
  "series_copy_review": {
    "series_id": null,
    "invariant_terms_preserved": true,
    "object_order_preserved": true,
    "new_information_explicit": true
  }
}
```

`title_mode` is `cover`, `factual-status`, `analytical-judgment`, `mechanism-rule`, `action-directive`, `transition-assertion`, `instructional-action`, or `closing`.

`storyline_function` is `none`, `evidence-bridge`, `mechanism-explanation`, `action-bridge`, `audience-transition`, `instruction-bridge`, or `scope-qualification`. Cover and closing slides use `none`; ordinary body slides do not.

`series_copy_review.series_id` equals Logic. Standalone slides use `null` but retain three `true` checks to prove that no cross-slide drift was introduced. For a series slide, its new learning must be visible in the title, storyline, or body.

## Atomic-unit rules

- `copy_id` is unique across the deck; `text` is non-empty and final.
- `source_logic_node_ids` is non-empty and references only nodes on the same slide.
- `logic_level` equals the mapped primary node level. Supplemental copy may map to the same node but does not create a new hierarchy level.
- `role` is `title`, `subtitle`, `storyline`, `group-label`, `item`, `evidence`, `data-label`, `data-value`, `data-unit`, `annotation`, `footnote`, or `closing`.
- `text_mode` is `sentence`, `label`, `list-item`, `label-value`, `dialogue`, `quote`, or `note`.
- `render_separately` is `true`; `merge_with_children` is `false`. Separate rendering means a traceable child target for each `copy_id`, not necessarily a separate text box or card. Targets may share a table, timeline, swimlane, chart, or grouped container.
- `intentional_line_breaks` is an array of character indices. Keep newline characters out of `text`.
- Do not simulate columns with pipes or three consecutive spaces.

## Node-mapping rules

- `node_copy_map` covers every Logic node exactly once.
- Every node has exactly one `primary_copy_id`; different nodes never share primary copy.
- The primary unit's `source_logic_node_ids` contains only its mapped node.
- A parent's primary text does not contain the full primary text of any child.
- A child's `parent_copy_id` equals the parent's `primary_copy_id`.
- Primary units in one Logic sibling group share `sibling_group_id`, `grammar_signature`, `role`, and `text_mode`. Split semantically different members in Logic first.

## Slide exceptions

- A cover has `title_copy_id` and an optional subtitle; `storyline_copy_id` may be `null`.
- A closing slide uses `closing`; its text comes from the user or approved copy, never from a framework, theme, or historical example.
- A body slide has a title and one-sentence storyline with no intentional break.
- A low-load, high-decision transition slide may omit a conventional body list but must advance audience state through `transition-assertion` and `audience-transition`.
- A dense analytical title may use a two-part expression and intentional break; do not reduce font size merely to force one line.
- Series slides preserve the names and order in `invariant_renderings.visible_terms`. A required alias change returns to Logic.
- A KPI label, display value, and unit use three `copy_id` values. Art Direction maps them to different child targets in one composite container; Output implements them.
- Speaker notes stay outside `copy_units` and never appear on the slide.
