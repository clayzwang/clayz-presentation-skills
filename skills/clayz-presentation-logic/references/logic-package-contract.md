# Logic package 3.1

New runs follow [Story and visual handoff](../../../packages/contracts/story-visual-handoff.md).
Logic writes the complete story, thesis, chapters, page claims and page allocation.
Copy decides exact wording, trimming and content grouping within those locked pages.
Art Direction owns visual composition; Output implements the native presentation.

The root retains `package_id`, `version`, `status`, `origin_namespace`, `brief`,
`acceptance_contract`, `resource_inventory`, `index_evidence`, `approvals` and
`configuration_sha256`. Use `contract_version: "3.1"`. Preserve actual source,
resource, configuration, calibration and work-record bindings.
`copy_layer` is null at `logic-approved`.

`story` is the full unabridged narrative, with title, thesis, audience,
desired_outcome, opening, conclusion, ordered chapters and substantive blocks.
Each chapter has chapter_id, title, purpose and blocks. A transition is optional.
Each block has story_id, text, claim_status, source_ids, qualifiers and
must_preserve. Sources bind source_id, resource_id and locator; retain provenance
and evidence limits. glossary, metric_dictionary, open_items and invariants are
arrays, empty when inapplicable. Facts and calculations need source evidence.

`logic_layer.slides` is the ordered page allocation. Each page contains:

- `slide_id`, `chapter_id` (null for bookends when appropriate), `narrative_role`;
- `claim`: complete substantive page claim, not final visible wording;
- `source_story_ids`: nonempty references allocating the story to this page;
- `data`: an array of supported quantitative records, empty when inapplicable.

All story blocks must be allocated, including material Copy may later trim.
Preserve the full story; do not shorten it to fit slides. Logic determines the
body-page count from the task. Unless explicitly omitted, include one opening
cover and one closing page, separate from the body count. Lock pagination with
`logic_layer.lock.slide_order_locked: true`. Other task-specific semantic metadata
may be supplied when useful; it is not a mandatory analytical template.

Data retains data_id, metric_name, display_value, raw_value (null if missing),
unit, period, definition_ref, source_ids and evidence_status. Keep definitions,
calculations and uncertainty inspectable. Optional relationships describe actual
meaning; they do not impose a node tree, analytical sequence or grouping quota.
Each independently handed-off content unit must carry enough context for Copy.

Copy preserves story and logic_layer exactly, binds the original Logic file via
logic_artifact, and writes copy_layer. Changes to page count, order, responsibilities,
claims or evidence return to Logic; routine wording and grouping remain Copy's work.
Do not proactively generate speaker notes or appendices. Existing/requested notes
remain readable. Research working records are distinct from PPT speaker notes.

The validators retain isolated replay support for historical 2.4 and 3.0 artifacts.
Their old node/reasoning schemas do not govern new 3.1 work. Never relabel an old
artifact without creating and validating a genuine revised handoff.
