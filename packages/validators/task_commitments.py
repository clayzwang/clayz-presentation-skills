#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Enrich one task-acceptance draft with small, source-aware commitments.

This module keeps deterministic defaults in the validator layer so that the
stage Skills do not become a second configuration store.  It does not decide
content, narrative structure, or whether a user has accepted a failure.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from typing import Any


CONTRACT = "io.clayz.presentation.task-acceptance/1.0"

# These are central fallback commitments used only when the merged config does
# not provide the corresponding value.  They are deliberately non-blocking:
# deterministic checks must report a miss, while release policy remains a
# Supervisor/user decision.
DEFAULT_POINT_SIZES: dict[str, int] = {
    "title": 24,
    "body": 18,
    "chart": 12,
    "footnote": 12,
    "page_number": 10,
}
DEFAULT_PAGE_NUMBER_POLICY: dict[str, Any] = {
    "required": True,
    "position": "footer-right",
    "scope": "body-and-closing",
    "start": 1,
    "cover_counting": False,
    "mechanism": "editable-footer-field",
}
DEFAULT_CJK_FAMILY = "Noto Sans CJK SC"
DEFAULT_LATIN_FAMILY = "Aptos"
DEFAULT_COVER_MODE = "topic-only"
DEFAULT_CONCLUSION_ROLES = ["analysis", "recommendation", "decision", "closing"]

_FONT_HINTS = (
    "cjk",
    "noto",
    "思源",
    "黑体",
    "宋体",
    "楷体",
    "微软雅黑",
    "pingfang",
    "hiragino",
    "yahei",
    "simsun",
    "stfangsong",
)

PAGE_NUMBER_POLICY_PATHS = (
    "page_number_policy",
    "page_numbers",
    "theme.page_number_policy",
    "theme.page_numbers",
    "theme.typography.page_numbering",
    "theme.master_page_numbering",
    "master.page_numbering",
    "layout.page_numbering",
    "delivery.page_numbering",
    "workflow.page_numbering",
    "workflow.delivery_policy.page_numbering",
)

_DEFAULT_SPECS: tuple[dict[str, Any], ...] = (
    {
        "requirement_id": "COMMIT-FONT-CJK",
        "category": "typography",
        "owner_stage": "output",
        "statement": "CJK text uses the configured CJK font family or a declared equivalent alias.",
        "verification_method": "inspect written PPTX font fields and rendered CJK glyphs",
        "kind": "font-cjk",
    },
    {
        "requirement_id": "COMMIT-FONT-LATIN",
        "category": "typography",
        "owner_stage": "output",
        "statement": "Latin text uses the configured Latin font family.",
        "verification_method": "inspect written PPTX font fields and final render",
        "kind": "font-latin",
    },
    {
        "requirement_id": "COMMIT-FONT-DIGITS",
        "category": "typography",
        "owner_stage": "output",
        "statement": "Digits use the configured numeric/Latin font family consistently.",
        "verification_method": "inspect numeric text runs in the written PPTX and final render",
        "kind": "font-digits",
    },
    {
        "requirement_id": "COMMIT-FONT-CHART",
        "category": "typography",
        "owner_stage": "output",
        "statement": "Chart labels, axes, legends and annotations inherit the applicable CJK, Latin and digit font roles, with explicit chart-role overrides only where configured.",
        "verification_method": "inspect chart text properties and full-size chart render",
        "kind": "font-chart",
    },
    {
        "requirement_id": "COMMIT-SIZE-TITLE",
        "category": "typography",
        "owner_stage": "output",
        "statement": "Title text meets the central title point-size minimum.",
        "verification_method": "inspect title text properties and rendered legibility",
        "kind": "size-title",
    },
    {
        "requirement_id": "COMMIT-SIZE-BODY",
        "category": "typography",
        "owner_stage": "output",
        "statement": "Audience body text meets the central body point-size minimum.",
        "verification_method": "inspect audience text sizes and full-size render",
        "kind": "size-body",
    },
    {
        "requirement_id": "COMMIT-SIZE-CHART",
        "category": "typography",
        "owner_stage": "output",
        "statement": "Chart text meets the central chart point-size minimum.",
        "verification_method": "inspect chart labels/axes/legends and full-size render",
        "kind": "size-chart",
    },
    {
        "requirement_id": "COMMIT-SIZE-FOOTNOTE",
        "category": "typography",
        "owner_stage": "output",
        "statement": "Footnote and source text meets the central footnote point-size minimum.",
        "verification_method": "inspect footnote text properties and rendered legibility",
        "kind": "size-footnote",
    },
    {
        "requirement_id": "COMMIT-SIZE-PAGE-NUMBER",
        "category": "typography",
        "owner_stage": "output",
        "statement": "Page-number text meets the central page-number point-size minimum.",
        "verification_method": "inspect inherited page-number fields and final render",
        "kind": "size-page-number",
    },
    {
        "requirement_id": "COMMIT-COVER",
        "category": "delivery",
        "owner_stage": "logic",
        "statement": "Honor cover_policy: include one opening cover when required and do not add one when the policy explicitly says it is not required.",
        "verification_method": "compare the Logic page-role sequence with cover_policy and final slide order",
        "kind": "cover",
    },
    {
        "requirement_id": "COMMIT-CLOSING",
        "category": "delivery",
        "owner_stage": "logic",
        "statement": "Honor the closing policy independently: include one closing synthesis/action page when required and do not add one when explicitly excluded.",
        "verification_method": "compare the Logic page-role sequence with cover_policy and final slide order",
        "kind": "closing",
    },
    {
        "requirement_id": "COMMIT-PAGE-NUMBER",
        "category": "delivery",
        "owner_stage": "output",
        "statement": "Honor the page-number policy, including required state, position, applicable-slide range, sequence start, cover-counting rule and mechanism.",
        "verification_method": "inspect master/page-number fields and final rendered page sequence",
        "kind": "page-number",
    },
    {
        "requirement_id": "COMMIT-CHART-UNIT",
        "category": "visual",
        "owner_stage": "logic",
        "statement": "Every quantitative chart states its metric unit, or explicitly records that it is unitless.",
        "verification_method": "compare chart data contract, labels and source evidence with the final render",
        "kind": "chart-unit",
    },
)


