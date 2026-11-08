#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Verify all evidence hashes and restore a portable report to its full legacy representation."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'packages' / 'validators'))
from report_evidence import load_report

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('report', type=Path)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        p.error('refusing to overwrite an existing file')
    a.output.write_text(json.dumps(load_report(a.report), ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

if __name__ == '__main__':
    main()
