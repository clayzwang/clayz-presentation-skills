#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Visible-only reader packets and immutable two-pass review evidence.

These helpers validate inputs, provenance and ordering. They neither launch an
LLM nor infer comprehension from a schema, an empty findings list or a hash.
Fresh contexts and their receipts must come from the actual host.
"""
from __future__ import annotations

import hashlib
import base64
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

CONTRACT = "io.clayz.presentation.reader-review/1.0"
PACKET = "io.clayz.presentation.reader-packet/1.0"
FIRST_READ = "io.clayz.presentation.reader-first-read/1.0"
PHASES = ("title", "content", "final", "copy")
NEW_PHASES = ("title", "content", "final")
ROLES = {"title", "subtitle", "heading", "body", "annotation"}
PROMPT = (
    "Read as the audience described in the brief. Use only the supplied visible "
    "pages, without research, author notes, design rationale or prior reviews. "
    "First read the titles as a sequence, then read the complete pages. Explain "
    "in your own words what the material teaches, its mechanisms and concrete "
    "comparisons when relevant. Cite pages and visible wording. Identify where "
    "you must guess, cannot answer the task, or can only repeat a label. Record "
    "uncertainty; do not invent missing facts. Do not look up sources or improve "
    "the wording before saving this first understanding. Return assessment, "
    "title_reading, understanding and findings as specified in the reader-review "
    "contract. These are editorial observations, not numerical quality scores."
)


def phase_prompt(phase):
    if phase == "title":
        return PROMPT.replace("First read the titles as a sequence, then read the complete pages.",
                              "Read only the supplied title sequence; do not infer unseen body text.")
    return PROMPT


def projection(package, phase):
    pages = visible_copy(package)
    if phase == "title":
        for page in pages:
            page["text"] = [u for u in page["text"] if u["role"] == "title"]
            if not page["text"]:
                raise ValueError("title reader requires a visible title on every page")
    return pages


def semantic_input(package, phase):
    # Whitelist record metadata out, but keep the entire authoritative research.
    return {"run_binding": package["run_binding"], "research": package.get("research"),
            "brief": package.get("brief"), "pages": projection(package, phase)}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read(path: Path | str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                   separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def ref(path: Path | str) -> dict[str, Any]:
    path = Path(path).resolve()
    raw = path.read_bytes()
    if not raw:
        raise ValueError(f"empty reader evidence: {path}")
    return {"path": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def write(path: Path, value: Any) -> None:
    path = Path(path).resolve()
    root = Path(__file__).resolve().parents[2]
    if path.is_relative_to(root):
        raise ValueError("reader artifacts must be outside the installed plugin")
    from packages.validators.handoff_io import write_record
    write_record(path, value)


def load_ref(value: dict[str, Any], *, json_value: bool = True) -> Any:
    if not isinstance(value, dict) or set(value) != {"path", "sha256", "bytes"}:
        raise ValueError("reader evidence must contain path, sha256 and bytes")
    if not Path(value["path"]).is_absolute() or ref(value["path"]) != value:
        raise ValueError("reader evidence differs from bound bytes")
    return read(value["path"]) if json_value else Path(value["path"])


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _time(value: str) -> datetime:
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.utcoffset() is None:
        raise ValueError("reader timestamps must include timezone")
    return result


def visible_copy(package: dict[str, Any]) -> list[dict[str, Any]]:
    pages = []
    for slide in package["copy_layer"]["slides"]:
        units = []
        for unit in slide["copy_units"]:
            if unit.get("role") not in ROLES or not _text(unit.get("text")):
                raise ValueError("reader packet needs current visible Copy units")
            row = {key: unit[key] for key in ("copy_id", "role", "text")}
            if unit["role"] == "heading":
                row["heading_level"] = unit["heading_level"]
            units.append(row)
        pages.append({"slide_id": slide["slide_id"], "text": units})
    ids = [page["slide_id"] for page in pages]
    if not pages or len(set(ids)) != len(ids):
        raise ValueError("reader packet needs distinct current pages")
    return pages


def prepare_packet(*, phase: str, package: Path, brief: Path, directory: Path,
                   output: Path, pptx: Path | None = None,
                   renders: Path | None = None, unavailable_reason: str | None = None,
                   title_review: Path | None = None) -> dict[str, Any]:
    """The host receives directory only. The manifest stays with the auditor."""
    if phase not in PHASES:
        raise ValueError("reader phase must be title, content, final (or legacy copy)")
    package_value, brief_value = read(package), read(brief)
    if set(brief_value) != {"audience", "purpose", "task"} or not all(_text(v) for v in brief_value.values()):
        raise ValueError("neutral reader brief requires only audience, purpose and task")
    if phase == "content":
        if title_review is None:
            raise ValueError("content preparation requires --title-review; finish title reconciliation first")
        title = validate_review(read(title_review), current_package=package_value)
        if title["review"]["phase"] != "title":
            raise ValueError("content preparation requires a title review")
        require_pass(title)
    binding = package_value["run_binding"]
    pages = projection(package_value, phase)
    directory = directory.resolve()
    if output.resolve().is_relative_to(Path(__file__).resolve().parents[2]):
        raise ValueError("reader artifacts must be outside the installed plugin")
    if output.exists():
        existing = read(output)
        payload = validate_packet(existing)
        if (existing["phase"] == phase and existing["package"] == ref(package)
                and payload["brief"] == brief_value and Path(existing["input"]["path"]).parent == directory
                and existing["pptx"] == (ref(pptx) if phase == "final" and pptx else None)
                and existing["renders"] == (ref(renders) if phase == "final" and renders else None)
                and existing["unavailable_reason"] == unavailable_reason):
            return existing
        raise FileExistsError("reader packet input changed; use a new revision, preserve prior reading")
    if directory.exists() or output.resolve().is_relative_to(directory):
        raise ValueError("use a new reader directory and keep manifest outside it")
    if directory.is_relative_to(Path(__file__).resolve().parents[2]):
        raise ValueError("reader packets must be outside the installed plugin")
    assets = []
    render_ref = None
    if phase == "final":
        if pptx is None:
            raise ValueError("final reading requires the actual PPTX")
        if renders is None and not _text(unavailable_reason):
            raise ValueError("final reading requires renders or an explicit unavailable reason")
    if phase == "final" and renders is not None:
        render_value = read(renders)
        if render_value.get("pptx_sha256") != ref(pptx)["sha256"]:
            raise ValueError("reader renders are bound to a different PPTX")
        if [r.get("slide_id") for r in render_value.get("slides", [])] != [p["slide_id"] for p in pages]:
            raise ValueError("reader renders must cover every page in current order")
        from PIL import Image
        for row in render_value["slides"]:
            path = load_ref({k: row[k] for k in ("path", "sha256", "bytes")}, json_value=False)
            with Image.open(path) as image:
                image.load()
    directory.mkdir(parents=True)
    if phase == "final" and renders is not None:
        render_value = read(renders)
        if render_value.get("pptx_sha256") != ref(pptx)["sha256"]:
            raise ValueError("reader renders are bound to a different PPTX")
        rows = render_value.get("slides", [])
        if [r.get("slide_id") for r in rows] != [p["slide_id"] for p in pages]:
            raise ValueError("reader renders must cover every page in current order")
        from PIL import Image
        final_pages = []
        for index, row in enumerate(rows):
            original = load_ref({k: row[k] for k in ("path", "sha256", "bytes")}, json_value=False)
            name = f"page-{index + 1:03d}.png"
            # Re-encode pixels: do not leak PNG text/EXIF/ICC author metadata.
            with Image.open(original) as image:
                image.load()
                clean = Image.frombytes("RGB", image.size, image.convert("RGB").tobytes())
                clean.save(directory / name)
            assets.append(ref(directory / name))
            final_pages.append({"slide_id": row["slide_id"], "image": name})
        pages = final_pages
        render_ref = ref(renders)
    elif phase == "final":
        pages = []
    payload = {"brief": brief_value, "instruction": phase_prompt(phase), "pages": pages}
    write(directory / "reader-input.json", payload)
    packet = {"contract": PACKET, "phase": phase,
              "run_id": binding["run_id"], "task_request_sha256": binding["task_request_sha256"],
              "package": ref(package), "pptx": ref(pptx) if phase == "final" else None,
              "renders": render_ref, "input": ref(directory / "reader-input.json"),
              "assets": assets, "unavailable_reason": unavailable_reason, "created_at": now()}
    validate_packet(packet)
    write(output, packet)
    return packet


def validate_packet(packet: dict[str, Any]) -> dict[str, Any]:
    if packet.get("contract") != PACKET or packet.get("phase") not in PHASES:
        raise ValueError("invalid reader packet contract/phase")
    package = load_ref(packet["package"])
    binding = package["run_binding"]
    if any(packet[k] != binding[k] for k in ("run_id", "task_request_sha256")):
        raise ValueError("reader packet task/run differs from source")
    payload = load_ref(packet["input"])
    if set(payload) != {"brief", "instruction", "pages"} or payload["instruction"] != phase_prompt(packet["phase"]):
        raise ValueError("reader input contains unauthorized fields/instructions")
    if set(payload["brief"]) != {"audience", "purpose", "task"} or not all(_text(v) for v in payload["brief"].values()):
        raise ValueError("reader brief must contain neutral audience, purpose and task")
    directory = Path(packet["input"]["path"]).parent
    allowed = {Path(packet["input"]["path"])}
    for asset in packet["assets"]:
        path = load_ref(asset, json_value=False)
        if path.parent != directory or path.suffix != ".png" or path.is_symlink():
            raise ValueError("reader assets must be contained PNG files")
        allowed.add(path)
    if any(p.is_symlink() for p in directory.iterdir()) or set(directory.iterdir()) != allowed:
        raise ValueError("reader input directory includes undeclared files")
    source_pages = projection(package, packet["phase"])
    if packet["phase"] != "final":
        if payload["pages"] != source_pages or packet["assets"] or packet["pptx"] or packet["renders"]:
            raise ValueError("Copy reader input differs from visible-only text projection")
    else:
        pptx = load_ref(packet["pptx"], json_value=False)
        if packet["renders"] is None:
            if payload["pages"] or packet["assets"] or not _text(packet.get("unavailable_reason")):
                raise ValueError("unavailable final reading must disclose missing renders")
            return payload
        renders = load_ref(packet["renders"])
        if renders.get("pptx_sha256") != ref(pptx)["sha256"]:
            raise ValueError("final reader render/PPTX mismatch")
        expected = [{"slide_id": p["slide_id"], "image": f"page-{i+1:03d}.png"} for i, p in enumerate(source_pages)]
        if [r.get("slide_id") for r in renders.get("slides", [])] != [p["slide_id"] for p in source_pages]:
            raise ValueError("reader renders must cover current pages in order")
        if payload["pages"] != expected or len(packet["assets"]) != len(expected):
            raise ValueError("final reader pages/order differ from source")
        from PIL import Image
        for index, (row, page) in enumerate(zip(renders["slides"], expected)):
            original = load_ref({k: row[k] for k in ("path", "sha256", "bytes")}, json_value=False)
            if row["slide_id"] != page["slide_id"]:
                raise ValueError("reader render slide ID mismatch")
            with Image.open(original) as a, Image.open(directory / page["image"]) as b:
                if b.info or a.size != b.size or a.convert("RGB").tobytes() != b.convert("RGB").tobytes():
                    raise ValueError("reader image differs from source pixels or carries metadata")
    _time(packet["created_at"])
    return payload


def validate_context(context: dict[str, Any], packet: dict[str, Any]) -> None:
    required = {"execution_mode", "context_id", "production_context_id", "history_inherited",
                "host_receipt", "access_scope", "limitations"}
    if set(context) != required or context["access_scope"] not in {"host-restricted", "instruction-only", "unavailable"}:
        raise ValueError("reader context must disclose execution, history, access and limitations")
    if not isinstance(context["limitations"], list) or not all(_text(v) for v in context["limitations"]):
        raise ValueError("reader context limitations must be text observations")
    if not all(_text(context[k]) for k in ("context_id", "production_context_id")):
        raise ValueError("reader and production context IDs are required")
    if context["execution_mode"] == "same-context-limited":
        if not context["limitations"] or context["access_scope"] == "host-restricted":
            raise ValueError("shared-context reading must disclose its limitation")
        return
    if context["execution_mode"] not in {"separate-context", "same-model-new-context", "separate-process"}:
        raise ValueError("invalid reader execution mode")
    if context["history_inherited"] is not False or context["context_id"] == context["production_context_id"]:
        raise ValueError("fresh reader context must not inherit production history")
    receipt = load_ref(context["host_receipt"])
    # Host adapters capture real dispatch output; these fields are attestations,
    # not proof of identity or operating-system access isolation.
    for key in ("context_id", "production_context_id", "history_inherited", "access_scope"):
        if receipt.get(key) != context[key]:
            raise ValueError(f"reader host receipt disagrees with {key}")
    inputs = [packet["input"], *packet["assets"]]
    if receipt.get("input_files") != inputs or not receipt.get("host_tool"):
        raise ValueError("reader host receipt must bind exact dispatched inputs and tool")
    load_ref(receipt["raw_receipt"], json_value=False)
    if context["access_scope"] != "host-restricted" and not context["limitations"]:
        raise ValueError("instruction-only isolation must disclose shared tool/file access")


def validate_first(value: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    if value.get("contract") != FIRST_READ or value.get("status") not in {"observed", "not-run"}:
        raise ValueError("invalid first-read contract/status")
    packet = load_ref(value["packet"])
    payload = validate_packet(packet)
    validate_context(value["context"], packet)
    if _time(value["recorded_at"]) < _time(packet["created_at"]):
        raise ValueError("first reading precedes packet")
    response = value["response"]
    if value["status"] == "not-run":
        if response is not None or not _text(value.get("reason")):
            raise ValueError("unavailable reader review needs a reason and no fabricated response")
        return packet, payload
    if packet["phase"] == "final" and packet["renders"] is None:
        raise ValueError("final reader cannot claim observed without final renders")
    if not isinstance(response, dict) or set(response) != {"assessment", "title_reading", "understanding", "findings"}:
        raise ValueError("reader response needs actual title reading, understanding and findings")
    if response["assessment"] not in {"understood", "understanding-gaps", "insufficient-input"}:
        raise ValueError("invalid professional reader assessment")
    if not _text(response["title_reading"]) or not isinstance(response["understanding"], list) or not response["understanding"]:
        raise ValueError("reader must record actual title reading and retelling")
    slide_ids = {p["slide_id"] for p in payload["pages"]}
    for row in response["understanding"]:
        if set(row) != {"question", "answer", "slide_ids", "visible_evidence", "uncertainty"}:
            raise ValueError("retelling must preserve question, answer, evidence and uncertainty")
        if not all(_text(row[k]) for k in ("question", "answer")) or not isinstance(row["visible_evidence"], str) or not isinstance(row["uncertainty"], str):
            raise ValueError("invalid retelling text")
        if not isinstance(row["slide_ids"], list) or not set(row["slide_ids"]) <= slide_ids:
            raise ValueError("retelling refers to unknown pages")
        if not row["slide_ids"] and not _text(row["uncertainty"]):
            raise ValueError("unlocated retelling must disclose uncertainty")
    ids = set()
    copy_locations = {u["copy_id"]: p["slide_id"] for p in projection(load_ref(packet["package"]), packet["phase"]) for u in p["text"]}
    if not isinstance(response["findings"], list):
        raise ValueError("reader findings must be an array")
    for row in response["findings"]:
        if set(row) != {"finding_id", "slide_ids", "copy_ids", "statement", "reader_impact"}:
            raise ValueError("reader finding needs exact location and reader impact")
        if not all(_text(row[k]) for k in ("finding_id", "statement", "reader_impact")) or row["finding_id"] in ids:
            raise ValueError("reader findings need unique IDs and concrete statements")
        if not row["slide_ids"] or not set(row["slide_ids"]) <= slide_ids or not isinstance(row["copy_ids"], list):
            raise ValueError("reader finding location is invalid")
        if any(copy_locations.get(cid) not in row["slide_ids"] for cid in row["copy_ids"]):
            raise ValueError("reader finding copy IDs must belong to cited pages")
        ids.add(row["finding_id"])
    if response["assessment"] == "understanding-gaps" and not ids:
        raise ValueError("understanding gaps need concrete findings")
    if response["assessment"] == "understood" and ids:
        raise ValueError("reader findings cannot coexist with an unqualified understood assessment")
    return packet, payload


def record_first(*, packet: Path, context: Path, output: Path,
                 response: Path | None = None, reason: str | None = None) -> dict[str, Any]:
    value = {"contract": FIRST_READ, "packet": ref(packet), "context": read(context),
             "status": "observed" if response else "not-run", "response": read(response) if response else None,
             "reason": reason, "recorded_at": now()}
    validate_first(value)
    write(output, value)
    return value


def record_review(*, first_read: Path, dispositions: Path, evidence: list[Path],
                  output: Path, previous_reviews: list[Path] = (), comparison: Path | None = None) -> dict[str, Any]:
    first = read(first_read)
    packet, _ = validate_first(first)
    value = {"contract": CONTRACT, "phase": packet["phase"], "run_id": packet["run_id"],
             "task_request_sha256": packet["task_request_sha256"], "first_read": ref(first_read),
             "evidence": [ref(p) for p in evidence], "dispositions": read(dispositions),
             "previous_reviews": [ref(p) for p in previous_reviews], "reconciled_at": now()}
    if comparison is not None:
        value["comparison"] = read(comparison)
    validate_review(value)
    write(output, value)
    return value


def validate_review(value: dict[str, Any], *, package_sha256: str | None = None,
                    pptx_sha256: str | None = None, current_package: dict[str, Any] | None = None) -> dict[str, Any]:
    if value.get("contract") != CONTRACT:
        raise ValueError("invalid reader review contract")
    first = load_ref(value["first_read"])
    packet, payload = validate_first(first)
    if any(value[k] != packet[k] for k in ("phase", "run_id", "task_request_sha256")):
        raise ValueError("reader review phase/task/run differs from first reading")
    if current_package is not None and semantic_input(load_ref(packet["package"]), value["phase"]) != semantic_input(current_package, value["phase"]):
        raise ValueError(f"{value['phase']} reader is stale: visible content or Logic baseline changed; rerun affected reading")
    if current_package is None and package_sha256 and packet["package"]["sha256"] != package_sha256:
        raise ValueError("reader review is stale for current Copy revision")
    if value["phase"] == "final" and pptx_sha256 and packet["pptx"]["sha256"] != pptx_sha256:
        raise ValueError("reader review is stale for current PPTX")
    if _time(value["reconciled_at"]) < _time(first["recorded_at"]):
        raise ValueError("reconciliation precedes frozen first reading")
    history = []
    for item in value["previous_reviews"]:
        previous = load_ref(item)
        history.append(validate_review(previous))
        if any(previous[k] != value[k] for k in ("phase", "run_id", "task_request_sha256")) or _time(previous["reconciled_at"]) > _time(first["recorded_at"]):
            raise ValueError("previous reader review must be from the same task/phase and precede this reading")
    for item in value["evidence"]:
        load_ref(item, json_value=False)
    if first["status"] == "observed" and not value["evidence"]:
        raise ValueError("observed reading needs second-pass evidence")
    findings = first["response"]["findings"] if first["response"] else []
    ids = {f["finding_id"] for f in findings}
    rows = value["dispositions"]
    if not isinstance(rows, list) or len(rows) != len(ids) or {r.get("finding_id") for r in rows} != ids:
        raise ValueError("every first-read finding needs exactly one disposition")
    for row in rows:
        if set(row) != {"finding_id", "owner_layer", "status", "explanation", "evidence_refs"}:
            raise ValueError("reader disposition fields are invalid")
        if row["status"] not in {"open", "disputed-with-evidence"}:
            raise ValueError("a repair requires a new reading of the revised artifact; preserve this finding")
        if row["owner_layer"] not in {"logic", "copy", "art-direction", "output", "supervisor"} or not _text(row["explanation"]):
            raise ValueError("reader disposition needs earliest owner and explanation")
        if not row["evidence_refs"] or not all(r in value["evidence"] for r in row["evidence_refs"]):
            raise ValueError("reader disposition must cite bound second-pass evidence")
    comparison = value.get("comparison")
    if value["phase"] in {"title", "content"} or comparison is not None:
        if not isinstance(comparison, dict) or set(comparison) != {"baseline", "checks", "verdict", "explanation"}:
            raise ValueError("second pass requires comparison: baseline, checks, verdict, explanation")
        baseline = load_ref(comparison["baseline"])
        if comparison["baseline"] not in value["evidence"]:
            raise ValueError("comparison baseline must be bound second-pass evidence")
        source = load_ref(packet["package"])
        if baseline.get("run_binding") != source["run_binding"]:
            raise ValueError("comparison baseline belongs to another task/run")
        if value["phase"] in {"title", "content"}:
            if baseline.get("status") != "logic-approved" or not baseline.get("research") or baseline["research"] != source.get("research"):
                raise ValueError("title/content comparison requires the original approved Logic research")
        elif semantic_input(baseline, "content") != semantic_input(source, "content") or baseline.get("status") != "copy-approved":
            raise ValueError("final comparison requires the approved Copy baseline")
        checks = {"research_conclusions"} if value["phase"] == "title" else {"accuracy", "completeness", "reasoning"}
        if not isinstance(comparison["checks"], dict) or set(comparison["checks"]) != checks or not all(_text(v) for v in comparison["checks"].values()):
            raise ValueError(f"comparison requires grounded observations for {sorted(checks)}")
        if comparison["verdict"] not in {"pass", "return-copy", "return-art", "return-logic"} or not _text(comparison["explanation"]):
            raise ValueError("comparison requires an explicit verdict and evidence explanation")
    host_evidence = None
    if first["context"]["host_receipt"] is not None:
        host_receipt = load_ref(first["context"]["host_receipt"])
        raw = load_ref(host_receipt["raw_receipt"], json_value=False)
        host_evidence = {"receipt": host_receipt, "raw_receipt": {
            "ref": host_receipt["raw_receipt"], "base64": base64.b64encode(raw.read_bytes()).decode()}}
    return {"review": value, "first_read": first, "packet": packet,
            "visible_input": payload, "host_evidence": host_evidence, "history": history,
            "assessment": first["response"]["assessment"] if first["response"] else "not-run",
            "independence": first["context"]["execution_mode"],
            "input_scope": first["context"]["access_scope"]}


def required_for_config(config: dict[str, Any]) -> bool:
    return config.get("workflow", {}).get("reader_review", {}).get("required") is True


def validate_copy_review_order(auditor: dict[str, Any], calibration: dict[str, Any]) -> None:
    reviews = audit_reviews(auditor)
    for phase in ("copy", "title", "content"):
        if phase not in reviews:
            continue
        review = reviews[phase]["review"]
        reviewed, calibrated = _time(review["reconciled_at"]), _time(calibration["recorded_at"])
        if "." not in calibration["recorded_at"] and phase == "copy":
            reviewed = reviewed.replace(microsecond=0)
        if reviewed > calibrated:
            raise ValueError("Copy reader review must precede Copy-to-Art calibration; do not backfill it after Output")


def audit_reviews(auditor: dict[str, Any], *, required: bool = False, config: dict[str, Any] | None = None) -> dict[str, Any]:
    sources = {r["kind"]: r for r in auditor.get("source_records", [])}
    result = {}
    config_row = sources.get("config")
    config = config if config is not None else (load_ref({k: config_row[k] for k in ("path", "sha256", "bytes")}) if config_row else {})
    default_phases = list(NEW_PHASES) if "reader-review-title" in sources or "reader-review-content" in sources else ["copy", "final"]
    phases = config.get("workflow", {}).get("reader_review", {}).get("phases", default_phases)
    package_row = sources.get("package")
    current = load_ref({k: package_row[k] for k in ("path", "sha256", "bytes")}) if package_row else None
    for phase in dict.fromkeys([*phases, *PHASES]):
        row = sources.get(f"reader-review-{phase}")
        if row is None:
            if required and phase in phases:
                raise ValueError(f"reader-review-{phase} is required (record unavailable execution explicitly)")
            continue
        value = load_ref({k: row[k] for k in ("path", "sha256", "bytes")})
        review = validate_review(value, package_sha256=sources.get("package", {}).get("sha256"),
                                 pptx_sha256=auditor.get("final_pptx", {}).get("sha256"),
                                 current_package=current if phase in phases and phases == list(NEW_PHASES) else None)
        if value["phase"] != phase or any(value[k] != auditor[k] for k in ("run_id", "task_request_sha256")):
            raise ValueError("reader review binding differs from final audit")
        if _time(value["reconciled_at"]) > _time(auditor["audited_at"]):
            raise ValueError("reader review was recorded after final audit")
        result[phase] = review
    seen = set()
    for review in result.values():
        context = review["first_read"]["context"]
        if context["context_id"] in seen and context["execution_mode"] != "same-context-limited":
            raise ValueError("each reader must use a new context, not an earlier reader context")
        seen.add(context["context_id"])
    if required and phases == list(NEW_PHASES):
        for review in result.values():
            require_pass(review)
        validate_sequence(result["title"], result["content"])
        if _time(result["content"]["review"]["reconciled_at"]) > _time(result["final"]["packet"]["created_at"]):
            raise ValueError("final reader must start after approved content reading")

    return result


def reader_status(reviews: dict[str, Any]) -> str:
    if any(r["assessment"] in {"not-run", "insufficient-input"} or r["independence"] == "same-context-limited" for r in reviews.values()):
        return "incomplete-evidence"
    if any(r["first_read"]["response"]["findings"] or r["review"].get("comparison", {}).get("verdict", "pass") != "pass" for r in reviews.values()):
        return "issues-found"
    return "observations-recorded"


def audit_reader_findings(auditor: dict[str, Any], reviews: dict[str, Any]) -> list[dict[str, Any]]:
    """Carry reader observations into the existing findings, without scoring prose."""
    sources = {r["kind"]: r for r in auditor.get("source_records", [])}
    result = []
    for phase, review in reviews.items():
        response = review["first_read"]["response"]
        if response is None:
            continue
        dispositions = {r["finding_id"]: r for r in review["review"]["dispositions"]}
        source = sources[f"reader-review-{phase}"]
        for finding in response["findings"]:
            disposition = dispositions[finding["finding_id"]]
            result.append({"finding_id": f"READER-{phase}-{finding['finding_id']}",
                "requirement_ids": [], "rule_ids": [], "slide_ids": finding["slide_ids"],
                "owner_layer": disposition["owner_layer"], "severity": "moderate",
                "statement": "Reader observation: " + finding["statement"],
                "expected": "The intended reader can explain the supported meaning from visible content.",
                "actual": finding["statement"], "impact": finding["reader_impact"],
                "evidence_refs": [f"reader-review-{phase} sha256={source['sha256']}"],
                "recommended_change": disposition["status"] + ": " + disposition["explanation"]})
    return result


def require_pass(review):
    phase = review["review"]["phase"]
    owner = "art-direction" if phase == "final" else "copy"
    comparison = review["review"].get("comparison", {})
    if comparison.get("verdict") == "return-logic":
        owner = "logic"
    if (review["assessment"] != "understood" or review["independence"] == "same-context-limited"
            or comparison.get("verdict") != "pass" or review["first_read"]["response"]["findings"]):
        raise ValueError(f"{phase} reader gate blocked; owner={owner}; repair affected content, preserve first reading, then reread. No downstream production.")


def validate_sequence(title, content):
    if title["first_read"]["context"]["context_id"] == content["first_read"]["context"]["context_id"]:
        raise ValueError("content reader requires a fresh context independent of title reader")
    if _time(title["review"]["reconciled_at"]) > _time(content["packet"]["created_at"]):
        raise ValueError("content reader must start after title reconciliation")


def check_art_gate(package, title_review, content_review):
    reviews = {}
    for phase, path in (("title", title_review), ("content", content_review)):
        if path is None:
            raise ValueError(f"Art blocked: --{phase}-review is required; finish Copy reading before design or rendering")
        result = validate_review(read(path), current_package=package)
        if result["review"]["phase"] != phase:
            raise ValueError(f"Art gate expected {phase} review")
        require_pass(result)
        reviews[phase] = result
    validate_sequence(reviews["title"], reviews["content"])
    return {"ready": True, "owner": "art-direction", "reviews": {
        "title": ref(title_review), "content": ref(content_review)},
        "content_sha256": digest(semantic_input(package, "content"))}


def repair_scope(before, after, *, artifact="copy"):
    if artifact in {"report", "audit-record", "receipt"}:
        return {"owner": "supervisor", "resume": ["repair-record", "validate", "assemble-report"], "render": False}
    if before.get("research") != after.get("research") or before.get("brief") != after.get("brief"):
        return {"owner": "logic", "resume": ["logic", "copy", "title", "content", "art-direction", "output", "final", "supervisor"], "render": True}
    if semantic_input(before, "title") != semantic_input(after, "title"):
        start = ["title", "content"]
    elif semantic_input(before, "content") != semantic_input(after, "content"):
        start = ["content"]
    else:
        return {"owner": "interface", "resume": ["rebind-records", "validate", "assemble-report"], "render": False}
    return {"owner": "copy", "resume": start + ["art-direction", "output", "final", "supervisor"], "render": True}
