# Reference-Cluster Discovery

Reference clusters help Art Direction discover structural alternatives without importing a template. The workflow is informed by the retrieval-and-layout decomposition described in [PPTAgent](https://github.com/icip-cas/PPTAgent). That source supports retrieval and structural discovery only; all admission, licensing, content, and visual decisions remain governed by this package.

## When to use it

Use cluster discovery when:

- no admitted record clearly matches the slide archetype;
- two plausible structural families need A/B comparison;
- a multi-slide series needs evidence about stable and changing elements; or
- the current plan repeatedly falls back to one silhouette.

## Discovery process

1. Query admitted metadata first: communication setting, material type, slide archetype, management stage, dominant medium, density, and sequence behavior.
2. Load only the smallest useful cluster within `reference_budget`.
3. Extract structural signals: approximate capacity, grouping, dominant-medium placement, reading path, and cross-slide invariants.
4. Translate those signals into local `area_plan` and semantic-layout-tree candidates. Do not copy source text, branding, or object styling.
5. Record query terms, loaded IDs, adopted signals, rejected signals, and the final human judgment.

Capacity and medium hints are soft signals. They never authorize a Copy change. If the conflict cannot be resolved inside the same composition, create a real A/B pair; if both fail, challenge Copy or Art Direction through the recorded backflow path.

## What must not be absorbed

- source masters, layouts, fonts, colors, or object styles;
- source copy or confidential data;
- cluster frequency as evidence of quality;
- parser heuristics as fixed thresholds; or
- any record that bypasses licensing, sensitivity checks, and human admission.

## Parsing boundaries

For native PPTX, inspect the editable object tree. For PDFs, distinguish text/vector pages from scans and apply OCR only when needed. Layout parsers may propose boxes, types, and reading order; they do not determine quality, importance, or approval. Preserve provenance and treat every automated extraction as a candidate observation.
