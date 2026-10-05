#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Story-first handoffs and immutable visual baselines for package 3.0.

This supplements the existing stage validators and publication path. It is not
a second authoring pipeline. Hashes prove binding, never aesthetic quality.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import math
import html
import zipfile
from datetime import datetime
from pathlib import Path

CONTRACT_VERSION = "1.3"
PACKAGE_VERSION = "3.3"
STORY_PACKAGE_VERSIONS = {"3.0", "3.1", "3.2", PACKAGE_VERSION}
PLAN_VERSION = "2.1"


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def text(value):
    return isinstance(value, str) and bool(value.strip())


def rows(value):
    return value if isinstance(value, list) else []


def timestamp(value):
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include timezone")
    return parsed


def file_bytes(ref):
    if not isinstance(ref, dict) or not text(ref.get("path")):
        raise ValueError("file reference requires path, sha256 and bytes")
    path = Path(ref["path"])
    if not path.is_absolute():
        raise ValueError("task artifact references must use absolute paths")
    payload = path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != ref.get("sha256") or len(payload) != ref.get("bytes"):
        raise ValueError("file bytes or SHA-256 mismatch")
    return payload


def image_bytes(ref):
    from PIL import Image
    payload = file_bytes(ref)
    with Image.open(io.BytesIO(payload)) as image:
        if image.format not in {"PNG", "JPEG"}:
            raise ValueError("preview must be PNG or JPEG")
        image.verify()
    return payload


def story_blocks(story):
    return [block for chapter in rows(story.get("chapters")) if isinstance(chapter, dict)
            for block in rows(chapter.get("blocks")) if isinstance(block, dict)]


def validate_story(story, *, legacy=False):
    errors = []
    if not isinstance(story, dict):
        return ["story: complete narrative document is required"]
    for key in ("title", "thesis", "audience", "desired_outcome", "opening", "conclusion"):
        if not text(story.get(key)):
            errors.append(f"story.{key}: substantive prose is required")
    chapters = rows(story.get("chapters"))
    if not chapters:
        errors.append("story.chapters: at least one complete chapter is required")
    ids, chapter_ids = set(), set()
    sources = rows(story.get("sources"))
    source_ids = {s.get("source_id") for s in sources if isinstance(s, dict)}
    if len(source_ids) != len(sources) or None in source_ids:
        errors.append("story.sources: unique source IDs required")
    for key in ("sources", "glossary", "metric_dictionary", "open_items", "invariants"):
        if not isinstance(story.get(key), list):
            errors.append(f"story.{key}: array required")
    for chapter in chapters:
        if not isinstance(chapter, dict):
            errors.append("story.chapters: objects required")
            continue
        cid = chapter.get("chapter_id")
        if not text(cid) or cid in chapter_ids:
            errors.append("story: unique chapter_id required")
        chapter_ids.add(cid)
        for key in (("title", "purpose", "transition") if legacy else ("title", "purpose")):
            if not text(chapter.get(key)):
                errors.append(f"story.chapter.{key}: prose required")
        if not rows(chapter.get("blocks")):
            errors.append("story.chapter.blocks: complete narrative paragraphs required")
        for block in rows(chapter.get("blocks")):
            if not isinstance(block, dict):
                errors.append("story.blocks: objects required")
                continue
            bid = block.get("story_id")
            if not text(bid) or bid in ids:
                errors.append("story: unique story_id required")
            ids.add(bid)
            if not text(block.get("text")):
                errors.append(f"story.{bid}: complete paragraph required, not only a heading")
            if block.get("claim_status") not in {"source-fact", "direct-calculation", "interpretation", "causal-claim", "forecast", "recommendation", "target", "hypothesis", "missing-data"}:
                errors.append(f"story.{bid}: explicit evidence status required")
            refs = block.get("source_ids")
            if not isinstance(refs, list) or any(s not in source_ids for s in refs):
                errors.append(f"story.{bid}: unknown source reference")
            elif block.get("claim_status") in {"source-fact", "direct-calculation"} and not refs:
                errors.append(f"story.{bid}: facts/calculations require sources")
            if not isinstance(block.get("must_preserve"), bool) or not isinstance(block.get("qualifiers"), list):
                errors.append(f"story.{bid}: must_preserve and qualifiers required")
    return errors


