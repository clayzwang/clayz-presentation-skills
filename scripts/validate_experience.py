#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Validate the static experience center, its manifest, and web assets."""

from __future__ import annotations

import argparse
import json
import re
from html.parser import HTMLParser
from pathlib import Path, PurePosixPath

from PIL import Image


EXPERIENCE_ROOT = Path("experience")
MANIFEST_PATH = EXPERIENCE_ROOT / "case-manifest.json"
LOCAL_PREFIXES = ("assets/", "app.js", "styles.css")
SLIDE_SOURCE_PATTERN = re.compile(r'\bsrc:\s*"([^"]+)"')


class AssetParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []
        self.assets: list[str] = []
        self.images_without_alt: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if attributes.get("id"):
            self.ids.append(attributes["id"] or "")
        if tag == "img" and "alt" not in attributes:
            self.images_without_alt.append(attributes.get("src") or "<missing src>")
        for attribute in ("src", "href"):
            value = attributes.get(attribute)
            if value and value.startswith(LOCAL_PREFIXES):
                self.assets.append(value)


def _safe_relative(value: str) -> Path | None:
    pure = PurePosixPath(value)
    if pure.is_absolute() or ".." in pure.parts:
        return None
    return Path(*pure.parts)


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    experience = root / EXPERIENCE_ROOT
    manifest_path = root / MANIFEST_PATH
    required = [experience / "index.html", experience / "styles.css", experience / "app.js", manifest_path]
    for path in required:
        if not path.is_file():
            errors.append(f"missing required experience file: {path.relative_to(root)}")
    if errors:
        return errors

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return [f"invalid experience manifest: {error}"]

    cases = manifest.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append("experience manifest must declare at least one case")
        cases = []

    published_downloads: dict[str, Path] = {}
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            errors.append(f"experience case {index} must be an object")
            continue
        for field in ("id", "title", "repository_path", "download"):
            if not isinstance(case.get(field), str) or not case[field].strip():
                errors.append(f"experience case {index} has invalid {field}")
        repository_path = case.get("repository_path")
        download = case.get("download")
        if not isinstance(repository_path, str) or not isinstance(download, str):
            continue
        repository_relative = _safe_relative(repository_path)
        download_relative = _safe_relative(download)
        if repository_relative is None:
            errors.append(f"unsafe repository_path in experience case {index}: {repository_path}")
            continue
        if download_relative is None:
            errors.append(f"unsafe download in experience case {index}: {download}")
            continue
        if not (root / repository_relative).is_file():
            errors.append(f"missing case artifact: {repository_path}")
        published_downloads[download] = repository_relative
        if not isinstance(case.get("slide_count"), int) or case["slide_count"] < 1:
            errors.append(f"experience case {index} has invalid slide_count")
        if not isinstance(case.get("preview_count"), int) or case["preview_count"] < 1:
            errors.append(f"experience case {index} has invalid preview_count")

    html_text = (experience / "index.html").read_text(encoding="utf-8")
    parser = AssetParser()
    parser.feed(html_text)
    if len(parser.ids) != len(set(parser.ids)):
        errors.append("experience index contains duplicate HTML ids")
    for image in parser.images_without_alt:
        errors.append(f"experience image is missing alt text: {image}")

    for asset in parser.assets:
        if asset in published_downloads:
            path = root / published_downloads[asset]
        elif asset.startswith("assets/showcase/"):
            path = root / asset
        else:
            path = experience / asset
        if not path.is_file():
            errors.append(f"broken experience asset reference: {asset}")

    app_text = (experience / "app.js").read_text(encoding="utf-8")
    slide_sources = SLIDE_SOURCE_PATTERN.findall(app_text)
    if not slide_sources:
        errors.append("experience slide viewer declares no slide sources")
    for source in slide_sources:
        relative = _safe_relative(source)
        if source.startswith("assets/showcase/"):
            source_path = root / relative if relative is not None else None
        else:
            source_path = experience / relative if relative is not None else None
        if source_path is None or not source_path.is_file():
            errors.append(f"missing slide viewer asset: {source}")

    preview_paths = sorted((experience / "assets" / "cases").rglob("*.png"))
    for path in preview_paths:
        with Image.open(path) as image:
            if image.mode not in {"RGB", "L"}:
                errors.append(f"web preview must be flattened without alpha: {path.relative_to(root)} ({image.mode})")
            ratio = image.width / image.height
            if not 1.75 <= ratio <= 1.82:
                errors.append(f"web preview must be approximately 16:9: {path.relative_to(root)} ({image.width}x{image.height})")

    declared_preview_count = sum(case.get("preview_count", 0) for case in cases if isinstance(case, dict))
    if len(preview_paths) > declared_preview_count:
        errors.append("experience contains more case previews than the manifest declares")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args()
    errors = validate(Path(args.root).resolve())
    print(json.dumps({"ok": not errors, "errors": errors}, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
