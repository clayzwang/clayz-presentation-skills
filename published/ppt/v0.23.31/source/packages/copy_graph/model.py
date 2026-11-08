"""Copy semantic graph v1.  No renderer, old Copy account, or layout imports.

Validation establishes structure and provenance, never editorial quality.
Relations are directed hyperedges. Parallel edges are intentional; their IDs
are independent of endpoints, so inclusion and reverse support can coexist.
"""
from __future__ import annotations

from collections import Counter, deque
from hashlib import sha256
from itertools import product
from pathlib import Path
import json
import math
import re

CONTRACT = "io.clayz.presentation.copy-graph/1.0"
RELATION_TYPES = frozenset(("并列", "包含", "因果", "递进", "对比", "时序", "流程",
                            "条件", "分支", "循环", "反馈", "关联", "依赖", "论证", "支撑"))
NODE_ID = re.compile(r"^(head|body)_[A-Za-z0-9_-]+$")
PAGE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*$")
CLAIMS = {"fact", "calculation", "interpretation", "guidance", "uncertainty"}
NODE_KEYS = {"id", "kind", "level", "page_id", "text", "content", "source_spans", "claim_status"}
EDGE_KEYS = {"id", "sources", "targets", "types", "direction", "scope", "meaning"}
GRAPH_KEYS = {"contract", "research_report", "pages", "nodes", "connections", "main_chain", "semantic_review"}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return sha256(canonical(value).encode()).hexdigest()


def file_ref(path):
    p = Path(path).resolve(strict=True)
    data = p.read_bytes()
    return {"path": str(p), "sha256": sha256(data).hexdigest(), "bytes": len(data)}


def read_ref(ref):
    if not isinstance(ref, dict) or set(ref) != {"path", "sha256", "bytes"}:
        raise ValueError("file reference must contain path, sha256 and bytes")
    if not Path(ref["path"]).is_absolute() or file_ref(ref["path"]) != ref:
        raise ValueError("file reference does not match actual absolute file bytes")
    return Path(ref["path"]).read_bytes()


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def strings(value, *, empty=False):
    return isinstance(value, list) and (empty or bool(value)) and all(nonempty(x) for x in value) and len(value) == len(set(value))


def source_segments(text):
    """Character offsets in the one original written report; no second account."""
    result = []
    for match in re.finditer(r"\S[\s\S]*?(?=\n\s*\n|\Z)", text):
        start, end = match.span()
        while end > start and text[end - 1].isspace():
            end -= 1
        result.append({"segment_id": f"report_{len(result)+1:04}", "start": start,
                       "end": end, "text": text[start:end]})
    return result


def array_shape(value):
    if not isinstance(value, list):
        if value is None or isinstance(value, (str, bool, int)) or isinstance(value, float) and math.isfinite(value):
            return ()
        raise ValueError("table cells must be finite JSON scalar values")
    if not value:
        raise ValueError("table dimensions cannot be empty")
    shapes = [array_shape(x) for x in value]
    if any(s != shapes[0] for s in shapes):
        raise ValueError("table must be a rectangular multidimensional array")
    return (len(value), *shapes[0])


def validate_table(table):
    if not isinstance(table, dict) or set(table) - {"type", "values", "axes", "unit", "period", "selection"}:
        raise ValueError("table body contains values, axes, unit, period and optional source selection only")
    if table.get("type") != "table" or not nonempty(table.get("unit")) or not nonempty(table.get("period")):
        raise ValueError("table needs its unit (or explicit unitless) and period (or explicit not applicable)")
    shape = array_shape(table.get("values"))
    axes = table.get("axes")
    if not shape or not isinstance(axes, list) or len(axes) != len(shape):
        raise ValueError("one named axis with source labels is required per table dimension")
    for i, axis in enumerate(axes):
        if not isinstance(axis, dict) or set(axis) != {"name", "labels"} or not nonempty(axis["name"]):
            raise ValueError("axis contains its source name and labels")
        if not isinstance(axis["labels"], list) or len(axis["labels"]) != shape[i] or any(not nonempty(x) for x in axis["labels"]):
            raise ValueError("axis labels must cover exactly its dimension")
    selection = table.get("selection")
    if selection is not None:
        if not isinstance(selection, dict) or set(selection) != {"original_shape", "axis_indices", "reason"}:
            raise ValueError("partial table needs original_shape, original axis_indices and a reason")
        original, indices = selection["original_shape"], selection["axis_indices"]
        if not isinstance(original, list) or len(original) != len(shape) or any(type(n) is not int or n <= 0 for n in original):
            raise ValueError("invalid original table dimensions")
        if not isinstance(indices, list) or len(indices) != len(shape) or not nonempty(selection["reason"]):
            raise ValueError("invalid table selection")
        for i, index in enumerate(indices):
            if not isinstance(index, list) or len(index) != shape[i] or len(set(index)) != len(index) or any(type(n) is not int or not 0 <= n < original[i] for n in index):
                raise ValueError("table selection must map every selected coordinate back to its original axis")
    return shape


