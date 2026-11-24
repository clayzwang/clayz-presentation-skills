#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Verify licensed release fonts and prepare a task-local Fontconfig environment."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]


def verified_fonts(root=ROOT, *, require=True):
    root = Path(root).resolve()
    manifest = root / 'assets/fonts/manifest.json'
    if not manifest.is_file():
        if require:
            raise ValueError('release font manifest is missing')
        return []
    data = json.loads(manifest.read_text(encoding='utf-8'))
    fonts = data.get('fonts', [])
    required = set(data.get('required_families', []))
    if require and required and not fonts:
        raise ValueError('required release font bytes and redistribution authorization are pending')
    result = []
    for entry in fonts:
        path = (root / entry['path']).resolve()
        license_path = (root / entry['license_path']).resolve()
        if not path.is_relative_to(root / 'assets/fonts') or not license_path.is_relative_to(root / 'assets/fonts'):
            raise ValueError('font or license path escapes font bundle')
        if entry.get('redistribution_authorized') is not True or not entry.get('source'):
            raise ValueError('font requires recorded source and redistribution authorization')
        for file, digest in [(path, entry['sha256']), (license_path, entry['license_sha256'])]:
            if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest() != digest:
                raise ValueError('font/license bytes differ from release manifest')
        if path.stat().st_size != entry['bytes']:
            raise ValueError('font byte count mismatch')
        result.append({**entry, 'resolved_path': str(path)})
    if require and required - {e['family'] for e in result}:
        raise ValueError('required font families are missing from the authorized bundle')
    return result


def prepare_fontconfig(task_dir, root=ROOT):
    fonts = verified_fonts(root)
    if not fonts:
        raise ValueError('No redistributable font is bundled. Install the requested font from a licensed source and verify it in the render environment; missing-font rendering remains diagnostic.')
    directory = Path(task_dir).resolve() / 'font-runtime'
    directory.mkdir(parents=True, exist_ok=True)
    config = directory / 'fonts.conf'
    font_dir = Path(root).resolve() / 'assets/fonts'
    config.write_text('<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd"><fontconfig>'
                      '<include ignore_missing="yes">/etc/fonts/fonts.conf</include>'
                      f'<dir>{escape(str(font_dir))}</dir><cachedir>{escape(str(directory / "cache"))}</cachedir>'
                      '</fontconfig>', encoding='utf-8')
    env = dict(os.environ, FONTCONFIG_FILE=str(config))
    if not shutil.which('fc-match'):
        raise ValueError('Fontconfig unavailable; install bundled fonts in the target application and verify there')
    observations = []
    for font in fonts:
        result = subprocess.run(['fc-match', '-f', '%{file}', font['family']], env=env,
                                check=True, capture_output=True, text=True, timeout=30)
        actual = Path(result.stdout.strip()).resolve()
        if actual != Path(font['resolved_path']):
            raise ValueError(f"font substitution: {font['family']} did not resolve to bundled bytes")
        observations.append({'family':font['family'], 'path':str(actual), 'sha256':font['sha256']})
    receipt = {'status':'font-bytes-resolved', 'environment':{'FONTCONFIG_FILE':str(config)},
               'fonts': observations, 'limitations':['Not PowerPoint/WPS native rendering acceptance.']}
    (directory / 'font-receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    return receipt


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=ROOT)
    p.add_argument('--prepare', type=Path, help='task root for isolated Fontconfig registration')
    a = p.parse_args()
    print(json.dumps(prepare_fontconfig(a.prepare, a.root) if a.prepare else verified_fonts(a.root), ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
