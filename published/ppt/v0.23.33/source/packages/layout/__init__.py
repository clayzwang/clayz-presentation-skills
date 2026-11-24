# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Renderer-neutral layout contracts, compilation, and coordinate solving."""

from __future__ import annotations

import sys
from pathlib import Path

if __package__ in {None, ""}:
    ROOT = Path(__file__).resolve().parents[2]
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))

from packages.layout.layout_contract import (
    LAYOUT_COMPILATION_CONTRACT,
    LAYOUT_CONTRACT_CONTRACT,
    LAYOUT_CONTRACT_REQUEST_CONTRACT,
    LAYOUT_CONTRACT_RESOLUTION_CONTRACT,
    LayoutContractError,
    compile_layout_contract,
    resolve_layout_contract,
    validate_layout_contract,
    validate_layout_contract_instance,
    validate_layout_contract_request,
)
from packages.layout.solve_relative_layout import solve, solve_compilation

__all__ = [
    "LAYOUT_COMPILATION_CONTRACT",
    "LAYOUT_CONTRACT_CONTRACT",
    "LAYOUT_CONTRACT_REQUEST_CONTRACT",
    "LAYOUT_CONTRACT_RESOLUTION_CONTRACT",
    "LayoutContractError",
    "compile_layout_contract",
    "resolve_layout_contract",
    "solve",
    "solve_compilation",
    "validate_layout_contract",
    "validate_layout_contract_instance",
    "validate_layout_contract_request",
]