def node_text(node):
    if node["kind"] == "head":
        return node["text"]
    content = node["content"]
    return content["text"] if content["type"] == "text" else ""


def validate_node(node, report_text):
    if not isinstance(node, dict) or set(node) - NODE_KEYS:
        raise ValueError("nodes carry semantic content, not geometry, font sizes or presentation instructions")
    if not all(k in node for k in ("id", "kind", "level", "page_id", "source_spans", "claim_status")):
        raise ValueError("node identity, type, level, page, provenance and claim status are required")
    if not nonempty(node["id"]) or not NODE_ID.fullmatch(node["id"]) or not node["id"].startswith(node["kind"] + "_"):
        raise ValueError("stable IDs must visibly distinguish head_ and body_ nodes")
    if "__" in node["id"]:
        raise ValueError("double underscore is reserved for derived native table locations, not semantic node IDs")
    if node["kind"] not in {"head", "body"} or type(node["level"]) is not int or node["level"] < 1 or not nonempty(node["page_id"]) or not PAGE_ID.fullmatch(node["page_id"]):
        raise ValueError("invalid node kind, level or page")
    if node["claim_status"] not in CLAIMS:
        raise ValueError("node must distinguish fact, calculation, interpretation, guidance or uncertainty")
    if node["kind"] == "head":
        if "content" in node or not nonempty(node.get("text")):
            raise ValueError("head requires its complete title text")
    else:
        if "text" in node or not isinstance(node.get("content"), dict):
            raise ValueError("body requires structured text or table content")
        c = node["content"]
        if c.get("type") == "table":
            validate_table(c)
        elif set(c) != {"type", "text"} or c["type"] != "text" or not nonempty(c["text"]):
            raise ValueError("text body contains exactly type and complete text")
    spans = node["source_spans"]
    if not isinstance(spans, list) or not spans:
        raise ValueError("every head/body must trace directly to the original Logic report")
    for span in spans:
        if not isinstance(span, dict) or set(span) - {"start", "end", "operation", "reason"}:
            raise ValueError("invalid original report span")
        a, b = span.get("start"), span.get("end")
        if type(a) is not int or type(b) is not int or not 0 <= a < b <= len(report_text):
            raise ValueError("report character offsets are outside the original report")
        mode = span.get("operation")
        if mode == "verbatim":
            if node_text(node) != report_text[a:b] or len(spans) != 1:
                raise ValueError("verbatim text differs from the original report")
        elif mode not in {"edited", "derived", "table-selection"} or not nonempty(span.get("reason")):
            raise ValueError("editing/derivation/table selection requires a concrete preservation explanation")
        if node["kind"] == "body" and node["content"]["type"] == "table" and mode not in {"table-selection", "derived"}:
            raise ValueError("array body must trace an original table selection or explain a derivation from report text")


