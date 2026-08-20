# Relative Layout Production Contract

This contract converts approved region relationships into editable coordinates without adding composition judgment. Its relative-layout tree is informed by the Flexbox/Yoga approach in [pom](https://github.com/hirokisakabe/pom); exact provenance and boundaries are in `provenance/manifest.yaml`. Final delivery uses the renderer and theme selected by central configuration and remains subject to Output QA.

## Applicability

Prefer a hybrid of fixed frame and internal relative layout:

- Fixed frame: inherited master objects, title zone, dynamic slide number, persistent navigation, dominant visual anchor, and semantic-whitespace boundary.
- Relative layout: rows, columns, 12-column grid, equal-weight modules, fixed-plus-flex columns, and nested regions inside an approved content zone.
- Absolute positioning: connectors, label leaders, chart masks, and objects that require pixel-level alignment.

Relative layout absorbs technical variation in line wrapping, peer-module count, and content height. It may not alter `area_plan`, main backbone, area weight, reading path, dominant medium, density, semantic whitespace, or series persistence.

## Mapping approved fields to a layout tree

| Approved field | Output implementation |
|---|---|
| 12-column spans in `area_plan` | renderer 12-column `grid` and `columnSpan` |
| region area ratios | fixed tracks, `fill`, or proportionally flexible tracks |
| `reading_path` | `row`/`column` child order; never coordinate crossing that changes order |
| `contains_copy_ids` | a named container holds the corresponding `COPY::<copy_id>` objects |
| `copy_unit_map.render_target_id` | containers and native objects use stable `name` values verified after reopen |
| `persistent_elements` | fixed outer-frame coordinates; the same series reuses object names, sizes, and layers |
| `semantic_whitespace` | protected track or fixed blank region excluded from `fill` |
| `progressive_change` | add or remove only approved child nodes; do not rebuild the entire tree |

## Renderer implementation order

1. Load the generated theme or user-supplied master selected by central configuration and determine the body safety `frame`.
2. Build the layout tree inside `frame` with the renderer's row, column, grid, and layer capabilities.
3. Fix non-drifting tracks first, then allocate remaining space to `fill`. Equal-weight peers all use `fill`; do not hand-calculate each width.
4. Render named text containers with approved type sizes and intentional line breaks. Use `hug` only where a local region may grow; it may not consume protected whitespace.
5. Keep charts, tables, images, and connectors native or precisely positioned. Read named container bounds where needed rather than turning the slide into a flowing webpage.
6. Export a layout manifest and, after the final write, verify object names, bounds, order, overlap, and overflow.

## Capacity and overflow adjudication

Disable automatic fitting that silently shrinks type, spacing, or the whole slide. Resolve capacity in this order:

1. optimize line breaks, flexible tracks, and peer spacing inside approved regions;
2. verify that fixed tracks do not consume space incorrectly;
3. produce overflow diagnostics and layout evidence; and
4. return to Art Direction, Copy, or Logic for upstream or user adjudication.

Never go below `typography_contract`, consume `semantic_whitespace`, delete copy, switch medium, change area, or split/merge modules without approval.

## Diagnostics and acceptance

- Test at least short/long text and fewer/more peer-module variants for each layout family.
- The final PPTX must still pass configured font, glyph-pixel, theme/master inheritance, target-application, readability, object-manifest, and full-deck render checks.
- Text present in XML but absent in final rendered glyphs is a failure; lack of layout overflow does not override it.
- `NODE_OVERLAP`, `NODE_OUT_OF_BOUNDS`, and clean results from the relative-layout engine are supporting evidence only, never a substitute for slide-by-slide visual inspection.
- `pom` may be used for research, probes, and diagnostic comparison. It is not the delivery engine and may not rebuild themes, masters, or the font system from an existing PPTX.
