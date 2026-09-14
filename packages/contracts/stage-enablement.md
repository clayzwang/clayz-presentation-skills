# Stage enablement and execution

This contract governs current task behavior when older stage references describe
mandatory adoption, full replays, fixed presentation formulas, or one-pass stage
boundaries. Shared locks and existing machine contracts still apply; revision
notes do not waive validation or authorize a fabricated lifecycle event.

## Authority and useful outputs

Release coordination belongs to development and deployment, not ordinary PPT
authoring. Use `component_version_guard.py --mode application` (the default) to
check the installed package offline. Status `installed` permits all production
stages and final delivery; it does not claim latest or official publication.
GitHub/Codex/ChatGPT release differences, network unavailability, and development
candidate expiry are not authoring blockers. Retain actual package integrity,
internal contract compatibility, private-runtime and Provider binding checks.
Only an explicit developer `--mode release-check` enforces remote latest-release
and candidate-acceptance policy. This supersedes older latest-only or candidate-
only authoring instructions in bundled references and component-version prose.

User requirements, source facts and meaning remain authoritative. Record each
requirement as user-specified, personal-profile default, or an agent proposal;
never label an inferred page limit or narrative choice as user-confirmed.
Record cover_required and closing_required independently in cover_policy.
For the owner's full decks both default to true; preserve an explicit exception
for either role. Distinguish body-page count and total-page count.

Supervisor starts each production run by turning the user's stated objective,
hard requirements, soft requirements and delivery policy into the shared
acceptance contract. The precedence remains the user request, saved personal
configuration, then defaults. Supervisor parses and records the objective,
commitments and user-authorized changes, but does not become a new authority
that overrides the user or saved layer. Hard requirements are commitments to
implement and check, not a reason to invent evidence or force an endless repair
loop. If one is unmet, record a truthful `fail`; deliver the bound artifact
with the finding by default unless the user explicitly required that named
failure to block delivery.

## Entry mode routing and confirmed knowledge

The root facade exposes three entry modes around the existing production stages:
resource inspection, discussion-based knowledge learning, and PPT enablement.
Classify the request before running presentation production. Inspection reports
installed components, the available Library snapshot, and tool definitions; it
is read-only and is neither production preflight nor a finalized retrieval
receipt. PPT advice may end after the user has a useful answer. A request to
create, revise, or audit a deck enters the existing `Logic -> Copy -> Art
Direction -> Output -> Supervisor` flow. A shared Independent Auditor module
runs after Output as a post-production audit input to Supervisor; it does not
add a sixth production stage or a second retrieval path.

## One production path and layered preferences

Always run the same production path. Merge bundled defaults, available saved
personal configuration, then this task's explicit overrides. Personal settings
are a reusable input layer that can grow with use, not a second runtime or
private edition. Library attachment is optional resource availability, not a
workflow switch. New runs use the constant `unified` in the historical
`resource_inventory.runtime_mode` and `index_evidence.mode` transport fields.
Old `public-core`/`owner-personal` values are only historical compatibility.

Use `scripts/cloud_learning_cli.py configure-task` once before production. It
writes a v2 `task-selection.json` and merged `task-config.json` in a new task
directory. Pass a readable saved preference document with `--personal-config`
and explicit current requirements with `--task-overrides`. These are internal
arguments, not a user questionnaire. If neither exists, use defaults plus any
already configured personal bootstrap settings; do not invent personal data.
Read merged preferences from the selection and carry them into stage work.
The files record real source hashes and layer snapshots; do not edit derived
configs to bypass checks. Preflight uses both `--config` and `--task-selection`.

Use `--previous-selection` for a task revision. Adding/changing the Library
locator or disabling optional references must retain already loaded personal
settings and current requirements, including the master. A missing original
preference file cannot erase its previously loaded snapshot. Newly supplied
preference files must actually be read; failures do not overwrite prior work.
User requirements override saved preferences, which override defaults.

