#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Render PPTX through one LibreOffice process and one Poppler process."""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pptx", type=Path)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--dpi", type=int, default=160)
    args = parser.parse_args()
    source = args.pptx.resolve()
    output = args.output_dir.resolve()
    office = shutil.which("soffice") or shutil.which("libreoffice")
    raster = shutil.which("pdftoppm")
    if not source.is_file() or source.suffix.lower() != ".pptx":
        print("ERROR: source must be an existing .pptx", file=sys.stderr)
        return 2
    if not office:
        print("ERROR: LibreOffice is unavailable", file=sys.stderr)
        return 2
    if not raster:
        print("ERROR: pdftoppm is unavailable; PDF support remains optional until this render route is selected", file=sys.stderr)
        return 2
    output.mkdir(parents=True, exist_ok=True)
    subprocess.run([office, "--headless", "--convert-to", "pdf", "--outdir", str(output), str(source)], check=True)
    pdf = output / f"{source.stem}.pdf"
    if not pdf.is_file():
        print(f"ERROR: LibreOffice did not create {pdf}", file=sys.stderr)
        return 2
    subprocess.run([raster, "-png", "-r", str(args.dpi), str(pdf), str(output / "slide")], check=True)
    print(f"rendered {source} to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
