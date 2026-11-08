"""Small stdout CLI; full transport evidence stays in governed local files."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from packages.transport_economy import Economy, validate_scope, write_new


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--registry', type=Path, required=True)
    sub = p.add_subparsers(dest='command', required=True)
    c = sub.add_parser('context')
    for name in ('context-id', 'case', 'run-id', 'role', 'mode'):
        c.add_argument('--'+name, required=True)
    c.add_argument('--fork-turns')
    c.add_argument('--provenance', default='caller-observed-dispatch')
    a = sub.add_parser('prepare')
    for name in ('case', 'packet', 'context-id', 'output'):
        a.add_argument('--'+name, required=True)
    a.add_argument('--reread-reason')
    old = sub.add_parser('adopt')
    for name in ('case', 'packet', 'context-id', 'coverage'):
        old.add_argument('--'+name, required=True)
    v = sub.add_parser('observe')
    for name in ('entry-id', 'context-id', 'observation'):
        v.add_argument('--'+name, required=True)
    v.add_argument('--actual-data-url-chars', type=int)
    v.add_argument('--mime')
    v.add_argument('--reuse', action='store_true')
    f = sub.add_parser('complete')
    for name in ('plan-path', 'context-id', 'coverage'):
        f.add_argument('--'+name, required=True)
    r = sub.add_parser('report')
    r.add_argument('--case')
    r.add_argument('--output', type=Path)
    x = sub.add_parser('scope')
    x.add_argument('--case', required=True)
    x.add_argument('--packet', required=True)
    x.add_argument('--prompt')
    args = vars(p.parse_args())
    store, command = Economy(args.pop('registry')), args.pop('command')
    if command == 'scope':
        payload, binding = validate_scope(**args)
        result = dict(scope_valid=True, run_id=binding['run_id'],
                      packet_id=payload.get('packet_id'))
    elif command == 'report':
        output = args.pop('output')
        result = store.report(**args)
        if output:
            write_new(output, result)
    else:
        result = getattr(store, command)(**args)
        if command == 'prepare':
            result = dict(plan_path=args['output'], pages=len(result['items']),
                          send=sum(i['action']=='send' for i in result['items']),
                          reuse=sum(i['action']!='send' for i in result['items']))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
