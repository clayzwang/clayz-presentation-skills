# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Native professional stage files; runtime configuration stays with Supervisor.

These functions record, bind and inspect files. They do not research, write an
argument, choose a paragraph count, approve quality, or execute another agent.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import io
import zipfile
from xml.etree import ElementTree
from datetime import datetime, timezone
from pathlib import Path

CONTRACT = "io.clayz.presentation.stage-files/1.0"
INPUT_CONTRACT = "io.clayz.presentation.stage-input/1.0"
ACCOUNT_CONTRACT = "io.clayz.presentation.copy-account/1.0"
COLLECTION_CONTRACT = "io.clayz.presentation.training-materials/1.0"
STAGES = ("logic", "copy", "art-direction", "output", "supervisor")
BRIEF_FIELDS = {
    "logic": {"topic", "audience", "research_requirements", "materials"},
    "copy": {"purpose", "audience", "pagination_requirements", "wording_requirements"},
    "art-direction": {"purpose", "audience", "format_requirements", "master", "fonts", "colors", "knowledge"},
    "output": {"delivery_requirements", "editable_requirements", "target_applications"},
    "supervisor": {"user_request", "tool_version", "knowledge_version", "acceptance_requirements"},
}
PREDECESSORS = {"logic": (), "copy": ("logic",), "art-direction": ("copy",),
                "output": ("art-direction",), "supervisor": STAGES[:-1]}
OUTPUT_ROLES = {
    "logic": {"report", "process", "evidence", "data"},
    "copy": {"account", "content", "process"},
    "art-direction": {"design", "renders", "process"},
    "output": {"pptx", "pdf", "renders", "qa", "process"},
    "supervisor": {"report", "exceptions"},
}


def now():
    return datetime.now(timezone.utc).isoformat()


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def file_ref(path):
    path = Path(path).resolve(strict=True)
    if not path.is_file():
        raise ValueError(f"File required: {path}")
    payload = path.read_bytes()
    return {"path": str(path), "sha256": hashlib.sha256(payload).hexdigest(), "bytes": len(payload)}


def read_ref(ref):
    if not isinstance(ref, dict) or set(ref) != {"path", "sha256", "bytes"}:
        raise ValueError("File reference requires only path, sha256 and bytes")
    actual = file_ref(ref["path"])
    if actual != ref:
        raise ValueError(f"Changed file: {ref['path']}")
    return Path(ref["path"]).read_bytes()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def json_ref(ref):
    return json.loads(read_ref(ref))


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    return file_ref(path)


def check_input(value):
    if not isinstance(value, dict) or value.get("contract") != INPUT_CONTRACT:
        raise ValueError("Native stage input required")
    if set(value) != {"contract", "stage", "brief", "inputs", "recorded_at"}:
        raise ValueError("Stage input cannot carry runtime/configuration snapshots")
    stage = value.get("stage")
    brief = value.get("brief")
    if stage not in STAGES or not isinstance(brief, dict) or set(brief) - BRIEF_FIELDS[stage]:
        raise ValueError(f"Only the {stage} professional brief fields are accepted")
    if not brief or not isinstance(value.get("inputs"), list):
        raise ValueError("A professional brief and input file list are required")
    if stage in {'logic', 'copy', 'output'}:
        for key, item in brief.items():
            if stage == 'logic' and key == 'materials':
                if not isinstance(item, list):
                    raise ValueError('Logic materials must be actual file references')
                for material in item:
                    read_ref(material)
            elif not (nonempty(item) or isinstance(item, list) and all(nonempty(v) for v in item)):
                raise ValueError(f'{stage}.{key}: use task wording, not embedded configuration objects')
    required = {"logic": "topic", "copy": "purpose", "art-direction": "purpose",
                "output": "delivery_requirements", "supervisor": "user_request"}[stage]
    if not brief.get(required):
        raise ValueError(f"{stage} brief requires {required}")
    predecessor_stages = []
    for ref in value["inputs"]:
        predecessor = json_ref(ref)
        check_handoff(predecessor)
        predecessor_stages.append(predecessor["stage"])
    if sorted(predecessor_stages) != sorted(PREDECESSORS[stage]):
        raise ValueError(f"{stage} input requires exactly these prior stage files: {PREDECESSORS[stage]}")
    return value


def prepare_input(stage, brief, inputs, output):
    value = {"contract": INPUT_CONTRACT, "stage": stage, "brief": read_json(brief),
             "inputs": [file_ref(p) for p in inputs], "recorded_at": now()}
    check_input(value)
    return write_new(output, value)