A saved personal document can be a small JSON object such as
`{"config":{"theme":{"typography":{"body_minimum_pt":20}}},"preferences":{"writing":"Preserve useful supporting detail"}}`.
It need not duplicate the full default configuration. Configuration patches
use the supported theme/layout/locale fields; general writing preferences are
context for the model, not topic facts or permission to change program checks.

The Library locator may be omitted, added or changed later with
`--library-locator`. `--without-library` omits optional Library knowledge;
`--with-library` allows it when available. Neither changes the configuration
layers or visual identity. A locator is pending until actual host search/read
tools or explicit file attachments provide readable references and bytes.
Record unavailable resources honestly, without claiming a connection or
looping on authorization. Continue with available inputs unless a specific
user-required source, master or actual production capability is missing.

Runtime preflight keeps the complete resolved capability list for auditability.
In the calibrated path, a real PPTX writer may be `attemptable` while
`available` remains false because master preservation, layout inheritance,
East Asian font naming, render coverage, or another capability has not yet
been observed. Treat those entries as pending/unverified evidence rather than
as proof that the writer is unavailable; use the selected master in the actual
Output attempt and record observed results or failures. A missing real writer
or minimum editable-content prerequisite still blocks the route; static
inspection or other capability gaps remain evidence to collect, and an
internal `spec-only` plan is never an editable PPTX.

Always use the shared Index and the same five stages. Add actual selected
knowledge sources to that Index when available. Do not require all Provider
IDs in an installed legacy profile, or a persistent version-learning store,
merely to start a PPT. If task sources need materialization, use the existing
source manifest and materializer with real provenance/hashes; if no such
sources are used, owner_materialization is not-applicable. Check every source
that is actually declared required. Profile configuration is not evidence for
the presentation topic. Maintenance/version/test documents are not automatic
business knowledge just because they are in the Library.

Saved personal configuration belongs in the user's Library when actual host
storage supports it. Reuse readable saved values on future tasks; save changes
only through the existing real write/verification workflow when requested.
One-time task overrides are not automatically permanent preferences. Without
host persistence, preserve/export the task configuration and state that it is
task-local; never claim cross-session memory without a real saved/read record.

New content can reuse the selected master: preserve the actual cover, body and
closing layout mapping, rather than interpreting new creation as a blank deck.
For a comparison with/without Library knowledge, keep the same configuration
and visual identity, separate task records and distinct final outputs. This is
the same workflow with different inputs. Each final bundle is a PPTX, the
complete assembled supervision JSON with five work records and the bound
independent audit artifact, and the readable Markdown report derived from that
JSON. The Markdown is an additional reading surface, never a replacement or a
second fact source.


## Execution and research generation

Infer content responsibility from the user's task and the maturity of supplied
material, not from word count, the presence of an attachment, or a mandatory
report/decision/SOP classification. New production runs record
`brief.preflight.generation_mode` as `execution`, `research`, or `mixed`.
This is an internal content decision, independent of Library availability; do not present a setup questionnaire or request permission
to do the research/content work inherent in the task. State the approach
briefly and proceed. Older artifacts without this field remain supported.

- Execution: when substantive content is supplied and the task is to convert
  it into a deck, preserve its meaningful facts, numbers, qualifications,
  relationships and instructions. Organize, condense and clarify without
  reducing detailed evidence to large slogans. Track coverage through the
  existing source IDs, page responsibilities and Copy units; place necessary
  supporting detail in appropriate pages or requested notes/appendices.
  Complete routine transitions directly. Flag contradictions and substantive
  unknowns; do not invent facts or launch unrelated research simply to satisfy
  a workflow. Honor an explicit request to retain wording or structure.
- Research: when given a topic, question or incomplete material, first identify
  what must be understood, actively gather credible evidence, examine contrary
  explanations and relevant responses, compare definitions/time windows/units,
  and synthesize mechanisms, implications and remaining uncertainty. Develop
  substantive content before allocating slides or designing large headlines.
  Use exact sources and meaningful limitations; website count, elapsed time,
  word count and slide count do not establish depth. When tools cannot obtain
  needed evidence, report the concrete gap and limit the claim instead of
  pretending research was completed.
