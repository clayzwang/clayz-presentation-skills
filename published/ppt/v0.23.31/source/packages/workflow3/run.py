"""The shared four-stage path and bounded, reader-specific returns."""
from __future__ import annotations
import copy
import os
from pathlib import Path
import subprocess
import sys
from . import CONTRACT, io, interfaces

ROOT = Path(__file__).resolve().parents[2]
MODES = ("fast", "normal", "train")
READERS = {"content":{"after":"copy","return_to":"logic"},
           "layout":{"after":"art","return_to":"art"},
           "final":{"after":"output","return_to":"copy"}}


def init(directory, task, mode="normal", config=None, knowledge_manifest=None):
    if mode not in MODES: raise ValueError("mode must be fast, normal or train")
    root = Path(directory).resolve()
    if root == ROOT or ROOT in root.parents:
        raise ValueError("run files must be outside the tool installation")
    if root.exists() and any(root.iterdir()): raise ValueError("new run requires an empty directory")
    root.mkdir(parents=True,exist_ok=True)
    request = io.snapshot(root,task)
    preferred=ROOT/"config/personal-extension-resolved.json"
    cfg = io.read(config or (preferred if preferred.is_file()else ROOT/"config/default.json"))
    # The legacy title/content/final gate belongs to the legacy report path.
    # New mode gates live below; there is one resolved config for this run.
    cfg = copy.deepcopy(cfg)
    cfg["workflow"]["reader_review"]["required"] = False
    # Three independently bounded reader returns may each replay downstream
    # production. Do not silently reuse a legacy global one-repair budget.
    # Actual use is still recorded; these maxima are route ceilings, not work
    # to consume or permission to rerender without a new change/failure.
    if mode!="fast":
        cfg["runtime"]["budgets"].update(maximum_authoring_writes=4,maximum_repair_cycles=3,maximum_full_deck_renders=4)
    cfg["workflow"]["mode_system"] = {
        "contract":CONTRACT,"mode":mode,"production_stages":list(interfaces.STAGES),
        "readers":{} if mode=="fast" else copy.deepcopy(READERS),
        "reader_return_limit":1,"supervisor_audit":mode!="fast",
        "training_package_required":mode=="train",
        "legacy_reader_gate":"replaced-by-mode-workflow; not a reader pass"}
    cfg_path = root/"task-config.json";io.write_new(cfg_path,cfg)
    challenge_path=root/"run-challenge.json"
    cmd=[sys.executable,"-B",str(ROOT/"scripts/runtime_preflight.py"),"--issue-challenge",
         "--task-request",str(io.resolve(root,request)),"--output",str(challenge_path)]
    result=subprocess.run(cmd,capture_output=True,text=True,env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"})
    io.write_new(root/"challenge-command.json",{"command":cmd,"exit_code":result.returncode,"stdout":result.stdout,"stderr":result.stderr})
    if result.returncode: raise ValueError("native run-challenge issuance failed; original failure retained")
    challenge=io.read(challenge_path)
    knowledge=io.snapshot(root,knowledge_manifest) if knowledge_manifest else None
    rules={"contract":"io.clayz.presentation.canonical-workflow-rules/1.0",
           "task_request":request,"mode":mode,"production_stages":list(interfaces.STAGES),
           "reader_plan":cfg["workflow"]["mode_system"]["readers"],"return_limit_each":1,
           "source_of_authority":"current user request; unspecified professional rules inherit the bound tool and knowledge",
           "quality_policy":"preserve fail/deferred/unknown; only explicit user release conditions block otherwise complete quality-limited delivery"}
    rules_path=root/"workflow-rules.json";io.write_new(rules_path,rules)
    value={"contract":CONTRACT,"run_id":challenge["run_id"],"created_at":io.now(),"mode":mode,
           "task_request":request,"task_request_sha256":request["sha256"],
           "config":io.snapshot(root,cfg_path),"rules":io.snapshot(root,rules_path),
           "challenge":io.snapshot(root,challenge_path),"knowledge_manifest":knowledge,
           "tool_version":(ROOT/"VERSION").read_text().strip(),"readers":rules["reader_plan"]}
    io.write_new(root/"run.json",value)
    (root/"events").mkdir()
    with io.locked(root):io.append(root,"initialized",{"canonical_rules":value["rules"]})
    return value


def state(root):
    value=io.read(Path(root)/"run.json")
    if value.get("contract")!=CONTRACT:raise ValueError("supported mode workflow required")
    for key in ("task_request","config","rules","challenge"):
        io.resolve(root,value[key])
    stages,reviews,returns,active,packets={}, {}, {k:0 for k in READERS}, [], {}
    for event in io.events(root):
        kind,p=event["kind"],event["payload"]
        if kind=="stage-committed": stages[p["stage"]]={**p,"event_sha256":event["record_sha256"]}
        elif kind=="reader-first": reviews.setdefault(p["role"],{})["first"]=p
        elif kind=="reader-comparison": reviews.setdefault(p["role"],{})["comparison"]=p
        elif kind=="repair-started":
            returns[p["reader"]]+=1;active.append(p)
            start=interfaces.STAGES.index(p["owner"])
            for stage in interfaces.STAGES[start:]:stages.pop(stage,None)
            # Keep all original reader identities and frozen first readings.
            # Their source hashes become stale automatically, requiring a
            # same-reader refresh on affected new downstream files.
        elif kind=="reader-confirmed":
            reviews.setdefault(p["role"],{})["confirmation"]=p
            active=[a for a in active if a["reader"]!=p["role"]]
        elif kind=="environment-recorded":value["environment"]=p
        elif kind=="training-bound":value["training"]=p
        elif kind=="packet-prepared":packets[(p["role"],p["phase"])]=p
    return {"run":value,"stages":stages,"reviews":reviews,"returns":returns,"active_repair":active[-1]if active else None,"active_repairs":active,"packets":packets}


def reader_closed(s,role):
    review=s["reviews"].get(role,{})
    spec=READERS.get(role)
    if spec and spec["after"] not in s["stages"]:return False
    current=source_sha(s,role)
    for phase in ("confirmation","comparison"):
        item=review.get(phase,{})
        if item.get("source_sha256")!=current:continue
        if item.get("verdict")=="pass":return True
        if phase=="confirmation" and s["returns"].get(role,0)>=1:return True
    return False


def source_sha(s,role):
    if role in READERS:
        stage=s["stages"].get(READERS[role]["after"])
        if not stage:raise ValueError("reader producer stage is not current")
        return stage["event_sha256"]
    if role=="audit":
        if any(k not in s["stages"] for k in interfaces.STAGES):raise ValueError("actual final output required")
        selected={k:s["stages"][k]["event_sha256"]for k in interfaces.STAGES}
        selected["reader_records"]={k:s["reviews"].get(k,{})for k in READERS}
        return io.digest(io.canonical(selected))
    raise ValueError("unknown reader role")


def commit_stage(root, stage, paths, actor_context=None):
    stage="art" if stage=="art-direction" else stage
    if stage not in interfaces.STAGES:raise ValueError("unknown production stage")
    with io.locked(root):
        s=state(root);index=interfaces.STAGES.index(stage)
        if s["run"]["mode"]=="train"and"training"not in s["run"]:raise ValueError("bind explicit training goals before any production stage starts")
        if stage in s["stages"]:raise ValueError("stage already active; use its bounded reader return, not an unrecorded overwrite")
        if any(k not in s["stages"]for k in interfaces.STAGES[:index]):raise ValueError("upstream stage is not current")
        if stage=="art" and s["run"].get("knowledge_manifest") and "knowledge"not in paths:raise ValueError("Art must preserve its actual knowledge reading/application evidence")
        if s["run"]["mode"]!="fast":
            gate={"art":"content","output":"layout"}.get(stage)
            if gate and not reader_closed(s,gate):raise ValueError(gate+" reader must finish before this stage")
        dependency=s["stages"].get(interfaces.STAGES[index-1],{}).get("interface") if index else None
        if stage=="art":dependency={**dependency,"logic_dependency":s["stages"]["logic"]["interface"]}
        artifact=interfaces.capture(root,stage,paths,dependency)
        if stage=="copy":artifact["logic_dependency"]=s["stages"]["logic"]["interface"]
        payload={"stage":stage,"interface":artifact,"canonical_rules":s["run"]["rules"],"actor_context":actor_context}
        return io.append(root,"stage-committed",payload)


def begin_repair(root, role):
    if role not in READERS:raise ValueError("only content/layout/final readers have a return")
    with io.locked(root):
        s=state(root)
        if s["run"]["mode"]=="fast":raise ValueError("fast mode has no independent reader returns")
        if any(a["reader"]==role for a in s["active_repairs"]):raise ValueError("this reader return is already in progress")
        review=s["reviews"].get(role,{})
        latest=review.get("confirmation",review.get("comparison",{}))
        if latest.get("verdict")!="repair" or latest.get("source_sha256")!=source_sha(s,role):raise ValueError("actual current reader repair verdict required")
        if s["returns"][role]>=1:raise ValueError("this reader's single return is already used; retain residuals")
        return io.append(root,"repair-started",{"reader":role,"owner":READERS[role]["return_to"],"number":1,"from_comparison":review["comparison"],"canonical_rules":s["run"]["rules"]})


def bind_environment(root, receipt):
    with io.locked(root):
        s=state(root);v=io.read(receipt)
        if v.get("contract")!="io.clayz.presentation.runtime-preflight/1.3"or not v.get("scan_id")or v.get("selected_route",{}).get("locked")is not True:raise ValueError("actual native preflight contract and locked route required")
        binding=v.get("run_binding",v.get("binding",{}))
        if binding.get("run_id")!=s["run"]["run_id"] or binding.get("task_request_sha256")!=s["run"]["task_request_sha256"]:
            raise ValueError("preflight must bind this issued run and exact task bytes")
        if v.get("config_binding",{}).get("sha256")!=s["run"]["config"]["sha256"]:raise ValueError("preflight must use this single resolved configuration")
        if binding.get("challenge_sha256")!=s["run"]["challenge"]["sha256"]:raise ValueError("preflight must consume this issued challenge")
        ledgers={}
        for key in ("issuance_receipt","consumption_receipt"):
            raw=Path(binding[key]).read_bytes()
            if io.digest(raw)!=binding[key+"_sha256"]:raise ValueError("native challenge ledger bytes changed")
            ledgers[key]=io.snapshot(root,binding[key])
        if "environment"in s["run"]:raise ValueError("capability scan is already bound")
        return io.append(root,"environment-recorded",{"receipt":io.snapshot(root,receipt),"ledgers":ledgers})


def bind_training(root, training_manifest, session):
    with io.locked(root):
        s=state(root)
        if s["run"]["mode"]!="train":raise ValueError("training binding belongs to train mode")
        if "training"in s["run"]:raise ValueError("training package already bound")
        manifest=io.read(training_manifest);value=io.read(session)
        if manifest.get("contract")!="io.clayz.presentation.training-package/1.0" or value.get("contract")!="io.clayz.presentation.training-session/1.0"or value.get("production_run_id")!=s["run"]["run_id"]or not value.get("goals"):
            raise ValueError("actual compatible training package/session for this run required")
        if value.get("production_run",{}).get("sha256")!=io.digest((Path(root)/"run.json").read_bytes()):raise ValueError("training session must pin this actual immutable production run")
        return io.append(root,"training-bound",{"package":io.snapshot(root,training_manifest),"session":io.snapshot(root,session)})
