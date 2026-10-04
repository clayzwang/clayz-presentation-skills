# PPT v3.3 Copy-layer contract

New tasks on v0.18.0 use the [research and visual handoff](../../../packages/contracts/story-visual-handoff.md).
Copy organizes and rewrites the full Logic story while preserving its meaning.

`copy_layer` binds `logic_version`, `pagination_owner:"copy"`,
`research_sha256`, `semantic_preservation_review` and ordered `slides`.
A slide has `slide_id` and `copy_units`. Optional chapter labels,
`narrative_role`, `data_ids` or requested historical notes describe content,
not its presentation. There is no duplicate Logic page projection.

Each visible unit is:

```json
{"copy_id":"S01-H3","role":"heading","heading_level":3,"text":"A heading at the level this story needs"}
```

The roles are `title` (main Storyline), `subtitle` (secondary Storyline),
`heading` (positive heading_level), `body` and `annotation`.
Every category is optional; levels may be skipped and no title, subordinate
heading or body pairing is required. Text may contain natural paragraph breaks.
Units have no visual flags, grouping graph, reading-order number or media request.

Keep provenance separately at root: `copy_provenance` maps each visible
`copy_id` to its source finding IDs. It does not constrain Art's composition.
Bind the original immutable approved Logic file as `logic_artifact`; retain
research, task identity, acceptance and configuration/run bindings.

Art may merge text into shared objects, choose different styles for equal
textual levels, or change visual reading order while preserving meaning.
Only actual text, meaning, coverage and explicit user requirements remain binding.
Historical 3.2 and earlier artifacts retain their versioned replay validation.
