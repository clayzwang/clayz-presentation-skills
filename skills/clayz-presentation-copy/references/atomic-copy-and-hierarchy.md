# Atomic copy and hierarchical writing

## Read the tree before the sentence

List `node_id -> primary_copy_id -> text` before drafting a slide. A sentence that states both a parent category and its children may flatten the hierarchy.

### Colon test

For “Label: A, B, C,” ask:

1. Is the label a parent concept of A/B/C?
2. Are A/B/C peer items or ordered steps?
3. Does each item need its own explanation, icon, owner, data, or action?

If any answer is yes, assign separate `copy_id` values to the label and each child. A colon may remain inside a complete sentence, but it must not carry an unmodeled hierarchy.

### Prepare for punctuation-light expression

The visual layer should carry hierarchy and relationships that punctuation often simulates. Copy first separates `label: content`, `condition: result`, or `option: number` into mappable parent, child, condition, evidence, and conclusion units. Then remove colons, semicolons, slashes, and parentheses that exist only to imitate layout. Downstream stages may use position, area, alignment, nesting, connectors, convergence, charts, or tables; Copy chooses none of them.

### Comma test

When commas, slashes, “and,” or similar conjunctions join items that can be executed, compared, or tracked independently, split them into peer atomic units. Preserve fixed terms and indivisible phrases.

## Titles and storylines

- A title answers “What is the most important judgment on this slide?” Prefer a conclusion over empty labels such as “Overview” or “Next steps.”
- A storyline answers “How does one sentence connect the claim to the body?” It is one complete, single-line, verbatim-locked sentence.
- Title and storyline may map to the same root node but use different `copy_id` values. The title is normally the root's primary copy; the storyline is supplemental.
- Do not paraphrase the title in the storyline or concatenate the body list into a long sentence.

### Title-mode routing

| Slide task | `title_mode` | Writing approach |
|---|---|---|
| Fact or overview | `factual-status` | State object, period, and status without exaggerating causes |
| Operating diagnosis | `analytical-judgment` | Conclusion plus key comparison or concentration |
| Mechanism or policy | `mechanism-rule` | Rule change, operating mechanism, and behavioral effect |
| Action or decision | `action-directive` | Who acts on which gap and how the action is tested |
| Transition or section | `transition-assertion` | One directional judgment that moves the audience forward |
| Training or SOP | `instructional-action` | Concrete operation and checkpoint for the slide |

Titles are not always short. A dense operating slide may use “topic label + complete judgment”; a transition slide should be brief and directional. Preserve intentional breaks rather than shrinking text to force one line.

## Parallel peers

Assign every sibling group a `grammar_signature`.

| Signature | Structure | Example |
|---|---|---|
| `verb-object` | Verb + object | Improve onboarding; clarify permission defaults |
| `noun-category` | Noun category | Onboarding guidance; permission settings |
| `problem-impact` | Problem + impact | Insufficient features limit stage fit; unclear entry reduces adoption |
| `metric-value` | Metric + display value | Activation 62%; weekly retention 41% |
| `stage-action` | Stage + key action | Pilot: validate rules; rollout: replicate mechanism |

Within a group, check part of speech, subject, tense, voice, granularity, punctuation, and approximate length. Length variation is not automatically wrong, but a four-word label beside three explanatory sentences usually means the hierarchy was not separated.

## Numbers and labels

Do not bury numbers in generic sentences. Split a KPI into at least metric label, display value, and unit. Place benchmark, period, and definition in adjacent annotations or footnotes. Copy locks displayed values and punctuation; Output controls spatial relationship and visual weight.

## Intentional line breaks

Keep `text` as standard text without newline characters. Record deliberate break positions as character indices. Never split a number from its unit, a proper noun, entity, product, quantifier, negation, or fixed phrase. If automatic wrapping damages meaning, Output adjusts width or typography tokens, or returns the issue upstream; it does not rewrite copy.

## Series language

- Preserve fixed segment, product, role, metric, and stage names in Logic-locked order.
- Retain a recognizable series motif in titles while stating each slide's new judgment.
- Progressive-reveal slides may repeat established short labels but not long explanations.
- A policy series may progress through upgrade -> policy design -> expected effect.
- From/To copy states old constraint, rule change, behavior change, and result; “complex -> simple” is not a mechanism.
- Outside a meaningful series, do not replicate a hollow “four-word label + explanation” template.

## Remove generic AI wording

- Remove empty boosters such as enable, empower, comprehensively, continuously, and further unless they have a verifiable meaning.
- Avoid giving every child the same hollow slogan-plus-explanation structure.
- Give actions objects, judgments evidence, and targets a deadline or measurement basis.
- Do not invent a third item merely for visual completeness.
- Do not simulate three hierarchy levels inside one text box with colons, semicolons, and line breaks.
- If repeated `label: sentence` patterns appear, check for an unseparated hierarchy, mapping, or calculation.
- Do not replace an unresolved dilemma or trade-off with a campaign slogan.

## Return conditions

Return to Logic when a parent cannot summarize its children, siblings cannot share one grammar, one node carries two semantic roles, copy becomes valid only after adding new facts, title strength exceeds evidence, or the slide has two content centers that do not share one claim.
