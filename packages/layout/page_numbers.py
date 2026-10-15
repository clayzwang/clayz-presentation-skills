"""Plan visible page fields separately from pages counted in the sequence.

Optional authoring support for the configured body-and-closing policy. Callers
still create native fields and check geometry, fonts and the reopened deck.
"""
from dataclasses import dataclass
from typing import Mapping, Sequence


@dataclass(frozen=True)
class PageNumberDecision:
    physical_page: int
    narrative_role: str
    counted: bool
    sequence_number: int | None
    visible_number: int | None


def plan_page_numbers(
    narrative_roles: Sequence[str], policy: Mapping[str, object]
) -> tuple[PageNumberDecision, ...]:
    """Keep cover counting independent from visibility; reject unknown scope.

    For start=1, a counted cover makes the first body page 2; an uncounted
    cover makes it 1. The cover has no visible field under body-and-closing.
    Disabling numbering suppresses fields while retaining count decisions.
    """
    roles = tuple(narrative_roles)
    if any(role not in {"cover", "body", "closing"} for role in roles):
        raise ValueError("Explicit cover/body/closing narrative roles required")
    if policy.get("scope") != "body-and-closing":
        raise ValueError("Unsupported page-number scope; do not infer visibility")
    required = policy.get("required")
    cover_counting = policy.get("cover_counting")
    start = policy.get("start")
    if type(required) is not bool or type(cover_counting) is not bool:
        raise ValueError("required and cover_counting must be booleans")
    if type(start) is not int or start < 1:
        raise ValueError("start must be a positive integer")
    next_number = start
    result = []
    for physical_page, role in enumerate(roles, start=1):
        counted = role != "cover" or cover_counting
        number = next_number if counted else None
        if counted:
            next_number += 1
        visible = number if required and role in {"body", "closing"} else None
        result.append(PageNumberDecision(physical_page, role, counted, number, visible))
    return tuple(result)
