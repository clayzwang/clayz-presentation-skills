# Build-Only Contract

## Core principle

Output turns a plan into objects; it does not reinterpret objects into a new plan. The approved plan is the execution baseline. Changing composition, medium, area, density, reading path, series persistence, motif, semantic whitespace, or persistent navigation merely “to look better” is out of scope without adjudication. Native implementation may expose an upstream problem; Output may challenge it through Supervisor and user adjudication, but may not silently change it.

## Object-production order

1. Load the generated theme or user-supplied master selected by central configuration and remove only permitted sample objects.
2. When using a master, verify and preserve inherited objects, dynamic slide numbers, and title zones; do not recreate them on the slide layer.
3. Create background zones and connectors.
4. Create native tables, charts, images, or the primary relation object.
5. Create nodes, text, and annotations.
6. Set `copy_id`, `render_target_id`, and object layer order.
7. Render, inspect, and repair.

Before step 3 for a shared `series_id`, establish a production baseline for persistent elements: stable object names, coordinates, sizes, styles, and layer order. Copy that baseline to later series slides and apply only `progressive_change`. A series-exit slide breaks the shell explicitly according to the approved plan.

## Technical deviation log

```json
{
  "contract_version": "1.0",
  "package_id": "example-deck",
  "art_direction_plan_version": "1.3",
  "deviations": [
    {
      "deviation_id": "DEV-S10-01",
      "slide_id": "S10",
      "planned": "hide category-axis labels",
      "actual": "retain the native chart and mask redundant labels with the background color",
      "reason": "compatibility engine ignores the hidden property",
      "changes_art_direction": false,
      "approved_by": "output-technical-contract",
      "backflow_status": "not-required"
    }
  ],
  "unresolved": []
}
```

An allowed deviation does not change the audience's first visual or semantics. Delivery is blocked while `unresolved` is nonempty.

## Compatibility

Prefer native charts, tables, and master fields. Compatibility repairs must be local and traceable and may not conceal data or alter comparisons. Verify differences among configured target applications from actual final renders, not inferred object properties.

If an exporter drops inherited dynamic `slidenum`, title placeholders, or layout dividers, stop using that export path and switch to a supported path that preserves inheritance. Do not imitate a repair with static numbers, slide-layer lines, or overlaid duplicates. After any master compatibility repair, rerun inherited-chrome uniqueness checks.

Cover and closing slides must not depend exclusively on layout-layer objects that target applications render unreliably. Add an editable slide-layer fallback only when a compatibility probe proves it is needed and central configuration permits it. A fallback must not create a second visual system or duplicate the master.

Rank compatibility evidence from strongest to weakest: target application opened the file, target-application render, production-side render, static OOXML inspection. Without stronger evidence, run the general compatibility suite and record the gap in delivery notes. Passing one local renderer does not prove every configured target.

## Delivery size

File size is an Output implementation concern and does not authorize a dominant-medium change. Unless the user specifies otherwise, use the lightweight profile: preprocess images for their final placed boxes, embed identical media once, and remove unused media, hidden attachments, and accidental fonts. If compression visibly harms one asset, increase only that asset's quality and log the technical deviation. Do not delete planned imagery, change area, or rasterize a full slide.

After the final write, generate `ppt-size-audit.json`. A soft total budget may be exceeded when there is no item-level inefficiency and QA records the concrete need. Repeated, unused, over-resolution, or accidentally embedded content must be repaired rather than hidden behind a total-size exception.
