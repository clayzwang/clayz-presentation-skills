# Four-Layer Interaction Failure Patterns

For every pattern, assign primary responsibility to the first artifact that introduced the drift and record separately which downstream gate should have caught it.

## Content and narrative failures

### Design starts before content is ready

Symptoms: the copy still oscillates between a methodology and concrete content; aggregates such as “next N months,” total, average, or portfolio lack period/item detail; Art Direction fills gaps with boxes, arrows, or false whitespace.

Regression: expand to the smallest evidence set that could change the conclusion, relation, decision, or expression, then compress. Unready content does not enter design. When decisive facts are missing, Supervisor consolidates the minimum questions once and returns control.

### Natural question chain is broken

Symptoms: fact → explanation → choice, or dilemma → objective → path, is split into isolated template slides that require the presenter to supply the logic.

Regression: each slide answers the audience's next natural question. A split needs its own conclusion, necessary evidence, and real transition.

### Declaration precedes dilemma

Symptoms: a management request announces a direction before establishing necessity, success criteria, and option trade-offs.

Regression: assertion strength cannot exceed evidence or authorization. Establish the dilemma before the choice.

### Logic relation is underspecified

Symptoms: Copy or Art Direction must guess whether items are peers, joint conditions, sequence, or cause.

Regression: encode joint gates explicitly as conjunctive conditions; use `sequence` only for real time or state change.

### Copy relation drifts

Symptoms: Logic says “A and B must both hold,” while Copy says “first A, then B,” or numbering creates order among equal peers.

Regression: compare title, storyline, and body implications against `semantic_relations` slide by slide.

### Cross-slide invariants drift

Symptoms: audience segment, product, stage, data-entity order, metric definition, or analytical axis changes silently, destroying comparison.

Regression: lock `cross_slide_contract`, inherit it exactly at every layer, and inspect slides side by side.

## Art Direction and interface failures

### Punctuation-dependent layout and related-data cardification

Symptoms: hierarchy exists only through repeated “label: content”; target, forecast, gap, baseline, increment, or phased data are split into unequal light boxes.

Regression: make visual grammar replace punctuation. Encode related data in one chart or table and place the conclusion adjacent to it.

### Art Direction reinterprets the business

Symptoms: arrows, stage axes, quadrants, or area weights change an otherwise correct relation or emphasize a secondary conclusion for novelty.

Regression: every backbone, region responsibility, connector, and first visual cites the related Logic node or `copy_id`.

### Art Direction contradicts itself

Symptoms: `dominant_medium=table` without a `table-cell`; first visual says “primary number” while imagery receives the largest area; selected A/B candidate differs from the locked composition.

Regression: verify dominant medium, first visual, area plan, target types, object requirements, and A/B result as one machine-checkable constraint set.

### Atomization pressure

Symptoms: `render_separately` becomes “one card per copy unit.”

Regression: atomic copy preserves meaning and traceability but does not prescribe a rectangle. Compound media can contain independently traceable atoms.

### Meaningful isomorphism is broken

Symptoms: a quarterly accumulation, stable map order, policy series, or continuous drill-down has locked persistence, yet Art Direction or Output moves objects, changes the backbone, or reorders entities merely to make each slide different.

Regression: one `series_id` uses a shared production baseline and changes only `progressive_change`. Inspect early, middle, and late series slides together.

### Meaningless isomorphism is rationalized

Symptoms: ordinary slides repeat one three-column shell, card array, or bottom conclusion band under the claim of brand consistency.

Regression: only a Logic series contract authorizes highly similar backbones. Otherwise prove the tasks are truly the same or break the repetition.

### Semantic whitespace is mishandled

Symptoms: future space is filled with explanation; a leadership transition becomes a complete information slide; or content collapsed into a corner is called intentional whitespace.

Regression: every whitespace region needs a type, location, and narrative responsibility. Resolve nonsemantic emptiness through `area_plan`.

### Motif or navigation becomes UI

Symptoms: a motif becomes decoration on every slide; persistent navigation becomes buttons, tabs, or a large color block that competes with evidence.

