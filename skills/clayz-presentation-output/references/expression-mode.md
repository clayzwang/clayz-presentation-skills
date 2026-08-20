# Expression Modes: Charts, Shapes, Tables, Icons, and Images

## 1. Assign a visual responsibility first

Every visual element must serve one or more responsibilities:

1. **Evidence**: show a value, difference, structure, or trend accurately.
2. **Relationship**: show how objects are parallel, contained, sequenced, influential, or in feedback.
3. **Context**: establish people, place, product, time, or a real setting.
4. **Emphasis**: make the script package's priority conclusion appear first.
5. **Memory**: leave a repeatable impression through an apt metaphor or consistent image.

Delete decorative lines, boxes, icons, images, or shadows that have no responsibility.

Visual grammar also replaces punctuation: area and type size express hierarchy; nesting and spacing express ownership; alignment expresses peers; arrows express direction; shared destinations express convergence; charts and tables express data relations. If removing colons, semicolons, brackets, and numbering makes the relation disappear, the visual grammar is not doing its job.

## 2. Shapes and connectors

### Shape semantics

- Rectangle: stable information region, step, role, or module.
- Circle: core, node, set, cycle, or whole without a start/end.
- Ring: layer, cycle, proportion, or orbit around a core.
- Container or light surface: ownership and grouping.
- Line: separation, alignment, scale, or weak relation.
- Arrow: real direction, flow, causality, or influence.
- Bracket or brace: several items share one parent concept.
- Dashed line: assumption, indirect relation, future state, or weak boundary; always label it.

### Production rules

- Prefer square or mildly rounded corners. Keep corner radius, border, and padding consistent among peers.
- Create connectors before nodes so lines sit below nodes.
- Lines may not cross nodes, text, or slide numbers. Use orthogonal routing or split complex relations.
- Do not place paragraphs inside large arrows; arrows carry direction and text remains in readable regions.
- Match shape area to content weight. Shrink a large block holding two short words or turn it into a label.
- Light boxes represent real boundaries or groups, not content length. Four consecutive light boxes without distinct semantic responsibilities should become a chart, table, nesting, or open layout.
- Do not randomly add shadows, outlines, or colors to peer objects.
- Do not turn every `page_message_tree` node into an equal rounded card. Express parent/child relations through nesting, indentation, braces, alignment, table columns, and fine grouping lines.

## 3. Charts

### Selection order

Choose the comparison before the chart: category comparison → bar; time trend → line; composition → stacked; contribution bridge → waterfall; distribution → histogram/box; correlation → scatter; two-dimensional position → matrix/bubble; precise multi-field comparison → table.

### Visual rules

- One primary chart per slide, with at most one or two supporting indicators when needed.
- Use one accent for the key series or point; recede other series to grayscale.
- Directly label key values and conclusion ranges; reduce legends and gridlines.
- Include axes, units, period, sample, definition, and source.
- Follow display values in the content package for decimals, percent, and percentage points.
- No 3D, exploded or volumetric pies, glow, gradient bars, or decorative icons as data marks.
- Truncated axes, log axes, and dual axes require explicit necessity and visible disclosure.
- Encoded area, angle, and length must remain proportional to data.
- Axis, legend, data-label, entity-label, and annotation text must meet the configured chart-text minimum. When crowded, enlarge the plot, remove nonessential ticks, facet, or split the slide.

### Scatterplots

- Different entities are independent observations; show markers only by default and never connect by input order.
- Directly label every point with its entity name. Do not require a legend, color, number, or appendix lookup.
- Resolve collisions in order with offsets, label-to-point leaders, a larger plot area, facets, or a split slide. A leader connects a label to its own point and does not express an entity relation.
- Only analytically meaningful lines may remain: target, 100-percent, median, statistical fit, iso-value, or a time path for one entity. Give every line a visible explanation.
- A fit line must serve a correlation or explanatory task. Do not add it for completeness. Connecting lines, smoothing, and area fills across independent entities are off by default.

### Data integrity

Build charts from script-package data fields or source data, never by eyeballing screenshots. Every locked display value must be findable in the final deck; if the axis does not show each one, preserve it in a data label, table, or note.

## 4. Tables and key numbers

### Tables

- Use tables for multiple objects, fields, and exact values; remove columns irrelevant to the slide conclusion.
- Make headers, units, period, totals, missing values, and notes clear.
- Align numbers by decimal or digit width and text to the left. Do not mix year-over-year, period-over-period, and attainment in one column.
- Emphasize a key row or column in one way only: accent text, light fill, fine rule, or bold.
- Management detail may be dense, but never paste an Excel screenshot or shrink a table into an unreadable image.

### Key numbers

