# Architecture pattern library

Use these cards after selecting and reviewing sources from `architecture-source-index.json`. Each card captures a reusable relationship grammar, not a visual template.

## Contents

1. Outcome-to-foundation house
2. Evidence ladder
3. Build-time and run-time split
4. Producer-platform-consumer mesh
5. Platform plane and workload plane
6. Cross-cutting control rails
7. Maturity or medallion progression
8. Semantic mediation core
9. Human decision gate
10. Governed feedback flywheel
11. Investigation orchestration loop
12. Hybrid boundary map
13. Landing-zone hierarchy
14. Lifecycle conveyor
15. Capability decomposition map
16. Observability and quality overlay

## Pattern cards

### 1. Outcome-to-foundation house

- **Question it answers:** What outcome is supported by which ordered capabilities and shared controls?
- **Relationship grammar:** outcome roof → capability floors → operating foundation, with shared controls spanning the floors.
- **Source signals:** IBM capability models, SAP North Star, Oracle data platforms, and cloud landing-zone architectures.
- **ChatBI adaptation:** place decision quality and business action at the roof; place investigation, executable semantics, data computation, and infrastructure below it.
- **Synthesis move:** derive floor order from dependency and evidence transformation, then choose roof, pillars, and foundation labels from the current business problem.

### 2. Evidence ladder

- **Question it answers:** How does raw enterprise reality become an accountable decision?
- **Relationship grammar:** event or record → governed data → business meaning → evidence → hypothesis → judgment → approved action.
- **Source signals:** analytics pipelines, document-intelligence flows, AI governance, and data-product architectures.
- **ChatBI adaptation:** make provenance, effective time, metric grain, counter-evidence, and uncertainty visible between retrieval and judgment.
- **Synthesis move:** write one testable verb on every transition; if a transition cannot be named, split or remove it.

### 3. Build-time and run-time split

- **Question it answers:** Which work prepares knowledge, and which work answers a live question?
- **Relationship grammar:** ingestion/indexing/evaluation path beside query/retrieval/reasoning/response path, connected through versioned knowledge assets.
- **Source signals:** IBM, Google Cloud, Oracle, NVIDIA, and Microsoft RAG architectures.
- **ChatBI adaptation:** separate metric definition, semantic versioning, test cases, and source indexing from interactive investigation and decision support.
- **Synthesis move:** draw the shared artifact in the center and show who releases it into runtime.

### 4. Producer-platform-consumer mesh

- **Question it answers:** How can distributed owners share trustworthy data without a central bottleneck?
- **Relationship grammar:** domain producers ↔ self-service platform/catalog ↔ consumers, bounded by federated governance.
- **Source signals:** Google Cloud data mesh, AWS data mesh, Oracle decentralized platform, and Databricks governance.
- **ChatBI adaptation:** show business domains as owners of definitions and evidence; show the cognitive platform as enablement and arbitration, not as the owner of business truth.
- **Synthesis move:** name the contract exchanged across every boundary: metric, data product, evidence package, or approved action.

### 5. Platform plane and workload plane

- **Question it answers:** What is centrally enabled, and what remains specific to each business use case?
- **Relationship grammar:** shared platform plane below or beside multiple workload planes, with inherited services and guardrails.
- **Source signals:** Azure landing zones, Google Cloud landing zones, NVIDIA AI factories, and Databricks platform architecture.
- **ChatBI adaptation:** keep identity, observability, model access, semantic registry, evidence ledger, and release mechanisms shared; keep questions, hypotheses, decision rights, and actions workload-specific.
- **Synthesis move:** label inheritance arrows separately from runtime data flows.

### 6. Cross-cutting control rails

- **Question it answers:** Which concerns constrain several stages rather than appearing as one box?
- **Relationship grammar:** vertical pillars or horizontal rails for governance, security, quality, provenance, cost, and observability across multiple layers.
- **Source signals:** IBM data fabric, AWS analytics lens, SAP North Star, Oracle data platform, and Databricks governance.
- **ChatBI adaptation:** use controls to show who defines, enforces, observes, challenges, and rolls back—not merely that governance exists.
- **Synthesis move:** connect each rail to the exact stages it constrains and annotate the mechanism.

### 7. Maturity or medallion progression

- **Question it answers:** How does an asset become more usable and trustworthy over ordered stages?
- **Relationship grammar:** raw/bronze → conformed/silver → curated/gold → semantic or action-ready output.
- **Source signals:** Microsoft Fabric, Snowflake pipelines, Databricks, AWS analytics lens, and Oracle lakehouse.
- **ChatBI adaptation:** progress from source record to reconciled fact to metric-ready evidence to decision-ready claim.
- **Synthesis move:** name the quality gain and accountability gain achieved at every stage.

### 8. Semantic mediation core

- **Question it answers:** What converts technical data into stable business meaning?
- **Relationship grammar:** sources and models on one side, users and decisions on the other, with objects, relations, metrics, policies, lineage, and effective time in the middle.
- **Source signals:** SAP Knowledge Graph, Snowflake semantic views, IBM data fabric, Oracle analytics, and enterprise catalogs.
- **ChatBI adaptation:** distinguish terminology matching from executable semantics that can calculate, reconcile, trace, and version business meaning.
- **Synthesis move:** show at least one example object-relation-metric chain crossing the semantic core.