- Mixed: use execution for mature sections and research for unresolved ones.
  Record their scope in existing brief constraints/page notes and preserve
  their different content responsibilities. Routine editorial gaps do not
  justify rewriting a supplied argument or restarting the whole deck.

Management reports, decision proposals, SOPs and related archetypes are optional
reasoning aids, not mandatory categories, enumerations or approval gates.
`material_type`, `management_stage`, `narrative_archetype` and
`narrative.management_stage_path` may be omitted or described in task-specific
terms. Optional confirmation metadata may truthfully say `agent-inferred`;
never invent user confirmation or request it merely to fill these fields.
Audience and intended outcome still guide the work and may be inferred when
the task supports it. This supersedes older type-selection instructions.

At the content handoff, Supervisor examines the actual supplied material and
Logic/Copy artifacts: execution preserves coverage and meaning; research
supports a substantive explanation with traceable evidence; mixed work does
both for the declared sections. Logic sends its result to both Copy and
Supervisor; Supervisor returns a hash-bound calibration finding for Copy to
absorb before locking final Copy. Copy and Art Direction, then Art Direction
and Output, use the same dual-recipient handoff and calibration rule. Return
thin or unsupported content to Logic, or losses of approved meaning to Copy.
Do not approve empty headings, repeated conclusions or a source list as a
substitute for analysis. Visual and final artifact checks remain necessary:
distinguish cover/body/closing layouts, inspect template text remnants, and
validate the real PPTX/report pair. A short narrative claiming success is not
the complete supervision report.

Discussion learning is a separate conversation route. A draft is a review
object, not a production artifact, and cannot enter retrieval. It records the
session, title, responsible stage (`logic`, `copy`, `art-direction`, or
`output`), consensus, applicability, limitations, provenance category
(`source-fact`, `user-experience`, or `joint-inference`), evidence references,
unresolved questions, language, purpose tags, and optional attachment metadata.
An attachment has a stable ID, filename, SHA-256, origin, rights, and a
page/section locator when known. The absence of an attachment or external
evidence remains visible.

Only the actual user's confirmation of the exact draft digest, including
attachment metadata and hashes, may cross the commit boundary. Agreement does
not make an interpretation an externally verified fact. A changed draft or
attachment needs a new confirmation. Committed revisions are immutable and
name their parent explicitly; there is no silent last-writer-wins update.
Publish the knowledge, confirmation, attachment metadata/hashes, and the
existing-format Provider index as one complete verified snapshot. Readers may
retrieve only that snapshot. A failed, concurrent, or stale-parent commit
leaves the previous verified snapshot usable; a missing store is unavailable,
not an empty successful Library.

Logic owns the substantive meaning of every page. Before slide allocation,
develop a concise business explanation connecting current operation and actors,
motivation and stakes, target state, change mechanism, options, evidence,
conditions and uncertainty. Use where/where-to/how as a reasoning lens, not three
mandatory slides. Test the explanation as if the audience had not read the chat.
Can it explain who replaces whom, which function remains, why the change helps,
and what could invalidate the recommendation? Resolve these gaps before Copy.
When more research cannot change a material decision or uncertainty, synthesize.
Depth is assessed by the explanation, never by elapsed thinking time or prose length.

Copy makes that explanation precise and natural. Parallel semantics need not
force identical sentence grammar. Art Direction follows the master's Storyline
requirements; smaller supporting text beneath it is optional and has no reserved
slot that must be filled. Repetition of a visual structure is useful when it makes
comparison or progression easier. Explain purposeful repetition in existing
decision notes; do not vary layouts just to satisfy a diversity count.

Approval means a usable current revision and a truthful record of its open
issues. A later stage may propose an upstream correction; the responsible stage
updates its artifact and dependent outputs are invalidated. Routine reversible
corrections within the user's task do not require another user approval. Ask
only when a material business choice, scope or explicit no-delivery condition
needs it. Quality findings do not become passes merely because the artifact is
delivered.

## Supervisor calibration and independent audit