class TaskCommitmentError(ValueError):
    """Raised when a task-acceptance draft or merged config is malformed."""


def _as_mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TaskCommitmentError(f"{label} must be an object")
    return dict(value)


def _config_root(config: Mapping[str, Any]) -> dict[str, Any]:
    """Accept either a merged config or a wrapper containing ``config``."""

    if isinstance(config.get("theme"), Mapping) or isinstance(config.get("layout"), Mapping):
        return dict(config)
    nested = config.get("config")
    if isinstance(nested, Mapping):
        return dict(nested)
    return dict(config)


def _read_path(root: Mapping[str, Any], path: str) -> tuple[bool, Any]:
    current: Any = root
    for part in path.split("."):
        if not isinstance(current, Mapping) or part not in current:
            return False, None
        current = current[part]
    return True, current


def _first_value(root: Mapping[str, Any], paths: Sequence[str]) -> tuple[bool, Any, str]:
    for path in paths:
        found, value = _read_path(root, path)
        if found and value is not None:
            return True, value, path
    return False, None, paths[0] if paths else ""


def _string_list(value: Any) -> list[str]:
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [item.strip() for item in value if isinstance(item, str) and item.strip()]
    return []


def _origin_rows(origin_map: Any) -> list[dict[str, Any]]:
    if origin_map is None:
        return []
    rows: list[dict[str, Any]] = []
    if isinstance(origin_map, Mapping):
        for path, raw in origin_map.items():
            if isinstance(raw, Mapping):
                row = dict(raw)
                row.setdefault("path", str(path))
            else:
                row = {"path": str(path), "source": raw}
            rows.append(row)
        return rows
    if isinstance(origin_map, Sequence) and not isinstance(origin_map, (str, bytes, bytearray)):
        for raw in origin_map:
            if isinstance(raw, Mapping) and isinstance(raw.get("path"), str):
                rows.append(dict(raw))
    return rows


