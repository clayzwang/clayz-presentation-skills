# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Compatibility imports for the index-native retrieval runtime."""

from .capability import CAPABILITY_RESOLUTION_CONTRACT, mandatory_core, resolve_capabilities
from .constants import INDEX_CONTRACT, RECEIPT_CONTRACT, REQUEST_CONTRACT, IndexRuntimeError
from .io import read_json, write_json
from .provider import IndexProvider
from .retrieval import CompositeIndex
from .utils import tokenize
from .validation import validate_record, validate_request

__all__ = [
    "CAPABILITY_RESOLUTION_CONTRACT",
    "INDEX_CONTRACT",
    "RECEIPT_CONTRACT",
    "REQUEST_CONTRACT",
    "CompositeIndex",
    "IndexProvider",
    "IndexRuntimeError",
    "mandatory_core",
    "read_json",
    "resolve_capabilities",
    "tokenize",
    "validate_record",
    "validate_request",
    "write_json",
]
