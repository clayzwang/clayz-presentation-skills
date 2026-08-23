# Layout Contract Compilation

Output consumes an Art Direction-approved Layout Contract resolution, retrieval
receipt, task-local slot binding, and compiled Layout Tree. It does not select a
contract, choose a Theme or Visual Variant, or alter semantic topology.

Before coordinate solving, verify that the selected record appears in the
receipt, the catalog payload path stays under `catalog/layout-contracts/`, the
payload SHA-256 matches the record, every required slot meets its cardinality,
and every Semantic Layout Tree node and `copy_id` is bound at most once.

Run `packages/layout/compile_layout_contract.py`, then resolve the emitted tree
with the existing relative solver. Theme and Visual Variant remain marked
`external-not-consumed` in the compilation envelope; editable object creation
may apply them only after coordinates exist and only from approved inputs.

An `unresolved` resolution is not build permission. Return to the approved core
Semantic Layout Tree path without inventing a named contract or fallback tree.
