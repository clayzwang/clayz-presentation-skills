# Subject research, evidence reasoning, and Logic approval

## Contents

- [1. Understand the subject](#1-understand-the-subject)
- [2. Build a source and evidence ledger](#2-build-a-source-and-evidence-ledger)
- [3. Normalize terms and metrics](#3-normalize-terms-and-metrics)
- [4. Form conclusions that survive challenge](#4-form-conclusions-that-survive-challenge)
- [5. Turn conclusions into decisions and actions](#5-turn-conclusions-into-decisions-and-actions)
- [6. Prepare a handoff-ready Logic task](#6-prepare-a-handoff-ready-logic-task)
- [7. Special content types](#7-special-content-types)
- [8. Final review](#8-final-review)

## 1. Understand the subject

Turn “research is needed” into testable knowledge questions rather than broad topic searches.

| Layer | Required question | Typical material |
|---|---|---|
| Context | Why now, and what happened before? | History, project records, policy evolution |
| Actors and objects | Who is affected and how are they related? | User groups, data entities, roles, teams, processes |
| Mechanism | Why does the system behave this way? | Product rules, business flow, incentives, physical or technical principles |
| Measurement | What exactly does each number count? | Definitions, denominators, periods, scope, deduplication, refresh frequency |
| External environment | What changed in the market, industry, policy, or technology? | Official documents, industry data, primary research |
| Disagreement | Which claims have contrary evidence or alternative explanations? | Counterexamples, alternative hypotheses, stakeholder views |
| Action | Under what conditions can which action be taken? | Authority, resources, timing, risks, prerequisites |

Maintain a knowledge-needs list with the question, why it matters, current evidence, planned source, completion state, and which conclusion would be constrained if unresolved. Research items that can change the main argument or claim strength before illustrative enrichment.

### Expand enough, then stop

Completeness is not unlimited expansion. For a summary statement, drill down to the smallest evidence set that supports judgment. For “the next five months,” list the five monthly targets, baselines, assumptions, and results. For “a combination of two options,” list each option's efficiency, stability, cost, and boundary. Stop when added detail would change none of the main conclusion, relationship judgment, decision choice, or final expression. Keep useful audit detail in working papers, notes, or an appendix.

### Research boundaries

- Prefer user-owned primary material, raw data, formal rules, and authoritative sources.
- For unstable facts, retrieve the current version and retain publication date, effective period, and access date.
- Verify legal, financial, contractual, and safety claims against authoritative sources rather than marketing copy.
- Use a relevant specialist skill first for a specialized subject; Logic turns the verified findings into an accurate and understandable argument.
- When verification fails, record a hypothesis or information gap instead of filling it with common sense.

## 2. Build a source and evidence ledger

Record at least `source_id`, name, type, author or publisher, date, locator, supported claims, limitations, and whether the source is primary.

### Source priority

1. Raw data, executed contracts, official policies, regulatory documents, official product terms, and user-confirmed facts;
2. formal company reports, authoritative statistics, primary research, audited or reproducible calculations;
3. credible industry research and professional interpretation;
4. news, interviews, and secondary reviews;
5. unverified screenshots, rumors, and model memory.

Lower-priority sources may suggest hypotheses. They cannot alone support strong causal claims, precise numbers, or high-risk recommendations.

### Evidence states

| State | Definition | Permitted wording |
|---|---|---|
| Source fact | Directly stated by a source with a clear basis | “As of July, A was 25%.” |
| Direct calculation | Derived from known data with an explicit formula | “On the same basis, A/B is 1.46.” |
| Interpretation | Supported but not the only explanation | “This may relate to … and requires further validation.” |
| Causal judgment | Mechanism, timing, magnitude, and counterevidence are sufficiently supported | “X is one of the main drivers of this period's change.” |
| Forecast | Conditional claim about the future | “If condition C holds, … is expected.” |
| Recommendation | Choice proposed against objectives and constraints | “Prioritize …” |
| Target | Desired state chosen by management | “Set a target of …” |
| Hypothesis | Explanation still requiring evidence | “To validate: whether X causes Y.” |
| Missing data | Missing and not safely imputable | “[Missing: regional-scope data]” |

## 3. Normalize terms and metrics

For every metric, record its name, business definition, formula, numerator, denominator, time basis, population, account or record deduplication rule, unit, decimals, source, update time, limitations, and display format.

Common errors include:

- mixing monthly, year-to-date, and rolling-12-month measures;
- mixing users, accounts, orders, sessions, amounts, and value;
- comparing year-on-year and month-on-month rates with different denominators;
- showing attainment without the target version or elapsed-time basis;
- confusing percentage change with percentage-point change;
- interpreting a definition change as a business change;
- displaying rounded shares that appear not to total 100%.

Calculate, reconcile, and freeze numbers before writing conclusions. Attach conditions to conditional calculations. If active users fell 25% year on year while revenue for the same cohort rose 10%, per-user revenue rose about 46.7% only when both measures cover the same users, period, and scope. Otherwise state only that user scale and revenue moved in opposite directions.

## 4. Form conclusions that survive challenge

### Five analytical questions

1. **What happened?** Scale, trend, structure, gap, anomaly, and uncertainty.
2. **Where is it distributed?** Business unit, segment, product, touchpoint, time, region, and scenario.
3. **Why?** Quantified drivers versus unverified hypotheses.
4. **What does it mean?** Implications for goals, risks, opportunities, and resource allocation.
5. **What follows?** Choices, priority, ownership, timing, and validation metrics.

### Conclusion workflow

1. Write a fact-only sentence.
2. Decompose structure and contribution to locate the change.
3. List at least two alternative explanations.
4. For each explanation, state what evidence should exist if it is true.
5. Search for supporting and contrary evidence.
6. Decide whether evidence supports fact, association, major driver, or causality.
7. Record boundaries, counterexamples, and unresolved items.
8. Form the page claim, action objects, and logical hierarchy. Leave final titles to Copy.

### Causality checks

- **Mechanism:** through which intermediate steps does X affect Y?
- **Timing:** does X precede Y?
- **Magnitude:** can the size of X explain the size of Y?
- **Alternatives:** what else could create the same result?
- **Counterexamples:** where does X occur without Y, or Y without X?
- **Consistency:** is the direction stable across units, periods, and samples?
- **Intervention evidence:** does Y change when X is introduced or removed?
- **Boundary:** for which scope, period, and conditions does the claim hold?

When causal evidence is weak, replace “because” with “occurred alongside,” “may be affected by,” or “the leading hypothesis to validate is.”

| Evidence | Maximum defensible claim |
|---|---|
| One cross-section or anecdote | Describe the fact and raise a question; do not generalize causality |
| Same-definition trend across periods | State trend and turning point; mechanism is still required for causality |
| Quantified contribution decomposition | State where the main contribution or drag originates |
| Multiple sources plus consistent mechanism and counterevidence | State “one of the main drivers” |
| Reliable experiment, quasi-experiment, or strong intervention | Use causal wording inside the proven boundary |

## 5. Turn conclusions into decisions and actions

### Decision content

Prepare the decision required, available options, evaluation dimensions, recommended option, benefit, cost, risk, prerequisites, irreversible points, review timing, and exit plan. Do not stop at “strengthen” or “improve.”

### Action content

An executable action contains the object, owner, action, completion time, target state, metric, review frequency, resources, and dependencies. `action_traceability` points to the gap, evidence, or mechanism node that directly supports it. If evidence supports diagnosis but not a solution, propose a validation action before a large rollout. Do not approve an L3 management requirement without evidence mapping.

### From case to mechanism

A case includes the initial context, core conflict, action, result, why it worked, applicability, non-transferable elements, and next step. Convert a case into a testable mechanism; never present one successful sample as a universal rule.

### From review to new learning

An experiment review states the original hypothesis, intervention, observation, belief retained or rejected, new learning, and next validation metric and window. Observation without a changed understanding is a project record, not an experiment-learning loop.

## 6. Prepare a handoff-ready Logic task

Logic does not write final titles, body copy, punctuation, line breaks, or speaker notes. Before Copy receives the package, ensure that:

- the root claim has the necessary subject, object, time, scope, evidence strength, and boundary;
- each child node owns one object, action, evidence item, mechanism, result, or limitation;
- peer groups use the same decomposition dimension and can become parallel copy;
- labels, values, units, and comparison bases are semantically separable;
- evidence definitions, challenge boundaries, and transition intent have an explicit logical source without pre-writing the final script.

If hierarchy depends on a colon, comma, or manual line break, the message tree is incomplete. Split nodes before handing the issue to Copy.

## 7. Special content types

### Training and frontline communication

- Explain “why this matters to me” before method. Pair each concept with a real situation or micro-case.
- Use ordinary language without changing product, policy, or data meaning.
- State the exercise context, task, output, and reference judgment; do not merely write “discuss for five minutes.”

### Policy and product

- Separate current rule, change, affected parties, effective period, exceptions, example, and required action.
- Obtain price, service level, permission, and exception terms from formal material. Label assumptions in examples.

### Executive speech and large-event material

- Ground strong judgments in facts. Surround slogans with evidence or action.
- Use restrained, truthful emotion; do not invent crisis, victory, or consensus.

### Data analysis

- Include comparison basis, anomalies, contribution decomposition, management meaning, and next validation.
- Normalize period, definition, population, and calculations before combining related numbers.
- Do not prescribe chart types. State the comparison, priority numbers, and true semantics.

## 8. Final review

- Can every core number be traced to a source or formula within 30 seconds?
- Does every causal word pass the causality checks?
- Does every recommendation follow from a gap and goal?
- Does every action map to evidence, an owner, a metric, and a review date?
- Would deleting any slide create a clear information gap?
- Can adjacent slides be connected by a causal, question, time, or decision relationship?
- Are metric, role, product, and segment names consistent throughout?
- Can Copy receive every node without depending on punctuation, line breaks, or visual position?
- Can the audience restate the overall argument, section judgments, and next step?
- Is any content still expected from the visual designer? If yes, Logic is not ready.
- Does every “future N periods,” “average,” “overall,” or “combined” claim have visible detail and a formula in the working evidence? If not, expand it before approval.
