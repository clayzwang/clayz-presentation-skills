# Art Direction handoff — v0.18.0

New tasks use [research and visual handoff](../../../packages/contracts/story-visual-handoff.md),
package 3.3 and approved Art plan 2.1. Read both the complete image drafts and
matching specifications before implementing editable objects.

Implement Art's coordinates, type, hierarchy, grouping, media and reading paths.
copy_unit_map binds each visible ID to a native location. Shared targets with
disjoint text_range bindings are valid, including heading and body in one
editable text box or several units in one native cell. Equal textual levels
need not have the same style. Do not reconstruct a Copy parent/sibling tree,
require separate targets, or bind Copy's array order to visual order.

Preserve exact content and actual business relationships. Re-pagination or
wording changes return to Copy; research changes return to Logic; design changes
return to Art through the existing Supervisor calibration. Technical adjustment
within Art's declared bounds uses the existing deviation log. Supervisor does
not take over the design or add aesthetic approval gates.

No registered layout or pattern is required. Optional external tools supplied
by Art remain task tools, not global design restrictions. Keep native charts,
integrated tables, font naming, editable objects and real reopen/render
coverage under the existing production-reliability contract.