def validate_process(ref, source_ids=None, require_evidence=False):
    value = json_ref(ref)
    events = value.get("events") if isinstance(value, dict) else None
    if not isinstance(events, list) or not events:
        raise ValueError("Process file must contain the actual observable work events")
    for event in events:
        if not isinstance(event, dict) or not nonempty(event.get("action")) or not nonempty(event.get("record")):
            raise ValueError("A process event requires an action and a substantive factual record")
        if source_ids is not None:
            ids = event.get("source_ids", [])
            if not isinstance(ids, list) or any(s not in source_ids for s in ids):
                raise ValueError("Process event references an unknown source")
        artifacts = event.get('artifacts', [])
        if not isinstance(artifacts, list) or require_evidence and not artifacts:
            raise ValueError('Research process events must cite their actual saved work/source evidence')
        for evidence in artifacts:
            read_ref(evidence)
    return value


def validate_research_documents(documents):
    if not isinstance(documents, dict) or set(documents) != OUTPUT_ROLES["logic"]:
        raise ValueError("Research requires separate full report, process, evidence and data files")
    report = read_ref(documents["report"]).decode("utf-8")
    if not report.strip():
        raise ValueError("Full research report is empty")
    evidence = json_ref(documents["evidence"])
    sources = evidence.get("sources") if isinstance(evidence, dict) else None
    if not isinstance(sources, list) or not sources:
        raise ValueError("Evidence file must retain the actual sources")
    ids = []
    for source in sources:
        if not isinstance(source, dict) or any(not nonempty(source.get(k)) for k in ("source_id", "title", "locator")):
            raise ValueError("Each source requires identity, title and a usable location")
        ids.append(source["source_id"])
        snapshots = source.get('artifacts', [])
        if not isinstance(snapshots, list) or (not snapshots and
                not (source.get('access_status') == 'not-obtained' and nonempty(source.get('limitation')))):
            raise ValueError('A source needs actual saved evidence, or an explicit not-obtained limitation')
        for ref in snapshots:
            read_ref(ref)
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate source ID")
    validate_process(documents["process"], set(ids), require_evidence=True)
    data = json_ref(documents["data"])
    if not isinstance(data, list):
        raise ValueError("Data file must be an array, including [] when no calculations are needed")
    return report, sources, data


def make_handoff(stage, input_path, artifacts, output, **extra):
    value = {"contract": CONTRACT, "stage": stage, "input": file_ref(input_path),
             "artifacts": {k: file_ref(p) for k, p in artifacts.items()},
             "recorded_at": now(), **extra}
    check_handoff(value)
    return write_new(output, value)


def record_research(input_path, report, process, evidence, data, output):
    return make_handoff("logic", input_path,
                        {"report": report, "process": process, "evidence": evidence, "data": data}, output)


def record_account(input_path, account, output):
    input_value = check_input(read_json(input_path))
    if input_value["stage"] != "copy":
        raise ValueError("Copy account requires the Copy professional input")
    account_ref = file_ref(account)
    if not read_ref(account_ref).decode("utf-8").strip():
        raise ValueError("Reader-facing complete account is empty")
    return write_new(output, {"contract": ACCOUNT_CONTRACT, "input": file_ref(input_path),
                              "account": account_ref, "recorded_at": now()})


def check_account(value):
    if not isinstance(value, dict) or value.get("contract") != ACCOUNT_CONTRACT:
        raise ValueError("Register the complete Copy account before creating the page document")
    if check_input(json_ref(value["input"]))["stage"] != "copy":
        raise ValueError("Copy account is bound to the wrong stage")
    text = read_ref(value["account"]).decode("utf-8")
    if not text.strip():
        raise ValueError("Reader-facing account is empty")
    return text


