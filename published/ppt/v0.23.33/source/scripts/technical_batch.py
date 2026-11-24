"""Execute one immutable technical plan; show only bounded technical summaries."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from packages.technical_batch import execute
from packages.transport_economy import write_new

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--plan',type=Path,required=True)
p.add_argument('--registry',type=Path,required=True)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
visible,code=execute(a.plan,a.registry,a.output)
raw=(json.dumps(visible,ensure_ascii=False)+'\n').encode('utf-8')
written=sys.stdout.buffer.write(raw)
sys.stdout.buffer.flush()
write_new(a.output/'cli-output-accounting.json',dict(
    actual_cli_stdout_bytes=written,actual_model_visible_bytes=None,
    scope='Observed bytes written by this CLI to its stdout. A caller may redirect, filter or summarize it; this does not attest bytes forwarded to the model or VPN.'))
raise SystemExit(code)
