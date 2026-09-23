# Architecture

## Plugin entry modes

The same-name ChatGPT composite Skill now exposes these modes globally in Chat
and Work. Its native Library bridge uses the shared discussion and snapshot
modules in task scratch, then delegates actual Library writes/readback to the
observed host tools. A generated policy places the optional confirmed provider
within the existing Library root; it does not replace existing private sources.

The local plugin supports resource inspection, discussion-based knowledge
learning, and PPT enablement. The existing five production stages remain intact.
The shared Independent Auditor module is attached after Output for the final
file/render audit; it is part of the Supervisor publication unit and does not
add a sixth production stage.
See [the shared system contract](../packages/contracts/plugin-system.md).
Discussion and storage are supporting capabilities; they do not add a sixth
presentation stage. Maintenance governance remains outside the plugin.

Confirmed knowledge and attachments live in an owner-selected external Library.
Immutable, verified snapshots supply ordinary IndexRecord providers to the
existing CompositeIndex. Drafts never enter production retrieval. This local
filesystem implementation does not assert a live ChatGPT Library connection.

## Acceptance and audit replay

One hash-bound task acceptance contract is created before Logic and preserved
through all five stages. Supervisor records the user's objective, hard and soft
requirements, source precedence and delivery policy without universalizing one
user's preferences. Logic, Copy and Art Direction are sent to their next owner
and Supervisor with hash-bound calibration records; each next owner records its
decision before locking its artifact. Output sends the actual PPTX/object/render
evidence to Supervisor and the Independent Auditor. The final supervision
report binds the Auditor's `independent-audit/1.0` artifact, embeds immutable
Logic, Copy and Art Direction decision snapshots, traces every acceptance
requirement through final evidence, reconciles relevance-ranked retrieval, and
records generation efficiency. Quality findings can be delivered when bindings
are complete; missing or mismatched evidence still prevents a verified pair.
If no render route exists, the Auditor records deferred/not-run render coverage
and the written PPTX may still be delivered with that limitation.
The original stage artifacts remain the source of truth; embedded snapshots are
read-only hash-bound copies, not a parallel editing surface.

## Governance as enablement

The five stages give the model better questions, evidence, decision authority, tools, and feedback. They are not a substitute for professional judgment and must not reduce work to filling fields. Logic receives the deepest reasoning responsibility; private knowledge strengthens its evidence and methods but never replaces synthesis. Copy improves expression without repairing missing logic. Art Direction respects the active master's required Storyline treatment and decides only whether optional supporting copy adds value. Output binds the approved content to the master and executes one approved plan efficiently. Supervisor coordinates and calibrates the stages; the Independent Auditor challenges the actual final file and render without inheriting upstream pass claims. Supervisor preserves those findings and owns the release decision under the user's delivery policy.

Efficiency compresses transport and removes repeated retrieval, evidence copying, writes, and renders. It must never mean shallow Logic reasoning. Validators protect facts, authority, provenance, and observable quality; they do not prescribe one universal narrative, storyline placement, or slide shell.

## Reader understanding (v0.17.1)

[Reader-quality guidance](../packages/contracts/reader-quality.md) makes substantive explanation and natural language explicit across the same five stages. Existing work notes and findings carry the review; no new schema, word ban, brevity quota or automatic language score is introduced.

## Story-first and visual handoffs (v0.17.0)

See [the current handoff contract](../packages/contracts/story-visual-handoff.md).
Logic writes a complete story before pagination. Copy owns the page projection
used by existing renderers. Art Direction produces and locks image drafts plus
visual tags. Supervisor compares actual final renders against that baseline and
delivers the three real handoff documents with the images and audit evidence.

## Stage ownership

Production remains a continuous content -> layout/composition -> editable-PPT
flow. Each owner uses a provisional artifact, a concrete question, inspected
Library evidence, an applicability decision and a verified revision. Each
artifact is sent to its next owner and Supervisor; Supervisor returns a
hash-bound calibration before the next owner locks its revision. Output also
sends the actual PPTX and render evidence to the Independent Auditor. See
`packages/contracts/stage-enablement.md` at the repository root for the shared
iteration and dependency-invalidation policy. Separate responsibilities do not
require separate agents or prohibit evidence-driven upstream revision.

