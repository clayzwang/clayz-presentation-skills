# Synthetic Layout Contract Pipeline

This fixture proves the unreleased Stage 3 chain with synthetic copy IDs only:

1. `comparison-request.json` resolves exactly one registered, brand-neutral
   contract and produces a retrieval receipt.
2. `comparison-instance.json` binds approved copy IDs to named semantic slots;
   it contains no theme or visual-variant input.
3. `comparison-compilation.json` contains the five explicit layers and a
   compiled semantic Layout Tree.
4. `comparison-resolved.json` is the separate coordinate solver output.
5. `unresolved-request.json` produces `unresolved-resolution.json`; no fallback
   tree or invented contract is emitted.

All names, IDs, and copy bindings are synthetic. The fixture contains no
presentation asset, identity material, private data, or model payload.

Run the selected path:

```bash
python packages/layout/compile_layout_contract.py \
  examples/synthetic-layout-contract/comparison-request.json \
  examples/synthetic-layout-contract/comparison-instance.json \
  examples/synthetic-layout-contract/comparison-compilation.json \
  --receipt-output examples/synthetic-layout-contract/comparison-receipt.json \
  --resolution-output examples/synthetic-layout-contract/comparison-resolution.json \
  --resolved-output examples/synthetic-layout-contract/comparison-resolved.json
```
