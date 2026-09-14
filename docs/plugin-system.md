# Local plugin system

The local facade adds three entry modes around the existing five presentation
stages: resource inspection, discussion-based knowledge learning, and PPT
enablement. It does not add a sixth stage, claim a connected ChatGPT Library,
deploy a server, publish a package, or include governance and owner content.

## Entry modes

Use `scripts/plugin_cli.py` as the local facade. Its commands are:

- `inspect` checks installed components, the available Library snapshot, and
  tool definitions. It is read-only; it is not production preflight and does
  not create a retrieval receipt.
- `draft` prepares an immutable discussion review object. The object records
  the session, title, responsible stage (`logic`, `copy`, `art-direction`, or
  `output`), consensus, applicability, limitations, provenance category
  (`source-fact`, `user-experience`, or `joint-inference`), evidence
  references, unresolved questions, language, purpose tags, and attachments.
- `confirm` binds the actual user's decision to the exact draft digest,
  including attachment metadata and hashes. The confirmation records a user
  decision; it is not cryptographic proof of identity, and agreement does not
  make an interpretation externally verified.
- `commit` saves an immutable revision only after confirmation. Each new
  revision names its parent. Knowledge, confirmation, attachment metadata and
  hashes, and the existing-format Provider index are published as one complete
  verified snapshot. A changed draft or attachment requires new confirmation;
  failed, concurrent, or stale-parent writes leave the previous snapshot
  usable. A missing store is unavailable, not an empty successful Library.
- `retrieve` delegates to the existing Index and returns source and snapshot
  evidence. Drafts, unconfirmed consensus, and incomplete snapshots never
  enter retrieval.
- `read` materializes one verified consensus revision and its source attachment
  locations by record ID; it cannot read a draft or an incomplete snapshot.
- `tools` lists the existing production methods and code entrypoints.

Each attachment has a stable ID, filename, SHA-256, origin, rights, and a
page/section locator when known. Attachments may be absent when a discussion is
explicitly confirmed without external evidence; that absence remains visible.
Unresolved questions remain context and are never emitted as agreed knowledge.
Owner content stays outside the plugin root and is addressed by governed
`library://` bindings.

## PPT enablement

For a capability or route question, `tools` and `inspect` can produce a useful
answer without starting deck production. When the user asks to create, revise,
or audit a PPT, Supervisor runs the existing resource inventory, acceptance,
preflight, and evidence locks, then dispatches the unchanged
`Logic -> Copy -> Art Direction -> Output -> Supervisor` responsibilities.
Confirmed committed knowledge may be selected through the existing Index, with
its provenance, evidence limits, unresolved questions, and attachment hashes
preserved. No stage creates or commits discussion records.

Output follows the existing editable-object and render QA route. Inspection is
not a production approval, and a committed discussion snapshot is not an
automatic PPT requirement.

## Local command example

Run from the plugin root with Python and its `requirements.txt` dependencies.
The assistant prepares JSON handoffs; the owner reviews the readable consensus,
scope, evidence and attachment list, not command syntax. Use an external
persistent `../owner-library` directory and separate draft revision filenames.

```bash
python scripts/plugin_cli.py inspect --store ../owner-library
python scripts/plugin_cli.py tools
python scripts/plugin_cli.py draft --content ../work/content.json --attachment source-one=../work/source.pdf --output ../work/draft-1.json
python scripts/plugin_cli.py confirm --draft ../work/draft-1.json --expected-sha256 <reviewed-draft-sha256> --confirmed-by <owner> --decision <actual-user-decision> --confirm-human-decision --output ../work/confirmation-1.json
python scripts/plugin_cli.py commit --store ../owner-library --draft ../work/draft-1.json --confirmation ../work/confirmation-1.json --attachment source-one=../work/source.pdf
python scripts/plugin_cli.py retrieve --store ../owner-library --request ../work/retrieval-request.json
python scripts/plugin_cli.py read --store ../owner-library --record-id <selected-record-id> --snapshot <snapshot-id>
```

Angle-bracket values are placeholders. Never execute `confirm` merely because
this example includes the flag. The user's decision must already exist and
apply to the displayed draft digest. Revising the same session requires
`supersedes` to name its prior committed `draft_sha256`. A new independent
session uses `supersedes: null`.

Retrieval uses `packages/contracts/retrieval-request.schema.json`. The returned
index paths and provider IDs can be supplied to `scripts/index_runtime_cli.py`
for explicit selection/finalization. Keep the returned snapshot pinned for
the task; inspect/read the actual consensus and relevant attachment before
adopting it. Do not treat a search candidate as a finalized production receipt.

## Development acceptance

The implementation must retain the baseline suite and cover draft exclusion,
exact hash-bound confirmation, attachment drift, failed and concurrent commit,
stale parents, snapshot reuse and tampering, restart persistence, existing
engine retrieval, unavailable stores, all four knowledge ownership stages,
public/private boundaries, and local package closure. Contract tests do not
certify model judgment or visual quality.