def _origin_for(path: str, origin_map: Any, fallback: str | None = None) -> str:
    """Return a source label without inventing a user-origin claim."""

    rows = _origin_rows(origin_map)
    exact = [row for row in rows if row.get("path") == path]
    row = exact[0] if exact else None
    if row is None:
        # Some runtime origin maps use a leading ``config.`` prefix.
        row = next((item for item in rows if item.get("path") == f"config.{path}"), None)
    if row is not None:
        raw = row.get("source") or row.get("origin") or row.get("layer")
        if isinstance(raw, str) and raw.strip():
            return raw.strip()
    if fallback:
        return fallback
    return f"config:{path}"


def _source_rank(source: str) -> int:
    value = source.casefold().strip()
    if value == "user" or value.startswith("user:") or "user-request" in value:
        return 3
    if "personal" in value or "profile" in value:
        return 2
    if "default" in value or value.startswith("config:") or value.startswith("acceptance:"):
        return 1
    return 0


def _font_candidates(config: Mapping[str, Any], origin_map: Any = None) -> tuple[list[str], str]:
    typography = config.get("theme", {}).get("typography", {}) if isinstance(config.get("theme"), Mapping) else {}
    if not isinstance(typography, Mapping):
        typography = {}
    identities = typography.get("font_validation")
    values: list[str] = []
    if isinstance(identities, Mapping):
        deferred = identities.get("deferred_font_identities")
        if isinstance(deferred, Sequence) and not isinstance(deferred, (str, bytes, bytearray)):
            for identity in deferred:
                if not isinstance(identity, Mapping):
                    continue
                values.extend(_string_list(identity.get("canonical_family")))
                values.extend(_string_list(identity.get("pptx_family")))
                values.extend(_string_list(identity.get("aliases")))
    explicit = _string_list(typography.get("primary_fonts"))
    identity_path = "theme.typography.font_validation.deferred_font_identities"
    primary_path = "theme.typography.primary_fonts"
    if values and explicit:
        identity_source = _origin_for(identity_path, origin_map)
        primary_source = _origin_for(primary_path, origin_map)
        if _source_rank(primary_source) > _source_rank(identity_source):
            return explicit, primary_path
    if values:
        return list(dict.fromkeys(values)), identity_path
    if explicit:
        return explicit, primary_path
    return [], "theme.typography.primary_fonts"


