# Medium and Art Direction Fidelity Rules

## Six evidence segments are not interchangeable

1. **Art Direction**: locked first visual, zones, medium, density, reading path, and deck rhythm.
2. **Build deviation**: technical adjustment, whether it changes Art Direction, and who approved it.
3. **Objects**: actual PPTX objects.
4. **Render**: what the audience can recognize.
5. **QA**: whether Output accurately reconciles the first four.
6. **Target software**: whether configured presentation applications preserve the same fonts, covers, objects, and wrapping.

A plan saying “timeline” does not prove the render contains a recognizable timeline. One line object does not prove phase progression. A deviation log claiming no plan change and a checked QA box cannot override render evidence.

Also detect faithful execution of a bad plan. If design starts before content is ready, breaks the natural question chain, relies on punctuation, cardifies related data, or allocates large area to a weak statement, attribute the issue to the earliest Logic, Copy, or Art Direction artifact even when objects, render, and QA all agree.

A production-side render does not prove target compatibility. When any configured target application shows a blank cover/closing slide, missing-font warning, missing object, or wrapping drift, stronger target evidence overrides the production render. Inspect actual font display names, layout dependencies, and placeholder dependencies.

## First visual, area, and rhythm

- **First visual**: observe the thumbnail for 1–3 seconds. If a planned primary number, axis, image, or relation backbone is displaced by borders, equal cards, or large decoration, use `ART_DIRECTION_FIRST_VISUAL_DRIFT`.
- **Attention hierarchy**: derive the expected order from title promise, Logic decision weight, and Copy evidence; separately record the observed order. A bad plan yields `ART_DIRECTION_ATTENTION_HIERARCHY_MISMATCH`; faithful-plan drift yields `ART_DIRECTION_FIRST_VISUAL_DRIFT`. Saliency and automated attention are diagnostic only.
- **Area plan**: compare region responsibility, 12-column range, area ordering, and whitespace. If a key region is compressed or support dominates, use `ART_DIRECTION_AREA_PLAN_DRIFT`.
- **Semantic load**: compare each region's area with its information responsibility. Large weak regions, equal rejection/recommendation areas, or an unlabeled effective intersection yield `ART_DIRECTION_LOW_SEMANTIC_AREA`, even when percentages match.
- **Deck rhythm**: compare consecutive thumbnails for silhouette, dominant medium, density, and color-mass sequence. One repeated shell yields `ART_DIRECTION_RHYTHM_DRIFT`.
- **Purposeful series**: compare persistent elements and new focus for the same Logic `series_id`. Broken backbone, positional drift, or weak new focus yields `PURPOSEFUL_SERIES_BROKEN`.
- **Unjustified repetition**: consecutive non-series pages with one card/column/bottom-band shell yield `UNJUSTIFIED_SILHOUETTE_REPETITION`.
- **Cross-slide invariants**: any drift in name, order, definition, analytical axis, or grouping yields `CROSS_SLIDE_INVARIANT_DRIFT`.
- **Semantic whitespace**: filled `future-space`, `unknown-space`, or `pause` yields `SEMANTIC_WHITESPACE_FILLED`; ordinary imbalance labeled semantic yields `ART_DIRECTION_FALSE_SEMANTIC_WHITESPACE`.
- **Motif**: missing establishment, progression, or planned break yields `MOTIF_SEQUENCE_DRIFT`.
- **Persistent navigation**: UI-like navigation, excessive area, wrong order, or incorrect current marker yields `CONTEXT_RAIL_UI_DRIFT`.
- **Authorization**: Output cannot self-approve these changes as compatibility or fit fixes; without renewed Art Direction approval also report `BUILD_UNAPPROVED_DEVIATION`.

## Medium criteria

### Table

- Plan: `dominant_medium=table` and at least one atomic-copy target is `table-cell`.
- Object: prefer native `a:tbl`; a shape-based editable substitute for complex merged cells requires an approved exception and evidence of a clear grid, headers, and cell semantics.
- Render: the audience recognizes rows, columns, headers, and cross-reading, not independent cards.

Without `table-cell`, a native table, or an approved substitute, aligned shapes are not a table.

### Data chart

- Plan: `dominant_medium=data-chart` with explicit source, encoding, labels, and annotation mapping.
- Object: native chart or explicitly approved editable-vector substitute.
- Render: numeric comparison or trend is the first visual, not a small chart beside dominant cards.
- Legibility: axis, legend, data-label, entity-label, and annotation text meets the configured minimum. Object presence does not replace full-size reading inspection.

