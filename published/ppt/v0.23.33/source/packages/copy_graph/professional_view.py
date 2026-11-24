"""Read a Copy graph's professional content without following source paths.

This is a reading aid, not a graph replacement, validator, editor or quality
measure. Native identity and provenance checks still use the original graph.
"""
from copy import deepcopy

GRAPH_CONTRACT = "io.clayz.presentation.copy-graph/1.0"
VIEW_CONTRACT = "io.clayz.presentation.professional-content-view/1.0"
PAGE_FIELDS = ("id", "role", "storyline_id", "node_ids")
NODE_FIELDS = ("id", "kind", "level", "page_id", "claim_status")
EDGE_FIELDS = ("id", "sources", "targets", "types", "direction", "scope", "meaning")


def _fields(value, keys):
    if not isinstance(value, dict) or any(key not in value for key in keys):
        raise ValueError("Missing professional-content fields")
    return {key: deepcopy(value[key]) for key in keys}


def project(graph):
    """Return a detached semantic reading view; perform no file/network I/O."""
    if not isinstance(graph, dict) or graph.get("contract") != GRAPH_CONTRACT:
        raise ValueError("Expected an original Copy graph v1")
    for key in ("pages", "nodes", "connections", "main_chain"):
        if not isinstance(graph.get(key), list):
            raise ValueError("Expected original graph arrays")
    nodes = []
    for node in graph["nodes"]:
        value = _fields(node, NODE_FIELDS)
        if node["kind"] == "head":
            if not isinstance(node.get("text"), str):
                raise ValueError("Expected heading text")
            value["text"] = node["text"]
        elif node["kind"] == "body":
            content = node.get("content")
            if not isinstance(content, dict):
                raise ValueError("Expected structured body content")
            if content.get("type") == "text":
                if set(content) != {"type", "text"}:
                    raise ValueError("Unknown text content fields; do not silently omit meaning")
                value["content"] = _fields(content, ("type", "text"))
            elif content.get("type") == "table":
                fields = ("type", "values", "axes", "unit", "period")
                if set(content) - set(fields) - {"selection"}:
                    raise ValueError("Unknown table content fields; do not silently omit meaning")
                value["content"] = _fields(content, fields)
                selection = content.get("selection")
                if selection is not None:
                    if not isinstance(selection, dict) or set(selection) != {
                            "original_shape", "axis_indices", "reason"}:
                        raise ValueError("Unknown table selection context")
                    value["table_selection_context"] = _fields(
                        selection, ("original_shape", "axis_indices"))
            else:
                raise ValueError("Unsupported body content type")
        else:
            raise ValueError("Unsupported node kind")
        nodes.append(value)
    edges = []
    for edge in graph["connections"]:
        if not isinstance(edge, dict) or set(edge) != set(EDGE_FIELDS):
            raise ValueError("Unknown relationship fields; use the original graph")
        edges.append(_fields(edge, EDGE_FIELDS))
    return {
        "contract": VIEW_CONTRACT,
        "scope": (
            "Professional content reading only. Titles, body text, complete "
            "table values/axes/units/periods, page order, typed relationships, "
            "claim-status annotations and original partial-table coordinates "
            "are retained. Source spans/reasons, table selection rationale "
            "and author self-review are not shown. A claim-status annotation "
            "is producer context, not independent quality evidence. Selection "
            "rationale may contain scope explanations: consult the original "
            "graph whenever needed rather than inferring an exhaustive table. "
            "Keep the original graph for identity, provenance and all native "
            "handoffs. This view is not a new authoring input or a quality result."
        ),
        "pages": [_fields(page, PAGE_FIELDS) for page in graph["pages"]],
        "nodes": nodes,
        "connections": edges,
        "main_chain": deepcopy(graph["main_chain"]),
    }
