#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Lock real Art Direction drafts and export the three actual handoff documents."""
from __future__ import annotations
import argparse
import base64
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'packages' / 'validators'))
from story_handoff import build_stage_documents, digest, spec_digest, render_document
from validate_art_direction_plan import validate_plan
from validate_logic_package import validate_package
from config_policy import load_policy, load_config
from page_planning import (PLANNING_CONTRACT, validate_planning_record,
                           planning_reference, planning_markdown)


def write_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(value)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['record-planning', 'lock-design', 'export', 'logic-document'])
    parser.add_argument('--package', type=Path, required=True)
    parser.add_argument('--plan', type=Path)
    parser.add_argument('--planning', type=Path)
    parser.add_argument('--config', type=Path)
    parser.add_argument('--title-review', type=Path)
    parser.add_argument('--content-review', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        package = json.loads(args.package.read_text(encoding='utf-8'))
        if package.get('contract_version') not in {'3.0', '3.1', '3.2', '3.3', '3.4'}:
            raise ValueError('story/research handoffs require a supported package 3.x')
        if args.command in {'record-planning', 'lock-design'} and load_config(args.config).get('workflow', {}).get('reader_review', {}).get('phases') == ['title', 'content', 'final']:
            from packages.validators.reader_review import check_art_gate
            check_art_gate(package, args.title_review, args.content_review)
        if args.command == 'record-planning':
            if args.plan is None or package.get('contract_version') != '3.4':
                raise ValueError('record-planning requires --plan draft and Copy package 3.4')
            from validate_ppt_package import validate_package as validate_copy
            errors = validate_copy(package, 'copy-approved')
            draft = json.loads(args.plan.read_text(encoding='utf-8'))
            errors.extend(validate_planning_record(package, draft, require_recorded=False))
            if errors:
                raise ValueError('\n'.join(errors))
            draft.update(contract=PLANNING_CONTRACT, package_id=package['package_id'],
                         package_version=package['version'], copy_package_sha256=digest(package),
                         recorded_at=datetime.now(timezone.utc).isoformat())
            write_new(args.output, json.dumps(draft, ensure_ascii=False, indent=2)+'\n')
        elif args.command == 'logic-document':
            errors = validate_package(package, 'logic-approved')
            if package.get('status') != 'logic-approved':
                errors.append('provide original Logic artifact, not Copy projection')
            if errors:
                raise ValueError('\n'.join(errors))
            write_new(args.output, render_document('logic', package))
        else:
            if args.plan is None:
                raise ValueError('--plan is required')
            plan = json.loads(args.plan.read_text(encoding='utf-8'))
            if args.command == 'lock-design':
                if plan.get('visual_baseline', {}).get('status') == 'locked':
                    raise ValueError('already locked; create a new draft revision instead of relocking')
                if args.planning is not None:
                    plan['page_planning'] = planning_reference(args.planning)
                plan.setdefault('visual_baseline', {}).update(
                    status='locked', locked_at=datetime.now(timezone.utc).isoformat(),
                    copy_package_sha256=digest(package), spec_sha256=spec_digest(plan))
            errors = validate_plan(package, plan, load_policy(args.config))
            if errors:
                raise ValueError('\n'.join(errors))
            if args.command == 'lock-design':
                write_new(args.output, json.dumps(plan, ensure_ascii=False, indent=2)+'\n')
            else:
                bundle = build_stage_documents(package, plan)
                if args.output.exists():
                    raise ValueError('export destination already exists')
                args.output.mkdir(parents=True)
                for stage, document in bundle['documents'].items():
                    write_new(args.output / f'{stage}.md', document['markdown'])
                if plan.get('contract_version') == '2.3':
                    write_new(args.output / 'art-page-planning.md', planning_markdown(plan['page_planning']['content']))
                    write_new(args.output / 'art-page-planning.json',
                              base64.b64decode(plan['page_planning']['base64']).decode('utf-8'))
                write_new(args.output / 'stage-documents.json', json.dumps(bundle, ensure_ascii=False, indent=2)+'\n')
        print(f'PASS: {args.command}: {args.output}')
        return 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