def validate_edges(edges, nodes):
    if not isinstance(edges, list):
        raise ValueError("connections must be an array")
    ids, signatures = set(), set()
    for edge in edges:
        if not isinstance(edge, dict) or set(edge) != EDGE_KEYS:
            raise ValueError("connection requires ID, endpoint sets, types, direction, scope and specific meaning")
        eid = edge["id"]
        if not nonempty(eid) or eid in ids:
            raise ValueError("connection IDs must be unique; parallel edges have separate IDs")
        ids.add(eid)
        src, dst, types = edge["sources"], edge["targets"], edge["types"]
        if not strings(src) or not strings(dst) or set(src) & set(dst) or any(n not in nodes for n in src + dst):
            raise ValueError("connection endpoints must be known distinct nonempty node sets, without self loops")
        if not strings(types) or not set(types) <= RELATION_TYPES:
            raise ValueError("connection must name one or more of the fifteen agreed relation types")
        if edge["direction"] not in {"directed", "symmetric"} or edge["scope"] not in {"main", "page", "cross-page", "framing"} or not nonempty(edge["meaning"]):
            raise ValueError("connection direction, scope and actual meaning are required")
        if "包含" in types and edge["direction"] != "directed":
            raise ValueError("inclusion is directed; reverse support is a separate edge")
        signature = (tuple(sorted(src)), tuple(sorted(dst)), tuple(sorted(types)), edge["direction"], edge["scope"])
        if edge["direction"] == "symmetric":
            signature = (tuple(sorted((tuple(sorted(src)), tuple(sorted(dst))))), tuple(sorted(types)), "symmetric", edge["scope"])
        if signature in signatures:
            raise ValueError("duplicate connection; use distinct semantic types/direction rather than duplicate bookkeeping")
        signatures.add(signature)
        pages = {nodes[n]["page_id"] for n in src + dst}
        if edge["scope"] == "page" and len(pages) != 1:
            raise ValueError("a page connection cannot silently cross page boundaries")
    # Containment cannot cycle, while the full semantic graph can carry cycles
    # and feedback. Hyperedges are only expanded for this structural check.
    contains = {nid: set() for nid in nodes}
    for e in edges:
        if "包含" in e["types"]:
            for a, b in product(e["sources"], e["targets"]):
                contains[a].add(b)
    indegree = Counter(b for neighbors in contains.values() for b in neighbors)
    queue = deque(n for n in nodes if not indegree[n])
    visited = 0
    while queue:
        a = queue.popleft(); visited += 1
        for b in contains[a]:
            indegree[b] -= 1
            if not indegree[b]:
                queue.append(b)
    if visited != len(nodes):
        raise ValueError("title/content containment cannot cycle; use explicit feedback/cycle relations instead")


def connected(ids, edges):
    ids = set(ids)
    if not ids:
        return False
    neighbors = {n: set() for n in ids}
    for e in edges:
        ends = set(e["sources"] + e["targets"])
        if ends <= ids:
            for n in ends:
                neighbors[n].update(ends - {n})
    seen, queue = set(), [next(iter(ids))]
    while queue:
        n = queue.pop()
        if n not in seen:
            seen.add(n); queue.extend(neighbors[n] - seen)
    return seen == ids


