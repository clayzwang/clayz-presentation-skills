"""Three producer-owned interfaces. Contracts carry semantics, not authorship."""
from __future__ import annotations
import copy
import json
from pathlib import Path
from . import io

CONTRACT = "io.clayz.presentation.stage-interface/1.0"
STAGES = ("logic", "copy", "art", "output")
INTERFACES = {"logic":"logic-copy", "copy":"copy-art", "art":"art-output"}
REQUIRED = {
    "logic": {"report", "process", "evidence", "data"},
    "copy": {"graph", "generation", "interface", "process"},
    "art": {"design", "renders", "process"},
    "output": {"pptx", "pdf", "renders", "qa", "inventory", "process"},
}


def get_json(root, ref):
    return io.read(io.resolve(root, ref))


def capture_file_ref(root, ref):
    """A declared current dependency must exist; history stays recorded as data."""
    source = Path(ref["path"])
    data = source.read_bytes()
    if len(data) != ref["bytes"] or io.digest(data) != ref["sha256"]:
        raise ValueError("current producer dependency changed: " + str(source))
    return io.snapshot(root, source)


def graph(root, files, dependency):
    value = get_json(root, files["graph"])
    report = value.get("research_report", {})
    original = io.resolve(root, dependency["files"]["report"])
    if report.get("sha256") != io.digest(original.read_bytes()) or report.get("bytes") != original.stat().st_size:
        raise ValueError("Copy graph does not use the current complete Logic report")
    # The graph's delivered bytes remain untouched. Validation may relocate its
    # report reference to the same captured bytes after original paths move.
    check = copy.deepcopy(value)
    check["research_report"] = {"path":str(original), "sha256":io.digest(original.read_bytes()), "bytes":original.stat().st_size}
    from packages.copy_graph import model
    model.require_valid(check)
    receipt = get_json(root, files["interface"])
    if receipt.get("contract")!="io.clayz.presentation.copy-art-interface/1.0"or receipt.get("payload_contract")!=model.CONTRACT or receipt.get("mode") != "identity" or any(receipt.get(role,{}).get("sha256")!=files["graph"]["sha256"]or receipt.get(role,{}).get("bytes")!=files["graph"]["bytes"]for role in ("input","output")):
        raise ValueError("Copy→Art must preserve the complete graph bytes")
    return value