Supervisor is the run coordinator and calibration layer. It initiates the task,
keeps the shared acceptance contract visible, evaluates each stage handoff and
returns concrete findings for the next owner to accept, partially accept or
decline with a reason. It does not write Logic, Copy, Art Direction or Output
content, and it does not perform the independent final audit.

Output sends the completed PPTX and its object/render evidence to Supervisor
and to the shared Independent Auditor module. The Auditor reads the original
user request, the acceptance rules and Supervisor's commitments/changes, then
checks the actual written file and renders. It returns an
`io.clayz.presentation.independent-audit/1.0` artifact. The Auditor may use the
same locked CompositeIndex, but it has no separate learning silo or retrieval
engine. If the host cannot provide an isolated model/process or a fresh context,
the available review context may be used only with explicit disclosure of that
limitation; it must not be described as true process independence.

Supervisor preserves the Auditor's findings and decides release under the
user's delivery policy. Binding, identity, format and evidence-integrity
failures prevent a verified pair; quality findings, unavailable optional
knowledge and deferred target-application checks remain reportable and may be
delivered. The default is to deliver a binding-complete artifact with its
issues; only an explicit user no-delivery rule adds a quality-finding blocker.

## Stage work records and full work report

Create work records while doing the work, not from memory at final delivery.
Each stage saves an immutable task-local artifact revision, writes a brief
record draft describing observable work, decisions, checks and remaining
issues, then uses the existing publisher CLI to bind actual file bytes:

```text
python scripts/publish_supervised_pair.py record-stage --stage logic --draft logic-work-draft.json --challenge run-challenge.json --artifact package=logic-package.v1.json --output logic-work.v1.json
# optional richer evidence: --artifact work-notes=logic-work-notes.md
```

Draft fields are `summary` (nonempty), `decisions` (string array), `checks`
(nonempty array of `name`, `status`, `evidence_roles`), and `open_issues`
(string array). Check status is `pass`, `fail`, or `deferred`; pass requires
actual file evidence named by an artifact role. Record conclusions and
observable decisions, not private chain-of-thought. When a stage has richer
task-local notes, attach them through the existing artifact mechanism as
`work-notes` (JSON or Markdown, using the exact `--artifact` spelling exposed
by the current core). Notes may capture the task question, evidence and source
trace, counterevidence, assumptions, uncertainty, storyline, copy, design
decisions, calibration response, actual output, audit observation, release
reason, or a limitation. They are optional evidence attached while the work is
done; they are not a new schema, approval step, source of facts, or invitation
to fill a fixed template. The publisher binds the note bytes and the assembled
report names their presence or absence.

The script supplies run binding, timestamp, absolute artifact paths, sizes and
SHA-256; never hand-fill these as substitutes for executing the script. A
binding, identity, format or evidence-integrity failure cannot authorize the
next stage. A quality `fail`, open issue, deferred check, or omitted work note
may continue when it is named with evidence and the delivery policy allows it;
none may be relabeled `pass`. Missing notes are recorded as `not-recorded`.
The report must never claim a complete work history when a relevant stage,
decision, or observation was not captured; continue to deliver a binding-
complete result with the limitation disclosed when policy permits.

For any consequential quantitative comparison, Logic's existing artifacts and
record decisions/checks/evidence roles identify the source or reference, metric
and unit, observation period, scope, and denominator. Mark the comparison as
comparable, limited, or not comparable using those existing fields. If windows
differ, obtain genuinely comparable evidence or describe the figures separately
with a visible qualifier; heterogeneous totals do not support inferred growth,
share, or ranking. Copy preserves the qualifier, Art Direction places it beside
the chart, Output verifies the actual final text and render, and Supervisor
reviews key comparisons against the source. When there is no numeric content,
create no dummy comparison record.

Use fixed production stage order and real primary artifact roles:

| Stage | Required recorded artifacts |
|---|---|
| logic | `package`: its immutable Logic package |
| copy | `package`: the separate final Copy package retaining approved Logic |
| art-direction | `plan`: the real plan, including page-to-template layout mapping |
| output | `pptx`, `qa`, `inventory` (object inventory), and available `render-*` evidence or an explicit `deferred`/`not-run` render observation |
| supervisor | `draft`: its coordination/reconciliation report draft, the same final `pptx`, and the `auditor` artifact bound as `auditor_artifact` |

The optional `work-notes` artifact is additive to the primary roles above. It
should carry only information observed in the current task and should be
attached at the handoff where the judgment occurred. Do not recreate a missing
note from a later stage's memory or infer completeness from a populated
primary artifact.

For each stage after Logic, add `--previous-record <immediate-predecessor.json>`
to `record-stage`. Before starting the next stage, run `check-records` with
`--challenge <run-challenge.json>` and repeated `--record` arguments for the
complete available prefix, beginning with Logic. The check verifies file
bytes, chain, task, calibration bindings and ready findings. Missing binding
evidence returns to its owner; do not continue by writing an optimistic
summary. Quality findings remain visible and can travel with the current
revision. After a revision, retain old files, record the new revision and
refresh only affected downstream records; do not mutate artifacts already bound
by an earlier record.

After the four production records and the actual final deck are available,
Supervisor receives the independent audit artifact (the stage-five `auditor`
role) and writes its own coordination/reconciliation draft and work record. The
Auditor's draft and report are separate: Supervisor does not claim to be the
independent auditor or reconstruct missing work. Use the current core's
`assemble-report` with five ordered `--record` files, the primary artifacts,
the optional bound `work-notes`, the final PPTX evidence, runtime/config inputs,
and the `auditor_artifact`/`independent-audit/1.0` evidence. All paths refer to
actual task files. The collector assembles the new report3.6 JSON from the
primary artifacts and records, attaches the top-level `work_report` and
canonical `work_report_sha256`, includes actual PPTX statistics plus extracted
page text and speaker notes when observed, preserves the three Supervisor
calibrations and their downstream decisions, and derives the readable Markdown
report from that JSON. It then validates the assembled report before emitting
the result. The exact option names remain those exposed by the installed core;
do not invent a parallel collector.

The full work report is a durable explanation of the run, not a verbose copy of
the deck or a reconstruction of scattered administrative tables. It should let
an unfamiliar reader understand the task and acceptance requirements, evidence
and sources, contrary evidence, assumptions and uncertainty, storyline and
meaningful exclusions, final copy, page-level design intent, the three
calibration rounds and what each downstream owner absorbed, actual generated
PPTX facts, Independent Auditor observations, release decision, limitations
and improvements. The stage's notes provide richer context where it was
actually captured; the collector supplies deterministic facts from the primary
artifacts and work records. Professional judgment remains in the stage or
Supervisor record; scripts only bind, count, extract and aggregate.
The Markdown renderer should organize the available material into a readable
account of evidence, decisions and results, omit empty claims, and show the
reason or limitation where a section is unavailable. A key listing, raw JSON
dump, or generic old summary is not a complete work report. Missing historical
records must be labeled `not-recorded`; that label means the evidence was not
captured, not that the earlier work can be declared undone.
Keep external source and upstream snapshot identity, locator, rights and hash
trace in the task-local evidence. Task facts and work notes belong to the
task-local records and derived report; do not write them into the public plugin
source or treat the public source as a task report.

Publish only that assembled report3.6 JSON and its deterministically derived
`work-report.md` with the final PPTX through the existing publisher after the
independent audit binding and release timestamp check. The manifest records
`work-report.md` in its `derived_files` collection and binds its path and hash
to the formal report without creating a circular report hash. New runtime packs
use this path; old artifacts remain readable for historical audits. Do not handwrite a second final report, alter
Auditor findings, or patch installed validators/configuration thresholds to
obtain a pass. Report an actual script or evidence failure with its owner and
needed correction. A binding-complete report may be published with accurately
recorded quality issues under the default delivery policy, but absent notes or
unobserved checks remain disclosed as `not-recorded`, `deferred`, or
`uncertain` as applicable.