def validate_copy_document(content, account, account_record=None):
    from packages.validators.page_planning import validate_content_relationships
    account_text = check_account(account)
    if not isinstance(content, dict) or set(content) != {"account_record", "slides", "unit_sources", "semantic_review"}:
        raise ValueError("Copy content contains pages, account spans and the actual semantic review only")
    supplied_record = content["account_record"]
    if json_ref(supplied_record) != account or (account_record is not None and supplied_record != account_record):
        raise ValueError("The page document must consume the already registered account record")
    pages = content["slides"]
    if not isinstance(pages, list) or not pages or not nonempty(content["semantic_review"]):
        raise ValueError("Actual pages and semantic review are required")
    ids = set()
    page_ids = set()
    for page in pages:
        if not isinstance(page, dict) or not nonempty(page.get("slide_id")) or page["slide_id"] in page_ids:
            raise ValueError("Each page needs a unique identity")
        page_ids.add(page["slide_id"])
        units = page.get("copy_units")
        if not isinstance(units, list) or not units:
            raise ValueError("Page requires its actual text")
        for unit in units:
            if not isinstance(unit, dict) or set(unit) - {"copy_id", "text", "role", "heading_level"}:
                raise ValueError("Copy units cannot prescribe rendering or grouping")
            cid = unit.get("copy_id")
            if not nonempty(cid) or cid in ids or not nonempty(unit.get("text")):
                raise ValueError("Copy text and unique IDs are required")
            ids.add(cid)
            if unit.get("role") not in {"title", "subtitle", "heading", "body", "annotation"}:
                raise ValueError("Explicit text role required")
            if unit["role"] == "heading":
                level = unit.get("heading_level")
                if isinstance(level, bool) or not isinstance(level, int) or level < 1:
                    raise ValueError("A heading needs its actual explicit level; there is no default level")
            elif "heading_level" in unit:
                raise ValueError("Only headings have heading levels")
        errors = validate_content_relationships(page)
        if errors:
            raise ValueError("\n".join(errors))
    sources = content["unit_sources"]
    if not isinstance(sources, dict) or set(sources) != ids:
        raise ValueError("Every text unit must trace to the registered complete account")
    units = {u["copy_id"]: u for p in pages for u in p["copy_units"]}
    for cid, spans in sources.items():
        if not isinstance(spans, list) or not spans:
            raise ValueError(f"{cid}: actual account span required")
        for span in spans:
            start, end = span.get("start"), span.get("end")
            if (isinstance(start, bool) or isinstance(end, bool) or not isinstance(start, int)
                    or not isinstance(end, int) or not 0 <= start < end <= len(account_text)):
                raise ValueError(f"{cid}: invalid account character range")
            operation = span.get("operation")
            if operation == "verbatim":
                if len(spans) != 1 or units[cid]["text"] != account_text[start:end]:
                    raise ValueError(f"{cid}: verbatim unit differs from its account span")
            elif operation not in {"edited", "derived"} or not nonempty(span.get("reason")):
                raise ValueError(f"{cid}: explain the actual edit or derivation")
    return content


def record_copy(account_path, content_path, process, output):
    account = read_json(account_path)
    check_account(account)
    content = read_json(content_path)
    validate_copy_document(content, account, file_ref(account_path))
    return make_handoff("copy", account["input"]["path"],
                        {"account": account["account"]["path"], "content": content_path, "process": process},
                        output, account_record=file_ref(account_path))


def validate_renders(ref, expected_ids):
    value = json_ref(ref)
    slides = value.get("slides") if isinstance(value, dict) else None
    if not isinstance(slides, list) or [s.get("slide_id") for s in slides] != expected_ids:
        raise ValueError("Render manifest must cover every actual page in order")
    for slide in slides:
        payload = read_ref({k: slide[k] for k in ("path", "sha256", "bytes")})
        if not (payload.startswith(b"\x89PNG\r\n\x1a\n") or payload.startswith(b"\xff\xd8\xff")):
            raise ValueError("A page image must contain PNG or JPEG bytes")
    return value


def validate_output_files(pptx_ref, pdf_ref, expected_pages):
    try:
        with zipfile.ZipFile(io.BytesIO(read_ref(pptx_ref))) as archive:
            if '[Content_Types].xml' not in archive.namelist():
                raise ValueError('Editable PPTX content types are missing')
            root = ElementTree.fromstring(archive.read('ppt/presentation.xml'))
            ids = root.findall('.//{http://schemas.openxmlformats.org/presentationml/2006/main}sldId')
            if len(ids) != expected_pages:
                raise ValueError('PPTX slide count differs from the actual page files')
    except (zipfile.BadZipFile, KeyError, ElementTree.ParseError) as exc:
        raise ValueError('Actual readable PPTX files are required') from exc
    pdf = read_ref(pdf_ref)
    if not pdf.startswith(b'%PDF-') or b'%%EOF' not in pdf[-1024:]:
        raise ValueError('Actual PDF bytes are required')


