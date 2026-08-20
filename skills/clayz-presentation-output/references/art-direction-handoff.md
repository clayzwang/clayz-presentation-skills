# Art Direction Handoff Contract

Output accepts only `ppt-art-direction-plan.json` contract 1.3 with status `art-direction-approved`.

## Baseline fields that require adjudication before change

- Deck-wide: visual thesis, material route, first impression, silhouette, density, dominant-medium and motif sequences, series groups, and semantic-whitespace slides.
- Per slide: first visual, composition rationale, region responsibilities, area ratios, main backbone, silhouette, dominant medium, density, and reading path.
- Interfaces: `copy_id` mapping, parent/child targets, semantic layout tree, style tokens, medium-object requirements, semantic axes, recognition criteria, type minimums and parity policy, chart-label and line semantics, series behavior, persistent elements, progressive change, allowed variation, semantic whitespace, and persistent navigation.
- A/B: selected candidate, rejected candidate, and rejection reason.
- References: each case's intended use and non-copy boundary.

## Output may decide

- exact `x/y/w/h` inside an approved 12-column region;
- spacing, padding, line weight, and object layer order inside the locked composition;
- connector routing, image crop, and table column widths;
- native-chart compatibility masks and repairs for differences among target applications named by central configuration;
- optical alignment that does not change area or weight;
- absolute, relative, or hybrid coordinates inside a locked region. Relative layout may absorb line wrapping and peer-module count changes, but not alter the fixed frame, region responsibility, area weight, reading order, or semantic whitespace;
- a recognizable object hierarchy, parent/child grouping, reading order, and shape semantics that implement `semantic_layout_tree`. The tree does not replace `area_plan` geometry or `copy_unit_map` text and target truth, and must not be flattened into shallow peer boxes for implementation convenience; and
- exact reuse of locked persistent-element coordinates, sizes, styles, and layers inside one series contract. Do not extend that reuse to slides outside the series.

## Backflow

- To change medium, silhouette, main backbone, region, reading path, series backbone, motif, semantic whitespace, or persistent navigation: return to Art Direction.
- To delete, rewrite, or re-break copy: return to Copy.
- To change a relationship, hierarchy, number, or slide order: return to Logic.
- If upstream baselines cannot all be satisfied: stop production, record the conflict, evidence, expected drift, and feasible alternatives, then send it to Supervisor for synthesis and user adjudication.

Record every deviation in `ppt-build-deviation-log.json`. If `changes_art_direction=true`, a new Art Direction version and the user's approval basis are both required. The log cannot approve itself. A challenge does not alter the baseline; only the adjudicated new version does.