def _font_roles(config: Mapping[str, Any], origin_map: Any) -> dict[str, tuple[str, str]]:
    typography = config.get("theme", {}).get("typography", {}) if isinstance(config.get("theme"), Mapping) else {}
    if not isinstance(typography, Mapping):
        typography = {}
    candidates, candidates_path = _font_candidates(config, origin_map)

    identities = typography.get("font_validation")
    identity_rows = []
    if isinstance(identities, Mapping):
        raw_rows = identities.get("deferred_font_identities")
        if isinstance(raw_rows, Sequence) and not isinstance(raw_rows, (str, bytes, bytearray)):
            identity_rows = [row for row in raw_rows if isinstance(row, Mapping)]

    def identity_for(role: str) -> tuple[str, str] | None:
        for identity in identity_rows:
            roles = _string_list(identity.get("roles") or identity.get("applies_to") or identity.get("applies_to_roles"))
            if not roles and len(identity_rows) != 1:
                continue
            if roles and role not in {item.casefold().replace("_", "-") for item in roles}:
                continue
            family = _string_list(identity.get("pptx_family")) or _string_list(identity.get("canonical_family"))
            if family:
                return family[0], _origin_for(
                    "theme.typography.font_validation.deferred_font_identities", origin_map
                )
            if roles:
                continue
        return None

    role_map = typography.get("font_roles")

    def pick(role: str, paths: Sequence[str], *, cjk: bool = False, fallback: str) -> tuple[str, str]:
        if isinstance(role_map, Mapping):
            mapped = _string_list(role_map.get(role) or role_map.get(role.replace("-", "_")))
            if mapped:
                role_path = "theme.typography.font_roles." + role
                role_source = _origin_for(role_path, origin_map)
                candidate_source = _origin_for(candidates_path, origin_map)
                if _source_rank(role_source) >= _source_rank(candidate_source):
                    return mapped[0], role_source
        found, value, path = _first_value(config, paths)
        explicit = _string_list(value) if found else []
        if explicit:
            role_source = _origin_for(path, origin_map)
            candidate_source = _origin_for(candidates_path, origin_map)
            if _source_rank(role_source) >= _source_rank(candidate_source):
                return explicit[0], role_source
        identity = identity_for(role)
        if identity is not None:
            candidate_source = _origin_for(candidates_path, origin_map)
            if _source_rank(identity[1]) >= _source_rank(candidate_source):
                return identity
        # A single configured family is an explicit unified family, even when
        # its name is unknown. Never replace it with a name guessed from a
        # language hint.
        if len(candidates) == 1:
            return candidates[0], _origin_for(candidates_path, origin_map)
        matches = [item for item in candidates if any(hint in item.casefold() for hint in _FONT_HINTS)]
        if cjk and matches:
            return matches[0], _origin_for(candidates_path, origin_map)
        if not cjk:
            latin = [item for item in candidates if item not in matches and item.casefold() not in {"sans-serif", "serif"}]
            if latin:
                return latin[0], _origin_for(candidates_path, origin_map)
            if candidates:
                return candidates[0], _origin_for(candidates_path, origin_map)
        if candidates:
            # A configured family is safer than substituting a central fallback
            # when the role mapping cannot be resolved.  The resulting audit
            # can still report the unresolved role as a limitation.
            return candidates[0], _origin_for(candidates_path, origin_map)
        return fallback, f"default:task-commitments.font.{('cjk' if cjk else 'latin')}"

    cjk = pick("cjk", ("theme.typography.cjk_family", "theme.typography.cjk_fonts", "theme.typography.required_cjk_families"), cjk=True, fallback=DEFAULT_CJK_FAMILY)
    latin = pick("latin", ("theme.typography.latin_family", "theme.typography.latin_fonts"), fallback=DEFAULT_LATIN_FAMILY)
    digits = pick("digits", ("theme.typography.digit_family", "theme.typography.digit_fonts", "theme.typography.numeric_family", "theme.typography.numeric_fonts"), fallback=latin[0])
    chart = pick("chart", ("theme.typography.chart_family", "theme.typography.chart_fonts"), fallback=latin[0])
    return {"cjk": cjk, "latin": latin, "digits": digits, "chart": chart}


def _point_sizes(config: Mapping[str, Any], origin_map: Any) -> dict[str, tuple[int | float, str]]:
    paths: dict[str, tuple[str, ...]] = {
        "title": ("theme.typography.title_minimum_pt", "theme.typography.minimum_title_pt", "theme.typography.title_min_pt"),
        "body": ("theme.typography.body_minimum_pt", "theme.typography.minimum_audience_text_pt"),
        "chart": ("theme.typography.minimum_chart_text_pt", "theme.typography.chart_text_minimum_pt"),
        "footnote": ("theme.typography.footnote_minimum_pt", "theme.typography.minimum_footnote_text_pt", "theme.typography.footnote_min_pt"),
        "page_number": ("theme.typography.page_number_minimum_pt", "theme.typography.minimum_page_number_pt", "theme.typography.page_number_min_pt", "theme.typography.footer_minimum_pt"),
    }
    result: dict[str, tuple[int | float, str]] = {}
    for role, candidates in paths.items():
        found, value, path = _first_value(config, candidates)
        if found and isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 1:
            number: int | float = int(value) if int(value) == value else float(value)
            result[role] = (number, _origin_for(path, origin_map))
        else:
            result[role] = (DEFAULT_POINT_SIZES[role], f"default:task-commitments.point-size.{role}")
    return result


def _has_quantitative_chart(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key).casefold().replace("_", "-")
            if key_text in {"requires-chart-units", "quantitative-chart", "quantitative-chart-contract"}:
                if child is True or (isinstance(child, Mapping) and bool(child)):
                    return True
                if isinstance(child, str) and child.strip().casefold() not in {"false", "none", "no"}:
                    return True
            if key_text in {"chart", "charts", "data-chart-contract", "quantitative-execution-contract"} and child not in (None, False, [], ""):
                return True
            if key_text == "dominant-medium" and str(child).casefold() in {"data-chart", "chart", "scatterplot"}:
                return True
            if _has_quantitative_chart(child):
                return True
        return False
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_has_quantitative_chart(item) for item in value)
    if isinstance(value, str):
        text = value.casefold()
        return any(token in text for token in ("data-chart", "quantitative chart", "图表", "散点图")) and any(
            token in text for token in ("unit", "单位", "metric", "数值", "quantitative", "数据")
        )
    return False