def check_handoff(value):
    if not isinstance(value, dict) or value.get("contract") != CONTRACT:
        raise ValueError("Native professional file handoff required")
    stage = value.get("stage")
    allowed = {"contract", "stage", "input", "artifacts", "recorded_at"}
    if stage == "copy":
        allowed.add("account_record")
    if stage not in STAGES or set(value) != allowed:
        raise ValueError("Professional handoff cannot carry runtime/configuration snapshots")
    input_value = check_input(json_ref(value["input"]))
    if input_value["stage"] != stage:
        raise ValueError("Input and output stage differ")
    artifacts = value.get("artifacts")
    if not isinstance(artifacts, dict) or set(artifacts) != OUTPUT_ROLES[stage]:
        raise ValueError(f"{stage} requires these actual files: {OUTPUT_ROLES[stage]}")
    for ref in artifacts.values():
        if not read_ref(ref):
            raise ValueError("Stage artifact is empty")
    if stage == "logic":
        validate_research_documents(artifacts)
    elif stage == "copy":
        account = json_ref(value["account_record"])
        if account["input"] != value["input"] or account["account"] != artifacts["account"]:
            raise ValueError("Copy must use the registered account and its original input")
        validate_copy_document(json_ref(artifacts["content"]), account, value["account_record"])
        validate_process(artifacts["process"])
    elif stage in {"art-direction", "output"}:
        predecessor = json_ref(input_value["inputs"][0])
        if stage == "art-direction":
            content = json_ref(predecessor["artifacts"]["content"])
            design = json_ref(artifacts["design"])
            projection = design.get('art_content')
            actual_pages = content['slides']
            if projection is not None:
                if not isinstance(projection, dict) or not isinstance(projection.get('slides'), list):
                    raise ValueError('Art projection must preserve its actual pages and change record')
                from packages.validators.art_content import differences
                expected_changes = differences({'copy_layer': {'slides': content['slides']}}, projection['slides'])
                changes = projection.get('changes')
                keys = {'change_id', 'category', 'location', 'before', 'after'}
                if (not isinstance(changes, list)
                        or [{k: c.get(k) for k in keys} for c in changes] != expected_changes
                        or any(not all(nonempty(c.get(k)) for k in ('reason', 'evidence', 'impact')) for c in changes)):
                    raise ValueError('Art changes require the existing exact difference record and substantive reasons')
                actual_pages = projection['slides']
            expected = [s['slide_id'] for s in actual_pages]
            if [s.get("slide_id") for s in design.get("slides", [])] != expected:
                raise ValueError("Art design must cover its actual documented presentation pages")
        else:
            expected = [s["slide_id"] for s in json_ref(predecessor["artifacts"]["renders"])["slides"]]
            validate_output_files(artifacts['pptx'], artifacts['pdf'], len(expected))
            qa = json_ref(artifacts["qa"])
            if not isinstance(qa, dict):
                raise ValueError("Actual Output QA file required; a file handoff does not approve its result")
        validate_renders(artifacts["renders"], expected)
        validate_process(artifacts["process"])
    return value


def record_art(input_path, design, renders, process, output):
    return make_handoff("art-direction", input_path,
                        {"design": design, "renders": renders, "process": process}, output)


def record_output(input_path, pptx, pdf, renders, qa, process, output):
    return make_handoff("output", input_path,
                        {"pptx": pptx, "pdf": pdf, "renders": renders, "qa": qa, "process": process}, output)


def record_supervisor(input_path, report, exceptions, output):
    return make_handoff("supervisor", input_path, {"report": report, "exceptions": exceptions}, output)


def collect_materials(handoffs, user_request, tool_version, knowledge_version, tool_snapshot, knowledge_snapshot, output_dir,
                      supporting_artifacts=()):
    """Copy the actual run files for later analysis; never start another run."""
    output_dir = Path(output_dir)
    if output_dir.exists():
        raise ValueError("Use a new material collection directory")
    values = [check_handoff(read_json(p)) for p in handoffs]
    if sorted(v["stage"] for v in values) != sorted(STAGES):
        raise ValueError("Collect the actual five stage handoffs")
    files = {}
    def retain(ref):
        payload = read_ref(ref)
        key = ref["path"]
        if key in files:
            return
        name = f"files/{ref['sha256']}-{Path(key).name}"
        files[key] = {"original": ref, "stored_path": name}
        target = output_dir / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            target.write_bytes(payload)
        try:
            walk(json.loads(payload))
        except (UnicodeDecodeError, json.JSONDecodeError):
            pass
    def walk(value):
        if isinstance(value, dict):
            if {"path", "sha256", "bytes"}.issubset(value):
                retain({k: value[k] for k in ("path", "sha256", "bytes")})
            else:
                for child in value.values():
                    walk(child)
        elif isinstance(value, list):
            for child in value:
                walk(child)
    output_dir.mkdir(parents=True)
    required = {"user_request": file_ref(user_request), "tool_version": file_ref(tool_version),
                "knowledge_version": file_ref(knowledge_version), "tool_snapshot": file_ref(tool_snapshot),
                "knowledge_snapshot": file_ref(knowledge_snapshot)}
    supporting = [file_ref(p) for p in supporting_artifacts]
    for ref in [*required.values(), *(file_ref(p) for p in handoffs), *supporting]:
        retain(ref)
    manifest = {"contract": COLLECTION_CONTRACT, "recorded_at": now(), "inputs": required,
                "handoffs": [file_ref(p) for p in handoffs], "supporting_artifacts": supporting,
                "files": list(files.values()),
                "meaning": "Actual saved materials for later diagnosis and method improvement; not proof of quality or training."}
    return write_new(output_dir / "training-materials.json", manifest)


