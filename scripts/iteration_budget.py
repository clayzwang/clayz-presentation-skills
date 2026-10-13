#!/usr/bin/env python3
"""Bound task-local repair dispatches without changing any presentation gate."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path



def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def ref(path):
    path = Path(path).resolve()
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                bytes=path.stat().st_size)


def verify(value):
    if ref(value['path']) != value:
        raise ValueError('Iteration evidence bytes changed: ' + value['path'])


def state_path(lab, number):
    return Path(lab) / 'iteration-budgets' / f'r{number:02}.json'


def initialize(lab, number):
    policy = Path(lab) / 'iteration-policy.json'
    p = state_path(lab, number)
    if p.exists():
        value = read(p)
        verify(value['policy'])
        return p, value
    value = dict(round=number, policy=ref(policy), status='open', repairs=[],
                 historical_returns='not-reconstructed', cap_record=None)
    write(p, value)
    return p, value


def reserve(lab, number, issues, evidence, rationale, improvement):
    p, value = initialize(lab, number)
    limits = read(value['policy']['path'])['limits']
    if value['status'] != 'open':
        raise ValueError('Round is stopped; no additional repair dispatch')
    if not issues or not rationale.strip() or not improvement.strip():
        raise ValueError('Repair needs issue families, evidence, reason and observable improvement')
    if len(value['repairs']) >= limits['max_substantive_returns_per_company']:
        raise ValueError('Company repair limit reached; freeze findings and stop this round')
    for issue in set(issues):
        used = sum(issue in event['issues'] for event in value['repairs'])
        if used >= limits['max_repairs_per_issue_family']:
            raise ValueError('Issue-family repair limit reached: ' + issue)
    event = dict(issues=sorted(set(issues)), evidence=ref(evidence), rationale=rationale,
                 expected_observable_improvement=improvement,
                 reserved_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
    value['repairs'].append(event)
    write(p, value)
    return p, value


def cap(lab, number, cap_record, historical=False):
    p, value = initialize(lab, number)
    if historical and value['repairs']:
        raise ValueError('Historical cutoff must not relabel recorded current-policy repairs')
    if value['status'] != 'open':
        raise ValueError('Round is already stopped; preserve its original cutoff')
    record = read(cap_record)
    if record['round'] != number or record['delivery_verified'] is not False:
        raise ValueError('Cutoff cannot imply a verified delivery')
    if record['policy'] != value['policy']:
        raise ValueError('Cutoff policy differs from the enforced budget')
    verify(record['policy'])
    verify(record['user_steering'])
    if record['user_steering'] != read(value['policy']['path'])['user_steering']:
        raise ValueError('Cutoff must bind the original user steering')
    if not record['preserved_artifacts']:
        raise ValueError('Cutoff must preserve actual work and unresolved findings')
    for artifact in record['preserved_artifacts'].values():
        verify(artifact)
    value.update(status='capped', cap_record=ref(cap_record))
    if historical:
        value['historical_returns'] = 'existing overrun retained; not relabelled as two repairs'
    write(p, value)
    return p, value


def cap_existing(lab, number, cap_record):
    return cap(lab, number, cap_record, historical=True)


def admit_previous(lab, prior):
    if prior['status'] == 'complete-with-disclosed-limitations':
        return
    if prior['status'] != 'iteration-capped-with-open-findings':
        raise ValueError('Previous round is neither completed nor explicitly stopped')
    verify(prior['iteration_stop'])
    p, value = initialize(lab, prior['round'])
    if value['status'] != 'capped' or value['cap_record'] != prior['iteration_stop']:
        raise ValueError('Previous cutoff is not bound to the enforced repair budget')
    record = read(prior['iteration_stop']['path'])
    if record['round'] != prior['round'] or record['delivery_verified'] is not False:
        raise ValueError('Stopped round cannot be passed off as a delivery')
    if record['policy'] != value['policy']:
        raise ValueError('Stopped round is not bound to the enforced policy')
    verify(record['policy'])
    verify(record['user_steering'])
    for artifact in record['preserved_artifacts'].values():
        verify(artifact)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True, help='Task workspace containing iteration-policy.json')
    parser.add_argument('action', choices=['status', 'reserve', 'cap', 'cap-existing'])
    parser.add_argument('round', type=int)
    parser.add_argument('--issues', nargs='+')
    parser.add_argument('--evidence', type=Path)
    parser.add_argument('--rationale')
    parser.add_argument('--improvement')
    parser.add_argument('--cap-record', type=Path)
    args = parser.parse_args()
    if args.action == 'reserve':
        if not all([args.evidence, args.rationale, args.improvement]):
            parser.error('reserve requires --evidence, --rationale and --improvement')
        p, value = reserve(args.workspace, args.round, args.issues, args.evidence,
                           args.rationale, args.improvement)
    elif args.action in ['cap', 'cap-existing']:
        if not args.cap_record:
            parser.error('cap-existing requires --cap-record')
        p, value = cap(args.workspace, args.round, args.cap_record,
                       historical=args.action == 'cap-existing')
    else:
        p, value = initialize(args.workspace, args.round)
    print(json.dumps(dict(state=ref(p), budget=value), ensure_ascii=False))


if __name__ == '__main__':
    main()
