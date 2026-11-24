"""Project current professional knowledge without author/reader evaluation history.

Only committed Art snapshots are resolved. Embedded source/original paths are
provenance, never a request to read another file. This is a schema projection,
not a semantic classifier or an attestation of actual reading/design quality.
"""
from __future__ import annotations
from . import io

CONTRACT = "io.clayz.presentation.reader-knowledge-evidence/1.0"
SOURCE_CONTRACTS = {"io.clayz.presentation.art-knowledge-evidence/1.0"}
PROOF_ROLES = ("knowledge-node-return", "knowledge-cu-return",
               "knowledge-read-command", "knowledge-manifest")
NODE_TEXT = ("code", "kind", "parent", "title", "principle", "applicability",
             "limits", "provenance", "reading")
NODE_ARRAYS = ("actions", "flow_ids", "source_ids", "concepts", "related_codes")
CU_TEXT = ("id", "review_id", "title", "mapping_basis", "incorporation", "anchor")


def _identity(ref):
    return {k: ref[k] for k in ("sha256", "bytes")}


def _text_fields(value, keys):
    return {key: value[key] for key in keys if isinstance(value.get(key), str)}


def _strings(value):
    return [v for v in value if isinstance(v, str)] if isinstance(value, list) else []


def _professional_use(value):
    """Preserve current declared use lists, never a whole QA/history branch."""
    entries, unobserved = [], []
    supplied = [value] if isinstance(value, (str, dict)) else value
    if not isinstance(supplied, list):
        return None
    for index, item in enumerate(supplied):
        if isinstance(item, str) and item.strip():
            entries.append(item)
        elif isinstance(item, dict):
            clean = _text_fields(item, ("code", "application", "reason", "choice", "how", "where", "why"))
            for key in ("slide_ids", "node_ids", "targets"):
                if key in item:
                    clean[key] = _strings(item[key])
            if clean:
                entries.append(clean)
            else:
                unobserved.append({"index": index, "reason": "unrecognized professional use entry"})
        else:
            unobserved.append({"index": index, "reason": "unrecognized professional use entry"})
    return {"entries": entries, "unobserved": unobserved,
            "scope": "Author-declared current professional use only; not QA, a reader verdict, independently verified private understanding, or causal effect."}


def _nodes(value):
    if not isinstance(value, dict):
        return None
    selected = value.get("selected_nodes")
    if "selected_nodes" not in value:
        # Known bound knowledge-cli lookup envelope; never arbitrary nodes/history.
        hashes = ("manifest_sha256", "nodes_sha256", "selection_sha256")
        if (value.get("package_id") != "art-design-foundations"
                or not all(isinstance(value.get(k), str) and value[k].strip()
                           for k in ("version", "requested_code"))
                or not all(isinstance(value.get(k), str) and len(value[k]) == 64
                           and all(c in "0123456789abcdef" for c in value[k])
                           for k in hashes)):
            return None
        selected = value.get("nodes")
    if not isinstance(selected, list):
        return None
    nodes = []
    for node in selected:
        if not isinstance(node, dict) or not isinstance(node.get("code"), str):
            continue
        clean = _text_fields(node, NODE_TEXT)
        clean.update({k: _strings(node[k]) for k in NODE_ARRAYS if k in node})
        for key in ("positive_example", "negative_example"):
            if isinstance(node.get(key), dict):
                clean[key] = _text_fields(node[key], ("context", "example", "why"))
        nodes.append(clean)
    return {"selected_nodes": nodes}


def _compositions(value):
    if not isinstance(value, dict) or value.get("contract") != "io.clayz.presentation.composition-reading/1.0" or not isinstance(value.get("entries"), list):
        return None
    entries = []
    missing = []
    for index, entry in enumerate(value["entries"]):
        if not isinstance(entry, dict):
            missing.append({"entry_index": index, "reason": "unrecognized composition entry"})
            continue
        clean = _text_fields(entry, CU_TEXT)
        links = entry.get("knowledge_links")
        if isinstance(links, list):
            clean["knowledge_links"] = [_text_fields(link, ("code", "title", "knowledge_contribution")) for link in links if isinstance(link, dict)]
        body = entry.get("understanding")
        expected = entry.get("body_sha256")
        # The bound composition-reading/1.0 producer stores full CU text in
        # understanding; full_body=true or CU IDs alone do not establish it.
        if value.get("full_body") is True and isinstance(body, str) and body.strip() and isinstance(expected, str) and io.digest(body.encode("utf-8")) == expected:
            clean.update({"source_cu_text": body, "body_sha256": expected,
                          "source_field": "composition-reading/1.0.entries.understanding",
                          "body_availability": "submitted-source-text-with-matching-declared-hash",
                          "original_package_text_identity": "unobserved-in-projection"})
        else:
            clean["body_availability"] = "unobserved"
            if isinstance(expected, str):
                clean["declared_body_sha256"] = expected
            missing.append({"entry_index": index, "reason": "full CU text and its matching body hash were not observed"})
        entries.append(clean)
    return {"contract": value["contract"],
            **_text_fields(value, ("knowledge_version",)),
            "entries": entries, "unobserved": missing}


