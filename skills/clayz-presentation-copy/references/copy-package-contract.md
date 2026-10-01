# PPT v3.1 Copy-layer contract

Follow [Story and page handoff](../../../packages/contracts/story-visual-handoff.md).
Logic supplies the complete story and locked page allocation. Copy owns exact
wording, trimming, content grouping and tags; Art Direction adds visual tags and
Output implements them.

Preserve root identity, version, configuration, acceptance_contract,
resource_inventory, story and logic_layer; bind the actual logic_artifact.
Retain calibration and retrieval receipts. copy_layer.logic_version equals the
root version; pagination_owner is logic; story_sha256 binds the full story and
chapter_order is unchanged. Record actual number, qualifier and meaning review
in semantic_preservation_review.

Each page slide_id matches Logic order. Each copy_unit has copy_id, text, role,
text_mode, source_story_ids, parent_copy_id, sibling_group_id, logic_level, order,
render_separately, merge_with_children and intentional_line_breaks. copy_id is
unique across the deck. Story references stay within the allocated page. Parents
resolve on the page without cycles; null parent/group tags are valid. logic_level
describes Copy's own hierarchy, without a required Logic node correspondence.

render_separately is true and merge_with_children is false: each copy_id remains
independently traceable, without requiring separate text boxes or cards. order is
contiguous from 1. intentional_line_breaks stores valid character positions;
Copy controls wording and breaks. title_copy_id, optional storyline_copy_id and
footnote_copy_ids reference visible units. Necessary explanation can be a whole
sentence or paragraph; no parallel-grammar rule applies.

Old source_logic_node_ids and node_copy_map are not new-run requirements. Copy
may build its own message tree; Art consumes Copy hierarchy and grouping tags.
Page count/order/responsibility, claims or evidence changes return to Logic.
Copy revises wording/groups and refreshes downstream bindings. Do not proactively
generate speaker notes or appendices; historical or explicitly requested notes
remain readable and traceable. Historical 2.4 and 3.0 packages retain their own
replay validators.
