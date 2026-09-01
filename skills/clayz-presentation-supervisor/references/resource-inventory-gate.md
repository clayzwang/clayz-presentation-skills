# Pre-Logic resource inventory gate

Resource discovery is root control-plane work, not a sixth presentation stage. Supervisor owns it before Logic so a user can see what this host and account can actually use before quality depends on hidden assets.

Before inventory, run `scripts/component_version_guard.py`, compare the mounted component table with the official GitHub Latest Release, and print the table to the user. An unavailable freshness observation, an older component, or any version drift is blocking; do not reduce it to an inventory warning.

## Scan before authoring

For every new build, revision, or audit, scan and evidence all seven scopes:

1. mounted plugin runtime and all five governed Skills;
2. task inputs, including the request and every supplied document, spreadsheet, image, deck, or data file;
3. owner Library sources and Provider manifests, including whether the underlying bytes can actually be read and hashed;
4. bundled public Index and registered reference pools;
5. theme, master, template, logo, icon, brand, and other visual assets;
6. host authoring, rendering, inspection, and target-application capabilities; and
7. the actual font environment, including deferred-native fonts.

Owner-personal mode also records the version-private-learning state under the owner-Library scope: public-core version, learning key, first-run or reuse mode, separate learning-audit digest, persistent index digest, and source-set digest. The first run reads the admitted source bytes and builds the index. Later runs verify and reuse it. A nonpersistent state root, missing audit, changed source bytes, or incomplete knowledge-kind coverage blocks Logic.

Do not count a locator, manifest entry, remembered capability, or unavailable tool as an available resource. Collapse large pools into named, hash-bound entries with a quantity; do not dump hundreds of records into the user message.

Write `ppt-resource-inventory.json` under `io.clayz.presentation.resource-inventory/1.0`. Every resource records availability, rights, stages, quantity, fingerprint when materialized, selection decision, and a concrete reason. Finalize and validate it with:

```bash
python ../../scripts/finalize_resource_inventory.py \
  <resource-inventory-draft.json> <ppt-resource-inventory.json> \
  --brief-output <ppt-resource-inventory-brief.md> --require-ready
```

## Tell the user before Logic

After Provider materialization and route locking, but before any Logic, Copy, Art Direction, or Output work, send one concise commentary update that states:

- what was found, grouped by task material, owner resources, public resources, brand assets, fonts, and execution capabilities;
- the complete core-component version table and official latest version, after the gate has passed;
- whether private learning ran for the first time or reused the version-bound index, and which knowledge, template, standard, and method categories the learning audit covers;
- what is selected for this task and why;
- what is unavailable, deliberately not selected, or only conditionally useful; and
- the locked authoring/rendering route and that governed authoring is now starting.

Use user-facing names and counts, never private physical paths, credentials, or an unbounded record dump. The brief's structured resource-ID coverage must bind every inventoried, selected, non-selected, and unavailable resource; a generic “inventory complete” sentence cannot satisfy the gate. Say "will use" at this point; reserve "actually used" for the final reconciliation.

If the gate is ready, continue automatically after the message. Do not require a ceremonial confirmation. If a required resource is missing or inaccessible, show the exact gap and stop before Logic; ask only for the material choice or access needed to proceed. Never silently switch an owner-personal request to public-core mode.

## Preserve the lock

The Logic package carries the complete inventory. Art Direction and Output QA carry its immutable signature. New resources arriving after the brief require a new inventory revision, a new lock, and a new concise user update before use.

At final supervision, reconcile every initially selected resource as actually used or unused with a reason. Cover all five governed stages with evidence references and present the user with a short actual-use summary. No late, unlisted resource may appear in the usage record.
