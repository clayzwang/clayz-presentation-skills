"""Batch deterministic local commands without replaying full technical stdout.

Professional reading and judgment stay outside this API. This is not a sandbox,
budget authority, host-history deletion API, or a provider/VPN usage meter.
"""
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys
import time
from . import transport_economy as transport

CONTRACT='io.clayz.presentation.technical-batch/1'


def execute(plan_path, registry, output):
    plan_path=Path(plan_path).resolve(strict=True)
    plan=json.loads(plan_path.read_text())
    if plan.get('contract')!=CONTRACT:raise ValueError('technical_batch_contract_required')
    case=Path(plan['case_root']).resolve(strict=True)
    transport.within(plan_path,case)
    packet=transport.verify(plan['packet'])
    _,binding=transport.validate_scope(case,packet)
    if binding['run_id']!=plan['run_id']:raise ValueError('technical_batch_foreign_run')
    store=transport.Economy(registry)
    context=store.require_context(plan['context_id'],case,plan['run_id'])
    if context['role']!=plan['role']:raise ValueError('technical_batch_foreign_role')
    with store.connection() as db:
        transport.history_lifecycle.require_text_only_continuation(db,plan['context_id'])
    actions=plan.get('actions')
    if not isinstance(actions,list) or not actions:raise ValueError('finite_explicit_actions_required')
    tool=Path(__file__).resolve().parents[1]
    native_directory=binding.get('inheritance',{}).get('tool',{}).get('directory')
    native_tool=Path(native_directory).resolve(strict=True) if native_directory else None
    identifiers=[]
    for action in actions:
        name=action.get('id','')
        if not re.fullmatch(r'[A-Za-z0-9_-]{1,64}',name):raise ValueError('stable_action_id_required')
        identifiers.append(name)
        program=transport.verify(action['program'])
        if not (program.is_relative_to(case) or program.is_relative_to(tool) or
                (native_tool is not None and program.is_relative_to(native_tool))):
            raise ValueError('program_must_belong_to_current_case_or_bound_tool')
        if program.name=='office-runtime.py':raise ValueError('Office_stays_in_original_budgeted_runner')
        args=action.get('arguments',[])
        if not isinstance(args,list) or any(not isinstance(v,str) for v in args):
            raise ValueError('literal_argument_array_required')
        for arg in args:
            for round_name in re.findall(r'rounds/(R\d{2})(?:/|\b)',arg):
                if round_name!=case.name:raise ValueError('foreign_round_argument')
        timeout=action.get('timeout_seconds',120)
        if type(timeout) is not int or not 1<=timeout<=600:raise ValueError('bounded_timeout_required')
    if len(set(identifiers))!=len(identifiers):raise ValueError('unique_action_ids_required')
    output=transport.within(output,case)
    output.mkdir(parents=True,exist_ok=False)
    transport.write_new(output/'input-plan.json',plan)
    records=[];exitcode=0
    for action in actions:
        # Recheck each source immediately before execution; later actions are
        # never silently retried after partial success or a failure.
        program=transport.verify(action['program'])
        argv=[sys.executable,'-B',str(program),*action.get('arguments',[])]
        stdout=output/(action['id']+'.stdout.txt');stderr=output/(action['id']+'.stderr.txt')
        started=datetime.now(timezone.utc).isoformat();tick=time.monotonic();timed_out=False
        with stdout.open('xb') as out,stderr.open('xb') as err:
            try:
                result=subprocess.run(argv,cwd=case,stdout=out,stderr=err,
                    timeout=action.get('timeout_seconds',120),shell=False)
                code=result.returncode
            except subprocess.TimeoutExpired:
                code=124;timed_out=True
        summary=transport.command_summary(stdout.read_bytes(),stderr.read_bytes(),code)
        record=dict(id=action['id'],argv=argv,program=action['program'],returncode=code,
            timed_out=timed_out,started_at=started,wall_seconds=time.monotonic()-tick,
            stdout=transport.ref(stdout),stderr=transport.ref(stderr),summary=summary)
        transport.write_new(output/(action['id']+'.receipt.json'),record)
        records.append(record)
        if code:exitcode=code;break
    receipt=dict(contract='io.clayz.presentation.technical-batch-receipt/1',
        plan=transport.ref(plan_path),context_id=plan['context_id'],run_id=plan['run_id'],
        actions=records,planned_actions=len(actions),executed_actions=len(records),
        returncode=exitcode,professional_evaluation_changed=False,
        host_or_provider_token_saving=None,vpn_bytes_saved=None,
        scope='Actual deterministic commands and exact local outputs. Full professional evidence is separately read; no model judgment or permission isolation is attested.')
    transport.write_new(output/'receipt.json',receipt)
    visible=dict(batch_receipt=transport.ref(output/'receipt.json'),returncode=exitcode,
        executed_actions=len(records),planned_actions=len(actions),
        actions=[dict(id=r['id'],returncode=r['returncode'],summary=r['summary']) for r in records])
    raw=(json.dumps(visible,ensure_ascii=False)+'\n').encode()
    transport.write_new(output/'model-output-accounting.json',dict(
        serialized_cli_summary_bytes=len(raw),
        actual_cli_stdout_bytes=None,actual_model_visible_bytes=None,
        raw_technical_stdout_bytes=sum(r['stdout']['bytes'] for r in records),
        raw_technical_stderr_bytes=sum(r['stderr']['bytes'] for r in records),
        actual_batch_api_invocations=1,deterministic_commands_executed=len(records),
        provider_token_saving=None,vpn_bytes_saved=None,
        scope='Exact size of the serialized CLI-shaped result. The API returns data and emits no stdout. CLI emission is separately recorded; caller forwarding/model bytes/provider tokens/VPN savings remain unobserved.'))
    return visible,exitcode