def capture(root, stage, paths, dependency=None):
    if stage not in REQUIRED or not REQUIRED[stage] <= set(paths):
        raise ValueError("missing producer files for " + stage)
    if not all(isinstance(k,str) and isinstance(v,(str,Path)) for k,v in paths.items()):
        raise ValueError("stage files are role-to-file paths")
    files = {k:io.snapshot(root, v) for k,v in paths.items()}
    details = {"current_dependencies":{}, "history_ref_policy":"Historical JSON references are retained as observations, not restored or relabelled current files."}
    from packages.validators import stage_files
    process_ref={"path":str(io.resolve(root,files["process"])),"sha256":files["process"]["sha256"],"bytes":files["process"]["bytes"]}
    process=stage_files.validate_process(process_ref)
    details["process_evidence"]=[capture_file_ref(root,ref)for event in process["events"]for ref in event.get("artifacts",[])]
    if stage == "logic":
        text = io.resolve(root, files["report"]).read_text(encoding="utf-8")
        if not text.strip(): raise ValueError("complete written research is required")
        for role in ("process", "evidence", "data"): get_json(root, files[role])
        documents={key:{"path":str(io.resolve(root,files[key])),"sha256":files[key]["sha256"],"bytes":files[key]["bytes"]}for key in REQUIRED["logic"]}
        _,sources,_=stage_files.validate_research_documents(documents)
        details["source_evidence"]=[capture_file_ref(root,ref)for source in sources for ref in source.get("artifacts",[])]
    elif stage == "copy":
        value = graph(root, files, dependency)
        receipt=get_json(root,files["interface"])
        details["interface_input"]=capture_file_ref(root,receipt["input"])
        details["interface_output"]=capture_file_ref(root,receipt["output"])
        # Verify the actual native registration chain while original current
        # sources are present, then preserve every registration's bytes.
        from packages.copy_graph import workflow as native
        last_path = io.resolve(root, files["generation"])
        native.check_assembly(value, {"path":str(last_path), "sha256":files["generation"]["sha256"], "bytes":files["generation"]["bytes"]})
        lineage=[];ref={"path":str(last_path),"sha256":files["generation"]["sha256"],"bytes":files["generation"]["bytes"]}
        while ref is not None:
            current=capture_file_ref(root,ref);item=io.read(io.resolve(root,current))
            lineage.append(current);details["current_dependencies"].setdefault("copy_inputs",[]).append(capture_file_ref(root,item["input"]))
            ref=item["previous"]
        details["generation_records"] = list(reversed(lineage))
        details["graph_summary"] = {"pages":len(value["pages"]), "nodes":len(value["nodes"]), "connections":len(value["connections"]), "main_chain":value["main_chain"]}
    elif stage in {"art", "output"}:
        manifest = get_json(root, files["renders"])
        pages = manifest.get("slides")
        if not isinstance(pages,list) or not pages: raise ValueError("actual full-page render manifest is required")
        ids = [p.get("slide_id") for p in pages]
        details["pages"] = [{"slide_id":p["slide_id"], "image":capture_file_ref(root,p)} for p in pages]
        for page in details["pages"]:
            raw=io.resolve(root,page["image"]).read_bytes()
            if not(raw.startswith(b"\x89PNG\r\n\x1a\n")or raw.startswith(b"\xff\xd8\xff")):
                raise ValueError("actual raster page bytes required")
        if not isinstance(manifest.get("pptx"),dict):raise ValueError("render manifest must bind its actual source PPTX")
        details["current_dependencies"]["rendered_pptx"]=capture_file_ref(root,manifest["pptx"])
        if stage == "art":
            source_graph = graph(root, dependency["files"], dependency["logic_dependency"])
            design = get_json(root, files["design"])
            design_ids = [s.get("slide_id") for s in design.get("slides",[])]
            expected = [p["id"] for p in source_graph["pages"]]
            if ids != expected or design_ids != expected:
                raise ValueError("Art must preserve Copy pages/order and provide every actual page image")
            from packages.copy_graph import model
            lock=design.get("copy_structure_lock",{})
            if lock.get("graph_sha256")!=model.digest(source_graph) or lock.get("authority")!="presentation-only" or lock.get("interface",{}).get("sha256")!=dependency["files"]["interface"]["sha256"]:
                raise ValueError("Art must bind the exact Copy graph and identity receipt")
            # Native Art lock semantics on same-byte snapshots. Historical
            # absolute receipt paths need not remain on this execution host.
            if "art_content"in design or any(s.get("expression_additions")for s in design["slides"]):raise ValueError("Art cannot add or rewrite Copy content")
            observations=design.get("audit_observations")
            if not isinstance(observations,list):raise ValueError("actual Art audit observations required")
            known={n["id"]for n in source_graph["nodes"]}
            for row in observations:
                if not isinstance(row,dict)or set(row)!={"node_ids","observation","impact","disposition"}or not isinstance(row["node_ids"],list)or any(n not in known for n in row["node_ids"])or not row["observation"]or not row["impact"]or row["disposition"]!="audit-only":raise ValueError("Art objections must remain concrete audit-only observations")
            details["copy_graph_sha256"] = dependency["files"]["graph"]["sha256"]
            details["copy_graph"] = dependency["files"]["graph"]
        else:
            expected = [p["slide_id"] for p in dependency["details"]["pages"]]
            if ids != expected: raise ValueError("Output page images must match the approved Art order")
            if manifest["pptx"]["sha256"]!=files["pptx"]["sha256"]:raise ValueError("Output renders are not bound to the written final PPTX")
            if not io.resolve(root,files["pdf"]).read_bytes().startswith(b"%PDF-"):
                raise ValueError("actual PDF bytes are required")
            import zipfile
            with zipfile.ZipFile(io.resolve(root,files["pptx"])) as archive:
                if "ppt/presentation.xml" not in archive.namelist(): raise ValueError("actual PPTX required")
            from . import technical
            qa=get_json(root,files["qa"])
            details["technical_observations"]=technical.capture(root,qa,files,dependency)
            get_json(root,files["inventory"])
    return {"contract":CONTRACT, "interface":INTERFACES.get(stage,"output-delivery"),
            "producer":stage, "recorded_at":io.now(), "files":files, "details":details}


