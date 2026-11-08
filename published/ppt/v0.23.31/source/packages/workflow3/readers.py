"""Prepared packets, frozen independent understanding, and original-reader review."""
from __future__ import annotations
import json
from pathlib import Path
import uuid
from . import io, run, reader_knowledge

CONTRACT="io.clayz.presentation.mode-reader/1.0"
CRITERIA={
 "content":["storyline论证问题明确、结构完善、逻辑可靠、环节自然","各级标题层次清晰、表达连贯","下层事实可靠、解释充分、语言自然；复核节点及连接的实际语义"],
 "layout":["关系和类型已在合适的表征中得到利用","知识包得到实际读取、判断与应用","空间排布合理，主要关系可辨认，实际全页可读"],
 "final":["实际成品带来有价值的认识","表达清楚","逻辑正确；检查所有实际页图和可观察原生对象"],
 "audit":["原始用户要求及当前规则得到忠实执行","保留三个读者的原始判断、实际失败、残留和未观察检查","区分专业质量、记录完整性、执行状态与归档状态"]}


def _stage(s, name):
    if name not in s["stages"]:raise ValueError("missing current stage "+name)
    return s["stages"][name]["interface"]


def _file(root, destination, ref):
    source=io.resolve(root,ref);destination.parent.mkdir(parents=True,exist_ok=True)
    with destination.open("xb")as stream:stream.write(source.read_bytes())
    return {"path":str(destination.resolve()),"sha256":ref["sha256"],"bytes":ref["bytes"]}


def _visible_content(graph):
    """Keep displayed content; selection justification belongs to comparison."""
    nodes = []
    for node in graph["nodes"]:
        visible = {key: node[key] for key in
                   ("id", "kind", "level", "page_id", "text", "content") if key in node}
        if isinstance(visible.get("content"), dict):
            visible["content"] = {key: value for key, value in visible["content"].items()
                                  if key != "selection"}
        nodes.append(visible)
    return {"pages": graph["pages"], "nodes": nodes}


