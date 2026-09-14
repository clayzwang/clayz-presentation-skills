# Native ChatGPT Library workflow

This contract governs the same-name cloud Skill when it is called from
ordinary Chat or Work. It is host-mediated: the Skill discovers and uses the
host's actual native Library, file, and code capabilities, while the existing
IndexRecord/IndexProvider/CompositeIndex and the five presentation stages
remain the shared execution model.

## Scope and policy

- The Skill is globally callable and may be implicitly invoked or explicitly
  addressed with `@`. It has no dependency on a ChatGPT Project. `PPT` is the
  owner Library root; it is not a ChatGPT Project.
- The composer supplies `runtime/native-library-policy.json` from the existing
  host-library root for the optional owner route. The policy fixes `logical_root` to
  `library://clayz-confirmed/` and `provider_id` to
  `clayz.owner-consensus`; its `host_root` is that existing root plus
  `/_extension/confirmed-learning`. This is the binding for optional confirmed
  knowledge publication, not a prerequisite for reading a user-specified folder.
  If it is absent, ordinary observed file reads remain usable; no confirmed
  storage destination is invented. Physical bindings are task-local host observations and must not be
  copied into reusable records, profiles, or Skill prose.
- When Library reference use is enabled, or when the task explicitly asks to
  inspect the Library, inspect the actual host Library, file, and code
  capabilities and their available tool definitions. When no Library sources are used, use the
  bundled public Index without probing or scanning the owner Library merely to
  route the request. Never invent a tool name or claim that a host has files,
  code execution, a Library reader, or a writer without an observed capability.
  Do not use the local `plugin_cli.py` filesystem facade as a native Library
  implementation. Governance and maintenance management remains outside this
  Skill.
- Keep the access domains separate: the native Library service is a host
  capability; the configured display folder/path (including `PPT`) is a folder
  locator; a ChatGPT Project is project state; and a plugin, tool, or app is an
  integration identity. Presence or authorization in one domain proves
  nothing about the others.
- `library://...` and `host_root` are logical locators, not OS paths.
  They never prove that `/PPT`, a configured folder, or any physical host path
  is readable. Resolve a folder or path only through the host's observed
  native locate/search result.

## One path with optional Library inputs

All new production uses the merged v2 task selection and the constant unified
workflow. Defaults, saved personal settings and task overrides are layers,
not modes. Use `configure-task --personal-config ... --task-overrides ...`
when those files are available, then bind its config/selection in preflight.

The Library locator can be omitted, supplied later or revised through
`--previous-selection` and `--library-locator`. `--with-library` and
`--without-library` control reference use only; neither clears loaded personal
settings nor changes the master. The locator remains pending until observed
host tools actually read the files. No helper grants access or silently saves
settings across sessions. Read the merged profile/preferences as configuration,
not as topic evidence. Required task inputs remain required; optional Library
unavailability does not create another production path.


## Native access resolution

A Library locator may be supplied or changed later with `configure-task
--previous-selection ... --library-locator ... --output-dir ...`. Reuse the
previous visual identity and knowledge choice unless the user changes them.
The resulting locator is pending verification. Use it as the lookup context
for actual native search/read or explicit current-task file mappings; it does
not rename a logical namespace, change Provider identities, or grant access.
Missing native tools leave the private branch pending while an independently
requested public branch can finish. Preserve earlier reports and outputs.

When Library reference use is enabled, or when a task explicitly requests Library
inspection, resolve native access from live host evidence once per cold-start
attempt, in this order. Production without Library references uses the bundled public Index
and does not require native owner-Library discovery.

1. Inspect the current tool definitions once and keep the observed canonical
   app/tool identity and capability in the task log. If the host exposes a
   supported tool-discovery or lazy-loading surface, use it once for the needed
   native Library capability before concluding that capability is not exposed;
   a newly returned callable definition is changed evidence. A plugin catalog
   hit or permissions result is not a callable definition. Plain user
   authorization does not load a tool or establish a capability.
2. If the observed tools provide native Library locate/search, pass the
   configured display folder/path as a locator and accept only the actual file
   references they return. If more than one file could match, require precise
   disambiguation by the returned identity/metadata; never use a filename-first
   match.
