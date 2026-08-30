#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Regression tests for pre-Logic resource discovery, briefing, and usage."""

from __future__ import annotations

import copy
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
VALIDATORS = ROOT / "packages" / "validators"
for directory in (ROOT, VALIDATORS):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

from packages.index_runtime.utils import sha256_json  # noqa: E402
from resource_inventory import (  # noqa: E402
    finalize_resource_inventory,
    resource_inventory_signature,
    validate_resource_inventory,
    validate_resource_usage,
)
from validate_logic_package import validate_package  # noqa: E402


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _scope(scope: str, count: int, status: str = "complete") -> dict[str, Any]:
    return {
        "scope": scope,
        "status": status,
        "evidence_ref": f"evidence/{scope}.json",
        "discovered_entry_count": count,
        "note": f"{scope} was inspected deterministically",
    }


def _resource(
    resource_id: str,
    category: str,
    label: str,
    origin: str,
    locator: str,
    stages: list[str],
    fingerprint: str | None,
    *,
    quantity: int = 1,
    required: bool = True,
    rights: str = "owner-private",
) -> dict[str, Any]:
    return {
        "resource_id": resource_id,
        "category": category,
        "label": label,
        "origin": origin,
        "locator": locator,
        "availability": "available",
        "required": required,
        "stages": stages,
        "quantity": quantity,
        "fingerprint_sha256": fingerprint,
        "rights_context": rights,
        "decision": "selected",
        "decision_reason": f"selected because {label} is needed by this task",
        "evidence_ref": f"evidence/{resource_id}.json",
    }


def _draft() -> dict[str, Any]:
    resources = [
        _resource("task.request", "task-input", "user request", "task", "task://request", ["root", "logic"], "a" * 64, rights="task-provided"),
        _resource("plugin.five-skills", "plugin-skill", "five governed Skills", "plugin", "plugin://skills", ["root", "logic", "copy", "art-direction", "output", "supervisor"], "b" * 64, quantity=5, rights="public-open-source"),
        _resource("owner.learning-pools", "library-source", "owner learning and visual indexes", "owner-library", "library://example-presentation/learning", ["root", "logic", "copy", "art-direction", "output", "supervisor"], "c" * 64, quantity=8),
        _resource("public.index", "index-provider", "bundled public Index", "public-catalog", "public-index://builtin-catalog", ["root", "logic", "copy", "art-direction", "output", "supervisor"], "d" * 64, quantity=24, rights="public-open-source"),
        _resource("owner.theme", "theme", "owner presentation theme", "owner-library", "library://example-presentation/theme", ["root", "art-direction", "output", "supervisor"], "e" * 64),
        _resource("host.authoring-route", "authoring-route", "native presentation authoring route", "host", "host://native-presentation", ["root", "output", "supervisor"], None, rights="host-capability"),
        _resource("host.font-environment", "font", "inspected font environment", "host", "host://fonts", ["root", "output", "supervisor"], None, rights="host-capability"),
    ]
    return {
        "contract": "io.clayz.presentation.resource-inventory/1.0",
        "inventory_id": "inventory.regression.001",
        "revision": 1,
        "task_mode": "new-build",
        "runtime_mode": "owner-personal",
        "created_at": "2026-08-28T08:00:00+00:00",
        "scan_scope": [
            _scope("plugin-runtime", 2),
            _scope("task-inputs", 1),
            _scope("owner-library", 2),
            _scope("public-index", 1),
            _scope("brand-assets", 1),
            _scope("host-capabilities", 1),
            _scope("font-environment", 1),
        ],
        "resources": resources,
        "execution_route": {
            "status": "ready",
            "authoring_route": "native presentation authoring",
            "render_route": "native reopen and full-slide render",
            "target_application": "Microsoft PowerPoint",
            "evidence_ref": "runtime-preflight.json",
        },
        "user_brief": {
            "status": "presented",
            "presented_at": "2026-08-28T08:01:00+00:00",
            "channel": "commentary",
            "language": "zh-CN",
            "reported_resource_ids": sorted(item["resource_id"] for item in resources),
            "reported_selected_resource_ids": sorted(item["resource_id"] for item in resources),
            "reported_not_selected_resource_ids": [],
            "reported_unavailable_resource_ids": [],
            "discovered_lines": [
                "任务材料1项，完整插件与五个治理Skill均可用",
                "个人学习及视觉索引8类、公共Index 24项、个人主题1套",
            ],
            "selected_lines": [
                "本次将使用任务材料、个人学习与视觉索引、公共Index及个人主题",
                "制作与监督将使用已检查的原生演示文稿路线和字体环境",
            ],
            "unavailable_lines": [],
            "execution_line": "资源锁定完成，使用原生制作并在目标应用重新打开渲染，现在开始Logic",
        },
        "gate": {
            "verified_before_logic": True,
            "authoring_started_at": "2026-08-28T08:02:00+00:00",
        },
    }


def _valid_inventory() -> dict[str, Any]:
    return finalize_resource_inventory(_draft())


def test_ready_inventory() -> None:
    inventory = _valid_inventory()
    errors: list[str] = []
    validate_resource_inventory(inventory, "inventory", errors, require_ready=True)
    _assert(errors == [], f"ready inventory must pass: {errors}")
    _assert(inventory["gate"]["authoring_may_start"] is True, "ready inventory must authorize Logic")
    _assert(inventory["summary"]["item_quantity_total"] == 41, "pool quantities must be visible")


