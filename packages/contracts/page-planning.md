# Copy relationships and Art page planning — v0.19.0

New runs use content package **3.4** and Art plan **2.3**. Package 3.3 and
Art 2.1/2.2 remain historical replay contracts; never relabel old evidence.

## Copy supplies meaning relationships

Tell Art what each body passage explains or supports. State its local heading
ownership, shared ownership across headings, or explicit absence of local
heading ownership and its page-level purpose. An omitted relationship is
unknown, not evidence that a passage is independent. Explain relationships
among headings, including whether the content establishes parallel subjects,
sequence, conditions or another supported relationship. Same heading levels
and array order alone establish none of these relationships.

Record this separately from the text units, in each page's
`content_relationships`. Keep the text document's five roles unchanged:

```json
{
  "heading_relationships": "H1 is the entry action; H2 and H3 describe two supporting responsibilities. The source does not establish a strict sequence between them.",
  "body_relations": [
    {"copy_id":"B1","heading_ids":["H2"],"purpose":"Explains the contribution of the second responsibility and supports the page judgment."},
    {"copy_id":"B2","heading_ids":["H2","H3"],"purpose":"States a condition shared by both responsibilities."},
    {"copy_id":"B3","heading_ids":[],"purpose":"Qualifies the evidence for the whole page, without local heading ownership."}
  ]
}
```

This is a synthetic relationship example, not a layout template. Cover each
`body` ID exactly once. `heading_ids` is always explicit: one heading, multiple
headings, or `[]`; references identify headings on the same page. `purpose`
explains the role in natural language. Annotation relations may also be supplied
when useful. `body_relations:[]` is valid on a page without body text. Explain
the absence of local headings in `heading_relationships` when appropriate.
One heading may own both direct body text and child headings. Describe the child
relationship in `heading_relationships` and point the direct body's `heading_ids`
to that parent; body ownership is allowed at any heading level, not only leaves.
Art decides how to present this mixed hierarchy.
Do not invent a body for every heading or constrain Art's editable objects,
containers, styles, spatial reading order or shape boundaries.

Resolve a paragraph into multiple bodies as finely as coherent meaning permits;
one heading can own any number of bodies. Use existing `purpose` text to explain
each passage's concrete contribution and material dependency on another body,
such as supplying evidence for a judgment or qualifying its scope. A generic
"explains H1" is insufficient as an editorial explanation. Keep essential
subjects, connectors and conditions, and read the split text continuously.
These are semantic dependencies, not a visual order or an object-count command.
Art may compose several bodies in one paragraph/object while keeping them clear.

## Art plans the whole page before declaring objects

Read the entire Copy document and its relationships. Explain the page's central
message, available content groups and different passage functions, then decide
the composition, reading path, hierarchy and spatial weight that suit them.
Discuss consequential element treatments, including what stays concise, what
needs explanation, what belongs together and what should be prominent. Return
ambiguous meaning to Copy rather than treating placement as a semantic ruling.

Consider whether ordinals, labels, synthesized headings, emphasis or a slogan
would help. Record useful additions and their approved content basis; a decision
to add nothing is valid. Art may create additive expressive wording grounded in
the approved meaning. Keep approved Copy unchanged. Replacement text goes to
Copy; new facts or changed substantive relations go to their upstream owner.

Look for mutually supporting functions in one element or coherent visual unit.
For a genuine process, a block's pointing shape or interlocking arrangement can
carry both content and direction, permitting separate arrows to be omitted.
Line, type, shape, position and color can jointly communicate relationships.
Choose from the actual content and readable space; no arrow ban, compulsory
chevron, equal-size group rule or element-count target is introduced. Explain
important semantic containment separately from native editing groups: visual
nesting and shared page IDs do not themselves declare a PPTX parent/group.

Save the actual page planning **before refining native-object specifications**.
Use prose, not a layout menu or an aesthetic score. The planning draft has
ordered `slides`, with `slide_id` and:

- `page_message`: the page judgment and intended first understanding;
- `content_analysis`: content groups, ownership, roles, density and known gaps;
- `composition`: overall arrangement, reading path, emphasis and reasons;
- `element_strategy`: how consequential elements or combinations serve meaning;
- `addition_decision`: whether additions help and why;
- `expression_additions`: `[]` or items with `text`, `purpose`, and valid local
  `source_copy_ids` for their approved basis.

The fields preserve readable decisions and traceability, not private reasoning.
No prose quota or prescribed layout establishes quality.

```bash
python scripts/stage_documents.py record-planning --package copy-package.json \
  --plan page-planning-draft.json --output page-planning-r1.json
```

The command validates Copy, binds the exact Copy hash and package identity,
stamps its actual recording time, and refuses to overwrite a record. Proceed to
image drafts and matching object specifications. Inspect actual color drafts
and sequence, revise affected planning and design in new immutable revisions,
then lock the approved design:

```bash
python scripts/stage_documents.py lock-design --package copy-package.json \
  --plan art-plan-draft.json --planning page-planning-r1.json \
  --output art-plan-approved.json
```

Art 2.3 `page_planning` binds the original planning file by absolute path,
SHA-256 and byte count, plus exact base64 bytes and their decoded `content` for
portable inspection. Its recording time must precede the design lock. This
establishes recording order, not the order of private thought or an independent
attestation that no object was explored earlier. Do not retrofit missing
pre-design evidence after seeing the final PPTX. Output reads the planning,
complete drafts and matching specifications and preserves the Art baseline.

## Audit the planning and the actual realization

Use the existing Supervisor and Independent Auditor reports, observations and
delivery policy. Do not add a sixth stage or an aesthetic approval gate.
Each `design_comparison.slides` entry adds four observed checks:

- `page_planning`: actual recorded page decisions and chronology limitations;
- `content_relationships`: faithful expression of Copy ownership and relations;
- `expression_additions`: usefulness, approved basis and absence of new claims;
- `planned_realization`: whether objects, drafts and final renders realize the
  planned reader experience, including readability and actual attention.

Each uses `status:pass|fail|uncertain` and a concrete `observation`. Missing or
unobserved evidence is uncertain, with its limitation stated, never a fabricated
pass. Fail/uncertain checks bind report issue IDs and the earliest responsible
owner (`logic`, `copy`, `art-direction` or `output`); a report with such findings is not
clean. Check planning even when final render comparison is deferred; rendered
realization remains uncertain. Preserve independent findings unchanged.

Field presence, explanatory prose, object counts and faithful implementation do
not certify art quality. Read the actual page and check that the intended
grouping, hierarchy and reading path work. Route ambiguous meaning to Copy,
unsupported or ineffective design to Art, and implementation drift to Output.
Keep the original planning bytes and derived readable planning in the existing
stage documents and handoff ZIP; the report must survive loss of source paths.