Regression: define motif establishment, progression, and break. Navigation is subordinate orientation, stays within planned area, and carries no primary content.

### Attention hierarchy is wrong

Symptoms: the plan allocates a large region to weak explanation, gives rejection and recommendation equal weight, or leaves the effective intersection as an unlabeled strip.

Regression: audit semantic load per region, not area percentages alone. Primary conclusion, recommended path, and effective intersection need stronger area, hierarchy, or medium.

## Output and QA failures

### Output silently redesigns

Symptoms: Output replaces a locked first visual, partition, medium, rhythm, series persistence, motif, or whitespace because another slide type is easier or fits better.

Regression: any change to an Art Direction baseline becomes a challenge. Produce a new plan only after user adjudication, then compare the render against it.

### Build collapses into cards

Symptoms: tables, timelines, swimlanes, and matrices all become two or three columns of equal light boxes.

Regression: compare first visual, PPTX object types, rendered medium, and cross-slide silhouette together.

### Art Direction rhythm is flattened

Symptoms: all required objects exist, but repeated outer frames, bottom bands, and column ratios erase the planned variation in openness, density, and medium.

Regression: compare final thumbnails against `deck_rhythm` slide by slide.

### QA false pass

Symptoms: correct text and object presence are treated as proof that first visual, area, rhythm, and medium are faithful.

Regression: QA separately answers: what Art Direction required, what objects exist, what the render communicates, and whether a deviation is approved.

### Font shrinking hides capacity problems

Symptoms: body, axis, legend, data labels, entity labels, or notes fall below the configured audience minimum, or scattered odd/fractional sizes are introduced solely to fit.

Regression: record the minimum audience type size and every token violation. First enlarge the primary chart, reduce nonessential ticks, facet, split, or return to Copy.

### Scatter semantics and recognition are distorted

Symptoms: independent entities are connected by input order; names are missing, overlapping, or too small and require legend/number/color lookup.

Regression: markers and direct labels are the default. Keep only contract-defined, visibly labeled target, threshold, fit, iso-value, or same-entity time-path lines. Use offsets, label leaders, facets, or slide splits for crowding.

### Target-application compatibility drifts

Symptoms: the production render is healthy, but a configured target application shows a blank cover/closing slide, missing-font warning, missing object, or different wrapping.

Regression: target-application open evidence outranks production rendering. Verify actual font identity, layout dependencies, and placeholder dependencies. Add a slide-layer fallback only when a probe proves it necessary and it does not duplicate the master.

### Text objects exist but rendered glyphs are missing

Symptoms: final XML contains the complete text, while a final-reopen render shows only shapes, Latin text, or numbers. Typical causes include an unregistered font, fallback to a Latin-only face, a subset without needed glyphs, or QA using an in-memory pre-export render.

Regression: font preflight proves identity, required glyph coverage, and renderer-process resolution. Reopen the written PPTX and run per-slide glyph-pixel probes. XML presence or success on another machine is not sufficient.

### Inherited chrome is duplicated

Symptoms: Output clears a source body slide and redraws title lines or page numbers on the slide layer while inherited objects remain, producing double dividers or both static and dynamic page numbers.

Regression: remove only permitted sample blocks by stable source IDs. Validate uniqueness, not mere presence, for dynamic fields, page-number candidates, and configured title dividers; inspect the rendered positions and silhouette.

### Supervisor overreaches or repeatedly escalates

Symptoms: advice to pause becomes a veto, perfectionism repeatedly exits the process, or the same conflict is asked again without new evidence.

Regression: Supervisor diagnoses, consolidates, recommends, and returns control. Escalate the same conflict once unless new evidence appears. If the user proceeds, record risk and reversible assumptions.

## Responsibility method

1. Locate the first artifact where the issue appears.
2. Identify which downstream gate should have detected it.
3. Assign primary responsibility to the layer that introduced the drift and release responsibility separately.
4. Use percentages only with a sufficient cross-slide sample; otherwise use qualitative attribution.

Supervision improves interfaces, learning, and execution; it does not rank skills. Asset feedback may be recorded with evidence, but frequency is not quality, local task scores are not global parameters, and generated output does not automatically become a reference.
