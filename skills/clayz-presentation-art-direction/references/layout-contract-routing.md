# Layout Contract Routing

Layout Contract selection is an Art Direction responsibility. Build the request
from the already approved page role, semantic relations, purpose tags, locale,
and rights context. Select only a registered, human-admitted, materializable
record that appears in its retrieval receipt.

Bind every selected contract slot to task-local Semantic Layout Tree node IDs
and approved `copy_id` values. The binding may not rewrite copy, invent a node,
or mix in Theme, Visual Variant, renderer, asset, or coordinate data.

If there is no eligible contract, record `unresolved` and continue with the core
Semantic Layout Tree workflow without claiming a named contract. If several
contracts match, require an explicit preferred record ID; do not silently pick a
look-alike.

See `../../../docs/layout-contracts.md` for schemas, compilation, and public
asset boundaries.