def check_collection(manifest_path):
    manifest_path = Path(manifest_path)
    value = read_json(manifest_path)
    if value.get('contract') != COLLECTION_CONTRACT:
        raise ValueError('Training-material collection contract required')
    root = manifest_path.parent.resolve()
    retained = {}
    for entry in value.get('files', []):
        stored = (root / entry['stored_path']).resolve()
        if not stored.is_relative_to(root):
            raise ValueError('Stored material must remain inside the collection')
        actual = file_ref(stored)
        original = entry['original']
        if actual['sha256'] != original['sha256'] or actual['bytes'] != original['bytes']:
            raise ValueError('Retained material differs from the original bytes')
        if original['path'] in retained:
            raise ValueError('Duplicate retained original path')
        retained[original['path']] = (original, stored)
    def check_reference(ref):
        saved = retained.get(ref['path'])
        if saved is None or saved[0] != ref:
            raise ValueError('A required or nested referenced file is missing from the collection')
    def walk(item):
        if isinstance(item, dict):
            if {'path', 'sha256', 'bytes'}.issubset(item):
                check_reference({k: item[k] for k in ('path', 'sha256', 'bytes')})
            else:
                for child in item.values():
                    walk(child)
        elif isinstance(item, list):
            for child in item:
                walk(child)
    for ref in [*value.get('inputs', {}).values(), *value.get('handoffs', []), *value.get('supporting_artifacts', [])]:
        check_reference(ref)
    for _, stored in retained.values():
        try:
            walk(json.loads(stored.read_bytes()))
        except (UnicodeDecodeError, json.JSONDecodeError):
            pass
    return value


def read_collected_file(manifest_path, original_ref):
    value = check_collection(manifest_path)
    entry = next((e for e in value['files'] if e['original'] == original_ref), None)
    if entry is None:
        raise ValueError('Requested original file was not retained')
    return (Path(manifest_path).parent / entry['stored_path']).read_bytes()


def bind_logic(handoff_path, context_path, output):
    """Supervisor/tool operation; the author never receives this runtime envelope."""
    handoff = check_handoff(read_json(handoff_path))
    if handoff["stage"] != "logic":
        raise ValueError("Logic professional files required")
    context = read_json(context_path)
    _, sources, data = validate_research_documents(handoff["artifacts"])
    bindings = context.pop('source_resource_bindings', {})
    runtime_sources = []
    for source in sources:
        bound = dict(source)
        if not bound.get('resource_id'):
            bound['resource_id'] = bindings.get(source['source_id'])
        if not nonempty(bound.get('resource_id')):
            raise ValueError('Supervisor must bind each evidence source to an actually selected resource')
        runtime_sources.append(bound)
    context.update(contract_version="3.5", status="logic-approved", research={
        "documents": handoff["artifacts"], "sources": runtime_sources, "data": data,
        "findings": [], "glossary": [], "metric_dictionary": [], "open_items": [], "invariants": []},
        logic_layer=None, copy_layer=None, professional_handoff=file_ref(handoff_path))
    from packages.validators.validate_logic_package import validate_package
    errors = validate_package(context, "logic-approved")
    if errors:
        raise ValueError("\n".join(errors))
    return write_new(output, context)


