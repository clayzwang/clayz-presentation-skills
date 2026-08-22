# Reference-architecture synthesis method

Apply this method to capability houses, enterprise architecture overviews, data or AI platforms, and operating-system diagrams. Use it to turn a broad primary-source corpus into an independent, problem-specific architecture.

## Load the research resources

1. Read `architecture-source-index.json` for the reviewed 76-document official corpus.
2. Read `architecture-pattern-library.md` for reusable relationship grammars.
3. Create a task-local research ledger rather than copying source diagrams into the skill or deliverable.

## Method

### 1. Frame the architecture question

Write one sentence for each item:

- decision or operating outcome the diagram must support;
- audience and decision horizon;
- system boundary;
- transformation that must become understandable;
- named human roles that retain accountability.

Use these statements to choose sources and reject irrelevant visual complexity.

### 2. Build a balanced reading set

Filter the index by `focus` and `structure`. Start with sources closest to the problem, then add contrasting publishers and architecture families. For a broad benchmark, review the requested 50–100 distinct entries; for a focused page, select a smaller task set from the reviewed index.

Record for every selected source:

| Field | Purpose |
|---|---|
| `source_id` | link back to the reviewed index |
| `question_answered` | why this source belongs in the task set |
| `relationship_grammar` | layers, flows, boundaries, controls, loops, or ownership |
| `useful_move` | relationship worth adapting |
| `non_transferable` | vendor stack, brand, wording, icons, media, or coordinates |
| `decision` | adopt, adapt, contrast, or set aside |

### 3. Extract relationship evidence

For each diagram, describe its structure in plain verbs before thinking about layout:

- what enters and leaves;
- what transforms into what;
- what constrains several stages;
- who owns each definition or decision;
- where uncertainty, evaluation, or escalation appears;
- what returns as feedback and which artifact changes.

Cluster repeated relationships across publishers. A pattern becomes useful when it explains the current problem and can be expressed without vendor products or original visual treatment.

### 4. Select and combine pattern cards

Choose:

- one **spine** from the pattern library to establish the reading path;
- one **control** pattern to expose accountability;
- optionally one **evolution** pattern to explain learning, release, or feedback.

For a ChatBI house, a productive combination is:

- outcome-to-foundation house as the spine;
- evidence ladder, semantic mediation core, and investigation orchestration loop inside;
- cross-cutting control rails and a human decision gate around the interior;
- governed feedback flywheel returning outcomes to versioned artifacts.

### 5. Derive the house from the problem

Use seven structural roles as a working canvas:

| Role | Derivation question |
|---|---|
| Roof | What business outcome or decision promise closes the story? |
| Floors | Which capabilities form an ordered transformation rather than a noun inventory? |
| Pillars or rails | Which controls affect several floors, and through what mechanism? |
| Foundation | Which shared substrate makes the capabilities operable? |
| Upward path | How does enterprise reality become meaning, evidence, judgment, and action? |
| Return path | How do observed outcomes revise definitions, evidence, methods, or releases? |
| Decision gate | Which named role approves, challenges, revises, or escalates? |

Draft the relationship graph first. Then choose house geometry if it makes those relationships easier to read than a flow, mesh, or lifecycle.

### 6. Translate the graph into a slide

1. Allocate space in management reading order: outcome, transformation, controls, implementation.
2. Route the upward evidence path and return feedback path before placing rooms.
3. Give roof, floors, rails, foundation, and decision gate distinct visual jobs.
4. Use a small number of sub-capabilities to demonstrate each layer's responsibility.
5. Use native editable shapes and the user-approved theme.
6. Put source IDs and representative citations in speaker notes or the task source record.

### 7. Diagnose the draft

Ask the following questions and revise the relationship graph before polishing:

- Can a viewer explain why every floor sits where it does?
- Can a viewer follow one fact from source to action and back through feedback?
- Do governance, security, quality, provenance, and observability touch the mechanisms they influence?
- Is the boundary between model contribution and human accountability visible?
- Does the diagram express the current enterprise problem rather than a generic vendor stack?
- Can every adopted visual idea be traced to a source ID and a pattern-card adaptation?

### 8. Close the research ledger

Record:

- final source set and pattern cards;
- relationships adopted and alternatives discarded;
- task-specific labels and responsibilities;
- representative citations;
- gratitude statement for the referenced authors and teams;
- confirmation that no source diagram, wording, icons, brand identity, master, theme, media, or coordinates were redistributed.

## Source gratitude

The reviewed corpus includes public official work from IBM, Microsoft, Google Cloud, AWS, Oracle, SAP, NVIDIA, Databricks, Snowflake, and Apple. Thank you to the architects, technical writers, designers, engineers, reviewers, and documentation teams who made these materials available. Clayz uses the materials to study relationships and methods and redistributes none of their diagrams or branded assets.
