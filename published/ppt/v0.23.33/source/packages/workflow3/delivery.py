"""Mode-native paired delivery, portable evidence, and deterministic reporting."""
from __future__ import annotations
import json
import copy
from pathlib import Path
import shutil
import zipfile
from . import io, run

CONTRACT="io.clayz.presentation.mode-delivery/1.0"
REPORT_CONTRACT="io.clayz.presentation.mode-supervision-report/1.0"


def _read_response(root,item):
    return io.read(io.resolve(root,item["response"]))


def collect_report(root):
    s=run.state(root)
    if "output"not in s["stages"]:raise ValueError("actual Output files required")
    if "environment"not in s["run"]:raise ValueError("bind the actual same-run runtime preflight before delivery")
    mode=s["run"]["mode"]
    if mode!="fast":
        if not all(run.reader_closed(s,k)for k in run.READERS):raise ValueError("three current reader checks/confirmations required")
        audit=s["reviews"].get("audit",{}).get("comparison",{})
        if audit.get("source_sha256")!=run.source_sha(s,"audit") or audit.get("verdict")not in {"pass","deferred"}:raise ValueError("actual current Supervisor audit is required")
    if mode=="train" and "training"not in s["run"]:raise ValueError("train mode must bind its real external training package and session")
    readings={}
    for role,review in s["reviews"].items():
        readings[role]={phase:{"record":item,"actual_response":_read_response(root,item)}for phase,item in review.items()}
    output=s["stages"]["output"]["interface"]
    qa=io.read(io.resolve(root,output["files"]["qa"]))
    technical=output["details"].get("technical_observations",{})
    issues=bool(technical.get("unobserved_checks")or technical.get("failed_checks"))
    for role,value in readings.items():
        latest=value.get("confirmation",value.get("comparison",{})).get("actual_response",{})
        if latest.get("verdict")=="deferred" or latest.get("new_findings") or any(r.get("status")=="remaining"for r in latest.get("resolutions",[])):issues=True
        if "confirmation"not in value and latest.get("findings"):issues=True
    return {"contract":REPORT_CONTRACT,"created_at":io.now(),
            "run":s["run"],"mode":mode,"canonical_rules":s["run"]["rules"],
            "production_interfaces":s["stages"],"reader_records":readings,"return_counts":s["returns"],
            "actual_output_qa":qa,"history":io.events(root),
            "status":"issues-found"if issues else"record-complete",
            "review_scope":"fast has no independent readers/audit"if mode=="fast"else"content/layout/final readers plus record-only Supervisor audit; all original judgments retained",
            "quality_scope":"Record completeness is separate from observed quality. Missing/deferred checks are not a pass. One deck or protocol test cannot establish generic workflow improvement."}


def markdown(root,report):
    text=["# PPT完整工作报告", "", "模式："+report["mode"], "状态："+report["status"], "",report["review_scope"],report["quality_scope"],""]
    for stage,item in report["production_interfaces"].items():
        text += ["## "+stage,""]
        files=item["interface"]["files"]
        for role,ref in files.items():text += [f'- {role}: {ref["path"]} · SHA256 {ref["sha256"]}']
        if stage=="logic":text += ["",io.resolve(root,files["report"]).read_text(encoding="utf-8"),""]
        elif stage=="copy":
            from packages.copy_graph.model import markdown as graph_markdown
            projection=copy.deepcopy(io.read(io.resolve(root,files["graph"])))
            current_report=report["production_interfaces"]["logic"]["interface"]["files"]["report"]
            projection["research_report"]={"path":str(io.resolve(root,current_report)),"sha256":current_report["sha256"],"bytes":current_report["bytes"]}
            text += ["",graph_markdown(projection),""]
        elif stage=="art":
            design=io.read(io.resolve(root,files["design"]))
            for slide in design.get("slides",[]):
                text += ["### "+slide.get("slide_id",""),"", "```json",json.dumps(slide.get("design_intent",slide),ensure_ascii=False,indent=2),"```",""]
    text += ["## 原读者与审计记录", "", "```json",json.dumps(report["reader_records"],ensure_ascii=False,indent=2),"```", "", "## 原始Output QA", "", "```json",json.dumps(report["actual_output_qa"],ensure_ascii=False,indent=2),"```"]
    return "\n".join(text)+"\n"


