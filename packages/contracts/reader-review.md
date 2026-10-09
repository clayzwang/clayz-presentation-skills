# Reader review — v0.20.0

Read this contract with [reader quality](reader-quality.md). Supervisor schedules
two reader reviews inside the existing five-stage workflow: after Copy has saved
its current text and before Copy-to-Art calibration, and after Output has saved
the actual final renders. These reviews answer whether the audience can explain
the subject, mechanisms and supported differences from the visible material.

## Dispatch and input boundary

For a deck task, this contract explicitly calls for delegation to a fresh reader
agent/context when the host provides that capability. Root uses the host's actual
dispatch tool with **no inherited conversation** (for example `fork_turns="none"`
when supported). The final reader must be a different fresh context from the Copy
reader. A new role label, subprocess, JSON file or model name is not sufficient.
Observe the host capability; do not claim it is absent without checking it.

Use `scripts/reader_review.py prepare` to build the allowed input directory.
Send only its `reader-input.json` and, for final review, its numbered page PNGs.
Keep the packet manifest, package, research, prior feedback, work notes, Art
rationale, author assessment, speaker notes and review history with Supervisor.
Visible citations and qualifications remain in the actual text/images. Final
reading uses actual final page pixels, not the Art draft or extracted prose.
The builder projects allowed Copy fields and strips image metadata; it does not
judge whether a neutral brief or visible wording is substantively unbiased.

The brief contains only `audience`, `purpose`, `task`: a neutral description of
the original task and intended reader, without the author's proposed answer,
expected differences or suggested defects. Do not coach the reader to reproduce
the author's conclusion. The reader first reads titles as a sequence, then all
visible content, and retells the core meaning, mechanisms and comparisons in
their own words, citing pages/wording and where guessing is required.

Limit reader tools/files to this input when the host permits. Record actual
access as `host-restricted`, `instruction-only` or `unavailable`. Instruction-only
access can reduce inherited-context bias but does not establish filesystem or
network isolation. Save a capture of the real host dispatch output. A normalized
host receipt binds `host_tool`, `context_id`, `production_context_id`,
`history_inherited: false`, `access_scope`, exact `input_files` (input JSON then
assets) and a `raw_receipt` file reference. Normalization does not turn a
self-declaration into host evidence. Never fabricate these values or a response.

When fresh dispatch is unavailable, record the actual shared-context review as
`same-context-limited` with its limitation. When reading cannot run, record
`not-run`, a reason and no response. The same-context record still discloses
context IDs, inherited history and access scope; `host_receipt` may be null.
Unavailable final rendering can use `--unavailable-reason` with the final PPTX.
These gaps remain `incomplete-evidence`, not a reader-quality pass, and follow
the existing delivery policy without an extra user permission checkpoint.

## Freeze first understanding, then reconcile evidence

The first response contains:

- `assessment`: `understood`, `understanding-gaps` or `insufficient-input` — an
  actual professional judgment, never generated from structural validation.
- `title_reading`: what the title sequence communicates or fails to communicate.
- `understanding`: entries with `question`, `answer`, `slide_ids`,
  `visible_evidence` and `uncertainty`. Derive questions from the neutral task and
  pages, rather than copying the author's hidden outline.
- `findings`: entries with `finding_id`, `slide_ids`, `copy_ids` (may be empty
  for image-only reading), `statement`, `reader_impact`.

`record-first` saves this response and actual context into a new immutable file.
Only after that capture may the second pass read Logic, Copy, Art, sources and
QA. Read the complete substantive evidence and identify the earliest owner:
missing answers or unsupported differences → Logic; unclear or procedural
wording → Copy; unclear grouping/attention in the approved draft → Art; deviation
from the approved draft → Output. Retain Supervisor's missed-detection finding
where warranted. The reader's uncertainty is not itself proof of factual error.

`reconcile` binds the first-read file and second-pass evidence. Each first finding
gets exactly one disposition with `finding_id`, `owner_layer`, `status` (`open`
or `disputed-with-evidence`), `explanation`, `evidence_refs` drawn from the bound
evidence. Evidence may dispute an interpretation; it cannot erase what the reader
actually understood. Repair through the owning stage and re-read the revised
artifact in a fresh context. Link prior immutable reviews with `--previous-review`;
record changes and repair results in existing work notes/calibration findings.
Never relabel an old review as coverage of new bytes or backfill a pre-Art review
after Output. A review that finds no defect does not require an invented edit.

## Commands and bindings

```bash
python scripts/reader_review.py prepare --phase copy --package /task/copy.json --brief /task/reader-brief.json --directory /task/reader-copy-input --output /task/reader-copy-packet.json
# Host dispatch happens here, using only reader-copy-input, without history.
python scripts/reader_review.py record-first --packet /task/reader-copy-packet.json --context /task/reader-copy-context.json --response /task/reader-copy-response.json --output /task/reader-copy-first.json
python scripts/reader_review.py reconcile --first-read /task/reader-copy-first.json --dispositions /task/reader-copy-dispositions.json --evidence /task/logic.json --evidence /task/copy.json --output /task/reader-copy-review.json
```

The context JSON has `execution_mode`, `context_id`, `production_context_id`,
`history_inherited`, `host_receipt` (file reference or null), `access_scope`,
`limitations` (text array). Fresh execution modes are `separate-context`,
`same-model-new-context`, `separate-process`; fresh mode requires a matching real
host receipt. For not-run, omit `--response` and supply `--reason`.

Final preparation adds `--phase final --pptx /task/final.pptx --renders
/task/render-manifest.json`. The render manifest binds `pptx_sha256` and ordered
`slides`, each with `slide_id`, `path`, `sha256`, `bytes`. These are actual render
receipts, not generated claims. The input builder checks the current ordered
page coverage and pixel equivalence; existing Output QA establishes render provenance.

Bind both reconciled reviews to the existing Independent Auditor artifact:
`--source-record reader-review-copy=/task/reader-copy-review.json` and
`--source-record reader-review-final=/task/reader-final-review.json`. Include both
in `--expected-source-kind` along with package, plan, qa and inventory and all
other actual kinds. New configuration requires both records, including honest
unavailable records. Historical audits remain readable under their recorded
configuration. The work report collects the original retelling, context, packet,
dispositions and prior-review references; technical fidelity and reader
observations have distinct results in that same report.

The validators check input projection, byte/task/revision bindings, chronology,
declared dispatch evidence and preservation of findings. They do not certify
human-reader effectiveness, model identity, host honesty or language quality.