def validate(graph, *, report_text=None):
    """Return binding/schema errors. Semantic and title quality need readers."""
    try:
        if not isinstance(graph, dict) or set(graph) != GRAPH_KEYS or graph["contract"] != CONTRACT:
            raise ValueError("complete Copy graph v1 required; old account/slide protocols cannot be authoring input")
        text = read_ref(graph["research_report"]).decode("utf-8")
        if report_text is not None and text != report_text:
            raise ValueError("graph is not bound to the exact supplied Logic report")
        items, pages, edges = graph["nodes"], graph["pages"], graph["connections"]
        if not isinstance(items, list) or not items or not isinstance(pages, list) or not pages:
            raise ValueError("actual nodes and pages are required")
        nodes = {}
        for n in items:
            validate_node(n, text)
            if n["id"] in nodes:
                raise ValueError("duplicate node ID")
            nodes[n["id"]] = n
        page_ids, mapped, storylines = set(), [], []
        for i, page in enumerate(pages):
            if not isinstance(page, dict) or set(page) != {"id", "role", "storyline_id", "node_ids"} or not nonempty(page["id"]) or not PAGE_ID.fullmatch(page["id"]) or page["id"] in page_ids:
                raise ValueError("page requires a unique identity, role, storyline and complete node list")
            page_ids.add(page["id"])
            ids = page["node_ids"]
            if not strings(ids) or any(n not in nodes or nodes[n]["page_id"] != page["id"] for n in ids):
                raise ValueError("each page must own its known nodes exactly once")
            mapped.extend(ids)
            h1 = [n for n in ids if nodes[n]["kind"] == "head" and nodes[n]["level"] == 1]
            if page["role"] == "content":
                if len(h1) != 1 or page["storyline_id"] != h1[0]:
                    raise ValueError("each content page has exactly one level-1 head/storyline")
                storylines.append(h1[0])
                levels = {nodes[n]["level"] for n in ids if nodes[n]["kind"] == "head"}
                if levels != set(range(1, max(levels) + 1)):
                    raise ValueError("heading levels must be generated layer by layer, without skipped levels")
                if any(nodes[n]["kind"] == "body" and nodes[n]["level"] == 1 for n in ids):
                    raise ValueError("body nodes hang below the storyline; peer head/body nodes start at level 2")
            elif page["role"] not in {"cover", "closing"} or page["storyline_id"] is not None or len(h1) != 1:
                raise ValueError("cover/closing have a framing title and do not contribute a storyline")
            if page["role"] == "cover" and i != 0 or page["role"] == "closing" and i != len(pages) - 1:
                raise ValueError("cover and closing must occupy their actual ends")
        if Counter(mapped) != Counter(nodes.keys()):
            raise ValueError("every node must appear exactly once in its page")
        if not storylines or graph["main_chain"] != storylines:
            raise ValueError("main_chain must list all content storylines exactly in page order")
        validate_edges(edges, nodes)
        adjacent = set(zip(storylines, storylines[1:]))
        actual_main = set()
        for e in edges:
            if e["scope"] == "main":
                if len(e["sources"]) != 1 or len(e["targets"]) != 1:
                    raise ValueError("a main-chain connection joins adjacent storyline heads")
                pair = (e["sources"][0], e["targets"][0])
                if pair not in adjacent:
                    raise ValueError("main chain must proceed in order; optional cross-page links have a separate scope")
                actual_main.add(pair)
        if actual_main != adjacent:
            raise ValueError("all adjacent storylines need explicit typed main-chain connections")
        incident = {n for e in edges for n in e["sources"] + e["targets"]}
        if incident != set(nodes) or not connected(nodes, edges):
            raise ValueError("no isolated node or disconnected logical island is permitted")
        for p in pages:
            scopes = {"page", "framing"} if p["role"] in {"cover", "closing"} else {"page"}
            local = [e for e in edges if e["scope"] in scopes]
            if not connected(p["node_ids"], local):
                raise ValueError(f"{p['id']}: every page node must connect into its storyline network")
        review = graph["semantic_review"]
        if not isinstance(review, dict) or set(review) != {"storylines", "information_preservation", "selection_and_omissions", "uncertainty", "relations"} or not all(nonempty(v) for v in review.values()):
            raise ValueError("Copy must record actual title, information, omission, uncertainty and relation review")
        return []
    except (ValueError, TypeError, KeyError, OSError, UnicodeError) as e:
        return [str(e)]


def require_valid(graph):
    errors = validate(graph)
    if errors:
        raise ValueError("; ".join(errors))
    return graph


def coverage(graph):
    """Source-range inventory, expressly not a semantic-retention score."""
    text = read_ref(graph["research_report"]).decode()
    return {"scope": "original report range use only; not information or design quality",
            "segments": [{**s, "referencing_nodes": [n["id"] for n in graph["nodes"]
                          if any(r["start"] < s["end"] and r["end"] > s["start"] for r in n["source_spans"])]}
                         for s in source_segments(text)]}


def review_projection(graph, phase):
    """Second-pass evidence only: exclude the author's own quality verdicts.

    Blind first-read packets still come from native reader_review.prepare.
    This neither authors new content nor hides the original Logic report.
    """
    require_valid(graph)
    if phase not in {'title','content'}:
        raise ValueError('review evidence phase must be title or content')
    ids = set(graph['main_chain']) if phase == 'title' else {n['id'] for n in graph['nodes']}
    return {'scope':'second-pass source/content evidence; author semantic review excluded',
            'research_report':graph['research_report'],
            'main_chain':graph['main_chain'],
            'nodes':[n for n in graph['nodes'] if n['id'] in ids],
            'connections':[e for e in graph['connections'] if set(e['sources']+e['targets']) <= ids]}