### 9. Human decision gate

- **Question it answers:** Where does model assistance stop and organizational accountability begin?
- **Relationship grammar:** model proposal + evidence + uncertainty → named human role → approve/challenge/revise/escalate → accountable action.
- **Source signals:** IBM AI governance, Microsoft document review, SAP validation, Apple security and deployment responsibility boundaries.
- **ChatBI adaptation:** models may retrieve, calculate, compare, hypothesize, and recommend; named roles adjudicate definitions, conflicts, exceptions, and action.
- **Synthesis move:** draw the decision right as a gate with explicit inputs, possible outcomes, and owner.

### 10. Governed feedback flywheel

- **Question it answers:** How do outcomes improve the system without silently rewriting truth?
- **Relationship grammar:** production outcome → observation → attribution → expert adjudication → regression test → versioned release → monitored effect → rollback path.
- **Source signals:** IBM monitoring, NVIDIA data flywheel, Microsoft DataOps, Google evaluation subsystems, and SAP validation.
- **ChatBI adaptation:** feed back evidence and adjudicated corrections into metrics, semantic contracts, retrieval assets, and investigation methods separately.
- **Synthesis move:** show the artifact that changes at every feedback step and the role that authorizes the change.

### 11. Investigation orchestration loop

- **Question it answers:** How does an open-ended business question become a bounded analysis?
- **Relationship grammar:** context → hypotheses → tool calls → evidence and counter-evidence → uncertainty check → stopping condition → recommendation.
- **Source signals:** agentic AI, agentic RAG, AI-Q research agents, and modular LLM orchestration.
- **ChatBI adaptation:** treat querying as one tool inside investigation; include contradiction handling, scope control, and a stopping criterion.
- **Synthesis move:** expose the loop while keeping business approval outside it.

### 12. Hybrid boundary map

- **Question it answers:** Where do data, control, and responsibility cross organizational or infrastructure boundaries?
- **Relationship grammar:** bounded zones for enterprise, cloud, domain, partner, or edge; typed connections for data, control, identity, and feedback.
- **Source signals:** Oracle multicloud, IBM hybrid, AWS industrial edge, Google hybrid foundations, and Apple deployment.
- **ChatBI adaptation:** distinguish remote data access, replicated evidence, federated query, and authorized business action.
- **Synthesis move:** label both the crossing mechanism and the owner on each boundary.

### 13. Landing-zone hierarchy

- **Question it answers:** How do policies and shared services scale across environments and business workloads?
- **Relationship grammar:** enterprise or tenant root → platform foundation → environment or domain zones → workload instances, with inherited policies.
- **Source signals:** Microsoft and Google Cloud landing zones, Oracle compartments, and NVIDIA scale units.
- **ChatBI adaptation:** map enterprise cognitive governance to shared services, then show separate production spaces for domains, use cases, and release stages.
- **Synthesis move:** separate organizational hierarchy from runtime flow with different connector semantics.

### 14. Lifecycle conveyor

- **Question it answers:** How is an architecture built, released, operated, observed, and changed?
- **Relationship grammar:** discover → define → build → test → release → operate → observe → improve.
- **Source signals:** Microsoft DataOps, SAP methodology, NVIDIA deployment, and cloud Well-Architected frameworks.
- **ChatBI adaptation:** carry semantic definitions, evidence tests, investigation methods, and user-facing experiences through the lifecycle as distinct artifacts.
- **Synthesis move:** attach owner, entry condition, output artifact, and feedback destination to every stage.

### 15. Capability decomposition map

- **Question it answers:** What enterprise abilities are required without implying a process sequence?
- **Relationship grammar:** outcome-aligned capability domains → level-two groups → level-three abilities, with dependencies shown separately.
- **Source signals:** IBM GenAI capability model, SAP data capability work, and cloud adoption frameworks.
- **ChatBI adaptation:** use for scope and readiness; pair it with an evidence ladder or lifecycle when causality matters.
- **Synthesis move:** organize by responsibility and outcome, then add only the dependencies that change a decision.

### 16. Observability and quality overlay

- **Question it answers:** How is reliability demonstrated across the architecture?
- **Relationship grammar:** metrics, traces, lineage, quality tests, cost, risk, and user outcomes observed across build and runtime paths.
- **Source signals:** NVIDIA RAG sizing, cloud Well-Architected frameworks, IBM governance, and Databricks quality guidance.
- **ChatBI adaptation:** observe source freshness, semantic version, calculation reproducibility, retrieval evidence, answer uncertainty, decision latency, and realized outcome.
- **Synthesis move:** place observable signals at the mechanism they measure, then aggregate them into a management view.

## Combining cards

Select one **spine** pattern that determines the reading path, one **control** pattern that makes accountability visible, and optionally one **evolution** pattern that explains change over time. A ChatBI house commonly combines:

- outcome-to-foundation house as the spine;
- semantic mediation core and investigation orchestration loop as interior logic;
- cross-cutting control rails and human decision gate as accountability;
- governed feedback flywheel as evolution.

Record the selected cards, source IDs, adaptation decisions, and discarded alternatives in the task-local research ledger.