### Scatterplot

- Independent entities show markers only by default and are not connected by row, rank, or name order.
- Every point directly displays a readable entity name. Missing, overlapping, or undersized labels yield `SCATTER_ENTITY_LABEL_MISSING_OR_UNREADABLE`.
- Label leaders are short, fine, and connect labels to their own points; they are not entity relations.
- Target, 100-percent, median, statistical-fit, iso-value, and same-entity time-path lines must map to `data_chart_contract.semantic_lines` and have visible labels.
- Any unlabeled connection between different entities yields `SCATTER_UNJUSTIFIED_POINT_CONNECTIONS`, however thin or muted it is.

### Timeline

- Plan: explicit phases, order, milestones, information layers, and time progression as first visual.
- Object: continuous axis, nodes, phase divisions, and necessary direction evidence.
- Render: progression is recognizable at thumbnail size; dates/phases, actions, and deliverables separate at full size.

A horizontal line plus four equal light boxes that overpower the axis fails timeline recognizability.

### Swimlane

The plan defines a role/responsibility dimension and a phase/process dimension; objects create row/column zones or intersections; the render answers who does what at which stage. Three role cards are not a swimlane.

### Matrix

The plan defines two independent dimensions and their intersection; objects provide axes, quadrants, or row/column intersections; position encodes both. An unlabeled 2×2 card grid is not a matrix.

### Relationship or process diagram

`peer` relations use no directional connector. `sequence`, `condition`, `cause`, and `feedback` preserve direction or loops. Joint conditions must not become an unapproved sequence.

## Type-size legibility

- Continue to review core body copy against the 18-point baseline. Audience detail, chart text, and entity labels must meet central configuration with no hidden exceptions.
- Follow the configured point-size token/parity policy except for explicitly declared non-audience technical fields. Trace any violation to Art Direction capacity planning or Output shrinkage.
- Inspect both object properties and full-size renders. A nominally compliant property that is unreadable because of scaling, contrast, or obstruction still fails; a seemingly readable render below the minimum also fails.

## Atomic copy and visual grammar

`render_separately=true` means independently traceable, validated, and hierarchical copy; it does not require a separate rectangle. Copy atoms may occupy different cells of one table, layers of one timeline node, swimlane headers and intersections, chart labels and annotations, nested region labels and evidence, or child objects in one group.

If every body atom becomes a similarly filled, bordered, rounded, equal-area `shape`, inspect `COPY_ATOMIZATION_PRESSURE` and `BUILD_STRUCTURE_COLLAPSED_TO_CARDS`.

Repeated “label: content” groups that lose hierarchy when punctuation is removed yield `PUNCTUATION_DEPENDENT_LAYOUT`. One calculation chain split into light number boxes yields `RELATED_DATA_CARDIFICATION`, even if native objects exist.

## Cardification criteria

Cards are problematic only when they:

- become the first recognizable medium although the plan specifies another medium;
- flatten parent/child, stage, row/column, cause, condition, or responsibility-crossing relations;
- repeat across slides with only count or order changes; or
- make root judgment, primary method, or data evidence lose its anchor through equal weight.

Record both whether cardification occurred and which semantics it destroyed.

## Boundaries of automated visual signals

- PPTX objects, coordinates, type sizes, and final pixels are factual evidence. Image-layout detection supplements only PDFs, scans, or image-only sources without native object facts.
- CLIP or similar similarity retrieves comparable pages; it neither proves quality nor promotes a case to a positive reference.
- Attention models compare expected and observed attention. Visibility is not deserved importance or aesthetic quality.
- Automated scores retain dimensional evidence and uncertainty. One aggregate score never overrides contracts, facts, renders, or professional judgment.
- Supervisor uses such signals only for diagnosis and attribution, never to generate a replacement composition or choose A/B for Art Direction.

## Cross-slide review

Review a series with at least the previous, current, and next slides visible:

1. compare Logic invariants and Art Direction persistence;
2. inspect object position, scale, order, labels, and definitions;
3. name the current slide's only new information;
4. confirm new information gains focus while old information remains stable background; and
5. confirm the exit slide breaks the backbone only as planned.

Review non-series repetition side by side as well. A slide that passes alone can still fail across the deck.
