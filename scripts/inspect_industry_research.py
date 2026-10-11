#!/usr/bin/env python3
"""Inspect an optional industry research ledger and retain its real result."""
import argparse, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from packages.validators.industry_research import inspect
parser = argparse.ArgumentParser()
parser.add_argument('ledger'); parser.add_argument('--sources', required=True); parser.add_argument('--output', required=True)
args = parser.parse_args()
load = lambda p: json.loads(pathlib.Path(p).read_text())
result = inspect(load(args.ledger), [r['source_id'] for r in load(args.sources)])
pathlib.Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
print(json.dumps(result, ensure_ascii=False))
sys.exit(0 if result['ok'] else 1)
