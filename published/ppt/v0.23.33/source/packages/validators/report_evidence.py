# SPDX-License-Identifier: Apache-2.0
"""Lossless, content-addressed report transport; legacy report 3.6 stays readable."""
from __future__ import annotations
import base64
import hashlib
import json
from pathlib import Path

CONTRACT = "io.clayz.presentation.report-evidence/1.0"
FIELDS = {"content", "snapshot", "raw_text", "base64", "final_render_base64", "markdown", "raw_result"}


def payload(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def compact_report(report, directory):
    root = Path(directory)
    refs = {}
    def store(value, key):
        encoding = "json"
        data = json.dumps(value, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()
        suffix = ".json"
        if isinstance(value, str):
            encoding, data, suffix = "utf-8", value.encode(), ".txt"
            if key in {"base64", "final_render_base64"}:
                encoding, data = "base64", base64.b64decode(value, validate=True)
                suffix = ".png" if data.startswith(b"\x89PNG") else ".jpg"
        sha = hashlib.sha256(data).hexdigest()
        name = f"evidence/{sha}{suffix}"
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.read_bytes() != data:
            raise ValueError("evidence collision")
        path.write_bytes(data)
        ref = {"path": name, "sha256": sha, "bytes": len(data), "encoding": encoding}
        refs[(name, encoding)] = ref
        return {"$evidence": ref}
    def visit(value, key=""):
        if key in FIELDS and (key in {"base64", "final_render_base64"} or len(payload(value)) > 4096):
            # Recurse through structured content first: identical images/strings
            # are stored once even when their enclosing records differ.
            if isinstance(value, dict):
                value = {k: visit(v, k) for k, v in value.items()}
            elif isinstance(value, list):
                value = [visit(v) for v in value]
            return store(value, key)
        if isinstance(value, dict):
            return {k: visit(v, k) for k, v in value.items()}
        if isinstance(value, list):
            return [visit(v) for v in value]
        return value
    compact = visit(report)
    compact["evidence_storage"] = {
        "contract": CONTRACT, "expanded_sha256": hashlib.sha256(payload(report)).hexdigest(),
        "files": sorted(refs.values(), key=lambda r: (r["path"], r["encoding"]))}
    return compact


def expand_report(compact, directory):
    storage = compact.get("evidence_storage")
    if storage is None:
        return compact
    if storage.get("contract") != CONTRACT:
        raise ValueError("unsupported report evidence contract")
    root = Path(directory).resolve()
    declared = {json.dumps(r, sort_keys=True) for r in storage["files"]}
    used = set()
    active = set()
    def visit(value):
        if isinstance(value, dict) and "$evidence" in value:
            if set(value) != {"$evidence"}:
                raise ValueError("mixed evidence reference")
            ref = value["$evidence"]
            signature = json.dumps(ref, sort_keys=True)
            if signature not in declared or signature in active:
                raise ValueError("undeclared or cyclic evidence reference")
            path = (root / ref["path"]).resolve()
            if not path.is_relative_to(root / "evidence") or not path.is_file():
                raise ValueError("evidence path missing or escapes bundle")
            data = path.read_bytes()
            if len(data) != ref["bytes"] or hashlib.sha256(data).hexdigest() != ref["sha256"]:
                raise ValueError("evidence byte/hash mismatch")
            used.add(signature)
            active.add(signature)
            if ref["encoding"] == "json":
                result = visit(json.loads(data))
            elif ref["encoding"] == "utf-8":
                result = data.decode()
            elif ref["encoding"] == "base64":
                result = base64.b64encode(data).decode()
            else:
                raise ValueError("unsupported evidence encoding")
            active.remove(signature)
            return result
        if isinstance(value, dict):
            return {k: visit(v) for k, v in value.items()}
        if isinstance(value, list):
            return [visit(v) for v in value]
        return value
    expanded = visit({k:v for k,v in compact.items() if k != "evidence_storage"})
    if used != declared or hashlib.sha256(payload(expanded)).hexdigest() != storage["expanded_sha256"]:
        raise ValueError("expanded report identity mismatch or unused evidence")
    actual = {p.relative_to(root).as_posix() for p in (root / "evidence").rglob("*") if p.is_file()}
    if actual != {r["path"] for r in storage["files"]}:
        raise ValueError("evidence directory contains missing or unregistered files")
    return expanded


def load_report(path):
    path = Path(path)
    return expand_report(json.loads(path.read_text(encoding="utf-8")), path.parent)


def render_compact_markdown(compact):
    """Deterministic prose projection; full records remain in linked evidence."""
    from work_report import render_work_report_markdown
    def project(value):
        if isinstance(value, dict) and "$evidence" in value:
            r = value["$evidence"]
            return f"[完整证据 / Full evidence]({r['path']}) — SHA256 `{r['sha256']}`, {r['bytes']} bytes"
        if isinstance(value, dict):
            return {k: project(v) for k,v in value.items()}
        if isinstance(value, list):
            return [project(v) for v in value]
        return value
    projection = project({k:v for k,v in compact.items() if k not in {"stage_documents", "evidence_storage"}})
    work = projection.get("work_report", {})
    from work_report import _value_lines
    actual = work.get("actual_pptx", {})
    title = actual.get("title", actual.get("presentation_title", "Presentation"))
    lines = [f"# 工作报告 / Work report — {title}", "",
             "完整原始记录见同目录 JSON 与证据文件；下文展示研究、设计判断、修改和实际审计。", "",
             f"- Original work-report SHA256: `{compact.get('work_report_sha256', 'not-recorded')}`", ""]
    def section(title, value):
        lines.extend([f"## {title}", ""])
        lines.extend(_value_lines(value))
        lines.append("")
    section("任务与验收 / Task", work.get("task", {}))
    section("研究与不确定性 / Research", work.get("substantive_content", {}))
    section("故事与页序 / Story", work.get("storyline", {}))
    for page in work.get("copy", {}).get("slides", []):
        if isinstance(page, dict):
            section("Copy — " + str(page.get("slide_id", "page")),
                    {k:v for k,v in page.items() if k in {"slide_id", "title", "headline", "copy_units", "notes", "speaker_notes"}})
    art = work.get("art_direction", {})
    for page in art.get("slides", []):
        if isinstance(page, dict):
            section("Art — " + str(page.get("slide_id", "page")),
                    {k:v for k,v in page.items() if k in {"slide_id", "design_intent", "visual_hierarchy", "semantic_whitespace", "reading_path", "review", "revision_notes"}})
    section("阶段工作与修复 / Stage decisions", [
        {k:v for k,v in record.items() if k in {"stage", "recorded_at", "summary", "decisions", "checks", "open_issues", "limitations"}}
        for record in work.get("stages", []) if isinstance(record, dict)])
    section("监督校准 / Calibrations", work.get("calibrations", []))
    section("实际成品 / Actual output", {k:v for k,v in actual.items() if k in {"title", "slide_count", "totals", "media", "scope", "artifact"}})
    section("逐页审阅 / Page observations", [
        {k:v for k,v in page.items() if k not in {"final_render_base64", "final_render", "preview"}}
        for page in projection.get("design_comparison", {}).get("slides", [])])
    section("审计 / Audit", {k:v for k,v in work.get("auditor", {}).items() if k in {"status", "audit_status", "findings", "limitations", "coverage"}})
    section("放行与限制 / Release", work.get("release", {}))
    text = "\n".join(lines)
    text += "\n## 完整证据索引 / Complete evidence\n\n"
    text += "完整报告的语义校验使用恢复后的原始记录；本正文是同源阅读视图。\n\n"
    text += f"- Expanded report SHA256: `{compact['evidence_storage']['expanded_sha256']}`\n"
    for ref in compact["evidence_storage"]["files"]:
        text += f"- [{ref['path']}]({ref['path']}) — `{ref['sha256']}`, {ref['bytes']} bytes\n"
    return text
