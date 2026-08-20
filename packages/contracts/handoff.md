# Cross-stage handoff

Every stage artifact carries:

- `origin_namespace: io.clayz.presentation`;
- the resolved `configuration_sha256`;
- its artifact type and approval status;
- SHA-256 bindings to every upstream artifact it claims to use;
- stable IDs for slides, claims, copy units, layout nodes, objects, and findings.

Downstream stages may challenge an upstream artifact with evidence. They may not silently replace its source of truth.