def _explicit_bool(draft: Mapping[str, Any], paths: Sequence[tuple[str, ...]]) -> bool | None:
    for path in paths:
        current: Any = draft
        for part in path:
            if not isinstance(current, Mapping) or part not in current:
                current = None
                break
            current = current[part]
        if isinstance(current, bool):
            return current
    return None


def _page_number_policy(
    draft: Mapping[str, Any], config: Mapping[str, Any], origin_map: Any
) -> tuple[dict[str, Any], str]:
    """Resolve page-number commitments from task, config, then central defaults.

    ``inherit`` is accepted only when the task/config supplies a concrete
    template/master policy reference.  Otherwise the central values below are
    used explicitly so an unknown master cannot hide an untestable promise.
    """

    policy: dict[str, Any] = {}
    source = "default:task-commitments.page-number"
    draft_policy = draft.get("page_number_policy")
    if not isinstance(draft_policy, Mapping):
        draft_policy = draft.get("page_numbers")
    if isinstance(draft.get("page_number_policy"), Mapping):
        policy.update(dict(draft_policy))
        source = "acceptance:page_number_policy"
    elif isinstance(draft.get("page_numbers"), Mapping):
        policy.update(dict(draft_policy))
        source = "acceptance:page_numbers"
    else:
        found, value, path = _first_value(
            config,
            (
                *PAGE_NUMBER_POLICY_PATHS,
            ),
        )
        if found and isinstance(value, Mapping):
            policy.update(dict(value))
            source = _origin_for(path, origin_map)

    def field(name: str, aliases: Sequence[str] = ()) -> Any:
        for key in (name, *aliases):
            if key in policy and policy[key] is not None:
                return policy[key]
        # Read individual fields from central config when a policy object is
        # not available.  This lets a merged config bind page settings without
        # requiring a new top-level acceptance field.
        paths = tuple(f"{base}.{name}" for base in PAGE_NUMBER_POLICY_PATHS) + tuple(
            f"page_number_policy.{alias}" for alias in aliases
        )
        found, value, _ = _first_value(config, paths)
        return value if found else None

    required = field("required", ("enabled",))
    if not isinstance(required, bool):
        required = _explicit_bool(
            draft,
            (("page_numbers_required",), ("page_numbers", "required"), ("page_number_policy", "required")),
        )
    if not isinstance(required, bool):
        required = bool(DEFAULT_PAGE_NUMBER_POLICY["required"])

    template_ref = field("template_policy", ("template", "master", "inherit_from", "master_path"))
    if isinstance(template_ref, Mapping):
        template_ref = template_ref.get("path") or template_ref.get("id") or template_ref.get("uri")
    if not isinstance(template_ref, str) or not template_ref.strip():
        theme = config.get("theme") if isinstance(config.get("theme"), Mapping) else {}
        template_ref = theme.get("master_path") if isinstance(theme, Mapping) else None
    if isinstance(template_ref, str) and not template_ref.strip():
        template_ref = None

    position = field("position", ("footer_position",))
    if isinstance(position, str) and position.strip().casefold() in {"inherit", "inherited", "master"}:
        if isinstance(template_ref, str) and template_ref.strip():
            position = f"inherited:{template_ref.strip()}"
        else:
            position = DEFAULT_PAGE_NUMBER_POLICY["position"]
    if not isinstance(position, str) or not position.strip():
        position = DEFAULT_PAGE_NUMBER_POLICY["position"]

    scope = field("scope", ("slide_scope", "applies_to"))
    if isinstance(scope, str) and scope.strip().casefold() in {"inherit", "inherited", "master"}:
        if isinstance(template_ref, str) and template_ref.strip():
            scope = f"inherited:{template_ref.strip()}"
        else:
            scope = DEFAULT_PAGE_NUMBER_POLICY["scope"]
    if not isinstance(scope, str) or not scope.strip():
        scope = DEFAULT_PAGE_NUMBER_POLICY["scope"]
    start = field("start", ("start_number", "sequence_start"))
    if isinstance(start, bool) or not isinstance(start, (int, float)) or start < 0:
        start = DEFAULT_PAGE_NUMBER_POLICY["start"]
    elif int(start) == start:
        start = int(start)
    cover_counting = field("cover_counting", ("include_cover",))
    if not isinstance(cover_counting, bool):
        cover_counting = DEFAULT_PAGE_NUMBER_POLICY["cover_counting"]
    mechanism = field("mechanism", ("field", "mode"))
    if isinstance(mechanism, str) and mechanism.strip().casefold() in {"inherit", "inherited", "master"}:
        if isinstance(template_ref, str) and template_ref.strip():
            mechanism = f"inherited:{template_ref.strip()}"
        else:
            mechanism = DEFAULT_PAGE_NUMBER_POLICY["mechanism"]
    if not isinstance(mechanism, str) or not mechanism.strip():
        mechanism = DEFAULT_PAGE_NUMBER_POLICY["mechanism"]

    # Preserve the actual source for an explicit task policy; otherwise use a
    # field-level origin when the merged config exposes it.
    if source.startswith("default:"):
        for path in PAGE_NUMBER_POLICY_PATHS:
            found, _, _ = _first_value(config, (path,))
            if found:
                source = _origin_for(path, origin_map)
                break
        if source.startswith("default:"):
            for path in tuple(f"{base}.required" for base in PAGE_NUMBER_POLICY_PATHS):
                found, _, _ = _first_value(config, (path,))
                if found:
                    source = _origin_for(path, origin_map)
                    break

    return (
        {
            "required": required,
            "position": position,
            "scope": scope,
            "start": start,
            "cover_counting": cover_counting,
            "mechanism": mechanism,
        },
        source,
    )