def validate_logic_story(package, require_status):
    if package.get("contract_version") in {"3.2", "3.3"}:
        from research_handoff import validate_research_package
        return validate_research_package(package, require_status)
    from acceptance_contract import validate_acceptance_contract, validate_stage_retrieval_budget
    from resource_inventory import validate_resource_inventory
    from index_evidence import validate_index_evidence
    from validate_logic_package import validate_brief
    errors = validate_story(package.get("story"), legacy=package.get("contract_version") == "3.0")
    rank = {"draft": 0, "logic-approved": 1, "copy-approved": 2}
    if rank.get(package.get("status"), -1) < rank.get(require_status, 100):
        errors.append("story package: approval status insufficient")
    for key in ("package_id", "version"):
        if not text(package.get(key)):
            errors.append(f"story package.{key}: required")
    validate_acceptance_contract(package.get("acceptance_contract"), "acceptance_contract", errors)
    validate_resource_inventory(package.get("resource_inventory"), "resource_inventory", errors,
                                require_ready=package.get("status") != "draft")
    validate_brief(package.get("brief"), errors)
    stages = ["logic"] if package.get("status") != "draft" else []
    if package.get("status") == "copy-approved":
        stages.append("copy")
    validate_index_evidence(package.get("index_evidence"), stages, "index_evidence", errors)
    validate_stage_retrieval_budget(package.get("index_evidence"), package.get("acceptance_contract"), stages, "index_evidence", errors)
    story = package.get("story") or {}
    selected = package.get("resource_inventory", {}).get("selected_resource_ids", [])
    for source in rows(story.get("sources")):
        if not isinstance(source, dict) or source.get("resource_id") not in selected or not text(source.get("locator")):
            errors.append("story.sources: each source must bind a selected resource and locator")
    if package.get("status") == "logic-approved":
        if package.get("copy_layer") is not None or (package.get("contract_version") == "3.0" and package.get("logic_layer") is not None):
            errors.append("Logic hands off a story, not a locked page projection")
    if package.get("contract_version") == "3.1":
        errors.extend(validate_page_allocation(package))
    approval = package.get("approvals", {}).get("logic", {})
    if package.get("status") != "draft" and (approval.get("status") != "approved" or not text(approval.get("approved_by"))):
        errors.append("approvals.logic: approved stage decision required")
    return errors


def load_logic_origin(package):
    origin = json.loads(file_bytes(package.get("logic_artifact")))
    if origin.get("contract_version") not in STORY_PACKAGE_VERSIONS or origin.get("status") != "logic-approved":
        raise ValueError("logic_artifact must be the original versioned Logic handoff")
    return origin


def validate_copy_trace(package):
    if package.get("contract_version") == "3.3":
        from clean_content import validate_clean_copy
        return validate_clean_copy(package)
    if package.get("contract_version") == "3.2":
        from research_handoff import validate_research_copy
        return validate_research_copy(package)
    errors = []
    story = package.get("story") or {}
    try:
        origin = load_logic_origin(package)
        errors.extend(validate_logic_story(origin, "logic-approved"))
        if origin.get("contract_version") != package.get("contract_version"):
            errors.append("Copy must preserve the original package contract version")
        keys = ("story", "brief", "acceptance_contract", "resource_inventory", "package_id")
        if package.get("contract_version") == "3.1":
            keys += ("logic_layer",)
        for key in keys:
            if origin.get(key) != package.get(key):
                errors.append(f"Copy changed the immutable Logic {key}")
    except (OSError, ValueError, TypeError) as exc:
        errors.append(f"logic_artifact: {exc}")
    copy = package.get("copy_layer") or {}
    if copy.get("pagination_owner") != ("logic" if package.get("contract_version") == "3.1" else "copy") or copy.get("story_sha256") != digest(story):
        errors.append("Copy pagination must bind the original story SHA-256")
    chapter_order = [c.get("chapter_id") for c in rows(story.get("chapters")) if isinstance(c, dict)]
    if copy.get("chapter_order") != chapter_order:
        errors.append("Copy must preserve Logic chapter order")
    projection = package.get("logic_layer") or {}
    for key in (("sources", "glossary", "metric_dictionary", "open_items") if package.get("contract_version") == "3.0" else ()):
        if projection.get(key) != story.get(key):
            errors.append(f"Copy page projection must preserve story.{key}")
    blocks = {b.get("story_id"): b for b in story_blocks(story)}
    covered = set()
    for slide in rows(copy.get("slides")):
        for unit in rows(slide.get("copy_units")) + rows(slide.get("speaker_notes")):
            refs = unit.get("source_story_ids")
            if not isinstance(refs, list) or not refs or any(r not in blocks for r in refs):
                errors.append("every Copy unit/note must trace to valid story IDs")
            else:
                if package.get("contract_version") != "3.1" or unit in rows(slide.get("copy_units")):
                    covered.update(refs)
            # Review paraphrase equivalence professionally; no string-similarity gate.
    for bid, block in blocks.items():
        if block.get("must_preserve") and bid not in covered:
            errors.append(f"Copy omitted required story block {bid}")
    if not text(copy.get("semantic_preservation_review")):
        errors.append("Copy must record qualifier/number/relationship preservation review")
    return errors