3. Read the selected file through its bound returned reference. Only a
   successful byte read can establish a resource result, with the observed
   reference, byte count, and SHA-256 recorded. A logical URI or derived
   `/PPT` path cannot substitute for that read.
4. When native search is unavailable but the user explicitly attaches or maps
   the exact needed file in the current chat, use the current-chat-file read
   for that task. This is task-only evidence; do not call it a connected
   native Library service, permanent admission, or a saved host resource.

### Required Provider and owner-learning inputs

The following source-materialization checks apply only to actually selected
knowledge inputs, not to all Providers of an installed profile. With no such
sources, bind the bundled public Provider/Index and its real retrieval
receipts across all five stages; owner Library selection, private Providers,
owner-learning manifests, persistent owner-learning state, and
`task-private-learning` are not prerequisites. Mark the unselected owner
Library scope `not-applicable`, keep `owner_materialization.status` and its
learning mode `not-applicable`, and preserve all public retrieval and
presentation validation.

The `index_execution.source_manifest` value
(`runtime-input://owner-learning-manifest`) is generated by the Skill for the
current task after the pre-Logic scan. It is built only from sources actually
read, covered by an existing valid admission, and bound to observed SHA-256 values; it is not a
pre-existing user attachment or a Library artifact that the user must create.
If a required manifest cannot be read, report that first; after the manifest
read, report missing dependencies in order (declared index, then needed source
bytes), state `prerequisite sources unavailable; owner-learning manifest pending
generation`, and do not ask the user to invent or upload this internal manifest.

For every task-selected required Provider, keep the original binding and snapshot
gate: read its manifest through the locked runtime/native mount, then read the
index URI declared by that manifest, then read only the admitted source bytes
needed for the current question. Each step must use an observed native file
reference or an explicitly mapped current-chat file. A manifest/index
locator, guessed path, filename-only match, fabricated hash or admission, or
automatically granted Library permission does not establish a readable,
admitted, or verified Provider. An already-read attached template remains
task-bound evidence and does not prove whole-Library access.

Do not use `plugin-management` `get_app_permissions`, a free-text app name, or
a raw `not_installed` result to diagnose native Library or file access. Do not
default to migration, installation, linking, `@` addressing, or
re-authorization prompts. Suggest one only after discovery has returned a
canonical app identity, evidence that its actual tool supplies the needed
native Library/file capability, and an actionable current UI control. Without
all three, report the observed capability gap and keep the native route
unavailable; continue task-local or explicitly mapped work when allowed. Do
not derive an install action from the permission lookup.

When code execution is available, the deterministic resolver is:

```text
python scripts/cloud_learning_cli.py resolve-access --observation <observation.json> --previous-report <previous-report.json> --output <report.json>
```

Its observation input must be made from the actual current tool inventory and
attempt results; the previous report is only prior resolver state. Never
manufacture either input from planning text, chat claims, or a catalog. The
resolver returns `ready`, `partial`, `blocked`, or `no-resources`, plus
per-resource states, successful file hashes, and `retry_discovery`. These are
plain observations, not authenticated receipts; preserve the direct tool and
file references in the task log.

The observation contract is `io.clayz.presentation.host-access-observation/1.0`:
one stable `session_id`, `tools[{tool_id,kind,operations}]`,
`resources[{resource_id,logical_uri,host_locator,required}]` with optional
`expected_sha256`, `selected_reference`, and `explicit_attachment_ref`, and
`attempts[{resource_id,tool_id,operation,status}]` with
`matches[{reference,locator}]` for `locate`, and `reference`, `materialized_path`
for `read`. Use canonical tool
IDs actually observed in this task; examples are not executable tools. Reuse
the session ID with `--previous-report`; never create a timestamp or new ID only
to retry. A fresh real conversation starts a new session.

Here `ready` means that the requested required resources are readable for this
task. It does not mean the native Library writer, the whole `PPT` folder, or a
presentation production route is ready. A `readable-attachment` result is
current-chat-file evidence for this task only and is never a connected native
Library result. Save each resolver report as a new task-local revision (for
example `host-access-1.json`, then `host-access-2.json` with the first passed
as `--previous-report`); do not overwrite earlier evidence.