def publish(root, destination, tool_snapshot=None, knowledge_snapshot=None):
    with io.locked(root):
        report=collect_report(root);out=Path(destination).resolve()
        if out.exists():raise ValueError("new delivery directory required")
        out.mkdir(parents=True)
        # Copy only declared current snapshots; historical JSON pointers are
        # evidence statements and are not replayed as current dependencies.
        evidence={}
        for path in sorted((Path(root)/"objects").iterdir()):
            if path.is_file():
                data=path.read_bytes()
                expected=path.name.split(".",1)[0]
                if io.digest(data)!=expected:raise ValueError("run snapshot changed")
                target=out/"objects"/path.name;target.parent.mkdir(exist_ok=True)
                target.write_bytes(data);evidence["objects/"+path.name]={"sha256":io.digest(data),"bytes":len(data)}
        for role,path in (("tool-snapshot",tool_snapshot),("knowledge-snapshot",knowledge_snapshot)):
            if path:
                raw=Path(path).read_bytes();name="resources/"+role+".zip";target=out/name;target.parent.mkdir(exist_ok=True);target.write_bytes(raw);evidence[name]={"sha256":io.digest(raw),"bytes":len(raw)}
        files=report["production_interfaces"]["output"]["interface"]["files"]
        for role,name in (("pptx","presentation.pptx"),("pdf","presentation.pdf")):
            (out/name).write_bytes(io.resolve(root,files[role]).read_bytes())
        io.write_new(out/"ppt-supervision-report.json",report)
        (out/"work-report.md").write_text(markdown(root,report),encoding="utf-8")
        pages=report["production_interfaces"]["output"]["interface"]["details"]["pages"]
        with zipfile.ZipFile(out/"all-pages.zip","x",zipfile.ZIP_DEFLATED)as archive:
            index=[]
            for i,page in enumerate(pages,1):
                raw=io.resolve(root,page["image"]).read_bytes();name=f'{i:03d}-'+page["slide_id"]+".png"
                archive.writestr(name,raw);index.append({"ordinal":i,"slide_id":page["slide_id"],"zip_member":name,"sha256":io.digest(raw),"bytes":len(raw)})
            archive.writestr("pages-index.json",json.dumps(index,ensure_ascii=False,indent=2))
        for name in ("presentation.pptx","presentation.pdf","ppt-supervision-report.json","work-report.md","all-pages.zip"):
            raw=(out/name).read_bytes();evidence[name]={"sha256":io.digest(raw),"bytes":len(raw)}
        manifest={"contract":CONTRACT,"mode":report["mode"],"run_id":report["run"]["run_id"],
                  "task_request_sha256":report["run"]["task_request_sha256"],"created_at":io.now(),
                  "report_contract":report["contract"],"files":evidence,"quality_status":report["status"],
                  "legacy_report3_6":"not-used; this is the explicitly versioned mode-native contract, not a reclassification of historical runs"}
        io.write_new(out/"delivery-manifest.json",manifest)
        verified=verify(out)
        io.append(root,"delivery-published",{"directory":str(out),"manifest_sha256":io.digest((out/"delivery-manifest.json").read_bytes()),"quality_status":report["status"]})
        return verified


def verify(destination):
    out=Path(destination).resolve();manifest=io.read(out/"delivery-manifest.json")
    if manifest.get("contract")!=CONTRACT:raise ValueError("mode-native delivery manifest required")
    for name,ref in manifest["files"].items():
        if Path(name).is_absolute() or ".."in Path(name).parts:raise ValueError("unsafe delivery member")
        path=out/name
        if not path.resolve().is_relative_to(out) or path.is_symlink():raise ValueError("delivery member escapes bundle")
        data=path.read_bytes()
        if len(data)!=ref["bytes"] or io.digest(data)!=ref["sha256"]:raise ValueError("delivery bytes changed: "+name)
    report=io.read(out/"ppt-supervision-report.json")
    if report["run"]["run_id"]!=manifest["run_id"] or report["mode"]!=manifest["mode"]:raise ValueError("report identity mismatch")
    for role,name in (("pptx","presentation.pptx"),("pdf","presentation.pdf")):
        expected=report["production_interfaces"]["output"]["interface"]["files"][role]
        if (out/name).read_bytes()!=io.resolve(out,expected).read_bytes():raise ValueError("delivered file differs from actual Output: "+role)
    if (out/"work-report.md").read_text()!=markdown(out,report):raise ValueError("readable report differs from its original JSON")
    # Every top-level current snapshot used by the report must still resolve.
    for item in report["production_interfaces"].values():
        for ref in item["interface"]["files"].values():io.resolve(out,ref)
    with zipfile.ZipFile(out/"all-pages.zip")as archive:
        index=json.loads(archive.read("pages-index.json"))
        expected=report["production_interfaces"]["output"]["interface"]["details"]["pages"]
        if [p["slide_id"]for p in index]!=[p["slide_id"]for p in expected]:raise ValueError("page index order changed")
        for item,page in zip(index,expected):
            if item["sha256"]!=page["image"]["sha256"]or item["bytes"]!=page["image"]["bytes"]:raise ValueError("page ZIP differs from actual Output render")
            raw=archive.read(item["zip_member"])
            if io.digest(raw)!=item["sha256"] or len(raw)!=item["bytes"]:raise ValueError("page ZIP identity mismatch")
    return {"contract":CONTRACT,"status":"verified","bundle":str(out),"mode":manifest["mode"],"run_id":manifest["run_id"],"quality_status":manifest["quality_status"],"pptx":str(out/"presentation.pptx"),"pdf":str(out/"presentation.pdf"),"report":str(out/"ppt-supervision-report.json"),"markdown":str(out/"work-report.md"),"page_count":len(index),"scope":"Current mode-native file/report bindings only; original quality findings and deferred checks remain."}