- A large number needs a metric name, unit, period, and comparison baseline.
- Visual area follows importance, not number of digits.
- Do not create an equal-weight KPI card wall; arrange supporting metrics around primary evidence.
- Target, forecast, gap, baseline, increment, and phased values from one calculation chain belong in one chart or table with direct conclusion labels.
- Preserve signs, brackets, percent symbols, and decimal places exactly from the content package.

## 5. Icons

- Icons identify one object, action, role, or category; they do not replace complex conclusions.
- Build a deck-wide `icon-demand-list`. When nonempty, query the central reference registry by recognition purpose → object semantics → icon family. Use only human-admitted assets with traceable source, version, and license. If unavailable, record why and prefer no icon or a simple editable shape.
- Select one primary family for the deck's semantic coverage. Do not mix line, filled, 3D, skeuomorphic, and cartoon styles or incompatible radii, endpoints, perspective, and line weights.
- Use another traceable source only when the shared family has no semantically suitable asset. Prefer extending the same family and record family, stable asset ID, name, version, license, and source.
- Use no more than small, medium, and large sizes; keep visual line weight, color, container, and outside whitespace consistent.
- Peer icons on one slide use the same size, color, and position. Process icons must map to real actions.
- If no icon is accurate, omit it rather than use a misleading approximation.
- Do not generate ordinary icons as raster images. Brand logos identify that brand only.
- Store SVG locally and ensure the final PPTX does not depend on online URLs.

## 6. Photos and illustrations

### Photos

- Use photos for real people, places, products, events, and case evidence; prefer official or traceable sources.
- Avoid generic handshakes, conference tables, and false-smile business stock imagery.
- Define composition and crop before image search. Preserve aspect ratio and never stretch.
- Direct gaze, action, and visual momentum toward the content where practical; do not crop critical subjects.
- Crop screenshots to the part supporting the conclusion and state the conclusion beside it. Keep core tables and text editable.

### Original illustrations

- Use for abstract mechanisms, unified covers, section transitions, user contexts, and conceptual metaphors.
- Before image generation, specify responsibility, subject, setting, composition, negative-space direction, palette, style, and aspect ratio.
- Use only the central theme palette. Include no text, logo, or watermark, and reserve explicit negative space for content.
- Across slides, keep character, viewpoint, line language, lighting, and palette consistent. Inspect hands, faces, object structure, garbled text, and crop.
- Do not generate fake screenshots, product images, logos, data evidence, or fabricated photos of real people.

## 7. Emphasis and reading order

### First visual

The first visual must agree with the title proposition. Establish focus primarily through position, type size, contrast, and whitespace; color is secondary. When the script package has no priority, do not arbitrarily emphasize the first or last peer.

### Color

- `theme.colors.accent`: key conclusion, number, action, and current section.
- `theme.colors.text`: title, structure, and primary content.
- `theme.colors.accent_soft` and `surface`: supporting regions and groups.
- `theme.colors.muted` and `grid`: secondary information and weak lines.
- `theme.colors.background`: primary background.

A color keeps one meaning throughout the deck. Positive, warning, risk, and negative gap may not rely on added red/yellow/green alone; combine color with text, symbol, line style, or position.

### Borders and shadows

- If alignment, spacing, and a light surface can group content, do not add a border.
- Borders express boundary strength; shadows express depth. Do not make both strong.
- Use shadows only for overlays, primary cases, and overlap, with no more than two depth levels per slide.
- No web-button shadows, glow, inner shadow, or heavy black shadow.

## 8. Capacity and deck rhythm

- When capacity is insufficient, change structure within the approved plan, use the grid better, or split supporting evidence. Do not change locked content or go below the type baseline.
- When content itself is insufficient, do not fill the hole with containers, icons, method labels, or decoration. Record and backflow it.
- Audience detail and chart text follow the configured minimum; core body copy should normally be at least 18 pt. Smaller text is allowed only for explicitly configured non-audience technical fields, never body copy, chart text, or entity labels.
- The structure must support intentional line breaks; do not let PowerPoint split numbers, units, product names, or complete phrases arbitrarily.
- Avoid isomorphic card pages among ordinary slides. Logic series slides repeat the Art Direction backbone so comparison, accumulation, or drill-down works; only current focus and new information change.
- At thumbnail size, validate the backbone. At full size, verify that L1, L2, and necessary L3 content follow the same reading order.
- Business-analysis slides may be dense but need primary evidence. Strategy-deployment slides should vary among strong judgment, structure, and evidence. Training slides use large type, short sentences, and real contexts.
- Inspect whole-deck color and density at thumbnail size and slide-level order and detail at full size.
- `semantic_whitespace` is not waiting to be filled. Do not add decoration or weak explanation to `future-space`, `unknown-space`, or `pause`.
- `persistent_context_rail` is lightweight orientation only: no button states, tabs, heavy surfaces, or interaction shadows.