def prepare(root, role, phase, output):
    if role not in CRITERIA or phase not in {"first","comparison","confirmation"}:raise ValueError("unsupported reader packet")
    with io.locked(root):
        s=run.state(root)
        if s["run"]["mode"]=="fast":raise ValueError("fast mode does not run independent readers or side audit")
        if role=="audit" and not all(run.reader_closed(s,k)for k in run.READERS):raise ValueError("all three original reader checks must close before Supervisor audit")
        previous=s["reviews"].get(role,{})
        if phase=="first" and ("first"in previous or (role,"first")in s["packets"]):raise ValueError("first packet/reading already exists; preserve it")
        if phase!="first" and "first"not in previous:raise ValueError("freeze independent understanding before source comparison")
        if phase=="comparison" and "comparison"in previous:raise ValueError("original comparison is immutable; changed artifacts use original-reader confirmation")
        if phase=="confirmation" and role=="audit":raise ValueError("audit records only and never triggers repair")
        out=Path(output).resolve()
        if out.exists():raise ValueError("new packet directory required")
        out.mkdir(parents=True)
        files={"user_request":_file(root,out/"user-request.txt",s["run"]["task_request"])}
        if role=="content":
            graph=io.read(io.resolve(root,_stage(s,"copy")["files"]["graph"]))
            clean=_visible_content(graph)
            io.write_new(out/"visible-content.json",clean);files["visible_content"]={"path":str(out/"visible-content.json")}
        else:
            artifact=_stage(s,"art"if role=="layout"else"output")
            files["pages"]=[{"slide_id":page["slide_id"],**_file(root,out/"pages"/(f'{i:03d}-'+page["slide_id"]+".png"),page["image"])}for i,page in enumerate(artifact["details"]["pages"],1)]
            if role in {"final","audit"}:
                files["pptx"]=_file(root,out/"actual.pptx",artifact["files"]["pptx"])
                files["pdf"]=_file(root,out/"actual.pdf",artifact["files"]["pdf"])
        if phase!="first":
            # Clean semantic evidence excludes Copy's self-review. The full
            # research is available only after initial understanding freezes.
            files["research_report"]=_file(root,out/"research-report.md",_stage(s,"logic")["files"]["report"])
            graph=io.read(io.resolve(root,_stage(s,"copy")["files"]["graph"]))
            graph={k:v for k,v in graph.items()if k!="semantic_review"}
            io.write_new(out/"semantic-evidence.json",graph);files["semantic_evidence"]={"path":str(out/"semantic-evidence.json")}
            if role in {"layout","final","audit"}:
                design=io.read(io.resolve(root,_stage(s,"art")["files"]["design"]))
                # Author observations/approval are deliberately absent from the
                # three readers' clean comparisons; originals remain in audit.
                if role!="audit":
                    design={"copy_structure_lock":design.get("copy_structure_lock"),"slides":[{k:v for k,v in page.items()if k in {"slide_id","reading_sequence","copy_unit_map","medium_execution_contract"}}for page in design.get("slides",[])]}
                io.write_new(out/"design-evidence.json",design);files["design_evidence"]={"path":str(out/"design-evidence.json")}
                if "knowledge"in _stage(s,"art")["files"]:
                    knowledge=reader_knowledge.project(root,_stage(s,"art"))
                    path=out/"knowledge-reading-evidence.json";io.write_new(path,knowledge)
                    data=path.read_bytes();files["knowledge_reading_evidence"]={"path":str(path),"sha256":io.digest(data),"bytes":len(data)}
            if role=="audit":
                io.write_new(out/"audit-stage-records.json",{"stages":s["stages"],"readers":s["reviews"],"rules":io.read(io.resolve(root,s["run"]["rules"])),"events":io.events(root)})
                files["stage_records"]={"path":str(out/"audit-stage-records.json")}
            files["frozen_first"]=_file(root,out/"own-frozen-first.json",previous["first"]["response"])
        # Prepared readers receive a directly readable copy. The ledger's
        # original relative snapshot remains provenance, never an instruction
        # to walk outside the clean packet or guess a reference base.
        readable_rules = _file(root,out/"canonical-rules.json",s["run"]["rules"])
        packet={"contract":CONTRACT,"packet_id":uuid.uuid4().hex,"run_id":s["run"]["run_id"],
                "role":role,"phase":phase,"source_sha256":run.source_sha(s,role),"created_at":io.now(),
                "criteria":CRITERIA[role],"files":files,"canonical_rules":readable_rules,
                "canonical_rules_origin":s["run"]["rules"],
                "original_context_id":previous.get("first",{}).get("context_id"),
                "instructions":["First reading uses only this prepared packet; freeze independent understanding before source comparison.","Read canonical_rules as the copied file; canonical_rules_origin is provenance metadata, not permission to open extra run files.","Comparison/confirmation preserves the original frozen reading. Use the original text-only context or explicitly validated fresh-context-frozen-reader-lineage; never impersonate the original physical context. Preserve earlier verdicts and record remaining/new issues.","Actually view every available page image; fields, source matching and reader retelling do not establish generic workflow improvement.","State unobserved scope. Shared filesystem boundaries are instruction-only unless a host attests stronger isolation."]}
        path=out/"reader-input.json";io.write_new(path,packet)
        io.append(root,"packet-prepared",{"role":role,"phase":phase,"packet":io.snapshot(root,path),"source_sha256":packet["source_sha256"]})
        return {"packet":str(path),"role":role,"phase":phase}


def _context(root,path,first=None,packet=None,packet_path=None):
    value=io.read(path)
    for key in ("context_id","execution_mode","model_identity_disclosure","limitations","host_receipt"):
        if key not in value:raise ValueError("actual context disclosure missing "+key)
    if not isinstance(value["context_id"],str) or not value["context_id"].strip():raise ValueError("actual context ID required")
    if not isinstance(value["limitations"],list) or not isinstance(value["model_identity_disclosure"],str):raise ValueError("disclose model identity and concrete isolation limitations")
    raw=Path(value["host_receipt"])
    if not raw.is_file():raise ValueError("preserve the actual host return, including an empty followup return")
    if first and (value["context_id"]!=first["context_id"] or value.get("execution_mode")=="fresh-context-frozen-reader-lineage"):
        from . import reader_history
        if packet is None or packet_path is None:
            raise ValueError("confirmation must use the original reader or explicitly validated frozen-reader lineage")
        reader_history.validate(root,value,first,packet,packet_path)
    return value,io.snapshot(root,path),io.snapshot(root,raw)