def _is_explicit_requirement(existing: Mapping[str, Any]) -> bool:
    """Recognize user/confirmed values that must survive a config revision."""

    source = existing.get("source")
    if not isinstance(source, str) or not source.strip():
        # Generated commitments always carry a source.  An unmarked existing
        # requirement is therefore treated as an explicit caller value.
        return True
    value = source.casefold().strip()
    return value == "user" or value.startswith("user:") or "user-request" in value or value.startswith("confirmed:")


def _fill_requirement(
    existing: Mapping[str, Any], defaults: Mapping[str, Any], *, refresh_generated: bool = False
) -> dict[str, Any]:
    result = dict(existing)
    for key, value in defaults.items():
        if refresh_generated and key in {"expected", "source", "verification_method", "statement"}:
            result[key] = deepcopy(value)
        elif key not in result:
            result[key] = deepcopy(value)
    if "classification" not in result:
        result["classification"] = "hard"
    if "blocking" not in result:
        result["blocking"] = False
    return result


def _commitment(default: Mapping[str, Any], *, expected: Any, source: str) -> dict[str, Any]:
    return {
        "requirement_id": str(default["requirement_id"]),
        "category": str(default["category"]),
        "statement": str(default["statement"]),
        "owner_stage": str(default["owner_stage"]),
        "commitment_kind": str(default["kind"]),
        "expected": deepcopy(expected),
        "source": source,
        "classification": "hard",
        "verification_method": str(default["verification_method"]),
        "blocking": False,
    }