def spec_digest(plan):
    return digest({k: v for k, v in plan.items() if k != "visual_baseline"})


def validate_visual_baseline(package, plan):
    errors = []
    baseline = plan.get("visual_baseline")
    if not isinstance(baseline, dict):
        return ["Art Direction requires a locked full-deck visual_baseline"]
    if baseline.get("status") != "locked" or baseline.get("spec_sha256") != spec_digest(plan):
        errors.append("visual_baseline: locked specification hash mismatch")
    if baseline.get("copy_package_sha256") != digest(package):
        errors.append("visual_baseline: stale Copy package")
    try:
        timestamp(baseline.get("locked_at"))
    except ValueError:
        errors.append("visual_baseline.locked_at: timezone timestamp required")
    expected = rows(package.get("copy_layer", {}).get("slides"))
    previews = rows(baseline.get("slides"))
    if [p.get("slide_id") for p in previews if isinstance(p, dict)] != [p.get("slide_id") for p in expected]:
        errors.append("visual_baseline: one preview per Copy page in order is required")
    for page, preview in zip(expected, previews):
        if not isinstance(preview, dict):
            errors.append("visual_baseline.slides: objects required")
            continue
        try:
            image_bytes(preview.get("image"))
        except (OSError, ValueError, TypeError) as exc:
            errors.append(f"visual_baseline.{page.get('slide_id')}.image: {exc}")
        for key in ("legibility_review", "copy_and_data_review", "spec_consistency_review", "first_visual", "reading_path"):
            if not text(preview.get(key)):
                errors.append(f"visual_baseline.{key}: inspected observation required")
        elements = rows(preview.get("elements"))
        approved_data_ids = ({item.get("data_id") for item in rows((package.get("research") or {}).get("data")) if isinstance(item, dict)}
                             if package.get("contract_version") == "3.3" else
                             {item.get("data_id") for slide in rows((package.get("logic_layer") or {}).get("slides"))
                              for item in rows(slide.get("data")) if isinstance(item, dict)})
        element_ids, mapped = set(), []
        for element in elements:
            if not isinstance(element, dict):
                errors.append("visual elements must be objects")
                continue
            eid = element.get("element_id")
            if not text(eid) or eid in element_ids:
                errors.append("visual element IDs must be unique within a slide")
            element_ids.add(eid)
            refs = element.get("copy_ids")
            if not isinstance(refs, list):
                errors.append("visual element.copy_ids: array required; use [] for added assets")
            else:
                mapped.extend(refs)
            for key in ("kind", "purpose", "native_type", "group_id", "alignment"):
                if not text(element.get(key)):
                    errors.append(f"visual element.{key}: required")
            box = element.get("box")
            if not isinstance(box, list) or len(box) != 4 or any(isinstance(n, bool) or not isinstance(n, (int, float)) or not math.isfinite(n) for n in box):
                errors.append("visual element.box: normalized [x,y,w,h] required")
            elif min(box) < 0 or box[2] <= 0 or box[3] <= 0 or box[0]+box[2] > 1.000001 or box[1]+box[3] > 1.000001:
                errors.append("visual element.box: must fit normalized canvas")
            if refs and (not isinstance(element.get("typography"), dict) or not text(element["typography"].get("font_family")) or not isinstance(element["typography"].get("size_pt"), (int, float)) or element["typography"].get("size_pt", 0) <= 0):
                errors.append("text element requires resolved font family and positive size_pt")
            if element.get("kind") in {"icon", "image"} and not text(element.get("asset_ref")):
                errors.append("added icon/image requires asset_ref")
            if element.get("kind") == "chart" and (not text(element.get("chart_type")) or not rows(element.get("data_ids"))):
                errors.append("chart requires encoding type and approved data IDs")
            if element.get("kind") == "chart" and any(d not in approved_data_ids for d in rows(element.get("data_ids"))):
                errors.append("chart cannot introduce unapproved data IDs")
            if not isinstance(element.get("locked_properties"), list) or not isinstance(element.get("allowed_adjustments"), dict):
                errors.append("element must declare locked properties and bounded allowed adjustments")
        if sorted(mapped) != sorted(u.get("copy_id") for u in rows(page.get("copy_units"))):
            errors.append("visual elements must map every Copy unit exactly once")
    return errors