After one failed discovery, report the precise blocker once and do not loop or
re-ask for authorization. Recheck only after an actual tool/reference change,
a new session, or an explicit user fresh-check request. `retry_discovery`
records that condition; it is not a reason to promise a single UI step.

## Cold-start read and snapshot binding

When Library reference use is enabled and the host exposes a native reader, perform
a bounded, read-only cold-start read in this order:

1. Read the composer policy and reuse the one current tool-definition
   observation from Native access resolution.
2. Through an observed native reader, read the `CURRENT` pointer at the
   policy's `host_root`, when present, and use its snapshot ID to open the
   immutable snapshot's manifest, Provider manifest, and `records.jsonl`. Read
   resource bodies or attachments only for the current question.
3. Obtain the complete selected snapshot (or an equivalent host-native
   verification view) before declaring it verified; metadata-only index rows do
   not prove snapshot or attachment integrity. Verify the snapshot and index
   hashes before retrieval. Read only the relevant record/resource excerpts into
   model context and never scan or ingest the whole Library. A missing optional
   confirmed snapshot or missing `CURRENT` is a normal cold-start state and
   must be reported as unavailable rather than treated as an empty successful
   Library.
4. Lock the observed snapshot for the task. Do not silently change it when a
   later conversation turn adds knowledge.

After locking an owner snapshot, resolve `library://clayz-confirmed/` for that run to the
host-native locator `<host_root>/snapshots/<snapshot_id>/`. This notation is
not an OS path; use it only through the observed host reader. The index and
entry files live inside that immutable snapshot; do not map a record URI
directly to the store root, which does not contain the entries. Actual selected-source and merged-configuration requirements remain in force. When no Library sources are used, do not resolve this optional
owner snapshot merely to run the public workflow.

Before Logic, the user-facing resource brief keeps five categories separate:
required external resources; task-generated artifacts (including the
owner-learning manifest and its materialization/audit when actually materialized);
the optional confirmed snapshot; deferred environment acceptance; and research
evidence to collect. When no Library sources are used, identify the owner-library category as
not applicable and do not report a fabricated private learning mode.
A missing topic attachment is a deferred task input rather than a blocker when
the task authorizes research and an allowed research source is actually
available. Record the evidence and limits. Research can supplement the topic
but never replace a required private Provider; web/public search must never
substitute for private-provider bytes.

When the resolved configuration places a font identity under
`preserve-name-defer-native`, missing native font availability is deferred
acceptance and does not block Logic. Preserve the identity's exact
`pptx_family` in both Latin and East Asian PPTX fields and never substitute
silently. Missing PowerPoint or WPS is deferred target-application acceptance,
not a pre-Logic blocker; final claims remain limited until those checks run.

## Discussion, exact confirmation, and admission

`draft` prepares a review candidate with every content field required by
`packages/knowledge_session/discussion.py`:

`session_id`, `title`, `stage`, `applicable_stages`, `consensus`,
`applicability`, `limitations`, `provenance`, `evidence_refs`,
`unresolved_questions`, `language`, `purpose_tags`, `attachments`, and
`supersedes`.

The owner stage is one of `logic`, `copy`, `art-direction`, or `output`;
`applicable_stages` may add other of those four stages. Each attachment keeps
`attachment_id`, `filename`, `origin`, `rights`, and `locator`; preparation
adds its exact `sha256` and byte count. The candidate also carries its
canonical `draft_sha256`. It is a review object only: it is not an admitted
record, a retrieval candidate, or a production artifact.

Show the exact prepared draft digest and attachment metadata to the actual
user. `confirm` may cross the admission boundary only after that user confirms
that exact digest with a human decision (`confirm_human_decision=true`). The
confirmation binds `draft_sha256`, `confirmed_by`, `decision`, and
`confirmed_at` to that draft. Task authorization, assistant agreement, or a
prepared local mirror is not permanent admission, and agreement does not make
an interpretation an externally verified fact. Any changed content or
attachment requires a new draft and new confirmation.