def enrich_task_acceptance(
    draft: Mapping[str, Any],
    config: Mapping[str, Any],
    origin_map: Any = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return ``(enriched_draft, display_brief)``.

    Existing task/user values are copied and never overwritten.  Defaults are
    marked as `hard` implementation commitments with `blocking=False`; this
    preserves the distinction between a deterministic miss and a release gate.
    ``origin_map`` is optional runtime evidence.  Without it, this function
    labels a value as `config:` or `default:` and never claims it came from the
    user.
    """

    result = _as_mapping(draft, "draft")
    config_value = _as_mapping(config, "config")
    config_value = _config_root(config_value)
    requirements_raw = result.get("requirements", [])
    if not isinstance(requirements_raw, list):
        raise TaskCommitmentError("draft.requirements must be an array")
    requirements: list[dict[str, Any]] = []
    for index, item in enumerate(requirements_raw):
        if not isinstance(item, Mapping):
            raise TaskCommitmentError(f"draft.requirements[{index}] must be an object")
        requirements.append(dict(item))

    # Complete the existing contract's small typography policy without adding
    # narrative quotas or a second visual-configuration path.
    typography_policy = result.get("typography_policy", {})
    if typography_policy is None:
        typography_policy = {}
    if not isinstance(typography_policy, Mapping):
        raise TaskCommitmentError("draft.typography_policy must be an object")
    typography_policy = dict(typography_policy)
    typography_policy.setdefault("mode", "configured-family")
    typography_policy.setdefault("required_cjk_families", [])
    typography_policy.setdefault("exceptions", [])
    if not isinstance(typography_policy["required_cjk_families"], list):
        raise TaskCommitmentError("draft.typography_policy.required_cjk_families must be an array")
    fonts = _font_roles(config_value, origin_map)
    if not typography_policy["required_cjk_families"]:
        typography_policy["required_cjk_families"] = [fonts["cjk"][0]]
    else:
        # The task acceptance policy is already a resolved task value.  It
        # outranks a generic config font candidate, including when a personal
        # or user-provided family is not present in the public config.
        explicit_cjk = _string_list(typography_policy["required_cjk_families"])
        if explicit_cjk and explicit_cjk[0] != fonts["cjk"][0]:
            fonts["cjk"] = (
                explicit_cjk[0],
                _origin_for(
                    "typography_policy.required_cjk_families",
                    origin_map,
                    "acceptance:typography_policy.required_cjk_families",
                ),
            )
    result["typography_policy"] = typography_policy

    release_conditions = result.get("release_conditions", [])
    if release_conditions is None:
        release_conditions = []
    if not isinstance(release_conditions, list):
        raise TaskCommitmentError("draft.release_conditions must be an array")
    # Keep explicit no-delivery conditions structured and user-bound.  Empty
    # is the default; hard/soft classification alone never creates one.
    result["release_conditions"] = [deepcopy(item) for item in release_conditions]

    cover_policy = result.get("cover_policy", {})
    if cover_policy is None:
        cover_policy = {}
    if not isinstance(cover_policy, Mapping):
        raise TaskCommitmentError("draft.cover_policy must be an object")
    cover_policy = dict(cover_policy)
    mode = cover_policy.get("mode")
    if mode is None:
        mode = "not-applicable" if cover_policy.get("cover_required") is False and cover_policy.get("closing_required") is False else DEFAULT_COVER_MODE
        cover_policy["mode"] = mode
    cover_policy.setdefault("conclusion_allowed_roles", list(DEFAULT_CONCLUSION_ROLES))
    default_cover = mode != "not-applicable"
    cover_policy.setdefault("cover_required", default_cover)
    # Cover and closing are independent commitments.  A not-applicable cover
    # mode does not silently remove the closing synthesis/action page.
    cover_policy.setdefault("closing_required", True)
    result["cover_policy"] = cover_policy

    page_policy, page_policy_source = _page_number_policy(result, config_value, origin_map)
    page_number_required = bool(page_policy["required"])

    sizes = _point_sizes(config_value, origin_map)
    chart_applicable = _has_quantitative_chart(result)
    if not chart_applicable:
        chart_applicable = _has_quantitative_chart(config_value.get("task", {}))

    expected_by_kind: dict[str, Any] = {
        "font-cjk": fonts["cjk"][0],
        "font-latin": fonts["latin"][0],
        "font-digits": fonts["digits"][0],
        "font-chart": {
            "cjk": fonts["cjk"][0],
            "latin": fonts["chart"][0],
            "digits": fonts["digits"][0],
            "role_priority": "language-role family before generic chart family",
        },
        "size-title": sizes["title"][0],
        "size-body": sizes["body"][0],
        "size-chart": sizes["chart"][0],
        "size-footnote": sizes["footnote"][0],
        "size-page-number": sizes["page_number"][0],
        "cover": bool(cover_policy["cover_required"]),
        "closing": bool(cover_policy["closing_required"]),
        "page-number": page_policy,
        "chart-unit": "metric unit or an explicit unitless declaration when a quantitative chart is present; otherwise not-applicable",
    }
    source_by_kind: dict[str, str] = {
        "font-cjk": fonts["cjk"][1],
        "font-latin": fonts["latin"][1],
        "font-digits": fonts["digits"][1],
        "font-chart": (
            f"cjk:{fonts['cjk'][1]};latin:{fonts['chart'][1]};digits:{fonts['digits'][1]}"
        ),
        "size-title": sizes["title"][1],
        "size-body": sizes["body"][1],
        "size-chart": sizes["chart"][1],
        "size-footnote": sizes["footnote"][1],
        "size-page-number": sizes["page_number"][1],
        "cover": _origin_for("cover_policy.cover_required", origin_map, "default:task-commitments.cover-policy"),
        "closing": _origin_for("cover_policy.closing_required", origin_map, "default:task-commitments.cover-policy"),
        "page-number": page_policy_source,
        "chart-unit": "default:task-commitments.quantitative-chart-unit",
    }

    added: list[str] = []
    enriched: list[str] = []
    skipped: list[dict[str, str]] = []
    if not chart_applicable:
        skipped.append({"kind": "chart-unit", "reason": "no quantitative chart signal; rule remains not-applicable unless a chart is added"})
    for spec in _DEFAULT_SPECS:
        kind = str(spec["kind"])
        defaults = _commitment(spec, expected=expected_by_kind[kind], source=source_by_kind[kind])
        found_index: int | None = None
        for index, existing in enumerate(requirements):
            if (
                existing.get("requirement_id") == defaults["requirement_id"]
                or existing.get("commitment_kind") == kind
            ):
                found_index = index
                break
        if found_index is None:
            requirements.append(defaults)
            added.append(defaults["requirement_id"])
        else:
            existing = requirements[found_index]
            refresh_generated = (
                existing.get("requirement_id") == defaults["requirement_id"]
                and not _is_explicit_requirement(existing)
            )
            requirements[found_index] = _fill_requirement(
                existing, defaults, refresh_generated=refresh_generated
            )
            enriched.append(str(requirements[found_index].get("requirement_id", defaults["requirement_id"])))

    result["requirements"] = requirements

    commitments = [
        {
            key: deepcopy(item.get(key))
            for key in ("requirement_id", "statement", "expected", "source", "classification", "blocking", "verification_method", "commitment_kind")
            if key in item
        }
        for item in requirements
        if isinstance(item, Mapping) and (item.get("requirement_id") in set(added) or item.get("requirement_id") in set(enriched))
    ]
    lines = [
        "Central commitments are implementation checks; hard classification does not set a release block.",
        "Source precedence is user request > saved personal layer > default; an absent origin map is reported as config/default, never as user.",
        "Quality findings, optional knowledge gaps and deferred target checks remain reportable; binding or evidence-integrity failures affect verified publication.",
    ]
    for item in commitments:
        lines.append(
            f"{item['requirement_id']}: expected {item.get('expected')!r}; source {item.get('source', 'unspecified')}; "
            f"classification {item.get('classification', 'unspecified')}; blocking {item.get('blocking', 'unspecified')}."
        )

    brief = {
        "contract": "io.clayz.presentation.task-commitments/1.0",
        "source_precedence": ["user", "personal", "default"],
        "added_requirement_ids": added,
        "enriched_requirement_ids": enriched,
        "skipped": skipped,
        "commitments": commitments,
        "lines": lines,
        "text": "\n".join(lines),
        "delivery_policy": {
            "quality_findings_default": "deliver-with-findings",
            "optional_library_unavailable": "continue-and-disclose",
            "target_application_not_executed": "defer-and-disclose",
            "binding_or_evidence_integrity_failure": "block-verified-pair",
            "explicit_user_no_delivery_condition": "honor-as-release-condition",
        },
        "chart_unit_rule": "conditional-on-quantitative-chart; not-applicable when no quantitative chart exists",
        "chart_unit_applicable": chart_applicable,
        "release_conditions": deepcopy(release_conditions),
    }
    return result, brief


__all__ = [
    "CONTRACT",
    "DEFAULT_POINT_SIZES",
    "DEFAULT_PAGE_NUMBER_POLICY",
    "PAGE_NUMBER_POLICY_PATHS",
    "TaskCommitmentError",
    "enrich_task_acceptance",
]