def validate_output_baseline(package, plan, qa):
    if package.get("contract_version") not in STORY_PACKAGE_VERSIONS:
        return []
    errors = validate_visual_baseline(package, plan)
    baseline = plan.get("visual_baseline") or {}
    if qa.get("visual_baseline_sha256") != digest(baseline):
        errors.append("Output must bind the exact Art Direction visual baseline")
    try:
        if timestamp(qa.get("output_started_at")) < timestamp(baseline.get("locked_at")):
            errors.append("Output started before the visual baseline was locked")
    except ValueError:
        errors.append("Output start and design lock require timezone timestamps")
    return errors


def render_document(stage, value):
    lines = [f"# {stage}", ""]
    if stage == "logic" and value.get("contract_version") in {"3.2", "3.3"}:
        research = value["research"]
        lines += [research["research_question"], "", research["scope"], "", research["summary"], ""]
        for finding in research["findings"]:
            lines += [f"## {finding['finding_id']}: {finding['question']}", "", finding["text"], "",
                      f"[{finding['claim_status']}; sources: {', '.join(finding['source_ids'])}]", ""]
    elif stage == "logic":
        story = value["story"]
        lines += [story["title"], "", story["thesis"], "", story["opening"], ""]
        for chapter in story["chapters"]:
            lines += [f"## {chapter['title']}", "", chapter["purpose"], ""]
            for block in chapter["blocks"]:
                lines += [block["text"], "", f"[{block['story_id']}; {block['claim_status']}; sources: {', '.join(block['source_ids'])}]", ""]
            if chapter.get("transition"):
                lines += [chapter["transition"], ""]
        lines += [story["conclusion"], ""]
        for page in rows((value.get("logic_layer") or {}).get("slides")):
            lines += [f"## {page['slide_id']}: {page['claim']}", "", ", ".join(page["source_story_ids"]), ""]
    elif stage == "copy":
        for page in value["copy_layer"]["slides"]:
            lines += [f"## {page['slide_id']}", ""]
            for unit in page["copy_units"]:
                if value.get("contract_version") == "3.3":
                    level = f", level={unit['heading_level']}" if unit.get("role") == "heading" else ""
                    lines += [f"[{unit['copy_id']}; {unit['role']}{level}]", unit['text'], ""]
                else:
                    lines += [f"- {unit['copy_id']} ({unit['role']}, parent={unit['parent_copy_id']}): {unit['text']}"]
            lines += [""]
    else:
        for page in value["visual_baseline"]["slides"]:
            lines += [f"## {page['slide_id']}", "", page["first_visual"], "", page["reading_path"], ""]
    lines += ["## Complete handoff data", "", "```json", json.dumps(value, ensure_ascii=False, indent=2), "```", ""]
    return "\n".join(lines)