| Stage | Owns | Must not silently change |
| --- | --- | --- |
| Logic | audience, complete chaptered narrative, claims, evidence, qualifiers, semantic relationships | source facts or user constraints |
| Copy | pagination, page responsibilities, structured audience-facing wording, master-required Storyline, optional supporting copy, numbers, punctuation, intentional breaks, notes | logic, evidence status, chapter order or visual placement |
| Art Direction | locked full-deck image drafts, target coordinates, element specifications and tolerances, first visual, visual anchor, medium, area plan, semantic layout tree, optional supporting-copy treatment, rhythm | approved meaning, wording, or master-defined Storyline placement |
| Output | editable objects, coordinates, theme application, technical repair, final files | approved content or visual intent |
| Supervisor | task initiation, requirement/calibration coordination, evidence reconciliation, release disposition, and challenge record | any upstream or downstream artifact or Auditor finding |

The Independent Auditor is a shared post-Output review module, not an
additional production stage. It owns the actual file/render audit artifact and
returns it to Supervisor; it does not own a fifth learning silo or release
authority.

## Layout compilation layers

Theme and Visual Variant remain configuration and Art Direction concerns.
Registered Layout Contracts provide reusable semantic topology, while the
task-local Layout Tree binds approved Semantic Layout Tree nodes and copy IDs.
Art Direction specifies target coordinates and bounded adjustments in the task plan; Output realizes them and creates native objects. See
[`layout-contracts.md`](layout-contracts.md).

## Composition and dataset metadata layers

Registered Composition Patterns describe how approved semantic relations may
become spatial relationships, while Layout Contracts describe reusable semantic
topology. Art Direction owns both decisions but keeps them independent. A
Composition Plan is coordinate-free and receipt-bound; Output consumes it with
the independently approved Layout Contract or core Layout Tree. Supervisor may
use receipt-selected Failure Patterns only to diagnose rendered evidence and
route repair to the earliest responsible stage.

Reference and Sequence records are dataset-ready metadata, not bundled cases.
Their exporter excludes source text, media, coordinates, fonts, model features,
generated-artifact auto-admission, and automatic aesthetic truth. See
[`pattern-dataset-library.md`](pattern-dataset-library.md).

## Central configuration

All environmental and stylistic choices resolve from `config/default.json` or one explicit override. Skills may read the configuration but may not copy its values into their own instructions as fixed rules.

Resolution order:

1. Plugin-root `config/default.json`.
2. A readable saved personal configuration layer.
3. Explicit current-task overrides and user requirements.

The final resolved configuration hash belongs in every stage artifact as `configuration_sha256`.

## Distribution model

The source repository stores shared contracts and validators once. The Codex and marketplace plugin bundles five Skills around that shared root. The ChatGPT Skills host adapter compiles the same five stage sources and the shared Independent Auditor module into one publication unit with one root `SKILL.md`; detached uploads cannot share the root safely. This is a packaging transform, not another Public Core and not a sixth decision-making stage. v0.5.1 adds a deterministic runtime beneath Output rather than a sixth decision-making skill. It provides a public baseline adapter, one-shot preflight, route locking, bounded calls, and common plus operating-system packs. See [`runtime-architecture.md`](runtime-architecture.md).

## Portable knowledge model

The public distribution includes four stage learning areas—Logic, Copy, Art Direction, and Output—plus one shared source-and-index area. Supervisor and the Independent Auditor read the same locked evidence and route reusable observations to the earliest responsible stage; neither owns a fifth learning silo.

The default filesystem scaffold is empty and portable. It does not create or connect ChatGPT Library. Host adapters may map the same contract to another storage system, while human admission and no-auto-promotion remain invariant.

An observation becomes retrievable only after a separate human admission binds
its canonical hash. The rebuilt learning provider remains private and distinct
from the public built-in catalog. Retrieval benchmarks pin provider snapshots,
while migration converts only unchanged admitted legacy records. These feedback
and release-readiness services support the five stages; they do not add a sixth
stage or transfer approval authority. See
[`feedback-benchmark-release-readiness.md`](feedback-benchmark-release-readiness.md).

Every presentation run checks installed component consistency offline. Remote
release comparison belongs to explicit developer release checks; an installed
version need not equal any external host. A readable saved personal layer may
be reused within the same unified production path, and optional private
learning may be reused when an actual verified snapshot exists. Neither a
personal layer nor a Library locator creates a second runtime, resets the
master, or imposes a persistent-index prerequisite. Any derived private
execution index remains a runtime artifact, not another canonical knowledge
source.
