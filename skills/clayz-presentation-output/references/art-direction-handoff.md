# Art Direction handoff — v0.19.0

Read [content relationships and page planning](../../../packages/contracts/page-planning.md) for required semantic Copy relationships, recorded Art planning before object specifications, and planning-to-render audit.


New tasks use [research and visual handoff](../../../packages/contracts/story-visual-handoff.md),
package 3.4 and approved Art plan 2.3. Read both the complete image drafts and
matching specifications before implementing editable objects.

Implement Art's coordinates, type, hierarchy, grouping, media and reading paths.
copy_unit_map binds each visible ID to a native location. Shared targets with
disjoint text_range bindings are valid, including heading and body in one
editable text box or several units in one native cell. Equal textual levels
need not have the same style. Do not reconstruct a Copy parent/sibling tree,
derive separate targets from Copy IDs, or bind Copy's array order to visual order.

Art defines editing boundaries. Every baseline element has a unique native_name
and render_separately:true, with optional native_group_path (outermost first).
Create each declared object independently and preserve its exact grouping and
native type. A group keeps separate editable children while permitting joint
movement. Several Copy units may share an explicitly declared single object.
Do not merge, split, regroup or flatten Art's objects for convenience. Return
boundary changes to Art; character-range coverage cannot replace native-object
fidelity. Final PPTX comparison and QA inspect the actual named objects/groups.

Preserve exact content and actual business relationships. Re-pagination or
wording changes return to Copy; research changes return to Logic; design changes
return to Art through the existing Supervisor calibration. Technical adjustment
within Art's declared bounds uses the existing deviation log. Supervisor does
not take over the design or add aesthetic approval gates.

No registered layout or pattern is required. Optional external tools supplied
by Art remain task tools, not global design restrictions. Keep native charts,
integrated tables, font naming, editable objects and real reopen/render
coverage under the existing production-reliability contract.