def build_stage_documents(package, plan):
    origin = load_logic_origin(package)
    documents = {}
    for stage, value in (("logic", origin), ("copy", package), ("art_direction", plan)):
        markdown = render_document("art-direction" if stage == "art_direction" else stage, value)
        documents[stage] = {"content": value, "content_sha256": digest(value), "markdown": markdown,
                            "markdown_sha256": hashlib.sha256(markdown.encode()).hexdigest()}
    previews = []
    for page in plan["visual_baseline"]["slides"]:
        payload = image_bytes(page["image"])
        previews.append({"slide_id": page["slide_id"], "sha256": hashlib.sha256(payload).hexdigest(),
                         "base64": base64.b64encode(payload).decode()})
    return {"contract": "io.clayz.presentation.stage-documents/1.0", "documents": documents, "previews": previews}


def validate_design_audit(package, plan, qa, report, pptx=None):
    if package.get("contract_version") not in STORY_PACKAGE_VERSIONS:
        return []
    errors = validate_logic_story(package, "copy-approved") + validate_copy_trace(package)
    errors.extend(validate_output_baseline(package, plan, qa))
    try:
        if report.get("stage_documents") != build_stage_documents(package, plan):
            errors.append("report must include the exact three handoff documents and locked preview bytes")
    except (OSError, ValueError, TypeError, KeyError) as exc:
        errors.append(f"stage_documents: {exc}")
    comparison = report.get("design_comparison") or {}
    if comparison.get("visual_baseline_sha256") != digest(plan.get("visual_baseline")):
        errors.append("design comparison uses a different visual baseline")
    if pptx is None or not pptx.is_file():
        errors.append("design comparison requires the actual written PPTX")
    elif comparison.get("pptx_sha256") != hashlib.sha256(pptx.read_bytes()).hexdigest():
        errors.append("design comparison must bind actual final PPTX bytes")
    pages = rows(comparison.get("slides"))
    expected = rows(plan.get("visual_baseline", {}).get("slides"))
    if [p.get("slide_id") for p in pages] != [p.get("slide_id") for p in expected]:
        errors.append("design comparison must cover every page in order")
    issues = {i.get("issue_id", i.get("finding_id")) for i in rows(report.get("issues")) if isinstance(i, dict)}
    for page, design in zip(pages, expected):
        if page.get("preview_sha256") != design.get("image", {}).get("sha256"):
            errors.append("comparison preview hash differs from locked design")
        if page.get("status") == "deferred":
            if not text(page.get("reason")) or report.get("run_status") == "clean":
                errors.append("deferred render comparison needs an explicit limitation, never a clean verdict")
            continue
        if page.get("status") != "reviewed":
            errors.append("comparison status must be reviewed or deferred")
        try:
            payload = image_bytes(page.get("final_render"))
            if page.get("final_render_base64") != base64.b64encode(payload).decode():
                errors.append("report must embed the actual final render bytes")
        except (OSError, ValueError, TypeError) as exc:
            errors.append(f"comparison final render: {exc}")
        if page.get("rendered_from_pptx_sha256") != comparison.get("pptx_sha256"):
            errors.append("final render must bind the reopened final PPTX")
        for key in ("content", "visual_fidelity", "native_editability", "design_quality"):
            check = page.get(key) or {}
            if check.get("status") not in {"pass", "fail", "uncertain"} or not text(check.get("observation")):
                errors.append(f"comparison.{key}: actual observation and result required")
            if check.get("status") in {"fail", "uncertain"}:
                if check.get("earliest_owner") not in {"logic", "copy", "art-direction", "output"} or not check.get("issue_ids") or any(i not in issues for i in rows(check.get("issue_ids"))):
                    errors.append("comparison findings must resolve to report issues and earliest owner")
                if report.get("run_status") == "clean":
                    errors.append("failed/uncertain comparison cannot be reported clean")
    return errors


def embed_final_renders(report):
    """Preserve observed review text; only materialize inspected render bytes."""
    for page in rows(report.get("design_comparison", {}).get("slides")):
        if page.get("status") == "reviewed":
            page["final_render_base64"] = base64.b64encode(image_bytes(page.get("final_render"))).decode()


