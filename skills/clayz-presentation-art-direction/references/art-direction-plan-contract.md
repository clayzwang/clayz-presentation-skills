# Art Direction plan 2.2

For new tasks use [research and visual handoff](../../../packages/contracts/story-visual-handoff.md).
Validate with validate_art_direction_plan.py. Older contracts remain for replay.

Bind contract_version:"2.2", package_contract_version:"3.3", package_id,
package_version, status:"art-direction-approved", acceptance_contract,
resource_inventory_lock, communication_contract and the task index_evidence.
The global art_direction.approval retains status and approved_by.

reference_research records learning_package_available, source_strategy,
notes and optional references (source, locator, use). Learning is preferred
when available; web references and original design remain open. No built-in
Art design index or mandatory match exists.

slides preserves Copy's page sequence. Each page includes slide_id,
reading_sequence (all visible Copy IDs once, in Art's chosen order),
copy_unit_map and medium_execution_contract. The structure_type is a free
description; minimum_object_counts describes actual native objects.
Other design fields are chosen as useful for implementing this particular
design. No atomicity_review, parent target or sibling-style assertions apply.

A mapping is, for example:

```json
{"copy_id":"S01-P2","render_target_id":"TEXT-1","target_type":"shape","native_location":{"shape_name":"ART::TEXT-1","text_range":[17,35]}}
```

Several mappings may share the same target and native location, using disjoint
text ranges. Table cells additionally use zero-based row/column. Native chart
labels use shape_name, label_kind (title, series-name, category, value or
data-label), and series_index/point_index when needed. Bind the target to the
visual_baseline element_id and its copy_ids. Styling and reading order do not
derive mechanically from Copy's textual levels or array positions.

Lock readable full-deck images and matching visual_baseline specifications
before Output. The baseline carries actual coordinates, typography,
native types, copy/data/asset bindings and bounded technical adjustments.
Use stage_documents.py lock-design. Keep final PPTX production in Output.

Each visual_baseline element declares one native editing object with unique
native_name and render_separately:true. Its mapping shape_name equals native_name.
Several Copy IDs can belong to that single object. Independent editing needs
determine boundaries; use native groups to move distinct editable children
together. Optional native_group_path lists group names outermost first; omission
means ungrouped. Output must retain the named objects, their native types and
exact group paths, without merging, splitting, regrouping or flattening them.
These are Art object requirements, never Copy paragraph requirements.
Plan 2.1 remains supported for historical replay without the new fields.