def _command(value):
    if not isinstance(value, dict) or not isinstance(value.get("argv"), list) or not isinstance(value.get("returncode"), int):
        return None
    # Keep actual execution metadata. Never follow stdout_path or project
    # arbitrary notes/host prose as professional knowledge.
    return {**_text_fields(value, ("recorded_at",)), "returncode": value["returncode"],
            "scope": "Submitted command receipt only; not an attestation of model reading or adoption."}


def _manifest(value):
    if not isinstance(value, dict) or value.get("contract") != "io.clayz.presentation.art-learning-pack/1.0":
        return None
    return _text_fields(value, ("contract", "package_id", "package", "version", "knowledge_version", "composition_version", "name"))


def project(root, art):
    """Return a derived clean document; the committed originals stay intact.

    Unknown schema, absent proofs and corrupt/uncommitted references are
    explicit unobserved evidence, never a substituted pass. Only the four
    current named proof roles are eligible; historical source/ref trees are
    not recursively collected.
    """
    result = {"contract": CONTRACT, "projection": "current-professional-whitelist/1.1",
              "proofs": [], "unobserved": [],
              "scope": "Professional content and submitted-byte provenance only; actual model reading, adoption quality and native behavior are not established."}
    files = art.get("files", {})
    ref = files.get("knowledge")
    if not isinstance(ref, dict):
        result["unobserved"].append({"scope": "knowledge", "reason": "no current committed knowledge snapshot"})
        return result
    try:
        source = io.read(io.resolve(root, ref))
        result["source_snapshot"] = _identity(ref)
    except (ValueError, OSError, TypeError, KeyError):
        result["unobserved"].append({"scope": "knowledge", "reason": "current submitted knowledge snapshot could not be hash-verified and decoded"})
        return result
    if not isinstance(source, dict) or source.get("contract") not in SOURCE_CONTRACTS:
        result["unobserved"].append({"scope": "knowledge", "reason": "unrecognized professional knowledge evidence schema"})
        return result
    result["source_contract"] = source["contract"]
    result.update(_text_fields(source, ("version", "recorded_at", "navigation_scope", "actual_adoption")))
    if "actual_adoption" in source:
        use = _professional_use(source["actual_adoption"])
        if use is None:
            result["unobserved"].append({"scope": "actual_adoption", "reason": "unrecognized professional use declaration type"})
        else:
            result["author_professional_use"] = use
    # reason fields describe current professional method adoption. Whole
    # revision_adoption/visual/effect/self-evaluation branches are excluded;
    # a legitimate method reason containing the word reader is not redacted.
    parsers = {"knowledge-node-return": _nodes, "knowledge-cu-return": _compositions,
               "knowledge-read-command": _command, "knowledge-manifest": _manifest}
    declared = source.get("raw_returns", [])
    declared = declared if isinstance(declared, list) else []
    if isinstance(source.get("manifest"), dict):
        declared = declared + [source["manifest"]]
    matched = set()
    for role in PROOF_ROLES:
        proof = files.get(role)
        if not isinstance(proof, dict):
            result["unobserved"].append({"scope": role, "reason": "no current committed named proof snapshot"})
            continue
        try:
            # io.resolve requires a safe run-relative path and exact bytes/hash;
            # embedded original_path and declared external paths are ignored.
            value = io.read(io.resolve(root, proof))
            clean = parsers[role](value)
            if clean is None:
                raise ValueError("unrecognized proof schema")
            result["proofs"].append({"role": role, "source_snapshot": _identity(proof), "professional_content": clean})
            if role == "knowledge-manifest":
                result["source_package_snapshot"] = _identity(proof)
            matched.add((proof["sha256"], proof["bytes"]))
            if role == "knowledge-cu-return":
                result["unobserved"].extend({"scope": role, **row} for row in clean["unobserved"])
        except (ValueError, OSError, TypeError, KeyError):
            result["unobserved"].append({"scope": role, "reason": "submitted named proof could not be hash-verified or has an unsupported schema"})
    for index, item in enumerate(declared):
        if not isinstance(item, dict) or not isinstance(item.get("sha256"), str) or not isinstance(item.get("bytes"), int) or (item["sha256"], item["bytes"]) not in matched:
            result["unobserved"].append({"scope": "declared-proof", "index": index, "reason": "no matching hash-verified current named proof; embedded path was not followed"})
    return result