If native tools are absent, a discussion candidate may remain as a task-local
review object. Do not invent a native-access hash, resource inventory, saved
status, or host admission; a real hash of supplied bytes remains only the
candidate's own digest until native readback and the existing confirmation and
publication rules succeed.

## Host-mediated publication

The independent `scripts/cloud_learning_cli.py` facade, when it is present and
the host exposes code execution, may provide these deterministic operations:

- `draft`: prepare the complete review candidate and attachment hashes.
- `confirm`: bind the actual user's decision to the exact draft digest.
- `stage`: build a full local task mirror containing the candidate, confirmation,
  attachments, Provider index, manifest, and publication plan; its status is
  `awaiting-host-write`.
- `verify`: perform the fresh native readback described below.
- `read`: open one exact verified consensus and its attachment bindings by record ID.
- `inspect` / `retrieve`: inspect or search the mirrored, verified snapshot through
  the existing IndexProvider/CompositeIndex; retrieve emits a standard receipt.

Use `python scripts/cloud_learning_cli.py <command> --help` for exact arguments.
All review objects, mirrors, plans and readback reports belong in task scratch
outside the installed Skill directory. The mirrors are never the durable Library.

The local stage mirror is a plan and evidence input, not a native Library
commit. When an actual host writer is available, write the immutable snapshot
directory, confirmed drafts, original attachments, Provider manifest, and
existing-format `records.jsonl` first. Re-read `CURRENT` immediately before
publishing the pointer and compare it with the expected old snapshot/hash
(`null` when creating the first snapshot). Abort on a changed or stale parent;
never use last-writer-wins. This re-read alone is not a race-proof update: if the
host lacks a conditional or versioned update (or equivalent single-writer
guarantee), concurrent writers are unsupported and `CURRENT` must not be
written. Write or replace `CURRENT` last, and only through the observed host
writer. The writer must leave the prior verified snapshot usable if the
operation fails.

If no native writer is discovered, preserve the candidate and the
`awaiting-host-write` plan, state the exact missing capability, and continue
the discussion. Do not redirect the user to NAS or MCP and do not block pure
discussion or unrelated PPT thinking. A missing writer does not block readable
sources. If a required private resource is unavailable, the affected governed
approval or Output remains blocked; keep the existing Provider, profile, brand,
and five-stage gates and do not silently switch to Presentations or remove a
gate; use an alternative only when the user explicitly chooses it. Do not
request a new Project by default. Never claim distributed
atomicity or an authenticated host receipt merely because a local stage
succeeded.

The write-plan and fresh-readback rules above remain unchanged. Native access
resolution only reports whether a resource can be read and does not turn a
local plan into a host write or a plain observation into a receipt.

## Fresh verification and retrieval

`verify` must start from a fresh host read, re-read `CURRENT`, download the
complete selected snapshot from the native Library, and check the manifest,
Provider index, confirmed drafts, confirmations, and every attachment against
their declared hashes. A successful status is `verified-readback`; staged
local bytes are not readback evidence. A pointer conflict, missing file,
hash mismatch, or incomplete snapshot keeps the prior snapshot usable and the
new publication unverified.

`inspect` and `retrieve` reuse the shared native snapshot and existing index;
they do not create a second search cache. Retrieval can use only the locked,
complete snapshot and must preserve the provider ID, snapshot digest, source
URI, and relevant rights/limitations in the existing receipt. A no-match is a
valid result.

For PPT production using a verified confirmed snapshot, add the verified `clayz.owner-consensus`
IndexProvider as an optional supplemental provider alongside the existing locked
Providers in one CompositeIndex. Keep the existing private Provider/profile/
brand bindings intact; the optional provider never satisfies or replaces a
required Provider. Every stage receipt in that run uses the same confirmed
snapshot. When no Library sources are used, use only the bundled public Provider/Index and do
not add an owner Provider or private gate.
If new knowledge is published mid-run, use it only in a new run snapshot or
explicitly invalidate and restart the affected stage from the root. Never
silently change a locked source set.