def professional_projection(root, stage, artifact, output, brief=None, stage_goals=None):
    """Author receives role-specific files; envelopes and prior verdicts stay out."""
    from packages.validators.stage_files import BRIEF_FIELDS
    allowed=set(BRIEF_FIELDS["art-direction"if stage=="art"else stage])
    if stage=="logic":allowed.add("user_request")
    if not isinstance(brief or{},dict)or set(brief or{})-allowed:raise ValueError("only stage-specific professional brief fields belong in the author packet")
    output = Path(output)
    if output.exists(): raise ValueError("use a new professional packet directory")
    output.mkdir(parents=True)
    if stage == "logic": roles = {}
    elif stage == "copy": roles = {"report":artifact["files"]["report"]}
    elif stage == "art": roles = {"graph":artifact["files"]["graph"]}
    elif stage == "output": roles = {"design":artifact["files"]["design"],"renders":artifact["files"]["renders"]}
    else: raise ValueError("projection target must be logic/copy/art/output")
    refs = {}
    for role,ref in roles.items():
        source = io.resolve(root,ref)
        target = output/(role+source.suffix)
        target.write_bytes(source.read_bytes())
        refs[role] = {"path":str(target.resolve()),"sha256":ref["sha256"],"bytes":ref["bytes"]}
    technical_files = {}
    if stage in {"art", "output"}:
        # The run's frozen configuration is technical input, never company
        # content or an installed-default substitute. Preserve exact bytes.
        config_ref = io.read(Path(root) / "run.json")["config"]
        config_source = io.resolve(root, config_ref)
        config_bytes = config_source.read_bytes()
        if (io.digest(config_bytes) != config_ref["sha256"]
                or len(config_bytes) != config_ref["bytes"]):
            raise ValueError("bound canonical task config identity differs")
        target = output / "canonical-task-config.json"
        target.write_bytes(config_bytes)
        technical_files["canonical_task_config"] = {
            "path": str(target.resolve()), "sha256": config_ref["sha256"],
            "bytes": config_ref["bytes"],
        }
    if stage == "art":
        # Identity is needed to bind Art's presentation-only lock, but it is
        # technical evidence rather than additional company content. Keep the
        # exact graph as Art's sole content input and copy its actual receipt.
        receipt = artifact["files"]["interface"]
        source = io.resolve(root, receipt)
        target = output / "copy-art-identity-receipt.json"
        target.write_bytes(source.read_bytes())
        technical_files["copy_art_identity_receipt"] = {
            "path": str(target.resolve()), "sha256": receipt["sha256"],
            "bytes": receipt["bytes"],
        }
    if stage == "output":
        source=io.resolve(root,artifact["details"]["current_dependencies"]["rendered_pptx"])
        target=output/"editable-source.pptx";target.write_bytes(source.read_bytes())
        refs["editable_source_pptx"]={"path":str(target.resolve()),"sha256":io.digest(target.read_bytes())}
        refs["production_resources"]={}
        for role,ref in artifact["files"].items():
            # These reserved roles prove Art's knowledge reading. They stay
            # in the original stage/audit snapshots, not Output production data.
            if role not in {"design", "renders", "process", "knowledge",
                            "knowledge-node-return", "knowledge-cu-return",
                            "knowledge-read-command", "knowledge-manifest"}:
                source=io.resolve(root,ref);target=output/("resource-"+io.identifier(role)+source.suffix)
                target.write_bytes(source.read_bytes());refs["production_resources"][role]={"path":str(target.resolve()),"sha256":ref["sha256"]}
        refs["page_images"] = []
        for page in artifact["details"]["pages"]:
            source=io.resolve(root,page["image"]);target=output/(page["slide_id"]+".png")
            target.write_bytes(source.read_bytes());refs["page_images"].append({"slide_id":page["slide_id"],"path":str(target.resolve()),"sha256":page["image"]["sha256"]})
    packet={"contract":"io.clayz.presentation.professional-input/2.0","stage":stage,"content_files":refs,"brief":brief or{},"training_goals":stage_goals or[],"scope":"Producer content only. Professional audience/format requirements are separate; author self-evaluations are not content. Training goals contain no prior case drafts or reader answers."}
    if technical_files:
        packet["technical_files"] = technical_files
    io.write_new(output/"professional-input.json",packet)
    return str((output/"professional-input.json").resolve())