def validate_embedded_documents(report):
    """Portable integrity check independent of the originating task filesystem."""
    errors = []
    bundle = report.get("stage_documents")
    if not isinstance(bundle, dict):
        return ["stage_documents: missing"]
    documents = bundle.get("documents") or {}
    if set(documents) != {"logic", "copy", "art_direction"}:
        return ["stage_documents: three original documents required"]
    for stage, document in documents.items():
        try:
            content = document["content"]
            expected = render_document("art-direction" if stage == "art_direction" else stage, content)
            if document.get("content_sha256") != digest(content) or document.get("markdown") != expected or document.get("markdown_sha256") != hashlib.sha256(expected.encode()).hexdigest():
                errors.append(f"embedded {stage} document differs from its source data")
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"embedded {stage} document: {exc}")
    try:
        plan = documents["art_direction"]["content"]
        copy = documents["copy"]["content"]
        logic = documents["logic"]["content"]
        baseline = plan["visual_baseline"]
        if baseline.get("spec_sha256") != spec_digest(plan) or baseline.get("copy_package_sha256") != digest(copy) or copy.get("story") != logic.get("story") or copy.get("research") != logic.get("research"):
            errors.append("embedded cross-stage source bindings mismatch")
        expected = baseline["slides"]
        previews = rows(bundle.get("previews"))
        if [p.get("slide_id") for p in previews] != [p.get("slide_id") for p in expected]:
            errors.append("embedded previews omit/reorder pages")
        for preview, design in zip(previews, expected):
            payload = base64.b64decode(preview.get("base64", ""), validate=True)
            sha = hashlib.sha256(payload).hexdigest()
            if not payload or sha != preview.get("sha256") or sha != design["image"]["sha256"]:
                errors.append("embedded preview bytes mismatch")
        for page in rows(report.get("design_comparison", {}).get("slides")):
            if page.get("status") == "reviewed":
                payload = base64.b64decode(page.get("final_render_base64", ""), validate=True)
                if not payload or hashlib.sha256(payload).hexdigest() != page.get("final_render", {}).get("sha256"):
                    errors.append("embedded final render bytes mismatch")
    except (KeyError, ValueError, TypeError) as exc:
        errors.append(f"embedded visual evidence: {exc}")
    return errors


def handoff_archive_bytes(report):
    """Deterministic derived companion; all content comes from the report."""
    errors = validate_embedded_documents(report)
    if errors:
        raise ValueError("; ".join(errors))
    bundle = report["stage_documents"]
    files = {}
    for stage, document in bundle["documents"].items():
        files[f"{stage}.md"] = document["markdown"].encode()
        files[f"{stage}.json"] = (json.dumps(document["content"], ensure_ascii=False, indent=2)+"\n").encode()
    comparisons = {p["slide_id"]: p for p in rows(report.get("design_comparison", {}).get("slides"))}
    parts = ['<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>Design and final PPTX comparison</title>',
             '<style>body{font:16px system-ui;margin:2rem;max-width:1600px} .pair{display:grid;grid-template-columns:1fr 1fr;gap:1rem} img{width:100%;border:1px solid #aaa}pre{white-space:pre-wrap}section{margin:3rem 0}h1{font-size:1.7rem}@media(max-width:700px){.pair{grid-template-columns:1fr}}</style>',
             '<h1>图片稿与最终 PPTX 对照</h1><p>左：锁定的 Art Direction 图片稿；右：最终 PPTX 实际渲染。可编辑性以对象检查为准。</p>']
    for number, preview in enumerate(bundle["previews"], 1):
        payload = base64.b64decode(preview["base64"])
        extension = "png" if payload.startswith(b"\x89PNG") else "jpg"
        name = f"images/{number:03d}-design.{extension}"
        files[name] = payload
        page = comparisons.get(preview["slide_id"], {})
        parts += [f'<section><h2>{html.escape(preview["slide_id"])}</h2><div class="pair"><figure><figcaption>设计稿</figcaption><img src="{name}"></figure>']
        if page.get("status") == "reviewed":
            final = base64.b64decode(page["final_render_base64"])
            extension = "png" if final.startswith(b"\x89PNG") else "jpg"
            name = f"images/{number:03d}-final.{extension}"
            files[name] = final
            parts += [f'<figure><figcaption>最终渲染</figcaption><img src="{name}"></figure>']
        else:
            parts += [f'<p>对照延后：{html.escape(str(page.get("reason", "未记录")))}</p>']
        observations = {k:v for k,v in page.items() if k not in {"final_render_base64", "final_render"}}
        parts += ['</div><pre>'+html.escape(json.dumps(observations, ensure_ascii=False, indent=2))+'</pre></section>']
    parts += ['</html>']
    files['comparison.html'] = '\n'.join(parts).encode()
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, payload in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, payload)
    return buffer.getvalue()


