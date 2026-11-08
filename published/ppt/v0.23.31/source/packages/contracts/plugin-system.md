# Local presentation plugin system

This contract adds three entry modes around the existing five production stages:
resource inspection, discussion-based knowledge learning, and PPT enablement.
Governance/maintenance skills are external management components and never part
of this plugin. This local implementation does not claim a connected ChatGPT
Library, deploy a server, or publish anything.

## Shared boundaries

- Keep one Public Core, IndexRecord/IndexProvider/CompositeIndex retrieval engine,
  and the existing five stage artifacts and validators.
- Store owner content outside the plugin root. Explicit filesystem bindings are
  host inputs; canonical knowledge uses library:// URIs, never host paths.
- Discussion drafts are not production artifacts and cannot enter retrieval.
- A human confirms the exact draft digest including attachment metadata and
  hashes. Confirmation is a host-recorded user decision, not cryptographic proof
  of human identity. The assistant must have the actual user's decision.
- A changed draft or attachment needs a new confirmation. Agreement does not
  turn an interpretation into an externally verified fact.
- Committed revisions are immutable. New revisions explicitly name their parent;
  existing tasks keep their snapshot. No silent last-writer-wins updates.
- Knowledge committed during an already locked production run becomes available
  to subsequent runs. To use it immediately, begin a new task snapshot and
  invalidate affected artifacts from the earliest responsible stage. A direct
  user correction can still be handled as current task input through normal
  stage backflow; it does not silently change the Library lock.
- Publish knowledge, confirmation, attachments and the existing-format provider
  index together. Readers see only a complete verified snapshot. Failed writes
  leave the previous snapshot usable. A missing store means unavailable, not an
  empty successful Library.

## Discussion content

A draft identifies a session, title, responsible stage (logic/copy/art-direction/
output), consensus, applicability, limitations, provenance category
(source-fact/user-experience/joint-inference), evidence references, unresolved
questions, language, purpose tags, and attachments. Each attachment has a stable
ID, filename, SHA-256, origin, rights, and locator (page/section when known).
Optional `applicable_stages` allows one owned record to serve several production
stages without copying it into parallel stores; the default is its owner stage.
The allowed values are logic/copy/art-direction/output, never a Supervisor silo.
Retrieval eligibility includes the owner stage plus applicable_stages; each
adopting stage preserves that same record revision/hash in its existing receipt.
Unresolved questions remain context and are never asserted as agreed knowledge.
The consensus may have no attachment when it records an explicitly confirmed
discussion; the absence of external evidence stays visible.

## Command surface

`scripts/plugin_cli.py` is the local facade. `inspect` checks installed components,
Library snapshot integrity and available tool definitions; `draft` prepares an
immutable review object; `confirm` binds a human decision; `commit` saves a
verified snapshot; `retrieve` delegates to the existing index and returns source
and snapshot evidence; `tools` lists the existing production methods and code
entrypoints. JSON files are internal handoffs; the assistant handles them.

An inspection is not a production preflight or a finalized retrieval receipt.
Production continues through the existing inventory, acceptance, preflight,
stage-specific reasoning, explicit selection, editable build and render QA.
PPT advice can stop at a useful answer when that is the user's requested result.

## Development acceptance

Exercise draft exclusion; actual hash-bound confirmation; attachment drift;
failed and concurrent commit; stale parent; snapshot reuse and tampering;
cross-process restart and existing-engine retrieval; unavailable store; all four
knowledge ownership stages; public/private retrieval boundaries; local package
closure and exclusion of governance and owner data. Retain the full baseline
suite. Tests of contracts do not certify model judgment or visual quality.
