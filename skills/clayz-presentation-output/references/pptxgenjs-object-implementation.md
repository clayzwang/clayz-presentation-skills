# PptxGenJS object implementation route

Use this route only when the configured backend is PptxGenJS, a future reviewed configuration has enabled its security gate, and the approved plan can be expressed by supported editable objects. Public v0.2.0 deliberately disables the route because the current transitive dependency chain has unpatched high-severity denial-of-service advisories.

Clayz uses the public [PptxGenJS 4.0.1 documentation](https://gitbrent.github.io/PptxGenJS/) to maintain an original experimental adapter. PptxGenJS is MIT-licensed; exact version, commit, documentation links, redistribution boundaries, and current security block are recorded in `provenance/manifest.yaml` and `provenance/THIRD_PARTY_NOTICES.md`. No upstream source, dependency lock, demos, templates, slide masters, or media are bundled. The v0.2.0 adapter blocks images/SVG and requires explicit risk acknowledgement; it is not a production route.

## Input boundary

The adapter consumes `packages/contracts/render-manifest.schema.json`, a resolved technical manifest below approved Copy and Art Direction. It is not a new authoring layer. Before rendering:

- validate that each `object_id` is globally unique;
- bind every visible approved copy unit to one `copy_id` and object;
- resolve relative layout before object creation;
- allow only local or inline assets with known provenance;
- keep charts and tables native when the backend supports them;
- do not add a programmatic master when the user supplied a different active master.

## Object mapping

| Manifest object | PptxGenJS public API route | Output proof |
|---|---|---|
| `text` | `slide.addText` | exact text, type size, language, line breaks, object name |
| `shape` / `line` | `slide.addShape` | bounds, layer, semantic role, connector meaning |
| `image` | security-blocked in v0.2.0 | return a capability gap; do not parse the asset |
| `svg` | security-blocked in v0.2.0 | return a capability gap; do not parse the asset |
| `table` | `slide.addTable` | row/column count, cell text, alignment, overflow |
| `chart` | `slide.addChart` | series, categories, labels, axes, editability |

Do not translate every copy unit into its own rectangle. Object type follows the approved medium and semantic layout tree.

## Fail-closed runtime

Do not install or run the dependency from this public version for untrusted or production input. The adapter is retained as a syntax-checked API mapping and fails unless a maintainer makes a separate, explicit risk decision. A blocked object or runtime route is environment feedback: select a safe configured backend or return the capability gap; never weaken the approved plan silently.

## Required verification

PptxGenJS writing success proves only that a file was emitted. Reopen the written PPTX, inspect object names and types, render every slide in at least one configured target application, verify CJK glyph pixels where relevant, and run the existing deviation, legibility, size, rhythm, Output QA, and Supervisor checks. Never advertise compatibility that was not observed.