def scalar_text(value):
    if value is None:
        return "未提供"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def table_tokens(node):
    """Deterministic native text locations, not editorial decomposition.

    One matrix remains one Copy element. Art may distribute these references
    across tables/charts/native objects, preserving all labels and values.
    """
    table = node["content"]; shape = validate_table(table); result = []
    def add(suffix, value, location):
        result.append({"copy_id": node["id"] + suffix, "text": value, "role": "body",
                       "graph_node_id": node["id"], "array_location": location})
    for i, axis in enumerate(table["axes"]):
        add(f"__axis_{i}_name", axis["name"], {"axis": i, "kind": "name"})
        for j, label in enumerate(axis["labels"]):
            add(f"__axis_{i}_{j}", label, {"axis": i, "index": j, "kind": "label"})
    for coordinate in product(*(range(n) for n in shape)):
        value = table["values"]
        for index in coordinate:
            value = value[index]
        add("__cell_" + "_".join(map(str, coordinate)), scalar_text(value), {"coordinate": list(coordinate), "kind": "value"})
    add("__unit", table["unit"], {"kind": "unit"})
    add("__period", table["period"], {"kind": "period"})
    return result


def projection(graph):
    """Read-only native inspection view. Never supplied as Copy author input."""
    require_valid(graph); nodes = {n["id"]: n for n in graph["nodes"]}; pages = []
    for p in graph["pages"]:
        units, relations = [], []
        for nid in p["node_ids"]:
            n = nodes[nid]
            if n["kind"] == "head":
                unit = {"copy_id": nid, "text": n["text"], "role": "title" if n["level"] == 1 else "heading"}
                if unit["role"] == "heading":
                    unit["heading_level"] = n["level"]
                units.append(unit)
            elif n["content"]["type"] == "text":
                units.append({"copy_id": nid, "text": n["content"]["text"], "role": "body"})
            else:
                units.extend({k: t[k] for k in ("copy_id", "text", "role")} for t in table_tokens(n))
        for u in units:
            if u["role"] == "body":
                root = u["copy_id"].split("__", 1)[0]
                es = [e for e in graph["connections"] if root in e["sources"] + e["targets"]]
                relations.append({"copy_id": u["copy_id"], "heading_ids": sorted({nid for e in es for nid in e["sources"] + e["targets"] if nodes[nid]["kind"] == "head" and nodes[nid]["level"] >= 2 and nodes[nid]["page_id"] == p["id"]}),
                                  "purpose": "；".join(e["meaning"] for e in es)})
        pages.append({"slide_id": p["id"], "narrative_role": "body" if p["role"] == "content" else p["role"],
                      "section_id": p["id"], "copy_units": units, "data_ids": [],
                      "content_relationships": {"heading_relationships": "按原Copy图的节点、层级和有类型连接理解；见copy_graph，不以本技术投影决定布局。",
                                                "body_relations": relations}})
    return pages


def markdown(graph):
    require_valid(graph); nodes = {n["id"]: n for n in graph["nodes"]}
    lines = ["# Copy：标题、正文与逻辑连接", "", f"协议：{CONTRACT}", "", "## 主链", ""]
    for nid in graph["main_chain"]:
        lines.append(f"- `{nid}` {nodes[nid]['text']}")
    for p in graph["pages"]:
        lines += ["", f"## {p['id']} · {p['role']}", ""]
        for nid in p["node_ids"]:
            n = nodes[nid]; lines += [f"### `{nid}` · {n['kind']} · level {n['level']}", ""]
            if n["kind"] == "body" and n["content"]["type"] == "table":
                lines += ["```json", json.dumps(n["content"], ensure_ascii=False, indent=2), "```", ""]
            else:
                lines += [node_text(n), ""]
        lines += ["逻辑连接（由Art选择是否显式表现）：", ""]
        for e in graph["connections"]:
            if set(e["sources"] + e["targets"]) <= set(p["node_ids"]):
                arrow = "↔" if e["direction"] == "symmetric" else "→"
                lines.append(f"- `{e['id']}` {e['sources']} {arrow} {e['targets']} · {'／'.join(e['types'])}：{e['meaning']}")
    lines += ["", "## 跨页连接", ""]
    for e in graph["connections"]:
        if e["scope"] != "page":
            lines.append(f"- `{e['id']}` {e['sources']} → {e['targets']} · {'／'.join(e['types'])}：{e['meaning']}")
    lines += ["", "## Copy实际复核", ""]
    for k, v in graph["semantic_review"].items():
        lines += [f"- {k}：{v}"]
    return "\n".join(lines) + "\n"
