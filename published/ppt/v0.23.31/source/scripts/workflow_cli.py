#!/usr/bin/env python3
"""Fast/normal/train workflow with three explicit stage interfaces."""
from pathlib import Path
import argparse
import json
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from packages.workflow3 import io,run,readers,interfaces,delivery


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest="command",required=True)
    a=sub.add_parser("init");a.add_argument("--directory",required=True);a.add_argument("--task",required=True);a.add_argument("--mode",choices=run.MODES,default="normal");a.add_argument("--config");a.add_argument("--knowledge-manifest")
    a=sub.add_parser("status");a.add_argument("--run",required=True)
    a=sub.add_parser("commit");a.add_argument("--run",required=True);a.add_argument("--stage",choices=interfaces.STAGES,required=True);a.add_argument("--files",required=True,help="JSON object: role to actual file path");a.add_argument("--actor-context")
    a=sub.add_parser("project");a.add_argument("--run",required=True);a.add_argument("--stage",choices=interfaces.STAGES,required=True);a.add_argument("--output",required=True);a.add_argument("--brief",help="Role-specific professional requirements JSON, not a runtime envelope")
    a=sub.add_parser("reader-prepare");a.add_argument("--run",required=True);a.add_argument("--role",choices=readers.CRITERIA,required=True);a.add_argument("--phase",choices=["first","comparison","confirmation"],required=True);a.add_argument("--output",required=True)
    a=sub.add_parser("reader-record");a.add_argument("--run",required=True);a.add_argument("--packet",required=True);a.add_argument("--response",required=True);a.add_argument("--context",required=True)
    a=sub.add_parser("repair");a.add_argument("--run",required=True);a.add_argument("--reader",choices=run.READERS,required=True)
    a=sub.add_parser("environment");a.add_argument("--run",required=True);a.add_argument("--receipt",required=True)
    a=sub.add_parser("bind-training");a.add_argument("--run",required=True);a.add_argument("--package",required=True);a.add_argument("--session",required=True)
    a=sub.add_parser("publish");a.add_argument("--run",required=True);a.add_argument("--output",required=True);a.add_argument("--tool-snapshot");a.add_argument("--knowledge-snapshot")
    a=sub.add_parser("verify-handoff");a.add_argument("--bundle",required=True)
    a=p.parse_args(argv)
    try:
        if a.command=="init":result=run.init(a.directory,a.task,a.mode,a.config,a.knowledge_manifest)
        elif a.command=="status":
            s=run.state(a.run);result={"run_id":s["run"]["run_id"],"mode":s["run"]["mode"],"current_stages":list(s["stages"]),"returns":s["returns"],"reader_closed":{r:run.reader_closed(s,r)for r in run.READERS if s["run"]["mode"]!="fast"},"active_repair":s["active_repair"]}
        elif a.command=="commit":result=run.commit_stage(a.run,a.stage,io.read(a.files),a.actor_context)
        elif a.command=="project":
            s=run.state(a.run);source={"copy":"logic","art":"copy","output":"art"}.get(a.stage)
            if s["run"]["mode"]=="train"and"training"not in s["run"]:raise ValueError("bind explicit training goals before author preparation")
            gate={"art":"content","output":"layout"}.get(a.stage)
            if s["run"]["mode"]!="fast"and gate and not run.reader_closed(s,gate):raise ValueError("finish the current "+gate+" reader before author preparation")
            brief=io.read(a.brief)if a.brief else{}
            stage_goals=[]
            if "training"in s["run"]:
                session=io.read(io.resolve(a.run,s["run"]["training"]["session"]))
                stage_goals=[row["goal"]for row in session["goals"]if row["goal"]["stage"]==a.stage]
            if a.stage=="logic":brief={**brief,"user_request":io.resolve(a.run,s["run"]["task_request"]).read_text(encoding="utf-8")}
            result={"professional_input":interfaces.professional_projection(a.run,a.stage,s["stages"][source]["interface"]if source else{},a.output,brief,stage_goals)}
        elif a.command=="reader-prepare":result=readers.prepare(a.run,a.role,a.phase,a.output)
        elif a.command=="reader-record":result=readers.record(a.run,a.packet,a.response,a.context)
        elif a.command=="repair":result=run.begin_repair(a.run,a.reader)
        elif a.command=="environment":result=run.bind_environment(a.run,a.receipt)
        elif a.command=="bind-training":result=run.bind_training(a.run,a.package,a.session)
        elif a.command=="publish":result=delivery.publish(a.run,a.output,a.tool_snapshot,a.knowledge_snapshot)
        else:result=delivery.verify(a.bundle)
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0
    except (OSError,ValueError,KeyError,TypeError)as e:
        print(json.dumps({"status":"failed","error":str(e)},ensure_ascii=False),file=sys.stderr);return 2


if __name__=="__main__":raise SystemExit(main())
