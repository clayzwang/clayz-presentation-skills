# Semantic page-logic model

## Purpose

Prove why content is grouped before downstream stages decide how the slide is drawn. A three- or four-level message tree shows depth but does not prove that categories and relationships are correct. This model blocks mixed abstraction levels, false relationships, and incomplete method chains.

## 1. Write a logic sentence without visual language

For every body slide, write one unbroken sentence:

> Who or what, through which mechanism, forms which relationship with which peer objects, and produces which result or action implication?

Do not use visual words such as left, right, above, below, circle, box, card, arrow, surround, or color. If the relationship cannot fit into one sentence, clarify the business relationship or split the slide before selecting a visual form.

Copy turns this sentence into a visible title and storyline. Logic locks semantics, not final wording or line breaks.

## 2. Type business objects

Choose the most specific semantic type for every object.

| Type | Identification question | Example |
|---|---|---|
| `channel-carrier` | Who carries delivery or contact? | Online entry, offline touchpoint, service team |
| `method` | How is an input converted into a result? | Onboarding, need identification, feature adoption |
| `principle` | Which rule constrains the method? | Establish first value before expanding use |
| `product` | What does the user buy or use? | Starter, Team, Enterprise plan |
| `project` | Which initiative organizes resources and actions? | Onboarding optimization, retention experiment |
| `scene` | In which real situation does the user appear? | First login, multi-user document |
| `entry-method` | How does guidance or service begin? | In-product guidance, onboarding questions |
| `exception` | What happens outside the normal path? | User needs only one feature |
| `user-segment` | Which users are addressed? | New users, team administrators |
| `need` | What does the user want to solve? | Fast onboarding, cross-team collaboration |
| `risk` | Which uncertainty must be managed? | Privacy, usability, adoption |
| `role` | Who owns or collaborates? | Adviser, specialist, delivery team |
| `action` | What does the actor do? | Ask, register, follow up |
| `capability` | Which repeatable capability is required? | Data recognition, professional delivery |
| `resource` | What does the method depend on? | Data, tools, budget |
| `metric` | How is it measured? | Activation, weekly retention, collaboration depth |
| `result` | What outcome is created? | Stable adoption, sustained retention |
| `stage` | Which real time or maturity stage? | Registration, activation, collaboration |

Use `other` only after defining the business meaning. Never use it to hide incomplete understanding.

## 3. Validate peers and parent-child structure

- Members of one sibling group use the same semantic type, granularity, and parent.
- Do not place a product beside a project, route, method, scene, entry method, exception, or result.
- Separate scene, entry method, and exception: what happened, how the actor enters, and what happens after deviation are different objects.
- If A governs B and C, A is the parent and B/C are peers. Do not flatten the governing statement beside its members.
- “Starter, Professional, Team, Enterprise” may sit under “cover collaboration needs at different scales.” The latter is a parent result or claim, not a fifth product.
- If four needs do not lead to one another, record them as equal peers. Do not invent order, cycles, or connectors.

## 4. Relationship grammar

Use a relationship only when business semantics prove it:

- `peer`: equal objects without direction;
- `contains`: whole contains parts;
- `supports` / `enables`: a tool, capability, or resource supports a method or result;
- `maps-to`: explicit mapping among segments, needs, risks, actions, or products;
- `sequence` / `transforms-to`: real temporal order or state transition;
- `cause`: evidence supports causality; otherwise mark a hypothesis;
- `condition`: the path is entered only when a condition is met;
- `feedback`: a result changes an earlier input or rule;
- `contrast`: objects are compared on the same dimension;
- `exception-to`: a boundary or exception limits the normal path;
- `evidence-for`: a fact, metric, or case supports a judgment.

Peer objects have no connection direction. Mapping is not automatically a process. Surrounding placement is not automatically a cycle. Numbering is not automatically sequence.

For `condition`, set `combination` to `all-of`, `any-of`, or `one-of`, and state the constraint in `logic_map.statement` and `do_not_change`. For example: “Both product and user-stage conditions must hold; do not rewrite them as sequential steps.” Reading order is not business order.

### Four-part state-transition contract

`transforms-to` is more than a visual old/new comparison. It must explain:

1. why the old constraint or incentive was insufficient;
2. which rule, resource, or responsibility changes;
3. how the change alters concrete behavior;
4. which result follows, for which scope and exceptions.

Without parts 2 or 3, use `contrast` and state that the page is only a same-dimension comparison.

## 5. Method chain

A method, SOP, operating principle, or action slide answers:

1. **What triggers it?** User signal, scenario, or prerequisite.
2. **What happens?** Actor action or question.
3. **What is identified?** Need, risk, gap, or opportunity.
4. **What does it map to?** Product, service, owner, or next action.
5. **How does it close?** Result, commitment, boundary, follow-up, or conversion.

A “three questions” method cannot stop at the questions. Map each row as `question -> identified need or risk -> corresponding feature or action`. If a link truly does not exist, explain why and reconsider whether the slide is a method page.

## 6. Operating systems and experiment learning

### Operability test

A map, model, mechanism, dashboard, or meeting page qualifies as an `operating-system` only when it contains:

- inputs: data, segment, signal, issue, or task;
- decision rules: classification, comparison, trigger, or trade-off;
- outputs: action, decision, ownership, or resource allocation;
- users: who uses it and in which context;
- cadence: refresh and meeting or action cycle;
- feedback: how results change the next input or rule;
- exceptions: where it does not apply or requires judgment.

Without key elements, call it a classification framework, relationship model, or static map.

### Experiment-learning contract

Model a review as `hypothesis -> intervention -> observation -> disconfirmed_belief -> new_learning -> next_test`. An observation becomes learning only when it states which belief was retained or rejected.

## 7. Cross-slide invariants and atomic handoff

When a segment, product, role, metric, or policy object repeats, declare which names, definitions, order, measurement basis, analytical axes, and groupings are invariant. Then state each slide's new evidence, level, or action. Logic does not prescribe repeated layout, but it identifies changes that would break comparison and repetition with no business reason.

- One node owns one semantic responsibility. Do not simulate hierarchy with pipes, repeated spaces, colon chains, or manual line breaks.
- Use numbering as a relation only for real steps or rankings. Ordinary peers use `peer`.
- Separate metric, value, unit, period, and benchmark so Copy can create atomic text.
- Keep sibling objects consistent in type, granularity, and decomposition dimension. Rebuild Logic when parallel copy is impossible.
- Keep boundaries, language limits, and sources in independent nodes or source fields rather than mixing them into the main judgment.

## 8. Handoff restatement test

Hide every visual idea and answer for each slide:

1. What is the most important method, judgment, or evidence?
2. Are primary categories peers at the same granularity and do they jointly support the claim?
3. To which primary object does every secondary explanation belong?
4. Which relationships are directed, and which are only peer or containment relationships?
5. For a method page, is the five-part method chain complete?
6. For From/To, are the old constraint, rule, behavior, and result complete?
7. For an operating system, are inputs, rules, outputs, users, cadence, and feedback present?
8. For a series, which objects remain invariant and what does this slide add?

Do not enter the page message tree or downstream expression design until every answer is clear.