def validate_page_allocation(package):
    """3.1: Logic owns the complete story and its page allocation, not Copy trees."""
    errors = []
    layer = package.get('logic_layer')
    if not isinstance(layer, dict):
        return ['logic_layer: Logic page allocation required in package 3.1']
    story = package.get('story') or {}
    blocks = {b.get('story_id'): b for b in story_blocks(story)}
    chapters = {c.get('chapter_id') for c in rows(story.get('chapters')) if isinstance(c, dict)}
    sources = {s.get('source_id') for s in rows(story.get('sources')) if isinstance(s, dict)}
    if (layer.get('lock') or {}).get('slide_order_locked') is not True:
        errors.append('logic_layer.lock.slide_order_locked: true required')
    slides = rows(layer.get('slides'))
    if not slides:
        errors.append('logic_layer.slides: complete page allocation required')
    ids, covered, data_ids = set(), set(), set()
    for page in slides:
        if not isinstance(page, dict):
            errors.append('logic_layer.slides: objects required')
            continue
        sid = page.get('slide_id')
        if not text(sid) or sid in ids:
            errors.append('logic_layer.slides: unique slide_id required')
        ids.add(sid)
        for key in ('claim', 'narrative_role'):
            if not text(page.get(key)):
                errors.append(f'logic_layer.{sid}.{key}: required')
        if page.get('chapter_id') not in chapters and page.get('chapter_id') is not None:
            errors.append(f'logic_layer.{sid}.chapter_id: unknown chapter')
        refs = page.get('source_story_ids')
        if not isinstance(refs, list) or not refs or any(r not in blocks for r in refs):
            errors.append(f'logic_layer.{sid}: valid source_story_ids required')
        else:
            covered.update(refs)
        # Evidence is independent of analytical templates and rhetorical roles.
        if not isinstance(page.get('data'), list):
            errors.append(f'logic_layer.{sid}.data: array required')
        for item in rows(page.get('data')):
            if not isinstance(item, dict):
                errors.append('page data: objects required')
                continue
            did = item.get('data_id')
            if not text(did) or did in data_ids:
                errors.append('page data: unique data_id required')
            data_ids.add(did)
            for key in ('metric_name', 'display_value', 'unit', 'period', 'definition_ref'):
                if not text(item.get(key)):
                    errors.append(f'page data.{did}.{key}: required')
            refs = item.get('source_ids')
            if not isinstance(refs, list) or any(r not in sources for r in refs):
                errors.append(f'page data.{did}: unknown source')
            if item.get('evidence_status') in {'source-fact', 'direct-calculation'} and not refs:
                errors.append(f'page data.{did}: facts/calculations require sources')
            if item.get('evidence_status') not in {'source-fact', 'direct-calculation', 'interpretation', 'causal-claim', 'forecast', 'recommendation', 'target', 'hypothesis', 'missing-data'}:
                errors.append(f'page data.{did}: explicit evidence status required')
            if 'raw_value' not in item:
                errors.append(f'page data.{did}.raw_value: required (null when unavailable)')
    if covered != set(blocks):
        errors.append('logic_layer: every story block must have a page allocation before Copy trims it')
    cover = (package.get('acceptance_contract') or {}).get('cover_policy') or {}
    for role, key, index in (('cover', 'cover_required', 0), ('closing', 'closing_required', -1)):
        required = cover.get(key, cover.get('mode') != 'not-applicable')
        if required and (sum(p.get('narrative_role') == role for p in slides if isinstance(p, dict)) != 1 or not slides or slides[index].get('narrative_role') != role):
            errors.append(f'logic_layer: one {role} page required at its sequence boundary')
    return errors