Before final delivery, run the current `verify-handoff` command against the
newly published bundle. It verifies the explicit PPTX, supervision JSON and
`work-report.md` candidate paths against the manifest. Use only its returned
paths, hashes, task/run identity, and PPTX statistics/page-text/notes summary in
the final response; never glob
for an older JSON or Markdown report. A returned path is evidence of selection,
not permission to hide a mismatch. An old report that contains only a short
summary is evidence-incomplete; that does not prove the earlier stages were not
performed. Distinguish `not-recorded` from a factual claim that work did not
occur.

## Artifact-led Library iteration

Keep the user-facing production flow continuous: content (Logic and Copy),
layout and composition (Art Direction), then editable PPT production (Output).
Supervisor evaluates stage handoffs and calibration at these transitions. The
Independent Auditor checks the actual final objects and renders; Supervisor
consumes that artifact for release. These are separate responsibilities, not
five isolated one-pass jobs. The same agent may execute them by explicitly
switching modules and artifact ownership; separate agents are optional when the
host and task authorize them.

For each production stage, use this loop before approving its current revision:

1. Read applicable source facts, definitions, user constraints and required brand
   rules first. Form a provisional argument, copy draft, visual hypothesis or
   implementation plan. It is a revisable proposal, not an answer to defend.
2. Name the concrete question that could improve it: a missing mechanism,
   ambiguous phrase, unclear comparison, weak hierarchy or implementation risk.
   Query the existing stage Library through the locked Index for that question.
3. Read the relevant source passage, method or case detail, not just its index
   title, tags, summary or hash. For visual cases inspect the actual available
   image or rendered page; metadata alone cannot substantiate visual comparison.
   Test fit against this audience, evidence, information relationship, load and
   master. Look for counterexamples as well as support for the initial proposal.
4. Adopt, adapt or reject on that basis. Update the owned artifact when warranted;
   a well-supported unchanged draft or an honest no-match is valid. Never invent
   a reference, force adoption, or import unrelated facts from a design example.
5. Verify the changed artifact against its page job and upstream constraints.
   Repeat only for a remaining material question, using existing cumulative
   retrieval budgets. Stop when further lookup will not change a decision; if a
   required fact remains unresolved, constrain the claim or return the gap.

Keep one compact decision note per material question in the existing artifact
notes or finalized receipt rationale: question; before-state; source/receipt ID
and precise passage or case pointer; applicability and adoption/rejection reason;
after-state (or unchanged); observed check and any pending check. Reference copy
IDs, slide IDs or implementation objects. Record decision summaries, not private
reasoning or copied Library bodies. Reuse these notes in the full work report
when they were captured; do not introduce another index, scoring system, or
fixed story type. The report collector may present the notes under useful
headings such as task, evidence, story, copy, design, calibration, actual,
audit, and release, but the headings are a readable organization aid rather
than a quota or mandatory narrative formula.
Index verification proves availability. Only the inspected source and observable
artifact change/check can support a claim of knowledge use or improvement.

Selecting another eligible record inside the already inventoried and locked
Provider pool is normal stage retrieval, not a new resource inventory or a new
user approval. A genuinely new Provider, snapshot, external asset pool, route or
configuration returns to the root for an explicit revision and affected evidence
invalidation. Do not silently mutate an existing lock or relabel a new asset as
an already authorized resource.

## Revision and review across stages

Approval applies to an artifact revision, not an irreversible stage boundary.
When a downstream check exposes an upstream problem, send the concrete defect,
affected slide/copy IDs and desired outcome to the earliest responsible stage.
Logic changes meaning or page sequence; Copy changes wording; Art Direction
changes visual hierarchy or composition; Output changes technical realization.
The owner updates its artifact, validates it and refreshes dependent hashes and
checks. Preserve superseded evidence; do not present it as current. Reuse only
unchanged portions whose dependencies still match. A content revision does not
itself require another environment scan or a different renderer.