def bind_copy(handoff_path, logic_runtime, context_path, output):
    handoff = check_handoff(read_json(handoff_path))
    if handoff["stage"] != "copy":
        raise ValueError("Copy professional files required")
    package = read_json(logic_runtime)
    context = read_json(context_path)
    content = json_ref(handoff["artifacts"]["content"])
    if not isinstance(context.get("approval"), dict):
        raise ValueError("Use the existing actual Copy approval record; binding never invents approval")
    index = context.get('index_evidence')
    if index is not None:
        original_index = package.get('index_evidence') or {}
        if (not isinstance(index, dict)
                or {k: v for k, v in index.items() if k != 'stage_receipts'} !=
                   {k: v for k, v in original_index.items() if k != 'stage_receipts'}
                or (index.get('stage_receipts') or {}).get('logic') !=
                   (original_index.get('stage_receipts') or {}).get('logic')):
            raise ValueError('Copy technical binding must preserve the Logic provider lock and original receipts')
        package['index_evidence'] = index
    package.update(status="copy-approved", logic_artifact=file_ref(logic_runtime),
                   professional_handoff=file_ref(handoff_path), copy_provenance=content["unit_sources"])
    package["approvals"]["copy"] = context["approval"]
    from packages.validators.story_handoff import digest
    package["copy_layer"] = {"logic_version": package["version"], "pagination_owner": "copy",
        "research_sha256": digest(package["research"]), "semantic_preservation_review": content["semantic_review"],
        "documents": {**handoff["artifacts"], "account_record": handoff["account_record"]}, "slides": content["slides"]}
    from packages.validators.validate_ppt_package import validate_package
    errors = validate_package(package, "copy-approved")
    if errors:
        raise ValueError("\n".join(errors))
    return write_new(output, package)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="command", required=True)
    commands = {
        "files-prepare": ("stage", "brief", "output"),
        "files-research": ("input", "report", "process", "evidence", "data", "output"),
        "files-account": ("input", "account", "output"),
        "files-copy": ("account-record", "content", "process", "output"),
        "files-art": ("input", "design", "renders", "process", "output"),
        "files-output": ("input", "pptx", "pdf", "renders", "qa", "process", "output"),
        "files-supervisor": ("input", "report", "exceptions", "output"),
        "files-check": ("handoff",),
        "files-collect": ("user-request", "tool-version", "knowledge-version", "tool-snapshot", "knowledge-snapshot", "output"),
        "files-check-collection": ("manifest",),
        "files-bind-logic": ("handoff", "context", "output"),
        "files-bind-copy": ("handoff", "logic-runtime", "context", "output"),
    }
    for name, fields in commands.items():
        sub = subs.add_parser(name)
        for field in fields:
            sub.add_argument("--" + field, required=True)
        if name == "files-prepare":
            sub.add_argument("--input", action="append", default=[])
        if name == "files-collect":
            sub.add_argument("--handoff", action="append", required=True)
            sub.add_argument("--supporting-artifact", action="append", default=[])
    args = parser.parse_args(argv)
    try:
        a = vars(args)
        name = a["command"]
        if name == "files-prepare":
            result = prepare_input(a["stage"], a["brief"], a["input"], a["output"])
        elif name == "files-research":
            result = record_research(*(a[k] for k in ("input", "report", "process", "evidence", "data", "output")))
        elif name == "files-account":
            result = record_account(a["input"], a["account"], a["output"])
        elif name == "files-copy":
            result = record_copy(a["account_record"], a["content"], a["process"], a["output"])
        elif name == "files-art":
            result = record_art(*(a[k] for k in ("input", "design", "renders", "process", "output")))
        elif name == "files-output":
            result = record_output(*(a[k] for k in ("input", "pptx", "pdf", "renders", "qa", "process", "output")))
        elif name == "files-supervisor":
            result = record_supervisor(a["input"], a["report"], a["exceptions"], a["output"])
        elif name == "files-collect":
            result = collect_materials(a["handoff"], a["user_request"], a["tool_version"], a["knowledge_version"],
                                       a['tool_snapshot'], a['knowledge_snapshot'], a["output"], a['supporting_artifact'])
        elif name == 'files-check-collection':
            check_collection(a['manifest'])
            result = file_ref(a['manifest'])
        elif name == "files-bind-logic":
            result = bind_logic(a["handoff"], a["context"], a["output"])
        elif name == "files-bind-copy":
            result = bind_copy(a["handoff"], a["logic_runtime"], a["context"], a["output"])
        else:
            check_handoff(read_json(a["handoff"]))
            result = file_ref(a["handoff"])
        print(json.dumps({"status": "files-recorded", "artifact": result,
                          "quality": "not-established-by-file-validation"}, ensure_ascii=False))
        return 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f"ERROR: {exc}")
        return 1