def validate_copy_tags(package):
    """3.1 keeps Copy grouping and provenance without the retired Logic node contract."""
    from validate_ppt_package import ROLES, TEXT_MODES
    errors = []
    research_mode = package.get('contract_version') == '3.2'
    ref_key = 'source_finding_ids' if research_mode else 'source_story_ids'
    copy = package.get('copy_layer')
    if not isinstance(copy, dict):
        return ['copy_layer: required']
    if copy.get('logic_version') != package.get('version'):
        errors.append('copy_layer.logic_version: must bind root version')
    approval = (package.get('approvals') or {}).get('copy') or {}
    if approval.get('status') != 'approved' or not text(approval.get('approved_by')):
        errors.append('approvals.copy: approved stage decision required')
    expected = rows((package.get('logic_layer') or {}).get('slides'))
    slides = rows(copy.get('slides'))
    if [s.get('slide_id') for s in slides if isinstance(s, dict)] != [s.get('slide_id') for s in expected if isinstance(s, dict)]:
        errors.append('copy_layer.slides: order must exactly match the approved page allocation')
    global_ids = set()
    for page, allocated in zip(slides, expected):
        if not isinstance(page, dict):
            errors.append('copy_layer.slides: objects required')
            continue
        units = rows(page.get('copy_units'))
        if not units:
            errors.append('copy_units: visible tagged content required')
        local = {u.get('copy_id'): u for u in units if isinstance(u, dict)}
        orders = []
        for unit in units:
            if not isinstance(unit, dict):
                errors.append('copy_units: objects required')
                continue
            cid = unit.get('copy_id')
            if not text(cid) or cid in global_ids:
                errors.append('copy_id: unique nonempty ID required across deck')
            global_ids.add(cid)
            if not text(unit.get('text')) or unit.get('role') not in ROLES or unit.get('text_mode') not in TEXT_MODES:
                errors.append(f'copy unit {cid}: text, role and text_mode required')
            if 'parent_copy_id' not in unit or (unit['parent_copy_id'] is not None and unit['parent_copy_id'] not in local):
                errors.append(f'copy unit {cid}: parent_copy_id must resolve on this page')
            parent_unit = local.get(unit.get('parent_copy_id'))
            if parent_unit and isinstance(unit.get('logic_level'), int) and isinstance(parent_unit.get('logic_level'), int) and unit['logic_level'] <= parent_unit['logic_level']:
                errors.append(f'copy unit {cid}: child hierarchy level must be deeper than its Copy parent')
            if 'sibling_group_id' not in unit or (unit['sibling_group_id'] is not None and not text(unit['sibling_group_id'])):
                errors.append(f'copy unit {cid}: sibling_group_id must be null or a group tag')
            ancestors = {cid}
            parent = unit.get('parent_copy_id')
            while parent in local:
                if parent in ancestors:
                    errors.append(f'copy unit {cid}: cyclic Copy hierarchy')
                    break
                ancestors.add(parent)
                parent = local[parent].get('parent_copy_id')
            if not isinstance(unit.get('logic_level'), int) or unit.get('logic_level', -1) < 0:
                errors.append(f'copy unit {cid}: nonnegative Copy hierarchy level required')
            if unit.get('render_separately') is not True or unit.get('merge_with_children') is not False:
                errors.append(f'copy unit {cid}: preserve independently tagged rendering')
            breaks = unit.get('intentional_line_breaks')
            if not isinstance(breaks, list) or any(not isinstance(n, int) or n <= 0 or n >= len(unit.get('text') or '') for n in breaks):
                errors.append(f'copy unit {cid}: valid intentional_line_breaks required')
            orders.append(unit.get('order'))
            if any(r not in allocated.get(ref_key, []) for r in rows(unit.get(ref_key))):
                errors.append(f'copy unit {cid}: source is allocated to a different approved page')
        if any(not isinstance(n, int) for n in orders) or sorted(orders) != list(range(1, len(units)+1)):
            errors.append('copy_units.order: unique contiguous order required')
        if page.get('title_copy_id') not in local:
            errors.append('title_copy_id: must reference a visible Copy unit')
        if page.get('storyline_copy_id') is not None and page.get('storyline_copy_id') not in local:
            errors.append('storyline_copy_id: unknown Copy unit')
        if any(cid not in local for cid in rows(page.get('footnote_copy_ids'))):
            errors.append('footnote_copy_ids: unknown Copy unit')
        # Optional historical/requested notes remain readable; no default generation.
        for note in rows(page.get('speaker_notes')):
            if not isinstance(note, dict) or not text(note.get('text')):
                errors.append('speaker_notes: supplied notes must contain text')
    return errors