Supervisor reviews content usefulness before layout, the page-specific visual
plan before full production, and actual objects/renders before delivery. Review
the artifact first, then the Library decision notes. Ask whether the reference
actually resolves the stated problem, whether an alternative was rejected for a
task-relevant reason, and whether the revision introduces a new conflict. Record
the outcome concisely in existing decision notes/checkpoints. Formal mediation
or a user question is needed only for a material business choice, scope change
or explicit no-delivery condition; a quality finding can remain open and be
delivered. Supervisor assigns repair and rechecks when useful; it does not take
over another stage, edit the Auditor artifact or create its own learning Library.

An improvement loop is not permission for endless rebuilding. Inspect targeted
prototypes when a material layout or implementation uncertainty warrants them;
reuse evidence and batch the final build. Distinguish pre-approval exploration
and responsible-stage revision from the configured bounded technical repair
cycle. Exhausting a budget does not turn an unresolved defect into a pass.

## Provider and source revision rules

A required Provider must be reachable and its snapshot verified. This is distinct
from requiring one record from every Provider to be adopted. Query available
sources for actual questions. An empty selection with a specific non-applicability
or knowledge-gap explanation is valid; it cannot claim complete knowledge coverage.
Unresolved facts still limit claims and must be resolved if needed for the task.
Human admission, permissions, source hashes, and no invention remain required.

Source revisions and plugin releases are separate. bootstrap_owner_learning.py
creates immutable snapshots for each manifest/source-set revision, and caches
unchanged parsed sources. Preserve old snapshot paths for existing tasks. A changed
source is admitted through the existing owner manifest workflow, not automatically
promoted by generation. Optional expected_sha256 binds admission to exact bytes.
Never revise the Provider lock in an already-running task without a new revision.

## Measured execution

Set performance_budget.enforcement to advisory for normal tasks; use hard only
for explicit user limits. Budgets guide resource allocation; they do not certify
quality or justify removing required evidence. A professional judgment has no
automatic pass merely because the file satisfies its schema.

Use scripts/task_runtime.py:

- checkpoint: derive file hashes and next-phase state after an actual completed stage.
- snapshots: assemble immutable Logic/Copy/Art Direction snapshots from files;
  insert that output into the final report programmatically, without rewriting it.
- check: measure command execution and append receipts. With --reuse, reuse a
  deterministic check only when its inputs and outputs match. Include checker
  scripts, dependencies, config, fonts and renderer identity in declared inputs.
  Do not cache live queries, native application acceptance, or professional review.

Share exact final render files between Output, Supervisor and the Independent
Auditor when the locked render route is available. Review is independent;
rendering need not be duplicated. For local edits rerender affected pages when
the route is available; global master, font, renderer or theme changes
invalidate all affected pages. Before final delivery, verify that the render
evidence covers the final deck, including cover and closing, when rendering was
executed. If rendering is unavailable or unselected, record `deferred` or
`not-run` coverage and its limitation; do not invent pixels or block a written
PPTX solely because no render was available. Never treat --help or import
success as evidence that a production workflow completed.

## Independent review

The Independent Auditor first reads the user request and the actual deck,
without relying on upstream pass claims. It evaluates understanding, evidence
and decision usefulness, then typography, overlap, wrapping, hierarchy and
master fidelity. Supervisor compares the returned findings with stage plans to
identify the earliest responsible stage and decide release. A registered
failure pattern can help diagnosis but is not required to observe a defect.
Document concrete observations; pending evidence stays pending. Assemble
mechanical report fields with scripts; keep actual reasoning outcomes and
findings concise but sufficient for an unfamiliar reader to follow the task,
evidence, decisions, actual artifact and release. A richer report records more
of the real work when notes exist; it does not justify inventing detail after
the fact.

## Trial acceptance

Use the same source material, model settings and available knowledge in baseline
and plugin trials. Measure task completion time, repeated calls and renders;
evaluate whether a reader can explain the initial situation, stakes, recommendation,
mechanism and conditions. Check required cover/closing, master Storyline, wrapping,
overlap and traceable claims. Repeat trials to avoid treating one fast run as proof.
Report automated checks, host installation, and real-deck outcomes separately.
