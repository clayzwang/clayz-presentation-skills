# Layout Contracts

Stage 3 adds a registered semantic layer above the existing task-local Semantic
Layout Tree and relative-layout solver. It does not add a sixth skill, a
template library, or a styling engine.

## Layer boundary

| Layer | Owns | Does not own |
| --- | --- | --- |
| Theme | configured colors, typefaces, and presentation defaults | semantic topology or contract selection |
| Visual Variant | approved expression choices such as density, shape language, and motif | registered slot topology or final coordinates |
| Layout Contract | brand-neutral roles, slots, relationships, relative weights, and selection metadata | copy, assets, theme, variant, or coordinates |
| Layout Tree | task-local binding of approved Semantic Layout Tree nodes and `copy_id` values into relative rows, columns, grids, and leaves | theme styling or renderer objects |
| Resolved coordinates | deterministic boxes produced by the existing solver | upstream semantic or visual decisions |

The compiler accepts no Theme or Visual Variant field. Its output marks both as
`external-not-consumed`, records the selected contract and retrieval receipt,
and leaves coordinates `pending`. The coordinate solver materializes only the
last layer.

## Selection and compilation

1. Art Direction emits a `layout-contract-request` using the approved page role,
   semantic relations, purpose tags, locale, and rights context.
2. The Index returns registered, human-admitted candidates with provider,
   revision, rights, and hash evidence.
3. Exactly one eligible candidate may be selected automatically. Multiple
   candidates require an explicit preferred ID; a preferred ID absent from the
   receipt is rejected.
4. A task-local instance binds approved Semantic Layout Tree node IDs and
   `copy_id` values to the selected contract's named slots.
5. The compiler verifies the receipt selection, registry record, payload path,
   payload SHA-256, slot cardinality, content kind, and one-time bindings before
   emitting a relative Layout Tree.
6. Output resolves that tree into coordinates and creates editable objects. It
   does not reselect the contract or change its semantic topology.

If there is no eligible registered contract, resolution is `unresolved` with
fallback action `use-core-semantic-layout-tree-without-claiming-a-contract`.
No contract, tree, theme, or variant is invented.

## Public boundary

`catalog/layout-contracts/` contains original JSON topology only. Machine
validation rejects unregistered or hash-drifted files and keeps the directory
free of presentation templates, masters, themes, brand kits, logos, font
binaries, private data, and model weights. Synthetic examples use synthetic IDs
and neutral semantics.

The separation between machine-readable presentation contracts, visual
variants, and rendering was conceptually informed by
[Tahta](https://github.com/zcag/tahta/tree/7720bc9fc139e8561c282259a4a2519b0c0877bd).
Clayz's schemas, retrieval rules, compiler, fixtures, and solver integration are
original. No Tahta code, contracts, layouts, variants, components, tokens,
fonts, examples, assets, themes, templates, or media are copied or redistributed.
