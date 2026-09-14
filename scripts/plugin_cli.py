#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Local plugin entrypoint for inspection, discussed knowledge, and PPT retrieval."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def read_object(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object: {path.name}")
    return value


def bindings(values: list[str]) -> dict[str, Path]:
    result = {}
    for raw in values:
        identifier, separator, value = raw.partition("=")
        if not separator or not identifier or not value or identifier in result:
            raise ValueError("attachments require unique ID=PATH bindings")
        result[identifier] = Path(value).resolve(strict=True)
    return result


def external_store(path: Path) -> Path:
    resolved = path.resolve()
    if resolved == ROOT or ROOT in resolved.parents:
        raise ValueError("owner Library and review files must be outside the plugin installation")
    return resolved


def emit(value: dict, output: Path | None) -> None:
    text = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if output:
        output = output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        # Drafts, confirmations and receipts are immutable review artifacts.
        if output.exists():
            if output.read_text(encoding="utf-8") != text:
                raise ValueError("output already exists with different content; use a new revision path")
        else:
            with output.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(text)
    print(text, end="")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect", help="offline package, Library and tool inventory")
    inspect.add_argument("--store", type=Path)
    inspect.add_argument("--output", type=Path)
    tools = commands.add_parser("tools", help="discover bundled methods and tool entrypoints")
    tools.add_argument("--output", type=Path)
    draft = commands.add_parser("draft", help="prepare exact consensus and attachment review")
    draft.add_argument("--content", type=Path, required=True)
    draft.add_argument("--attachment", action="append", default=[], metavar="ID=PATH")
    draft.add_argument("--output", type=Path, required=True)
    confirm = commands.add_parser("confirm", help="record the actual user's exact-draft decision")
    confirm.add_argument("--draft", type=Path, required=True)
    confirm.add_argument("--expected-sha256", required=True)
    confirm.add_argument("--confirmed-by", required=True)
    confirm.add_argument("--decision", required=True)
    confirm.add_argument("--confirm-human-decision", action="store_true")
    confirm.add_argument("--output", type=Path, required=True)
    commit = commands.add_parser("commit", help="atomically save confirmed knowledge and attachments")
    commit.add_argument("--store", type=Path, required=True)
    commit.add_argument("--draft", type=Path, required=True)
    commit.add_argument("--confirmation", type=Path, required=True)
    commit.add_argument("--attachment", action="append", default=[], metavar="ID=PATH")
    commit.add_argument("--output", type=Path)
    retrieve = commands.add_parser("retrieve", help="query confirmed knowledge through the shared index")
    retrieve.add_argument("--store", type=Path, required=True)
    retrieve.add_argument("--request", type=Path, required=True)
    retrieve.add_argument("--snapshot")
    retrieve.add_argument("--output", type=Path)
    read = commands.add_parser("read", help="read verified consensus and its source attachment locations")
    read.add_argument("--store", type=Path, required=True)
    read.add_argument("--record-id", required=True)
    read.add_argument("--snapshot")
    read.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    try:
        from packages.knowledge_session.discussion import prepare_draft, confirm_draft
        from packages.knowledge_session.store import commit_knowledge
        from packages.runtime.plugin_session import inspect_plugin, list_tools, retrieve_knowledge, materialize_knowledge

        if args.command in {"draft", "confirm"}:
            external_store(args.output)
        if args.command == "inspect":
            result = inspect_plugin(ROOT, external_store(args.store) if args.store else None)
        elif args.command == "tools":
            result = list_tools(ROOT)
        elif args.command == "draft":
            result = prepare_draft(read_object(args.content), bindings(args.attachment))
        elif args.command == "confirm":
            result = confirm_draft(
                read_object(args.draft), expected_sha256=args.expected_sha256,
                confirmed_by=args.confirmed_by, decision=args.decision,
                confirm_human_decision=args.confirm_human_decision,
            )
        elif args.command == "commit":
            # Catch a conflicting receipt filename before a durable commit.
            if args.output and args.output.exists():
                raise ValueError("commit output path already exists; choose a new receipt path")
            result = commit_knowledge(
                external_store(args.store), read_object(args.draft),
                read_object(args.confirmation), bindings(args.attachment),
            )
        elif args.command == "read":
            result = materialize_knowledge(ROOT, external_store(args.store), args.record_id, args.snapshot)
        else:
            result = retrieve_knowledge(
                ROOT, external_store(args.store), read_object(args.request), args.snapshot,
            )
        try:
            emit(result, args.output)
        except OSError as exc:
            if args.command != "commit":
                raise
            # Persistence already succeeded. Do not misreport it as a failed
            # transaction merely because a separate receipt destination failed.
            emit({**result, "committed": True, "receipt_output_error": str(exc)}, None)
        failed = result.get("status") == "blocked"
        if args.command in {"retrieve", "read"} and result.get("status") == "unavailable":
            failed = True
        return 2 if failed else 0
    except (ImportError, OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())
