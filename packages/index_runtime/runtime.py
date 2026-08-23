# SPDX-FileCopyrightText: 2026 clayz
# SPDX-License-Identifier: Apache-2.0
"""Compatibility imports for the index-native retrieval runtime."""

from .constants import INDEX_CONTRACT, RECEIPT_CONTRACT, REQUEST_CONTRACT, IndexRuntimeError
from .io import read_json, write_json
from .provider import IndexProvider
from .retrieval import CompositeIndex
from .utils import tokenize
from .validation import validate_record, validate_request

__all__ = [
    "INDEX_CONTRACT",
    "RECEIPT_CONTRACT",
    "REQUEST_CONTRACT",
    "CompositeIndex",
    "IndexProvider",
    "IndexRuntimeError",
    "read_json",
    "tokenize",
    "validate_record",
    "validate_request",
    "write_json",
]