def record(root, packet_path, response_path, context_path):
    with io.locked(root):
        s=run.state(root);packet=io.read(packet_path);role,phase=packet["role"],packet["phase"]
        prepared=s["packets"].get((role,phase),{})
        if packet.get("contract")!=CONTRACT or packet.get("run_id")!=s["run"]["run_id"] or prepared.get("packet",{}).get("sha256")!=io.digest(Path(packet_path).read_bytes()):raise ValueError("use the actual current prepare packet")
        if packet["source_sha256"]!=run.source_sha(s,role):raise ValueError("reader packet is stale")
        review=s["reviews"].get(role,{})
        if phase=="first" and "first"in review:raise ValueError("independent first reading already frozen")
        first=review.get("first")
        context,context_ref,host_ref=_context(root,context_path,first if phase!="first"else None,packet,packet_path)
        if phase=="first" and context["execution_mode"]not in {"same-model-new-context","isolated-context","isolated-executor"}:raise ValueError("a fresh independent reader context is required; disclose unavailable capability instead of claiming a pass")
        if phase=="first" and any(context["context_id"]==r.get("first",{}).get("context_id")for name,r in s["reviews"].items()if name!=role):raise ValueError("distinct first-reader contexts required")
        response=io.read(response_path)
        if not isinstance(response,dict):raise ValueError("actual reader response object required")
        for field in ("findings","new_findings"):
            rows=response.get(field,[])
            if not isinstance(rows,list):raise ValueError("findings must be concrete arrays")
            ids=[]
            for row in rows:
                if not isinstance(row,dict)or any(not row.get(k)for k in ("id","observation","impact","evidence")):raise ValueError("findings require stable id, observation, impact and evidence")
                io.identifier(row["id"]);ids.append(row["id"])
            if len(ids)!=len(set(ids)):raise ValueError("finding IDs must be unique")
        payload={"role":role,"source_sha256":packet["source_sha256"],"packet":io.snapshot(root,packet_path),
                 "response":io.snapshot(root,response_path),"context":context_ref,"host_receipt":host_ref,
                 "context_id":context["context_id"],"canonical_rules":s["run"]["rules"]}
        if context.get("execution_mode")=="fresh-context-frozen-reader-lineage":
            payload["transport_method"]="fresh-context-frozen-reader-lineage"
            payload["history_continuity"]=context["history_continuity"]
        if phase=="first":
            if not isinstance(response.get("understanding"),list) or not response["understanding"] or any(not isinstance(v,str)or not v.strip()for v in response["understanding"])or not response.get("assessment") or not isinstance(response.get("findings"),list):raise ValueError("freeze substantive understanding, assessment and concrete findings")
            event="reader-first"
        elif phase=="comparison":
            if "comparison"in review:raise ValueError("original comparison already frozen")
            if response.get("verdict")not in {"pass","repair","deferred"} or not response.get("explanation") or not isinstance(response.get("findings"),list):raise ValueError("actual comparison verdict/explanation/findings required")
            if role=="audit" and response["verdict"]=="repair":raise ValueError("Supervisor audit is record-only; use deferred with findings, not a return")
            if response["verdict"]=="repair"and not response["findings"]:raise ValueError("repair needs concrete findings")
            payload["verdict"]=response["verdict"];event="reader-comparison"
        else:
            if "comparison"not in review:raise ValueError("original comparison required")
            own=any(a["reader"]==role for a in s["active_repairs"])
            changed=review.get("confirmation",review["comparison"])["source_sha256"]!=packet["source_sha256"]
            if not own and not changed:raise ValueError("confirmation requires a real own repair or changed upstream artifact")
            resolutions=response.get("resolutions");new=response.get("new_findings")
            if not isinstance(resolutions,list) or not isinstance(new,list):raise ValueError("resolutions and new_findings arrays required")
            original_ids=set()
            for item in (io.read(io.resolve(root,review["first"]["response"])),io.read(io.resolve(root,review["comparison"]["response"]))):
                original_ids.update(f["id"]for f in item.get("findings",[])if isinstance(f,dict)and"id"in f)
            if "confirmation"in review:
                prior=io.read(io.resolve(root,review["confirmation"]["response"]))
                original_ids.update(f["id"]for f in prior.get("new_findings",[])if isinstance(f,dict)and"id"in f)
            if len(resolutions)!=len(original_ids) or {v.get("id")for v in resolutions}!=original_ids:raise ValueError("resolve every original finding exactly once")
            if any(v.get("status")not in {"resolved","remaining"} or not v.get("explanation")for v in resolutions):raise ValueError("concrete resolved/remaining judgments required")
            remaining=any(v["status"]=="remaining"for v in resolutions)or bool(new)
            payload["verdict"]="repair"if remaining else"pass"
            payload["disposition"]="closed-with-findings"if remaining and s["returns"].get(role,0)>=1 else("needs-return"if remaining else"closed")
            event="reader-confirmed"
        return io.append(root,event,payload)