def test_user_brief_precedes_logic() -> None:
    draft = _draft()
    draft["gate"]["authoring_started_at"] = "2026-08-28T07:59:00+00:00"
    inventory = finalize_resource_inventory(draft)
    errors: list[str] = []
    validate_resource_inventory(inventory, "inventory", errors, require_ready=True)
    _assert(any("must precede authoring start" in error for error in errors), "authoring before the brief must fail")

    pending = _draft()
    pending["user_brief"]["status"] = "pending"
    pending["user_brief"]["presented_at"] = None
    inventory = finalize_resource_inventory(pending)
    errors = []
    validate_resource_inventory(inventory, "inventory", errors, require_ready=True)
    _assert(any("required before Logic" in error for error in errors), "a pending brief must block Logic")


def test_missing_owner_resource_fails_closed() -> None:
    draft = _draft()
    library = next(item for item in draft["resources"] if item["resource_id"] == "owner.learning-pools")
    library["availability"] = "missing"
    library["decision"] = "unavailable"
    library["fingerprint_sha256"] = None
    next(item for item in draft["scan_scope"] if item["scope"] == "owner-library")["status"] = "partial"
    inventory = finalize_resource_inventory(draft)
    errors: list[str] = []
    validate_resource_inventory(inventory, "inventory", errors, require_ready=False)
    _assert(inventory["gate"]["status"] == "blocked", "missing owner resources must block")
    _assert("owner.learning-pools" in inventory["gate"]["blocking_resource_ids"], "the user must see the exact missing pool")
    _assert(inventory["gate"]["authoring_started_at"] is None, "blocked inventory cannot claim authoring started")


def test_user_brief_privacy() -> None:
    draft = _draft()
    synthetic_path = "C:" + "\\".join(("", "Users", "example", "private", "master.pptx"))
    draft["user_brief"]["selected_lines"][0] = f"Use {synthetic_path}"
    inventory = finalize_resource_inventory(draft)
    errors: list[str] = []
    validate_resource_inventory(inventory, "inventory", errors, require_ready=True)
    _assert(any("must not expose private paths" in error for error in errors), "user brief must sanitize private paths")


def test_user_brief_resource_coverage() -> None:
    draft = _draft()
    draft["user_brief"]["reported_selected_resource_ids"].remove("owner.theme")
    inventory = finalize_resource_inventory(draft)
    errors: list[str] = []
    validate_resource_inventory(inventory, "inventory", errors, require_ready=True)
    _assert(any("must cover every selected resource" in error for error in errors), "the brief must disclose every selected resource")


def _usage(inventory: dict[str, Any]) -> dict[str, Any]:
    used = list(inventory["selected_resource_ids"])
    stage_usage = [
        {"stage": "logic", "resource_ids": ["task.request", "plugin.five-skills", "owner.learning-pools", "public.index"], "evidence_refs": ["logic-package.json"]},
        {"stage": "copy", "resource_ids": ["plugin.five-skills", "owner.learning-pools"], "evidence_refs": ["copy-package.json"]},
        {"stage": "art-direction", "resource_ids": ["plugin.five-skills", "owner.learning-pools", "public.index", "owner.theme"], "evidence_refs": ["art-direction-plan.json"]},
        {"stage": "output", "resource_ids": ["plugin.five-skills", "owner.learning-pools", "owner.theme", "host.authoring-route", "host.font-environment"], "evidence_refs": ["object-inventory.json", "output-qa.json"]},
        {"stage": "supervisor", "resource_ids": used, "evidence_refs": ["supervision-report.json"]},
    ]
    lines = [
        "实际使用了任务材料、个人学习与视觉索引、公共Index和个人主题",
        "五个治理阶段均使用已盘点的原生制作路线与字体环境完成并复核",
    ]
    signature = resource_inventory_signature(inventory)
    return {
        "contract": "io.clayz.presentation.resource-usage/1.0",
        "inventory_id": signature["inventory_id"],
        "inventory_revision": signature["revision"],
        "inventory_lock_digest": signature["digest"],
        "used_resource_ids": used,
        "unused_selected_resources": [],
        "stage_usage": stage_usage,
        "user_summary": {
            "status": "presented",
            "presented_at": "2026-08-28T08:30:00+00:00",
            "lines": lines,
            "content_sha256": sha256_json(lines),
        },
    }


def test_final_usage_reconciliation() -> None:
    inventory = _valid_inventory()
    usage = _usage(inventory)
    errors: list[str] = []
    validate_resource_usage(usage, inventory, "usage", errors)
    _assert(errors == [], f"complete usage reconciliation must pass: {errors}")

    incomplete = copy.deepcopy(usage)
    incomplete["used_resource_ids"].remove("owner.theme")
    errors = []
    validate_resource_usage(incomplete, inventory, "usage", errors)
    _assert(any("reconciled as used or unused" in error for error in errors), "every selected resource requires a final disposition")


def test_logic_requires_inventory() -> None:
    errors = validate_package({}, "logic-approved")
    _assert(any("resource_inventory" in error for error in errors), "Logic must reject a missing Supervisor inventory")


def main() -> int:
    tests = (
        test_ready_inventory,
        test_user_brief_precedes_logic,
        test_missing_owner_resource_fails_closed,
        test_user_brief_privacy,
        test_user_brief_resource_coverage,
        test_final_usage_reconciliation,
        test_logic_requires_inventory,
    )
    try:
        for test in tests:
            test()
    except (AssertionError, OSError, ValueError, TypeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"ok": True, "tests": [test.__name__ for test in tests]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
